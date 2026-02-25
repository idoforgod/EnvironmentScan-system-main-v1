#!/usr/bin/env python3
"""
Dedup Gate — Programmatic Pipeline Gate for Cross-Scan Duplicate Detection
==========================================================================
Deterministic Python filter that catches topic-level duplicates BEFORE
the LLM deduplication-filter agent processes signals.

Replaces the LLM-instruction-based 4-stage cascade (Stages 1-2) with
a deterministic Python verification. The LLM agent still handles
uncertain/borderline cases (semantic and entity judgment).

Design Principle:
    "검증하라는 '지시'가 아닌, 검증을 '강제'하는 메커니즘."
    — Same principle as temporal_gate.py, applied to dedup.

Architecture:
    orchestrator
    ├── python3 dedup_gate.py  ← deterministic pre-filter (THIS)
    │     ├── Stage A: URL normalized exact match
    │     └── Stage B: Topic Fingerprint overlap coefficient
    │           ├── ≥ 0.60 → definite_duplicate
    │           ├── ≥ 0.30 → uncertain (flagged for LLM)
    │           └── < 0.30 → definite_new
    └── Task(@deduplication-filter)  ← LLM handles uncertain signals only

Usage (CLI):
    python3 env-scanning/core/dedup_gate.py \\
        --signals env-scanning/wf1-general/raw/daily-scan-2026-02-18.json \\
        --previous env-scanning/wf1-general/context/previous-signals.json \\
        --output env-scanning/wf1-general/filtered/gate-result-2026-02-18.json \\
        --workflow wf1-general

Usage (importable):
    from core.dedup_gate import run_dedup_gate
    result = run_dedup_gate(signals_path, previous_path, "wf1-general")

Exit codes:
    0 = PASS (gate completed; duplicates removed or flagged)
    1 = FAIL (critical error — input files missing or corrupt)
    2 = WARN (no previous signals found — all signals pass through)
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "2.0.0"
GATE_ID = "dedup_gate.py"

# Default thresholds (overridden by SOT at runtime)
DEFAULT_URL_EXACT = 1.0
DEFAULT_TOPIC_FINGERPRINT_DEFINITE = 0.60  # Stage B: ≥ this → definite_duplicate
DEFAULT_TOPIC_FINGERPRINT_UNCERTAIN = 0.30  # Stage B: ≥ this → uncertain (flagged for LLM)
DEFAULT_TITLE_SIMILARITY_DEFINITE = 0.90   # Stage C: Jaro-Winkler ≥ this → definite_duplicate
DEFAULT_TITLE_SIMILARITY_UNCERTAIN = 0.80  # Stage C: Jaro-Winkler ≥ this → uncertain
DEFAULT_ENTITY_OVERLAP_DEFINITE = 0.85     # Stage D: entity Jaccard ≥ this → definite_duplicate
DEFAULT_ENTITY_OVERLAP_UNCERTAIN = 0.70    # Stage D: entity Jaccard ≥ this → uncertain
DEFAULT_LOOKBACK_DAYS = 30                 # How far back to compare previous signals


# ---------------------------------------------------------------------------
# URL Normalization (reuses pattern from index_cache_manager.py)
# ---------------------------------------------------------------------------

def normalize_url(url: str) -> str:
    """
    Normalize URL for deduplication.

    Strips scheme, www prefix, trailing slashes, query params, and fragments.
    Example: https://www.cfr.org/reports/conflicts-watch-2026?ref=rss
             → cfr.org/reports/conflicts-watch-2026
    """
    if not url or not isinstance(url, str):
        return ""

    parsed = urlparse(url.strip())
    domain = parsed.netloc.replace("www.", "").lower()
    path = parsed.path.rstrip("/")

    return f"{domain}{path}"


# ---------------------------------------------------------------------------
# Text Normalization
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Normalize text: lowercase, remove punctuation, collapse whitespace.
    Example: "OpenAI Releases GPT-5!" → "openai releases gpt5"
    """
    if not text or not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = " ".join(text.split())
    return text


