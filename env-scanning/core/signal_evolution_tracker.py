#!/usr/bin/env python3
"""
Signal Evolution Tracker — Cross-Day Signal Matching & Timeline Mapping
========================================================================
Tracks how signals evolve across daily scans by matching today's signals
against historical "threads" in the evolution index. Produces evolution
state classifications (NEW, RECURRING, STRENGTHENING, WEAKENING, FADED,
TRANSFORMED) and timeline metrics (velocity, direction, expansion).

Pipeline Position (Step 3.1b):
    Step 3.1a: Create database backup (snapshot)
    → signal_evolution_tracker.py (THIS)  ← reads DB (pre-update) + today's signals
    Step 3.1c: Update signals database
    Step 3.1d: Verify database integrity

Key Design Decisions:
    - Does NOT depend on embedding_deduplicator.py (C2 fix: self-contained cosine sim)
    - Runs BEFORE DB update (C1 fix: avoids self-matching)
    - Evolution index is a separate persistent file (not inside database.json)
    - Atomic backup/restore for evolution-index.json

Design Principle (v2.3.1 — SOT Direct Reading):
    All tunable thresholds (title_similarity, semantic_similarity, fade_days,
    strengthening_delta, weakening_delta, max_thread_age_days, etc.) are read
    DIRECTLY from workflow-registry.yaml (SOT) by Python — not passed by the
    LLM orchestrator. This mirrors the pattern established by temporal_anchor.py
    in v2.2.1 ("계산은 Python이, 판단은 LLM이.").

Usage (CLI):
    python3 env-scanning/core/signal_evolution_tracker.py track \\
        --registry env-scanning/config/workflow-registry.yaml \\
        --input classified-signals-{date}.json \\
        --db signals/database.json \\
        --index signals/evolution-index.json \\
        --output analysis/evolution/evolution-map-{date}.json

Usage (importable):
    from core.signal_evolution_tracker import track_signal_evolution, load_evolution_config

Exit codes:
    0 = SUCCESS
    1 = ERROR (missing files, invalid data)
"""

import argparse
import copy
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("signal_evolution_tracker")

VERSION = "1.3.0"


# ---------------------------------------------------------------------------
# SOT Direct Reading (v2.3.1: 할루시네이션 원천봉쇄)
# ---------------------------------------------------------------------------
# Design Principle (from temporal_anchor.py):
#     "계산은 Python이, 판단은 LLM이."
#     All tunable thresholds are read DIRECTLY from the SOT by Python.
#     The LLM orchestrator passes only the --registry path, never numeric values.