# ---------------------------------------------------------------------------
# Topic Fingerprint + Overlap Coefficient
# ---------------------------------------------------------------------------
#
# Why NOT TF-IDF: With small corpora (<1000 docs), IDF weights are noisy
# and cosine similarity produces low scores even for obvious duplicates
# (e.g., "New START Treaty Expires" vs "New START Treaty Expiration Risk"
#  → TF-IDF cosine = 0.25, but they're clearly about the same event).
#
# Topic Fingerprint = union of (title meaningful words + explicit keywords).
# Overlap Coefficient = |A∩B| / min(|A|, |B|) — robust to set size differences.
# This catches "same topic, different wording" reliably.
# ---------------------------------------------------------------------------

# Stopwords excluded from fingerprint (common words with no topic signal)
_STOPWORDS: Set[str] = {
    "the", "and", "for", "with", "from", "that", "this", "will",
    "has", "have", "are", "was", "were", "been", "being", "their",
    "into", "over", "about", "between", "through", "after", "before",
    "during", "without", "under", "within", "against", "along",
    "could", "would", "should", "also", "more", "most", "than",
    "2024", "2025", "2026", "2027", "first", "last", "says", "show",
    "shows", "finds", "report", "reports", "study", "says", "year",
    "years", "according", "among", "based", "global", "world", "major",
}


def build_topic_fingerprint(signal: Dict[str, Any]) -> Set[str]:
    """
    Build a topic fingerprint from a signal.

    Combines:
    - Meaningful words from title (>3 chars, not stopwords)
    - Individual words from explicit keywords (content.keywords)

    Handles two signal schemas:
    - Raw scan: {title, content: {keywords: [...]}}
    - Previous-signals: {title, url, category}  (no keywords — title only)
    """
    words: Set[str] = set()

    # Title-derived words
    title = signal.get("title", "")
    if title:
        for w in normalize_text(title).split():
            if len(w) > 3 and w not in _STOPWORDS:
                words.add(w)

    # Explicit keywords (if available)
    content = signal.get("content", {})
    if isinstance(content, dict):
        kw_list = content.get("keywords", [])
        if isinstance(kw_list, list):
            for kw in kw_list:
                if isinstance(kw, str):
                    # Split multi-word keywords into individual words
                    for w in kw.lower().split():
                        if len(w) > 3 and w not in _STOPWORDS:
                            words.add(w)

    return words