def load_evolution_config(registry_path: str) -> Dict[str, Any]:
    """Load signal_evolution configuration directly from SOT (workflow-registry.yaml).

    This function is the SINGLE PROGRAMMATIC AUTHORITY for all evolution
    thresholds.  It mirrors the pattern established by temporal_anchor.py
    for temporal parameters — Python reads SOT directly, eliminating any
    possibility of LLM hallucination in threshold propagation.

    Args:
        registry_path: Path to workflow-registry.yaml

    Returns:
        Dict with keys: matching, lifecycle, state_detection, cross_workflow_correlation, enabled
    """
    reg_path = Path(registry_path)
    if not reg_path.exists():
        raise FileNotFoundError(f"SOT registry not found: {registry_path}")

    with open(reg_path, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    sig_evo = registry.get("system", {}).get("signal_evolution", {})
    if not sig_evo:
        logger.warning("system.signal_evolution section missing from SOT — using defaults")
        return _default_evolution_config()

    return {
        "enabled": sig_evo.get("enabled", False),
        "matching": sig_evo.get("matching", {}),
        "lifecycle": sig_evo.get("lifecycle", {}),
        "state_detection": sig_evo.get("state_detection", {}),
        "cross_workflow_correlation": sig_evo.get("cross_workflow_correlation", {}),
    }


def _default_evolution_config() -> Dict[str, Any]:
    """Hardcoded fallback config — used ONLY when SOT is unavailable (e.g. testing)."""
    return {
        "enabled": False,
        "matching": {
            "title_similarity_threshold": 0.80,
            "semantic_similarity_threshold": 0.70,
            "high_confidence_threshold": 0.85,
        },
        "lifecycle": {
            "fade_threshold_days": 3,
            "max_thread_age_days": 90,
            "min_appearances_for_velocity": 2,
        },
        "state_detection": {
            "strengthening_psst_delta": 5,
            "weakening_psst_delta": -5,
        },
        "cross_workflow_correlation": {
            "enabled": False,
            "matching": {
                "title_similarity_threshold": 0.75,
                "semantic_similarity_threshold": 0.65,
                "high_confidence_threshold": 0.80,
                "category_filter_enabled": True,
            },
        },
    }

# ---------------------------------------------------------------------------
# Empty Evolution Map (for graceful degradation when disabled)
# ---------------------------------------------------------------------------

def _empty_evolution_map(workflow_name: str, scan_date: str, reason: str = "disabled") -> dict:
    """Return a valid but empty evolution-map dict.

    Used when signal_evolution.enabled=false or when no signals to process.
    Ensures downstream consumers (statistics engine, injector) always receive
    a structurally valid evolution-map.
    """
    return {
        "tracker_version": VERSION,
        "workflow": workflow_name,
        "scan_date": scan_date,
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config_source": reason,
        "config_used": {},
        "summary": {
            "total_signals_today": 0,
            "new_signals": 0,
            "recurring_signals": 0,
            "strengthening_signals": 0,
            "weakening_signals": 0,
            "transformed_signals": 0,
            "faded_threads": 0,
            "active_threads": 0,
        },
        "evolution_entries": [],
        "faded_threads": [],
        "new_threads_created": [],
    }


# ---------------------------------------------------------------------------
# Evolution States
# ---------------------------------------------------------------------------

EVOLUTION_STATES = {
    "NEW": "신규",
    "RECURRING": "반복 등장",
    "STRENGTHENING": "강화",
    "WEAKENING": "약화",
    "FADED": "소멸",
    "TRANSFORMED": "변형",
}

# Direction enum
DIRECTIONS = ("ACCELERATING", "STABLE", "DECELERATING", "VOLATILE")

# ---------------------------------------------------------------------------
# Self-contained cosine similarity (C2 fix: no deduplicator dependency)
# ---------------------------------------------------------------------------

def _cosine_similarity(vec_a: list, vec_b: list) -> float:
    """Compute cosine similarity between two vectors without numpy dependency.

    Uses pure Python to avoid requiring numpy as a hard dependency.
    For the small vectors used in keyword overlap (typically 10-50 dims),
    this is fast enough.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a < 1e-8 or norm_b < 1e-8:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Title Similarity (Jaro-Winkler)
# ---------------------------------------------------------------------------

def _jaro_similarity(s1: str, s2: str) -> float:
    """Compute Jaro similarity between two strings."""
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 0:
        match_distance = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3
    return jaro


def _jaro_winkler_similarity(s1: str, s2: str, p: float = 0.1) -> float:
    """Compute Jaro-Winkler similarity. Higher values = more similar."""
    jaro = _jaro_similarity(s1, s2)
    # Count common prefix (up to 4 chars)
    prefix_len = 0
    for i in range(min(len(s1), len(s2), 4)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break
    return jaro + prefix_len * p * (1 - jaro)


# ---------------------------------------------------------------------------
# Keyword-based Semantic Similarity
# ---------------------------------------------------------------------------

def _extract_keywords(signal: dict) -> set:
    """Extract keywords from a signal for semantic comparison."""
    keywords = set()
    # From explicit keywords field
    content = signal.get("content", {})
    if isinstance(content, dict):
        for kw in content.get("keywords", []):
            keywords.add(kw.lower().strip())
    # From title words (basic tokenization)
    title = signal.get("title", "")
    for word in title.split():
        word = word.strip(".,;:!?()[]{}\"'").lower()
        if len(word) > 2:
            keywords.add(word)
    return keywords


def _keyword_vector_similarity(kw_set_a: set, kw_set_b: set) -> float:
    """Compute Jaccard similarity between two keyword sets as a proxy for semantic similarity."""
    if not kw_set_a or not kw_set_b:
        return 0.0
    intersection = kw_set_a & kw_set_b
    union = kw_set_a | kw_set_b
    return len(intersection) / len(union) if union else 0.0


# ---------------------------------------------------------------------------
# Core Matching
# ---------------------------------------------------------------------------

def match_signal_to_threads(
    signal: dict,
    evolution_index: dict,
    title_threshold: float = 0.80,
    semantic_threshold: float = 0.70,
    high_confidence_threshold: float = 0.85,
) -> Optional[tuple]:
    """Match a single signal to existing threads via 3-stage cascade.

    All thresholds are sourced from SOT via load_evolution_config().
    CLI overrides are accepted for testing only.

    Args:
        signal: Today's classified signal dict
        evolution_index: Current evolution index
        title_threshold: SOT matching.title_similarity_threshold
        semantic_threshold: SOT matching.semantic_similarity_threshold
        high_confidence_threshold: SOT matching.high_confidence_threshold
            (combined score threshold for HIGH confidence)

    Returns:
        (thread_id, confidence) tuple or None if no match.
        confidence: "HIGH" if combined >= high_confidence_threshold, else "MEDIUM".
    """
    signal_title = signal.get("title", "")
    signal_keywords = _extract_keywords(signal)
    threads = evolution_index.get("threads", {})

    best_match = None
    best_combined_score = 0.0

    for thread_id, thread in threads.items():
        if thread.get("state") == "FADED":
            continue  # Don't match against faded threads

        # Stage 1: Title similarity (Jaro-Winkler)
        title_sim = _jaro_winkler_similarity(
            signal_title.lower(),
            thread.get("canonical_title", "").lower(),
        )

        # Stage 2: Keyword/semantic similarity
        thread_keywords = set(kw.lower() for kw in thread.get("keywords", []))
        semantic_sim = _keyword_vector_similarity(signal_keywords, thread_keywords)

        # Stage 3: Confidence decision (thresholds from SOT)
        if title_sim >= title_threshold and semantic_sim >= semantic_threshold:
            combined = title_sim * 0.5 + semantic_sim * 0.5
            confidence = "HIGH" if combined >= high_confidence_threshold else "MEDIUM"
        elif semantic_sim >= semantic_threshold:
            confidence = "MEDIUM"
            combined = semantic_sim * 0.7 + title_sim * 0.3
        else:
            continue

        if combined > best_combined_score:
            best_combined_score = combined
            best_match = (thread_id, confidence)

    return best_match


# ---------------------------------------------------------------------------
# State Detection
# ---------------------------------------------------------------------------

def compute_thread_state(
    thread: dict,
    new_signal: dict,
    confidence: str,
    strengthening_delta: int = 5,
    weakening_delta: int = -5,
) -> str:
    """Determine the evolution state for a matched signal.

    Args:
        thread: Existing thread from evolution index
        new_signal: Today's classified signal
        confidence: "HIGH" or "MEDIUM" from matching
        strengthening_delta: pSST delta threshold for STRENGTHENING
        weakening_delta: pSST delta threshold for WEAKENING

    Returns:
        One of: "RECURRING", "STRENGTHENING", "WEAKENING", "TRANSFORMED"
    """
    appearances = thread.get("appearances", [])
    if not appearances:
        return "RECURRING"

    last_appearance = appearances[-1]
    prev_psst = last_appearance.get("psst_score", 0)
    curr_psst = new_signal.get("psst_score", 0)
    if curr_psst is None:
        curr_psst = 0
    if prev_psst is None:
        prev_psst = 0

    delta = curr_psst - prev_psst

    # TRANSFORMED: medium confidence + category change
    if confidence == "MEDIUM":
        prev_category = thread.get("primary_category", "")
        curr_category = new_signal.get("final_category", new_signal.get("preliminary_category", ""))
        if prev_category and curr_category and prev_category != curr_category:
            return "TRANSFORMED"

    # STRENGTHENING: pSST increase > threshold OR source count increase OR new STEEPs domain
    new_categories = set(thread.get("all_categories", []))
    curr_category = new_signal.get("final_category", new_signal.get("preliminary_category", ""))
    categories_expanded = curr_category and curr_category not in new_categories

    if delta > strengthening_delta or categories_expanded:
        return "STRENGTHENING"

    # WEAKENING: pSST decrease > threshold
    if delta < weakening_delta:
        return "WEAKENING"

    return "RECURRING"


def compute_evolution_metrics(thread: dict, min_appearances_for_velocity: int = 2) -> dict:
    """Compute velocity, direction, and expansion for a thread.

    Args:
        thread: Thread dict from evolution index
        min_appearances_for_velocity: SOT lifecycle.min_appearances_for_velocity.
            Minimum number of appearances required to compute velocity.
            Below this threshold, velocity is reported as 0.0.

    Returns:
        {"velocity": float, "direction": str, "expansion": float}
    """
    appearances = thread.get("appearances", [])

    # Velocity: linear regression slope of pSST scores over time
    velocity = 0.0
    if len(appearances) >= min_appearances_for_velocity:
        scores = [a.get("psst_score", 0) or 0 for a in appearances]
        n = len(scores)
        x_mean = (n - 1) / 2.0
        y_mean = sum(scores) / n
        numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        if denominator > 0:
            slope = numerator / denominator
            # Normalize to [-1, 1] range (assuming max slope ~ 10 per day)
            velocity = max(-1.0, min(1.0, slope / 10.0))

    # Direction
    if len(appearances) < 2:
        direction = "STABLE"
    elif len(appearances) < 3:
        direction = "ACCELERATING" if velocity > 0.1 else ("DECELERATING" if velocity < -0.1 else "STABLE")
    else:
        # Check last 3 appearances for volatility
        recent_scores = [a.get("psst_score", 0) or 0 for a in appearances[-3:]]
        deltas = [recent_scores[i+1] - recent_scores[i] for i in range(len(recent_scores)-1)]
        if len(deltas) >= 2 and deltas[0] * deltas[1] < 0:
            direction = "VOLATILE"
        elif velocity > 0.1:
            direction = "ACCELERATING"
        elif velocity < -0.1:
            direction = "DECELERATING"
        else:
            direction = "STABLE"

    # Expansion: STEEPs coverage (0.5) + source diversity (0.5)
    all_categories = set(thread.get("all_categories", []))
    steeps_coverage = len(all_categories) / 6.0  # 6 STEEPs categories
    # Source diversity: count unique sources across appearances
    unique_sources = set()
    for a in appearances:
        source = a.get("source", "")
        if source:
            unique_sources.add(source)
    source_diversity = min(1.0, len(unique_sources) / 5.0)  # Normalize to 5 sources max
    expansion = round(steeps_coverage * 0.5 + source_diversity * 0.5, 2)

    return {
        "velocity": round(velocity, 3),
        "direction": direction,
        "expansion": expansion,
    }


def detect_faded_threads(
    evolution_index: dict,
    current_date: str,
    fade_days: int = 3,
    max_thread_age_days: int = 90,
) -> list:
    """Detect threads that should be marked as FADED.

    A thread is faded if EITHER:
    1. Not seen for fade_days consecutive days (SOT lifecycle.fade_threshold_days)
    2. Thread age exceeds max_thread_age_days (SOT lifecycle.max_thread_age_days)

    Returns list of thread_ids that should be marked as FADED.
    """
    from datetime import datetime as dt
    faded = []
    try:
        current = dt.strptime(current_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return faded

    for thread_id, thread in evolution_index.get("threads", {}).items():
        if thread.get("state") == "FADED":
            continue

        # Condition 1: Not seen for fade_days
        last_seen = thread.get("last_seen_date", "")
        try:
            last_dt = dt.strptime(last_seen, "%Y-%m-%d")
            days_since_seen = (current - last_dt).days
            if days_since_seen >= fade_days:
                faded.append(thread_id)
                continue
        except (ValueError, TypeError):
            pass

        # Condition 2: Thread age exceeds max_thread_age_days
        created_date = thread.get("created_date", "")
        try:
            created_dt = dt.strptime(created_date, "%Y-%m-%d")
            thread_age = (current - created_dt).days
            if thread_age > max_thread_age_days:
                faded.append(thread_id)
        except (ValueError, TypeError):
            continue

    return faded


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def track_signal_evolution(
    classified_signals_path: str,
    signals_db_path: str,
    evolution_index_path: str,
    workflow_name: str,
    output_path: Optional[str] = None,
    scan_date: Optional[str] = None,
    registry_path: Optional[str] = None,
    priority_ranked_path: Optional[str] = None,
    title_threshold: Optional[float] = None,
    semantic_threshold: Optional[float] = None,
    high_confidence_threshold: Optional[float] = None,
    fade_days: Optional[int] = None,
    max_thread_age_days: Optional[int] = None,
    min_appearances_for_velocity: Optional[int] = None,
    strengthening_delta: Optional[int] = None,
    weakening_delta: Optional[int] = None,
) -> dict:
    """Main entry: match today's signals to history, produce evolution map + update index.

    Parameter Resolution (priority: CLI override > SOT > hardcoded default):
        1. If registry_path is given, load all thresholds from SOT directly
        2. Explicit non-None parameters override SOT values (for testing only)
        3. If neither SOT nor explicit value, use hardcoded defaults

    Args:
        classified_signals_path: Path to today's classified-signals JSON
        signals_db_path: Path to signals database (pre-update, read-only)
        evolution_index_path: Path to evolution-index.json (read/write)
        workflow_name: e.g. "wf1-general", "wf2-arxiv", "wf3-naver"
        output_path: Optional output path for evolution-map JSON
        scan_date: Override scan date (default: today, YYYY-MM-DD)
        registry_path: Path to workflow-registry.yaml (SOT).
            When provided, all thresholds are read from SOT directly.
        priority_ranked_path: Path to priority-ranked-{date}.json (L3 fix).
            When provided, back-fills psst_score from Step 2.3 output into
            classified signals that lack it.
        title_threshold: Override SOT matching.title_similarity_threshold
        semantic_threshold: Override SOT matching.semantic_similarity_threshold
        high_confidence_threshold: Override SOT matching.high_confidence_threshold
        fade_days: Override SOT lifecycle.fade_threshold_days
        max_thread_age_days: Override SOT lifecycle.max_thread_age_days
        min_appearances_for_velocity: Override SOT lifecycle.min_appearances_for_velocity
        strengthening_delta: Override SOT state_detection.strengthening_psst_delta
        weakening_delta: Override SOT state_detection.weakening_psst_delta

    Returns:
        Evolution map dict
    """
    # ── Resolve parameters from SOT (v2.3.1: 할루시네이션 원천봉쇄) ──
    if registry_path:
        evo_config = load_evolution_config(registry_path)
        logger.info(f"SOT loaded: {registry_path} (signal_evolution.enabled={evo_config['enabled']})")
    else:
        evo_config = _default_evolution_config()
        logger.warning("No --registry provided — using hardcoded defaults (test mode)")

    # Determine scan date early (needed for empty map)
    if not scan_date:
        scan_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── C2 fix: Enforce enabled flag — early exit when explicitly disabled in SOT ──
    # Only enforce when registry_path is explicitly provided (production mode).
    # Without registry (test/default mode), always process for backwards compatibility.
    if registry_path and not evo_config.get("enabled", False):
        logger.info("signal_evolution.enabled=false in SOT — returning empty evolution map")
        empty_map = _empty_evolution_map(workflow_name, scan_date, reason="signal_evolution.enabled=false")
        if output_path:
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(empty_map, f, ensure_ascii=False, indent=2)
            logger.info(f"Empty evolution map written: {output_path}")
        return empty_map

    matching = evo_config.get("matching", {})
    lifecycle = evo_config.get("lifecycle", {})
    state_det = evo_config.get("state_detection", {})

    # Priority: explicit parameter > SOT > hardcoded default
    _title_threshold = title_threshold if title_threshold is not None else matching.get("title_similarity_threshold", 0.80)
    _semantic_threshold = semantic_threshold if semantic_threshold is not None else matching.get("semantic_similarity_threshold", 0.70)
    _high_confidence_threshold = high_confidence_threshold if high_confidence_threshold is not None else matching.get("high_confidence_threshold", 0.85)
    _fade_days = fade_days if fade_days is not None else lifecycle.get("fade_threshold_days", 3)
    _max_thread_age_days = max_thread_age_days if max_thread_age_days is not None else lifecycle.get("max_thread_age_days", 90)
    _min_appearances = min_appearances_for_velocity if min_appearances_for_velocity is not None else lifecycle.get("min_appearances_for_velocity", 2)
    _strengthening_delta = strengthening_delta if strengthening_delta is not None else state_det.get("strengthening_psst_delta", 5)
    _weakening_delta = weakening_delta if weakening_delta is not None else state_det.get("weakening_psst_delta", -5)

    logger.info(
        f"Evolution config: title={_title_threshold}, semantic={_semantic_threshold}, "
        f"high_conf={_high_confidence_threshold}, fade={_fade_days}d, max_age={_max_thread_age_days}d, "
        f"min_vel={_min_appearances}, str_delta={_strengthening_delta}, weak_delta={_weakening_delta}"
    )

    # Derive WF prefix for thread IDs
    wf_prefix = workflow_name.replace("env-scanning/", "").replace("-", "").upper()
    if "wf1" in workflow_name.lower():
        wf_prefix = "WF1"
    elif "wf2" in workflow_name.lower():
        wf_prefix = "WF2"
    elif "wf3" in workflow_name.lower():
        wf_prefix = "WF3"

    # Load classified signals
    cs_path = Path(classified_signals_path)
    if not cs_path.exists():
        raise FileNotFoundError(f"Classified signals not found: {classified_signals_path}")
    with open(cs_path, "r", encoding="utf-8") as f:
        classified_data = json.load(f)
    # Key-variant fallback: direct list (v1.0), "classified_signals" (v2.1.0+), "signals" (v2.0.x), "items" (v1.x)
    if isinstance(classified_data, list):
        signals = classified_data
    else:
        signals = (classified_data.get("classified_signals")
                   or classified_data.get("signals")
                   or classified_data.get("items", []))

    # L1 fix (v1.3.0): Load signals DB for title enrichment
    signals_db_list = []
    db_path_obj = Path(signals_db_path)
    if db_path_obj.exists():
        try:
            with open(db_path_obj, "r", encoding="utf-8") as f:
                db_data = json.load(f)
            signals_db_list = db_data.get("signals", [])
            logger.info(f"Signals DB loaded for title enrichment: {len(signals_db_list)} signals")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not load signals DB for title enrichment: {e}")

    # L3 fix (v1.3.0): Build pSST lookup from priority-ranked file
    psst_lookup = {}
    if priority_ranked_path:
        psst_lookup = _build_psst_lookup(priority_ranked_path)

    # Load or create evolution index
    idx_path = Path(evolution_index_path)
    if idx_path.exists():
        # Atomic backup before modification
        backup_path = idx_path.with_name(f"evolution-index-backup-{scan_date}.json")
        shutil.copy2(str(idx_path), str(backup_path))
        logger.info(f"Evolution index backup: {backup_path}")
        with open(idx_path, "r", encoding="utf-8") as f:
            evolution_index = json.load(f)
    else:
        logger.info(f"No evolution index found, creating new: {evolution_index_path}")
        idx_path.parent.mkdir(parents=True, exist_ok=True)
        evolution_index = {
            "index_version": "1.0.0",
            "workflow": workflow_name,
            "total_threads": 0,
            "active_threads": 0,
            "threads": {},
            "thread_id_counter": 1,
        }

    # Process each signal
    evolution_entries = []
    new_threads_created = []
    counters = {
        "new": 0,
        "recurring": 0,
        "strengthening": 0,
        "weakening": 0,
        "transformed": 0,
    }

    for signal in signals:
        signal_id = signal.get("id", "")
        # L1 fix (v1.3.0): Multi-layer title enrichment — never empty
        signal_title = _enrich_signal_title(signal, signals_db_list)
        signal_category = signal.get("final_category", signal.get("preliminary_category", ""))
        # L3 fix (v1.3.0): pSST backfill from priority-ranked
        signal_psst = signal.get("psst_score")
        if signal_psst is None or signal_psst == 0:
            backfill_psst = psst_lookup.get(signal_id)
            if backfill_psst is not None:
                signal_psst = backfill_psst
                signal["psst_score"] = backfill_psst  # in-place enrichment
            else:
                signal_psst = 0
        if signal_psst is None:
            signal_psst = 0

        # Try to match against existing threads
        match_result = match_signal_to_threads(
            signal, evolution_index,
            title_threshold=_title_threshold,
            semantic_threshold=_semantic_threshold,
            high_confidence_threshold=_high_confidence_threshold,
        )

        if match_result:
            thread_id, confidence = match_result
            thread = evolution_index["threads"][thread_id]

            # Compute state
            state = compute_thread_state(
                thread, signal, confidence,
                strengthening_delta=_strengthening_delta,
                weakening_delta=_weakening_delta,
            )
            counters[state.lower()] = counters.get(state.lower(), 0) + 1

            # Update thread
            thread["last_seen_date"] = scan_date
            thread["state"] = state
            thread["appearance_count"] = thread.get("appearance_count", 0) + 1
            thread["appearances"].append({
                "scan_date": scan_date,
                "signal_id": signal_id,
                "title": signal_title,
                "psst_score": signal_psst,
                "source": signal.get("source", {}).get("name", "") if isinstance(signal.get("source"), dict) else str(signal.get("source", "")),
            })
            # Update categories
            if signal_category and signal_category not in thread.get("all_categories", []):
                thread.setdefault("all_categories", []).append(signal_category)
            # Update keywords
            new_keywords = _extract_keywords(signal)
            existing_keywords = set(thread.get("keywords", []))
            thread["keywords"] = list(existing_keywords | new_keywords)[:20]  # Cap at 20

            # Compute metrics
            metrics = compute_evolution_metrics(thread, min_appearances_for_velocity=_min_appearances)
            thread.setdefault("metrics_history", []).append({
                "date": scan_date,
                **metrics,
            })

            # Build evolution entry
            canonical_title = thread.get("canonical_title", signal_title)
            prev_appearances = thread["appearances"][:-1]
            history_summary = []
            for a in prev_appearances[-5:]:  # Last 5 appearances
                history_summary.append({
                    "date": a.get("scan_date", ""),
                    "title": a.get("title", canonical_title),
                    "psst": a.get("psst_score", 0),
                })
            history_summary.append({
                "date": scan_date,
                "title": signal_title,
                "psst": signal_psst,
            })

            prev_psst = prev_appearances[-1].get("psst_score", 0) if prev_appearances else 0
            delta = signal_psst - (prev_psst or 0)

            evolution_entries.append({
                "signal_id": signal_id,
                "thread_id": thread_id,
                "canonical_title": canonical_title,
                "state": state,
                "state_ko": EVOLUTION_STATES.get(state, state),
                "confidence": confidence,
                "appearance_count": thread.get("appearance_count", 1),
                "metrics": {
                    "velocity": metrics["velocity"],
                    "direction": metrics["direction"],
                    "expansion": metrics["expansion"],
                    "days_tracked": (
                        _days_between(thread.get("created_date", scan_date), scan_date)
                    ),
                    "psst_current": signal_psst,
                    "psst_previous": prev_psst or 0,
                    "psst_delta": f"+{delta}" if delta > 0 else str(delta),
                },
                "thread_history_summary": history_summary,
            })

        else:
            # NEW signal — create a new thread
            counters["new"] += 1
            counter = evolution_index.get("thread_id_counter", 1)
            thread_id = f"THREAD-{wf_prefix}-{counter:03d}"
            evolution_index["thread_id_counter"] = counter + 1

            new_thread = {
                "canonical_title": signal_title,
                "keywords": list(_extract_keywords(signal))[:20],
                "primary_category": signal_category,
                "all_categories": [signal_category] if signal_category else [],
                "created_date": scan_date,
                "last_seen_date": scan_date,
                "state": "NEW",
                "appearance_count": 1,
                "appearances": [{
                    "scan_date": scan_date,
                    "signal_id": signal_id,
                    "title": signal_title,
                    "psst_score": signal_psst,
                    "source": signal.get("source", {}).get("name", "") if isinstance(signal.get("source"), dict) else str(signal.get("source", "")),
                }],
                "metrics_history": [],
            }
            evolution_index["threads"][thread_id] = new_thread
            new_threads_created.append(thread_id)

            evolution_entries.append({
                "signal_id": signal_id,
                "thread_id": thread_id,
                "canonical_title": signal_title,
                "state": "NEW",
                "state_ko": EVOLUTION_STATES["NEW"],
                "confidence": "N/A",
                "appearance_count": 1,
                "metrics": {
                    "velocity": 0.0,
                    "direction": "STABLE",
                    "expansion": 0.0,
                    "days_tracked": 0,
                    "psst_current": signal_psst,
                    "psst_previous": 0,
                    "psst_delta": "0",
                },
                "thread_history_summary": [{"date": scan_date, "title": signal_title, "psst": signal_psst}],
            })

    # Detect faded threads
    faded_thread_ids = detect_faded_threads(
        evolution_index, scan_date,
        fade_days=_fade_days, max_thread_age_days=_max_thread_age_days,
    )
    faded_threads = []
    for thread_id in faded_thread_ids:
        thread = evolution_index["threads"].get(thread_id, {})
        thread["state"] = "FADED"
        faded_threads.append({
            "thread_id": thread_id,
            "canonical_title": thread.get("canonical_title", ""),
            "last_seen_date": thread.get("last_seen_date", ""),
            "appearance_count": thread.get("appearance_count", 0),
        })

    # Update index metadata
    active = sum(1 for t in evolution_index["threads"].values() if t.get("state") != "FADED")
    evolution_index["total_threads"] = len(evolution_index["threads"])
    evolution_index["active_threads"] = active

    # Save updated evolution index (atomic write)
    try:
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump(evolution_index, f, ensure_ascii=False, indent=2)
        # Verify JSON parseable
        with open(idx_path, "r", encoding="utf-8") as f:
            json.load(f)
        logger.info(f"Evolution index updated: {idx_path} ({active} active threads)")
    except Exception as e:
        # Restore from backup
        backup_path = idx_path.with_name(f"evolution-index-backup-{scan_date}.json")
        if backup_path.exists():
            shutil.copy2(str(backup_path), str(idx_path))
            logger.error(f"Index write failed, restored from backup: {e}")
        raise

    # Build evolution map
    total_signals = len(signals)
    evolution_map = {
        "tracker_version": VERSION,
        "workflow": workflow_name,
        "scan_date": scan_date,
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config_source": registry_path or "hardcoded_defaults",
        "config_used": {
            "title_threshold": _title_threshold,
            "semantic_threshold": _semantic_threshold,
            "high_confidence_threshold": _high_confidence_threshold,
            "fade_days": _fade_days,
            "max_thread_age_days": _max_thread_age_days,
            "min_appearances_for_velocity": _min_appearances,
            "strengthening_delta": _strengthening_delta,
            "weakening_delta": _weakening_delta,
        },
        "summary": {
            "total_signals_today": total_signals,
            "new_signals": counters["new"],
            "recurring_signals": counters["recurring"],
            "strengthening_signals": counters["strengthening"],
            "weakening_signals": counters["weakening"],
            "transformed_signals": counters.get("transformed", 0),
            "faded_threads": len(faded_threads),
            "active_threads": active,
        },
        "evolution_entries": evolution_entries,
        "faded_threads": faded_threads,
        "new_threads_created": new_threads_created,
    }

    # Write output
    if output_path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(evolution_map, f, ensure_ascii=False, indent=2)
        logger.info(f"Evolution map written: {output_path}")

    return evolution_map


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_psst_lookup(priority_ranked_path: str) -> Dict[str, float]:
    """Build a {signal_id: psst_score} lookup from a priority-ranked JSON file.

    L3 fix (v1.3.0): classified-signals lack psst_score (computed in Step 2.3),
    but priority-ranked files contain them. This function back-fills scores.

    Args:
        priority_ranked_path: Path to priority-ranked-{date}.json

    Returns:
        Dict mapping signal_id → psst_score. Empty dict on any error.
    """
    try:
        pr_path = Path(priority_ranked_path)
        if not pr_path.exists():
            logger.warning(f"Priority-ranked file not found: {priority_ranked_path}")
            return {}
        with open(pr_path, "r", encoding="utf-8") as f:
            pr_data = json.load(f)
        # priority-ranked files use "ranked_signals" or "signals" array
        signals = pr_data.get("ranked_signals", pr_data.get("signals", []))
        lookup = {}
        for sig in signals:
            sid = sig.get("id", sig.get("signal_id", ""))
            psst = sig.get("psst_score", sig.get("pSST_score"))
            if sid and psst is not None:
                lookup[sid] = psst
        logger.info(f"pSST lookup built: {len(lookup)} entries from {priority_ranked_path}")
        return lookup
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to build pSST lookup from {priority_ranked_path}: {e}")
        return {}


def _enrich_signal_title(signal: dict, signals_db_list: list) -> str:
    """Multi-layer title enrichment for robustness against missing titles.

    L1 fix (v1.3.0): Early classified-signals files (e.g. 02-03) sometimes lack
    a 'title' field. This function ensures canonical_title is never empty.

    Layer 1: Use signal's own title if present and non-empty.
    Layer 2: Look up the signal ID in the signals database (already loaded).
    Layer 3: Fall back to signal ID (better than empty string).
    """
    # Layer 1: signal's own title
    title = signal.get("title", "").strip()
    if title:
        return title

    # Layer 2: look up by signal ID in DB
    signal_id = signal.get("id", "")
    if signal_id and signals_db_list:
        for db_signal in signals_db_list:
            if db_signal.get("id") == signal_id:
                db_title = db_signal.get("title", "").strip()
                if db_title:
                    logger.debug(f"Title enriched from DB for {signal_id}: {db_title[:50]}")
                    return db_title
                break

    # Layer 3: use signal ID as fallback
    if signal_id:
        logger.debug(f"Title fallback to signal ID: {signal_id}")
        return signal_id

    return "untitled"


def _days_between(date_str_a: str, date_str_b: str) -> int:
    """Compute days between two YYYY-MM-DD date strings."""
    try:
        a = datetime.strptime(date_str_a, "%Y-%m-%d")
        b = datetime.strptime(date_str_b, "%Y-%m-%d")
        return abs((b - a).days)
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Cross-Workflow Thread Correlation (Integration Step Only)
# ---------------------------------------------------------------------------

def cross_correlate_threads(
    wf1_index_path: str,
    wf2_index_path: str,
    wf3_index_path: str,
    output_path: str,
    registry_path: Optional[str] = None,
    title_threshold: Optional[float] = None,
    semantic_threshold: Optional[float] = None,
) -> dict:
    """Cross-match threads across WF1/WF2/WF3 evolution indices.

    Only runs during integration step — preserves workflow independence.
    Detects academic→general pipeline and measures lead time.

    Thresholds are read from SOT cross_workflow_correlation.matching section.

    Returns:
        Cross-evolution-map dict
    """
    # ── Resolve thresholds from SOT (v2.3.1) ──
    if registry_path:
        evo_config = load_evolution_config(registry_path)
        cwc = evo_config.get("cross_workflow_correlation", {})
        cwc_matching = cwc.get("matching", {})

        # C2 fix: Enforce enabled flags
        if not evo_config.get("enabled", False) or not cwc.get("enabled", False):
            logger.info("signal_evolution or cross_workflow_correlation disabled — returning empty cross-map")
            empty = {"tracker_version": VERSION, "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "total_correlations": 0, "correlations": []}
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(empty, f, ensure_ascii=False, indent=2)
            return empty
    else:
        cwc_matching = {}

    _title_threshold = title_threshold if title_threshold is not None else cwc_matching.get("title_similarity_threshold", 0.75)
    _semantic_threshold = semantic_threshold if semantic_threshold is not None else cwc_matching.get("semantic_similarity_threshold", 0.65)
    _high_confidence_threshold = cwc_matching.get("high_confidence_threshold", 0.80)
    _category_filter_enabled = cwc_matching.get("category_filter_enabled", True)

    logger.info(
        f"Cross-correlation config: title={_title_threshold}, semantic={_semantic_threshold}, "
        f"high_conf={_high_confidence_threshold}, cat_filter={_category_filter_enabled}"
    )
    indices = {}
    for label, path in [("wf1", wf1_index_path), ("wf2", wf2_index_path), ("wf3", wf3_index_path)]:
        p = Path(path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                indices[label] = json.load(f)
        else:
            indices[label] = {"threads": {}}

    correlations = []
    wf_pairs = [("wf2", "wf1"), ("wf2", "wf3"), ("wf1", "wf3")]

    for src_wf, tgt_wf in wf_pairs:
        src_threads = indices.get(src_wf, {}).get("threads", {})
        tgt_threads = indices.get(tgt_wf, {}).get("threads", {})

        for src_id, src_thread in src_threads.items():
            src_title = src_thread.get("canonical_title", "")
            src_keywords = set(kw.lower() for kw in src_thread.get("keywords", []))

            for tgt_id, tgt_thread in tgt_threads.items():
                # L2 fix (v1.3.0): Category pre-filter — skip if different STEEPs
                if _category_filter_enabled:
                    src_cat = src_thread.get("primary_category", "")
                    tgt_cat = tgt_thread.get("primary_category", "")
                    if src_cat and tgt_cat and src_cat != tgt_cat:
                        continue

                tgt_title = tgt_thread.get("canonical_title", "")
                tgt_keywords = set(kw.lower() for kw in tgt_thread.get("keywords", []))

                title_sim = _jaro_winkler_similarity(src_title.lower(), tgt_title.lower())
                kw_sim = _keyword_vector_similarity(src_keywords, tgt_keywords)

                # L2 fix (v1.3.0): AND logic (was OR) + composite scoring
                # Cross-WF should be STRICTER than within-WF, not looser.
                if title_sim >= _title_threshold and kw_sim >= _semantic_threshold:
                    combined = title_sim * 0.5 + kw_sim * 0.5
                    confidence = "HIGH" if combined >= _high_confidence_threshold else "MEDIUM"

                    src_first = src_thread.get("created_date", "")
                    tgt_first = tgt_thread.get("created_date", "")
                    lead_days = _days_between(src_first, tgt_first) if src_first and tgt_first else 0

                    correlations.append({
                        "source_wf": src_wf,
                        "source_thread_id": src_id,
                        "source_title": src_title,
                        "target_wf": tgt_wf,
                        "target_thread_id": tgt_id,
                        "target_title": tgt_title,
                        "title_similarity": round(title_sim, 3),
                        "keyword_similarity": round(kw_sim, 3),
                        "combined_score": round(combined, 3),
                        "confidence": confidence,
                        "lead_days": lead_days,
                        "direction": f"{src_wf}→{tgt_wf}",
                    })

    cross_map = {
        "tracker_version": VERSION,
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_correlations": len(correlations),
        "correlations": correlations,
    }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cross_map, f, ensure_ascii=False, indent=2)

    logger.info(f"Cross-evolution map: {len(correlations)} correlations → {output_path}")
    return cross_map


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Signal Evolution Tracker — cross-day signal matching and timeline mapping"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Default: track (single-WF evolution)
    track_parser = subparsers.add_parser("track", help="Track evolution for a single workflow")
    track_parser.add_argument("--registry",
        default="env-scanning/config/workflow-registry.yaml",
        help="Path to workflow-registry.yaml (SOT) — all thresholds read from here")
    track_parser.add_argument("--input", "-i", required=True, help="Classified signals JSON")
    track_parser.add_argument("--db", required=True, help="Signals database JSON (pre-update)")
    track_parser.add_argument("--index", required=True, help="Evolution index JSON (read/write)")
    track_parser.add_argument("--workflow", default="wf1-general", help="Workflow name")
    track_parser.add_argument("--output", "-o", help="Output evolution map JSON")
    track_parser.add_argument("--scan-date", help="Override scan date (YYYY-MM-DD)")
    track_parser.add_argument("--priority-ranked", default=None,
        help="Path to priority-ranked JSON (L3 fix: pSST backfill from Step 2.3 output)")
    # CLI threshold overrides — for testing only. In production, SOT values are used.
    track_parser.add_argument("--title-threshold", type=float, default=None,
        help="Override SOT title_similarity_threshold (testing only)")
    track_parser.add_argument("--semantic-threshold", type=float, default=None,
        help="Override SOT semantic_similarity_threshold (testing only)")
    track_parser.add_argument("--fade-days", type=int, default=None,
        help="Override SOT fade_threshold_days (testing only)")

    # Cross-correlate (integration-only)
    cross_parser = subparsers.add_parser("cross-correlate", help="Cross-match threads across WF indices")
    cross_parser.add_argument("--registry",
        default="env-scanning/config/workflow-registry.yaml",
        help="Path to workflow-registry.yaml (SOT) — cross-correlation thresholds read from here")
    cross_parser.add_argument("--wf1-index", required=True, help="WF1 evolution index JSON")
    cross_parser.add_argument("--wf2-index", required=True, help="WF2 evolution index JSON")
    cross_parser.add_argument("--wf3-index", required=True, help="WF3 evolution index JSON")
    cross_parser.add_argument("--output", "-o", required=True, help="Output cross-evolution map JSON")
    # CLI threshold overrides — for testing only
    cross_parser.add_argument("--title-threshold", type=float, default=None,
        help="Override SOT cross_workflow_correlation.matching.title_similarity_threshold")
    cross_parser.add_argument("--semantic-threshold", type=float, default=None,
        help="Override SOT cross_workflow_correlation.matching.semantic_similarity_threshold")

    # Backward compat: if no subcommand, treat legacy args as "track"
    # Parse known args first to detect legacy invocation
    args, remaining = parser.parse_known_args()

    if args.command is None:
        # Legacy invocation (no subcommand): re-parse as track
        args = track_parser.parse_args(sys.argv[1:])
        args.command = "track"

    if args.command == "track":
        try:
            result = track_signal_evolution(
                classified_signals_path=args.input,
                signals_db_path=args.db,
                evolution_index_path=args.index,
                workflow_name=args.workflow,
                output_path=args.output,
                scan_date=args.scan_date,
                registry_path=args.registry,
                priority_ranked_path=args.priority_ranked,
                title_threshold=args.title_threshold,
                semantic_threshold=args.semantic_threshold,
                fade_days=args.fade_days,
            )

            summary = result["summary"]
            print("=" * 60)
            print(f"  Signal Evolution Tracker v{VERSION}")
            print(f"  Workflow: {args.workflow}")
            print(f"  Date: {result['scan_date']}")
            print("-" * 60)
            print(f"  Total signals: {summary['total_signals_today']}")
            print(f"  NEW: {summary['new_signals']}")
            print(f"  RECURRING: {summary['recurring_signals']}")
            print(f"  STRENGTHENING: {summary['strengthening_signals']}")
            print(f"  WEAKENING: {summary['weakening_signals']}")
            print(f"  FADED: {summary['faded_threads']}")
            print(f"  Active threads: {summary['active_threads']}")
            if args.output:
                print(f"  Output: {args.output}")
            print("=" * 60)
            sys.exit(0)

        except Exception as e:
            logger.error(f"Evolution tracking failed: {e}")
            sys.exit(1)

    elif args.command == "cross-correlate":
        try:
            result = cross_correlate_threads(
                wf1_index_path=args.wf1_index,
                wf2_index_path=args.wf2_index,
                wf3_index_path=args.wf3_index,
                output_path=args.output,
                registry_path=args.registry,
                title_threshold=args.title_threshold,
                semantic_threshold=args.semantic_threshold,
            )
            print("=" * 60)
            print(f"  Cross-Workflow Evolution Correlation v{VERSION}")
            print("-" * 60)
            print(f"  Correlations found: {result['total_correlations']}")
            print(f"  Output: {args.output}")
            print("=" * 60)
            sys.exit(0)

        except Exception as e:
            logger.error(f"Cross-correlation failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