def overlap_coefficient(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Overlap Coefficient = |A ∩ B| / min(|A|, |B|).

    More robust than Jaccard for sets of different sizes.
    Returns 0.0 if either set is empty.
    """
    if not set_a or not set_b:
        return 0.0

    intersection = len(set_a & set_b)
    min_size = min(len(set_a), len(set_b))

    if min_size == 0:
        return 0.0

    return intersection / min_size


# ---------------------------------------------------------------------------
# Stage C: Jaro-Winkler Title Similarity
# ---------------------------------------------------------------------------
# Ported from signal_evolution_tracker.py (pure Python, no external deps).
# Jaro-Winkler excels at short string comparison (titles) because it gives
# extra weight to matching prefixes — ideal for signal title dedup.
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


def title_similarity(title_a: str, title_b: str) -> float:
    """
    Compute normalized Jaro-Winkler similarity between two signal titles.
    Both titles are lowercased and stripped before comparison.
    """
    a = title_a.strip().lower()
    b = title_b.strip().lower()
    if not a or not b:
        return 0.0
    return _jaro_winkler_similarity(a, b)


# ---------------------------------------------------------------------------
# Stage D: Entity Extraction + Jaccard Overlap
# ---------------------------------------------------------------------------
# Pure Python entity extraction — no spaCy/NLTK dependency.
# Extracts: acronyms (NATO, BRICS), capitalized proper noun phrases
# (New START Treaty), and numbers with units (2048-bit, $50B).
# ---------------------------------------------------------------------------

# Common words that should NOT be treated as entities even when capitalized
_ENTITY_STOPWORDS: Set[str] = {
    "the", "and", "for", "with", "from", "that", "this", "will", "new",
    "has", "have", "are", "was", "were", "not", "its", "but", "all",
    "can", "may", "how", "why", "what", "when", "where", "who",
    "top", "key", "big", "use", "set", "get", "via", "per",
    "a", "an", "in", "on", "at", "to", "of", "by", "up",
    "report", "study", "analysis", "review", "update", "risk",
    "impact", "global", "world", "major", "says", "finds", "shows",
}


def extract_entities(signal: Dict[str, Any]) -> Set[str]:
    """
    Extract named entities from signal title and keywords.

    Detects:
    - Acronyms (2+ uppercase letters): NATO, BRICS, RSA, AI, GPT-5
    - Capitalized proper noun phrases from original title: "New START", "Hong Kong"
    - Technical terms from keywords

    Returns a set of lowercased entity strings for comparison.
    """
    entities: Set[str] = set()
    title = signal.get("title", "")

    if title:
        # 1. Extract acronyms (2+ uppercase letters, possibly with digits)
        acronyms = re.findall(r"\b[A-Z][A-Z0-9]{1,}(?:-[A-Z0-9]+)*\b", title)
        for acr in acronyms:
            entities.add(acr.lower())

        # 2. Extract capitalized noun phrases (sequences of capitalized words)
        # e.g., "New START Treaty", "Hong Kong", "European Union"
        cap_phrases = re.findall(r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", title)
        for phrase in cap_phrases:
            normalized = phrase.strip().lower()
            if normalized not in _ENTITY_STOPWORDS and len(normalized) > 3:
                entities.add(normalized)

        # 3. Extract individual capitalized words that are likely proper nouns
        words = title.split()
        for i, word in enumerate(words):
            # Skip first word (often capitalized regardless) and stopwords
            clean = re.sub(r"[^\w]", "", word)
            if clean and clean[0].isupper() and len(clean) > 2:
                low = clean.lower()
                if low not in _ENTITY_STOPWORDS:
                    entities.add(low)

    # 4. Include explicit keywords
    content = signal.get("content", {})
    if isinstance(content, dict):
        kw_list = content.get("keywords", [])
        if isinstance(kw_list, list):
            for kw in kw_list:
                if isinstance(kw, str) and len(kw) > 2:
                    entities.add(kw.lower().strip())

    return entities


def entity_overlap(entities_a: Set[str], entities_b: Set[str]) -> float:
    """
    Compute Jaccard similarity between two entity sets.

    Jaccard = |A ∩ B| / |A ∪ B|
    Returns 0.0 if both sets are empty.
    """
    if not entities_a and not entities_b:
        return 0.0
    if not entities_a or not entities_b:
        return 0.0

    intersection = len(entities_a & entities_b)
    union = len(entities_a | entities_b)

    if union == 0:
        return 0.0

    return intersection / union


# ---------------------------------------------------------------------------
# Signal Extraction (same pattern as temporal_gate.py)
# ---------------------------------------------------------------------------

def _extract_signals(data: Any) -> List[Dict[str, Any]]:
    """Extract signal list from various JSON structures."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "classified_signals" in data:
            return data["classified_signals"]
        if "items" in data:
            return data["items"]
        if "signals" in data:
            return data["signals"]
        if "new_signals" in data:
            return data["new_signals"]
    return []


def _extract_previous_signals(
    data: Any,
    lookback_days: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Extract previous signals and URL index from archive-loader output.

    Handles three formats:
    - v2.6.0+: {"url_index": {...}, "title_index": {...}, "signals": [...]}
      where signals have {id, title, url, category, collected_at}
    - Legacy: {"indexes": {"by_url": {...}}, "signals": [...]}
      where signals have {id, title, source: {url: ...}}
    - Database: {"version": ..., "signals": [{id, title, source: {url: ...}}]}

    IMPORTANT: URLs that map to multiple different signals (aggregator pages
    like nature.com/news) are EXCLUDED from the URL index to prevent false
    Stage A matches. These signals still participate in Stage B (topic match).

    Args:
        data: Raw JSON data from previous signals file.
        lookback_days: If set, only include signals collected within this many
            days from now. None = include all signals (no filtering).

    Returns:
        (signals_list, url_index)
        url_index: Map<normalized_url, signal_id>  (ambiguous URLs excluded)
    """
    signals = []

    if isinstance(data, dict):
        signals = data.get("signals", [])

    if isinstance(data, list):
        signals = data

    # Date-based lookback filtering (v2.9.0)
    if lookback_days is not None and lookback_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        filtered = []
        for sig in signals:
            collected = sig.get("collected_at", "")
            if not collected:
                # No date info — include to be safe (conservative)
                filtered.append(sig)
                continue
            try:
                # Parse ISO format (e.g., "2026-02-18T10:30:00Z")
                sig_dt = datetime.fromisoformat(collected.replace("Z", "+00:00"))
                if sig_dt >= cutoff:
                    filtered.append(sig)
            except (ValueError, TypeError):
                # Unparseable date — include to be safe
                filtered.append(sig)
        signals = filtered

    # Build URL index from signals, detecting ambiguous URLs
    # Phase 1: Collect all URL→signal_id mappings
    url_to_ids: Dict[str, List[str]] = {}
    for sig in signals:
        url = sig.get("url", "") or sig.get("source", {}).get("url", "")
        if url:
            norm = normalize_url(url)
            if norm:
                sig_id = sig.get("id", "unknown")
                if norm not in url_to_ids:
                    url_to_ids[norm] = []
                url_to_ids[norm].append(sig_id)

    # Phase 2: Only include URLs that map to exactly one signal
    # Ambiguous URLs (aggregator pages) are excluded from Stage A
    url_index: Dict[str, str] = {}
    for norm_url, sig_ids in url_to_ids.items():
        if len(sig_ids) == 1:
            url_index[norm_url] = sig_ids[0]
        # else: ambiguous URL — skip for URL matching, rely on Stage B+

    return signals, url_index


# ---------------------------------------------------------------------------
# Core Gate Function
# ---------------------------------------------------------------------------

def run_dedup_gate(
    signals_path: str,
    previous_path: str,
    workflow_name: str,
    output_path: Optional[str] = None,
    thresholds: Optional[Dict[str, float]] = None,
    enforce: str = "strict",
    lookback_days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run deterministic 4-stage dedup gate on new signals.

    Args:
        signals_path: Path to new signals JSON (raw scan output)
        previous_path: Path to previous-signals.json (archive-loader output)
        workflow_name: Workflow ID (e.g., "wf1-general")
        output_path: Optional path to write gate result JSON
        thresholds: Override thresholds for all 4 stages
        enforce: "strict" = remove definite dupes; "lenient" = log only
        lookback_days: Only compare against signals from last N days (None = all)

    Returns:
        Gate result dictionary with categorized signals
    """
    # --- 0. Parse thresholds ---
    th = thresholds or {}
    th_url = th.get("url_exact", DEFAULT_URL_EXACT)
    th_topic_definite = th.get("topic_fingerprint_definite", DEFAULT_TOPIC_FINGERPRINT_DEFINITE)
    th_topic_uncertain = th.get("topic_fingerprint_uncertain", DEFAULT_TOPIC_FINGERPRINT_UNCERTAIN)
    th_title_definite = th.get("title_similarity_definite", DEFAULT_TITLE_SIMILARITY_DEFINITE)
    th_title_uncertain = th.get("title_similarity_uncertain", DEFAULT_TITLE_SIMILARITY_UNCERTAIN)
    th_entity_definite = th.get("entity_overlap_definite", DEFAULT_ENTITY_OVERLAP_DEFINITE)
    th_entity_uncertain = th.get("entity_overlap_uncertain", DEFAULT_ENTITY_OVERLAP_UNCERTAIN)

    all_thresholds = {
        "url_exact": th_url,
        "topic_fingerprint_definite": th_topic_definite,
        "topic_fingerprint_uncertain": th_topic_uncertain,
        "title_similarity_definite": th_title_definite,
        "title_similarity_uncertain": th_title_uncertain,
        "entity_overlap_definite": th_entity_definite,
        "entity_overlap_uncertain": th_entity_uncertain,
    }

    empty_stage_counts = {"A_url": 0, "B_topic": 0, "C_title": 0, "D_entity": 0}

    # --- 1. Load new signals ---
    sig_path = Path(signals_path)
    if not sig_path.exists():
        raise FileNotFoundError(f"Signals file not found: {signals_path}")

    with open(sig_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    new_signals = _extract_signals(raw_data)
    if not new_signals:
        return _build_result(
            workflow_name, signals_path, previous_path,
            all_thresholds, enforce,
            new_signals=[], definite_new=[], definite_dupes=[],
            uncertain=[], stage_counts=dict(empty_stage_counts),
        )

    # --- 2. Load previous signals ---
    prev_path = Path(previous_path)
    if not prev_path.exists():
        # No previous signals — all pass through (WARN)
        return _build_result(
            workflow_name, signals_path, previous_path,
            all_thresholds, enforce,
            new_signals=new_signals, definite_new=new_signals,
            definite_dupes=[], uncertain=[],
            stage_counts=dict(empty_stage_counts),
            warn_no_previous=True,
        )

    with open(prev_path, "r", encoding="utf-8") as f:
        prev_data = json.load(f)

    prev_signals, prev_url_index = _extract_previous_signals(
        prev_data, lookback_days=lookback_days
    )

    if not prev_signals:
        return _build_result(
            workflow_name, signals_path, previous_path,
            all_thresholds, enforce,
            new_signals=new_signals, definite_new=new_signals,
            definite_dupes=[], uncertain=[],
            stage_counts=dict(empty_stage_counts),
            warn_no_previous=True,
        )

    # --- 3. Pre-compute fingerprints and entities for previous signals ---
    prev_fingerprints: Dict[str, Set[str]] = {}
    prev_entities: Dict[str, Set[str]] = {}
    for ps in prev_signals:
        ps_id = ps.get("id", "")
        prev_fingerprints[ps_id] = build_topic_fingerprint(ps)
        prev_entities[ps_id] = extract_entities(ps)

    # --- 4. Run 4-stage cascade for each new signal ---
    definite_new: List[Dict[str, Any]] = []
    definite_dupes: List[Dict[str, Any]] = []
    uncertain: List[Dict[str, Any]] = []
    stage_counts = dict(empty_stage_counts)

    for signal in new_signals:
        signal_id = signal.get("id", signal.get("title", "unknown"))
        signal_url = signal.get("source", {}).get("url", "")
        signal_fingerprint = build_topic_fingerprint(signal)
        signal_entities = extract_entities(signal)
        signal_title = signal.get("title", "")

        match_result = _run_cascade(
            signal_id=signal_id,
            signal_url=signal_url,
            signal_title=signal_title,
            signal_fingerprint=signal_fingerprint,
            signal_entities=signal_entities,
            prev_signals=prev_signals,
            prev_url_index=prev_url_index,
            prev_fingerprints=prev_fingerprints,
            prev_entities=prev_entities,
            th_url=th_url,
            th_topic_definite=th_topic_definite,
            th_topic_uncertain=th_topic_uncertain,
            th_title_definite=th_title_definite,
            th_title_uncertain=th_title_uncertain,
            th_entity_definite=th_entity_definite,
            th_entity_uncertain=th_entity_uncertain,
        )

        if match_result["verdict"] == "definite_duplicate":
            definite_dupes.append({
                "signal": signal,
                "match": match_result,
            })
            stage_counts[match_result["stage"]] += 1

        elif match_result["verdict"] == "uncertain":
            uncertain.append({
                "signal": signal,
                "match": match_result,
            })

        else:
            definite_new.append(signal)

    # --- 5. Build and write result ---
    result = _build_result(
        workflow_name, signals_path, previous_path,
        all_thresholds, enforce,
        new_signals, definite_new, definite_dupes, uncertain,
        stage_counts,
    )

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    # --- 6. Write filtered signals (same schema as dedup-filter output) ---
    if output_path and enforce == "strict":
        # Write pass-through signals (definite_new + uncertain) for LLM agent
        filtered_path = Path(output_path).parent / f"gate-filtered-{Path(signals_path).stem.replace('daily-scan-', '')}.json"
        filtered_output = {
            "gate_metadata": {
                "gate_id": GATE_ID,
                "gate_version": VERSION,
                "definite_new_count": len(definite_new),
                "uncertain_count": len(uncertain),
                "definite_dupe_count": len(definite_dupes),
                "total_input": len(new_signals),
            },
            "definite_new": definite_new,
            "uncertain": [u["signal"] for u in uncertain],
            "definite_duplicates_removed": [
                {
                    "signal_id": d["signal"].get("id", "unknown"),
                    "title": d["signal"].get("title", ""),
                    "matched_signal": d["match"].get("matched_signal_id", ""),
                    "matched_title": d["match"].get("matched_title", ""),
                    "stage": d["match"].get("stage", ""),
                    "score": d["match"].get("score", 0),
                }
                for d in definite_dupes
            ],
        }

        with open(filtered_path, "w", encoding="utf-8") as f:
            json.dump(filtered_output, f, indent=2, ensure_ascii=False)

    return result


def _run_cascade(
    signal_id: str,
    signal_url: str,
    signal_title: str,
    signal_fingerprint: Set[str],
    signal_entities: Set[str],
    prev_signals: List[Dict[str, Any]],
    prev_url_index: Dict[str, str],
    prev_fingerprints: Dict[str, Set[str]],
    prev_entities: Dict[str, Set[str]],
    th_url: float,
    th_topic_definite: float,
    th_topic_uncertain: float,
    th_title_definite: float,
    th_title_uncertain: float,
    th_entity_definite: float,
    th_entity_uncertain: float,
) -> Dict[str, Any]:
    """
    Run 4-stage cascade for a single signal.

    Stage A: URL normalized exact match → definite_duplicate
    Stage B: Topic Fingerprint overlap coefficient
    Stage C: Jaro-Winkler title similarity
    Stage D: Entity Jaccard overlap

    For each stage (B/C/D):
        ≥ definite threshold → definite_duplicate (early exit)
        ≥ uncertain threshold → candidate uncertain (continue to see if later stage is definite)

    After all stages: highest uncertain candidate becomes the verdict.
    If no stage matched any threshold → definite_new.

    Returns:
        {
            "verdict": "definite_duplicate" | "uncertain" | "definite_new",
            "stage": "A_url" | "B_topic" | "C_title" | "D_entity" | None,
            "score": float,
            "matched_signal_id": str,
            "matched_title": str,
        }
    """

    # Track the best uncertain match across all stages
    best_uncertain_score = 0.0
    best_uncertain_stage = ""
    best_uncertain_id = ""
    best_uncertain_title = ""

    # --- Stage A: URL Exact Match ---
    if signal_url:
        norm_url = normalize_url(signal_url)
        if norm_url and norm_url in prev_url_index:
            matched_id = prev_url_index[norm_url]
            matched_title = ""
            for ps in prev_signals:
                if ps.get("id") == matched_id:
                    matched_title = ps.get("title", "")
                    break

            return {
                "verdict": "definite_duplicate",
                "stage": "A_url",
                "score": 1.0,
                "matched_signal_id": matched_id,
                "matched_title": matched_title,
            }

    # --- Stage B: Topic Fingerprint Overlap Coefficient ---
    best_b_score = 0.0
    best_b_id = ""
    best_b_title = ""

    for ps in prev_signals:
        ps_id = ps.get("id", "")
        ps_fp = prev_fingerprints.get(ps_id, set())
        score = overlap_coefficient(signal_fingerprint, ps_fp)
        if score > best_b_score:
            best_b_score = score
            best_b_id = ps_id
            best_b_title = ps.get("title", "")

    if best_b_score >= th_topic_definite:
        return {
            "verdict": "definite_duplicate",
            "stage": "B_topic",
            "score": round(best_b_score, 4),
            "matched_signal_id": best_b_id,
            "matched_title": best_b_title,
        }
    if best_b_score >= th_topic_uncertain and best_b_score > best_uncertain_score:
        best_uncertain_score = best_b_score
        best_uncertain_stage = "B_topic"
        best_uncertain_id = best_b_id
        best_uncertain_title = best_b_title

    # --- Stage C: Jaro-Winkler Title Similarity ---
    best_c_score = 0.0
    best_c_id = ""
    best_c_title = ""

    if signal_title:
        for ps in prev_signals:
            ps_id = ps.get("id", "")
            ps_title = ps.get("title", "")
            if not ps_title:
                continue
            score = title_similarity(signal_title, ps_title)
            if score > best_c_score:
                best_c_score = score
                best_c_id = ps_id
                best_c_title = ps_title

    if best_c_score >= th_title_definite:
        return {
            "verdict": "definite_duplicate",
            "stage": "C_title",
            "score": round(best_c_score, 4),
            "matched_signal_id": best_c_id,
            "matched_title": best_c_title,
        }
    if best_c_score >= th_title_uncertain and best_c_score > best_uncertain_score:
        best_uncertain_score = best_c_score
        best_uncertain_stage = "C_title"
        best_uncertain_id = best_c_id
        best_uncertain_title = best_c_title

    # --- Stage D: Entity Overlap (Jaccard) ---
    best_d_score = 0.0
    best_d_id = ""
    best_d_title = ""

    if signal_entities:
        for ps in prev_signals:
            ps_id = ps.get("id", "")
            ps_ent = prev_entities.get(ps_id, set())
            if not ps_ent:
                continue
            score = entity_overlap(signal_entities, ps_ent)
            if score > best_d_score:
                best_d_score = score
                best_d_id = ps_id
                best_d_title = ps.get("title", "")

    if best_d_score >= th_entity_definite:
        return {
            "verdict": "definite_duplicate",
            "stage": "D_entity",
            "score": round(best_d_score, 4),
            "matched_signal_id": best_d_id,
            "matched_title": best_d_title,
        }
    if best_d_score >= th_entity_uncertain and best_d_score > best_uncertain_score:
        best_uncertain_score = best_d_score
        best_uncertain_stage = "D_entity"
        best_uncertain_id = best_d_id
        best_uncertain_title = best_d_title

    # --- Aggregate uncertain from any stage ---
    if best_uncertain_score > 0:
        return {
            "verdict": "uncertain",
            "stage": best_uncertain_stage,
            "score": round(best_uncertain_score, 4),
            "matched_signal_id": best_uncertain_id,
            "matched_title": best_uncertain_title,
        }

    # --- No match in any stage ---
    return {
        "verdict": "definite_new",
        "stage": None,
        "score": 0.0,
        "matched_signal_id": "",
        "matched_title": "",
    }


# ---------------------------------------------------------------------------
# Result Builder
# ---------------------------------------------------------------------------

def _build_result(
    workflow_name: str,
    signals_path: str,
    previous_path: str,
    thresholds: Dict[str, float],
    enforce: str,
    new_signals: List,
    definite_new: List,
    definite_dupes: List,
    uncertain: List,
    stage_counts: Dict[str, int],
    warn_no_previous: bool = False,
) -> Dict[str, Any]:
    """Build standardized gate result."""

    total = len(new_signals)

    if warn_no_previous:
        gate_status = "WARN"
        gate_message = f"No previous signals found. All {total} signals passed through."
    elif not definite_dupes and not uncertain:
        gate_status = "PASS"
        gate_message = f"All {total} signals are definite new. No duplicates detected."
    elif enforce == "strict":
        gate_status = "PASS_WITH_REMOVAL"
        gate_message = (
            f"{len(definite_dupes)} definite duplicate(s) removed. "
            f"{len(uncertain)} uncertain signal(s) flagged for LLM review. "
            f"{len(definite_new)} definite new signal(s) passed."
        )
    else:
        gate_status = "WARN"
        gate_message = (
            f"{len(definite_dupes)} definite duplicate(s) found (lenient — logged only). "
            f"{len(uncertain)} uncertain. All {total} signals retained."
        )

    return {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "workflow": workflow_name,
        "signals_file": str(signals_path),
        "previous_file": str(previous_path),
        "gate_status": gate_status,
        "gate_message": gate_message,
        "thresholds": thresholds,
        "enforce": enforce,
        "statistics": {
            "total_input": len(new_signals),
            "definite_new": len(definite_new),
            "definite_duplicates": len(definite_dupes),
            "uncertain": len(uncertain),
            "pass_through": len(definite_new) + len(uncertain),
        },
        "stage_breakdown": stage_counts,
        "duplicates": [
            {
                "signal_id": d["signal"].get("id", "unknown"),
                "signal_title": d["signal"].get("title", ""),
                "matched_signal_id": d["match"].get("matched_signal_id", ""),
                "matched_title": d["match"].get("matched_title", ""),
                "stage": d["match"].get("stage", ""),
                "score": d["match"].get("score", 0),
            }
            for d in definite_dupes
        ],
        "uncertain_signals": [
            {
                "signal_id": u["signal"].get("id", "unknown"),
                "signal_title": u["signal"].get("title", ""),
                "matched_signal_id": u["match"].get("matched_signal_id", ""),
                "matched_title": u["match"].get("matched_title", ""),
                "stage": u["match"].get("stage", ""),
                "score": u["match"].get("score", 0),
            }
            for u in uncertain
        ],
    }


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Dedup Gate — Programmatic pre-filter for cross-scan duplicate detection"
    )
    parser.add_argument(
        "--signals", required=True,
        help="Path to new signals JSON (raw scan output)",
    )
    parser.add_argument(
        "--previous", required=True,
        help="Path to previous-signals.json (archive-loader output)",
    )
    parser.add_argument(
        "--workflow", required=True,
        help="Workflow name (e.g., wf1-general, wf2-arxiv, wf3-naver)",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output path for gate result JSON",
    )
    parser.add_argument(
        "--definite-threshold", type=float, default=None,
        help="Override topic fingerprint threshold for definite_duplicate (default 0.60)",
    )
    parser.add_argument(
        "--uncertain-threshold", type=float, default=None,
        help="Override topic fingerprint threshold for uncertain (default 0.30)",
    )
    parser.add_argument(
        "--title-definite-threshold", type=float, default=None,
        help="Override Stage C title similarity definite threshold (default 0.90)",
    )
    parser.add_argument(
        "--title-uncertain-threshold", type=float, default=None,
        help="Override Stage C title similarity uncertain threshold (default 0.80)",
    )
    parser.add_argument(
        "--entity-definite-threshold", type=float, default=None,
        help="Override Stage D entity overlap definite threshold (default 0.85)",
    )
    parser.add_argument(
        "--entity-uncertain-threshold", type=float, default=None,
        help="Override Stage D entity overlap uncertain threshold (default 0.70)",
    )
    parser.add_argument(
        "--lookback-days", type=int, default=None,
        help="Only compare against signals from last N days (default: all)",
    )
    parser.add_argument(
        "--enforce", choices=["strict", "lenient"], default="strict",
        help="Enforcement mode: strict=remove dupes, lenient=log only",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Print result as JSON to stdout",
    )
    args = parser.parse_args()

    # Build thresholds from CLI args
    thresholds = {}
    if args.definite_threshold is not None:
        thresholds["topic_fingerprint_definite"] = args.definite_threshold
    if args.uncertain_threshold is not None:
        thresholds["topic_fingerprint_uncertain"] = args.uncertain_threshold
    if args.title_definite_threshold is not None:
        thresholds["title_similarity_definite"] = args.title_definite_threshold
    if args.title_uncertain_threshold is not None:
        thresholds["title_similarity_uncertain"] = args.title_uncertain_threshold
    if args.entity_definite_threshold is not None:
        thresholds["entity_overlap_definite"] = args.entity_definite_threshold
    if args.entity_uncertain_threshold is not None:
        thresholds["entity_overlap_uncertain"] = args.entity_uncertain_threshold

    try:
        result = run_dedup_gate(
            signals_path=args.signals,
            previous_path=args.previous,
            workflow_name=args.workflow,
            output_path=args.output,
            thresholds=thresholds if thresholds else None,
            enforce=args.enforce,
            lookback_days=args.lookback_days,
        )

        if args.json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Human-readable summary
            status = result["gate_status"]
            stats = result["statistics"]
            icon = "+" if status in ("PASS", "PASS_WITH_REMOVAL") else "!"

            print("=" * 65)
            print(f"  [{icon}] Dedup Gate v{VERSION}: {status}")
            print(f"  Workflow: {result['workflow']}")
            print(f"  {result['gate_message']}")
            print("-" * 65)
            print(f"  Input: {stats['total_input']}  |  "
                  f"New: {stats['definite_new']}  |  "
                  f"Dupes: {stats['definite_duplicates']}  |  "
                  f"Uncertain: {stats['uncertain']}")
            sb = result["stage_breakdown"]
            print(f"  Stage A (URL): {sb.get('A_url', 0)}  |  "
                  f"Stage B (Topic): {sb.get('B_topic', 0)}  |  "
                  f"Stage C (Title): {sb.get('C_title', 0)}  |  "
                  f"Stage D (Entity): {sb.get('D_entity', 0)}")
            print("=" * 65)

            if result["duplicates"]:
                print("  Definite Duplicates:")
                for d in result["duplicates"][:10]:
                    print(f"    [{d['stage']}] {d['signal_title'][:60]}...")
                    print(f"         matched: {d['matched_title'][:60]}... (score={d['score']})")
                if len(result["duplicates"]) > 10:
                    print(f"    ... and {len(result['duplicates']) - 10} more")

            if result["uncertain_signals"]:
                print("  Uncertain (needs LLM review):")
                for u in result["uncertain_signals"][:5]:
                    print(f"    [{u['stage']}] {u['signal_title'][:60]}...")
                    print(f"         similar to: {u['matched_title'][:60]}... (score={u['score']})")

        # Exit code
        if status == "PASS" or status == "PASS_WITH_REMOVAL":
            sys.exit(0)
        elif status == "WARN":
            sys.exit(2)
        else:
            sys.exit(1)

    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
