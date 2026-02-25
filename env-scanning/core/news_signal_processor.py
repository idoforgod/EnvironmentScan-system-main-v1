"""
News Signal Processor (WF4 Core Module)

FSSF / Tipping Point / Anomaly / Alert processing for WF4 (Multi&Global-News).
All computations are deterministic (Python stdlib math only, no numpy).

4 Operating Modes (CLI subcommands):
    - fssf-hints     : Compute FSSF classification hints from signal statistics
    - tipping-point  : Detect tipping point indicators via CSD analysis
    - anomaly        : Statistical anomaly detection (z-score, cross-domain, concentration)
    - alert-eval     : Evaluate 5 alert trigger conditions with severity levels

These functions are called by WF4 worker agents:
    - news-signal-detector (Phase 2, Step 2.1)
    - news-pattern-detector (Phase 2, Step 2.2)
    - news-alert-dispatcher (Phase 3, Step 3.3)

CLI Usage:
    python3 env-scanning/core/news_signal_processor.py fssf-hints \\
        --input classified-signals.json --history signals/database.json \\
        --output fssf-hints.json

    python3 env-scanning/core/news_signal_processor.py tipping-point \\
        --input signals/database.json --window 7 \\
        --output tipping-point-status.json

    python3 env-scanning/core/news_signal_processor.py anomaly \\
        --input classified-signals.json --window 14 \\
        --output anomaly-flags.json

    python3 env-scanning/core/news_signal_processor.py alert-eval \\
        --input processed-signals.json \\
        --output alert-evaluation.json
"""

import argparse
import json
import logging
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("news_signal_processor")


# ──────────────────────────────────────────────────────────────────────
# FSSF 8-Type Classification Constants
# ──────────────────────────────────────────────────────────────────────

FSSF_TYPES = [
    "Weak Signal",
    "Emerging Issue",
    "Trend",
    "Megatrend",
    "Driver",
    "Wild Card",
    "Discontinuity",
    "Precursor Event",
]

# Priority levels per FSSF type (for the absolute goal: catch signals FAST)
FSSF_PRIORITY: dict[str, str] = {
    "Weak Signal": "CRITICAL",
    "Wild Card": "CRITICAL",
    "Discontinuity": "CRITICAL",
    "Driver": "HIGH",
    "Emerging Issue": "HIGH",
    "Precursor Event": "HIGH",
    "Trend": "MEDIUM",
    "Megatrend": "MEDIUM",
}

# Three Horizons labels
HORIZON_LABELS = {"H1": "0-2yr", "H2": "2-7yr", "H3": "7yr+"}


# ──────────────────────────────────────────────────────────────────────
# FSSF Hints
# ──────────────────────────────────────────────────────────────────────

@dataclass
class FSSFHints:
    """Heuristic hints for FSSF classification.

    Pre-computed features that help the AI agent make better
    classification decisions. These are deterministic statistics,
    NOT final classifications.
    """
    frequency: float = 0.0          # Historical mention frequency (7-day avg)
    novelty_score: float = 0.0      # 0.0 = well-known, 1.0 = completely novel
    cross_domain_count: int = 1     # Number of STEEPs domains touched
    source_count: int = 1           # How many distinct sources report this
    is_event: bool = False          # Specific datable event
    is_first_occurrence: bool = False  # No historical precedent found
    breaks_pattern: bool = False    # Contradicts existing trends
    impact_breadth: str = "narrow"  # narrow | broad | global

    def suggest_fssf_type(self) -> tuple[str, float]:
        """Apply decision tree to suggest FSSF type with confidence.

        Returns (fssf_type, confidence).
        The AI agent should use this as a HINT, not a final answer.
        """
        if self.is_event:
            if self.is_first_occurrence:
                return ("Precursor Event", 0.7)
            if self.breaks_pattern:
                return ("Discontinuity", 0.7)

        if self.novelty_score > 0.8 and self.source_count <= 2:
            return ("Weak Signal", 0.65)
        if self.source_count <= 2 and self.frequency < 1.0:
            return ("Weak Signal", 0.6)
        if 3 <= self.source_count <= 10:
            return ("Emerging Issue", 0.6)
        if self.source_count > 10:
            if self.cross_domain_count >= 3 and self.impact_breadth == "global":
                return ("Megatrend", 0.6)
            return ("Trend", 0.6)

        return ("Emerging Issue", 0.4)  # Default with low confidence


def compute_fssf_hints(signal: dict, history: list[dict]) -> dict:
    """Compute FSSF hints (frequency, novelty, cross-domain) for a signal.

    Args:
        signal: Current signal dict (standard format with id, title,
                source, content, preliminary_category, collected_at).
        history: Historical signals list from the signals database.

    Returns:
        Dict with hint fields: frequency, novelty_score, cross_domain_count,
        source_count, suggested_fssf, fssf_confidence, suggested_horizon,
        horizon_confidence, and raw hint details.
    """
    title = signal.get("title", "")
    title_lower = title.lower()
    title_words = set(title_lower.split())

    # --- Frequency: count similar signals in history (keyword overlap >= 2) ---
    similar_count = 0
    lookback_days = 7
    for hist in history:
        hist_words = set(hist.get("title", "").lower().split())
        overlap = len(title_words & hist_words)
        if overlap >= 2:
            similar_count += 1

    frequency = similar_count / max(lookback_days, 1)

    # --- Novelty score: inverse of historical similarity ---
    if similar_count == 0:
        novelty_score = 1.0
    else:
        # Exponential decay: more history matches → lower novelty
        novelty_score = max(0.0, 1.0 - math.log1p(similar_count) / math.log1p(20))

    # --- Cross-domain count from content ---
    content = signal.get("content", {})
    abstract = content.get("abstract", "") if isinstance(content, dict) else ""
    steeps_indicators = {
        "S": ["social", "demographic", "education", "labor", "health", "generation",
              "사회", "인구", "교육", "건강", "세대"],
        "T": ["technology", "AI", "digital", "robot", "quantum", "innovation",
              "기술", "디지털", "로봇", "양자", "혁신"],
        "E_econ": ["economy", "finance", "investment", "market", "trade",
                   "경제", "금융", "투자", "시장", "무역"],
        "E_env": ["climate", "environment", "carbon", "pollution", "energy",
                  "기후", "환경", "탄소", "오염", "에너지"],
        "P": ["policy", "regulation", "law", "government", "international",
              "정책", "규제", "법안", "정부", "국제"],
        "s": ["values", "ethics", "psychology", "culture", "meaning",
              "가치관", "윤리", "심리", "종교", "문화"],
    }
    combined_text = (title + " " + abstract).lower()
    cross_domain_count = sum(
        1 for domain_kws in steeps_indicators.values()
        if any(kw.lower() in combined_text for kw in domain_kws)
    )
    cross_domain_count = max(cross_domain_count, 1)

    # --- Source count (distinct source names in this signal batch) ---
    source = signal.get("source", {})
    source_name = source.get("name", "") if isinstance(source, dict) else ""
    source_count = 1  # Per-signal; batch-level aggregation done by caller

    # --- Event detection ---
    event_keywords = [
        "발표", "출시", "선언", "합의", "체결", "발생", "사고",
        "시행", "개최", "통과", "승인", "결정", "폭발", "붕괴",
        "launch", "announce", "agreement", "incident", "approve",
        "release", "declare", "signed", "passed",
    ]
    is_event = any(kw in combined_text for kw in event_keywords)

    # --- Pattern break detection ---
    break_keywords = [
        "최초", "전례 없", "역사적", "예상 밖", "돌발", "반전",
        "급변", "전환", "처음으로", "이례적",
        "first-ever", "unprecedented", "historic", "unexpected",
        "reversal", "paradigm shift", "breakthrough",
    ]
    breaks_pattern = any(kw in combined_text for kw in break_keywords)

    # --- Build hints object ---
    hints = FSSFHints(
        frequency=round(frequency, 4),
        novelty_score=round(novelty_score, 4),
        cross_domain_count=cross_domain_count,
        source_count=source_count,
        is_event=is_event,
        is_first_occurrence=(similar_count == 0 and is_event),
        breaks_pattern=breaks_pattern,
        impact_breadth="global" if cross_domain_count >= 4 else (
            "broad" if cross_domain_count >= 3 else "narrow"
        ),
    )

    suggested_fssf, fssf_confidence = hints.suggest_fssf_type()

    # --- Three Horizons suggestion ---
    horizon, h_conf = _suggest_horizon(signal)

    return {
        "signal_id": signal.get("id", ""),
        "frequency": hints.frequency,
        "novelty_score": hints.novelty_score,
        "cross_domain_count": hints.cross_domain_count,
        "source_count": hints.source_count,
        "is_event": hints.is_event,
        "is_first_occurrence": hints.is_first_occurrence,
        "breaks_pattern": hints.breaks_pattern,
        "impact_breadth": hints.impact_breadth,
        "suggested_fssf": suggested_fssf,
        "fssf_confidence": fssf_confidence,
        "suggested_horizon": horizon,
        "horizon_confidence": h_conf,
    }


def _suggest_horizon(signal: dict) -> tuple[str, float]:
    """Suggest Three Horizons classification from signal content.

    Returns (horizon, confidence).
    """
    title = signal.get("title", "")
    content = signal.get("content", {})
    abstract = content.get("abstract", "") if isinstance(content, dict) else ""
    text = (title + " " + abstract).lower()

    h3_keywords = [
        "패러다임", "혁명", "근본적", "문명", "탈인간", "특이점",
        "양자", "핵융합", "유전자편집", "범용인공지능", "AGI",
        "뇌-컴퓨터", "우주식민", "인공생명",
        "paradigm", "revolution", "fundamental", "civilization",
        "singularity", "quantum", "fusion", "gene editing", "AGI",
        "brain-computer", "space colonization",
    ]
    h2_keywords = [
        "실험", "시범", "파일럿", "스타트업", "초기",
        "규제 논의", "표준화", "도입 검토", "시제품", "베타",
        "experiment", "pilot", "startup", "early-stage",
        "regulatory review", "standardization", "prototype", "beta",
    ]
    h1_keywords = [
        "시행", "적용", "현재", "올해", "이번", "당장",
        "내년", "예산", "집행", "개정", "시장 점유",
        "implemented", "current", "this year", "budget",
        "market share", "enforced", "amendment",
    ]

    h3_score = sum(1 for kw in h3_keywords if kw in text)
    h2_score = sum(1 for kw in h2_keywords if kw in text)
    h1_score = sum(1 for kw in h1_keywords if kw in text)

    total = h1_score + h2_score + h3_score
    if total == 0:
        return ("H1", 0.4)  # Default to current horizon

    if h3_score > h2_score and h3_score > h1_score:
        return ("H3", min(0.5 + h3_score * 0.1, 0.9))
    if h2_score > h1_score:
        return ("H2", min(0.5 + h2_score * 0.1, 0.9))
    return ("H1", min(0.5 + h1_score * 0.1, 0.9))


# ──────────────────────────────────────────────────────────────────────
# Tipping Point Detection (CSD — Critical Slowing Down)
# ──────────────────────────────────────────────────────────────────────

@dataclass
class TippingPointStatus:
    """Tipping point detection result for a signal or cluster."""
    signal_id: str
    alert_level: str  # GREEN | YELLOW | ORANGE | RED
    variance_trend: float = 0.0
    autocorrelation: float = 0.0
    flickering: bool = False
    evidence: str = ""

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "alert_level": self.alert_level,
            "variance_trend": round(self.variance_trend, 4),
            "autocorrelation": round(self.autocorrelation, 4),
            "flickering": self.flickering,
            "evidence": self.evidence,
        }


def compute_variance_trend(values: list[float]) -> float:
    """Compute rolling variance trend (CSD indicator).

    Compares variance of the recent half to the baseline half.
    Returns a ratio: >0 means variance is increasing, indicating
    potential CSD. Range is typically 0.0 to 2.0+.

    Uses standard library math only (no numpy).

    Args:
        values: Time series of daily signal counts.

    Returns:
        Variance trend ratio. 0.0 if insufficient data.
    """
    if len(values) < 4:
        return 0.0

    midpoint = len(values) // 2
    baseline = values[:midpoint]
    recent = values[midpoint:]

    baseline_var = _variance(baseline)
    recent_var = _variance(recent)

    if baseline_var == 0.0:
        return 0.0 if recent_var == 0.0 else 2.0

    return recent_var / baseline_var


def compute_autocorrelation(values: list[float], lag: int = 1) -> float:
    """Compute lag-1 autocorrelation (CSD indicator).

    High autocorrelation (> 0.7) indicates Critical Slowing Down —
    the system takes longer to recover from perturbations.

    Uses standard library math only (no numpy).

    Args:
        values: Time series of daily signal counts.
        lag: Autocorrelation lag (default 1).

    Returns:
        Autocorrelation coefficient in [-1.0, 1.0]. 0.0 if insufficient data.
    """
    n = len(values)
    if n < lag + 3:
        return 0.0

    mean = sum(values) / n
    denominator = sum((x - mean) ** 2 for x in values)
    if denominator == 0.0:
        return 0.0

    numerator = sum(
        (values[i] - mean) * (values[i + lag] - mean)
        for i in range(n - lag)
    )
    return numerator / denominator


def detect_flickering(values: list[float], threshold: float = 2.0) -> bool:
    """Detect flickering pattern (rapid oscillation indicator).

    Flickering occurs when a system rapidly alternates between states,
    indicating proximity to a tipping point. We detect this by counting
    sign changes relative to the mean and comparing against a threshold
    multiplied by the expected random rate.

    Args:
        values: Time series of daily signal counts.
        threshold: Multiplier for expected random oscillation rate.
                   Values above threshold * expected_rate flag as flickering.

    Returns:
        True if flickering pattern is detected, False otherwise.
    """
    if len(values) < 4:
        return False

    mean = sum(values) / len(values)
    deviations = [v - mean for v in values]

    # Count sign changes (oscillations around the mean)
    sign_changes = 0
    for i in range(1, len(deviations)):
        if deviations[i] * deviations[i - 1] < 0:
            sign_changes += 1

    # Expected random sign change rate is ~0.5 per step
    expected_rate = 0.5 * (len(deviations) - 1)

    if expected_rate == 0.0:
        return False

    oscillation_ratio = sign_changes / expected_rate
    return oscillation_ratio > threshold


def _determine_alert_level(
    variance_trend: float,
    autocorrelation: float,
) -> str:
    """Determine tipping point alert level from CSD indicators.

    Decision table:
        variance_trend > 0.5 AND autocorrelation > 0.7 → RED
        variance_trend > 0.3 AND autocorrelation > 0.5 → ORANGE
        variance_trend > 0.1 OR  autocorrelation > 0.3 → YELLOW
        else → GREEN
    """
    if variance_trend > 0.5 and autocorrelation > 0.7:
        return "RED"
    if variance_trend > 0.3 and autocorrelation > 0.5:
        return "ORANGE"
    if variance_trend > 0.1 or autocorrelation > 0.3:
        return "YELLOW"
    return "GREEN"


def compute_tipping_point(daily_counts: list[dict], window: int = 7) -> dict:
    """Compute CSD indicators: variance trend, autocorrelation, flickering.

    Processes a time series of daily signal counts per cluster/category
    from the signals database history.

    Args:
        daily_counts: List of dicts, each with 'date' and 'count' keys,
                      OR list of dicts with 'date' and per-category counts.
                      Supports two formats:
                        Format A: [{"date": "2026-02-01", "count": 5}, ...]
                        Format B: [{"date": "2026-02-01", "S": 3, "T": 2, ...}, ...]
        window: Rolling window size for CSD computation (default 7).

    Returns:
        Dict with per-cluster tipping point status and overall alert.
    """
    if not daily_counts:
        return {
            "overall_alert": "GREEN",
            "clusters": [],
            "summary": {
                "total_clusters_analyzed": 0,
                "window_size": window,
            },
        }

    # Detect format and extract time series per cluster
    cluster_series: dict[str, list[float]] = defaultdict(list)

    if "count" in daily_counts[0]:
        # Format A: single time series
        sorted_entries = sorted(daily_counts, key=lambda d: d.get("date", ""))
        values = [float(entry.get("count", 0)) for entry in sorted_entries]
        cluster_series["_all"] = values
    else:
        # Format B: per-category counts
        # Support two sub-formats:
        #   B1: {"date": "...", "T": 5, "E": 3}  (flat)
        #   B2: {"date": "...", "counts": {"T": 5, "E": 3}}  (nested)
        sorted_entries = sorted(daily_counts, key=lambda d: d.get("date", ""))

        # Detect nested format and flatten if needed
        normalized: list[dict] = []
        for entry in sorted_entries:
            if "counts" in entry and isinstance(entry["counts"], dict):
                flat = {"date": entry.get("date", "")}
                flat.update(entry["counts"])
                normalized.append(flat)
            else:
                normalized.append(entry)

        # Extract all category keys (excluding 'date')
        categories: set[str] = set()
        for entry in normalized:
            for key in entry:
                if key != "date":
                    categories.add(key)

        for cat in categories:
            cluster_series[cat] = [
                float(entry.get(cat, 0)) for entry in normalized
            ]

    # Compute CSD indicators for each cluster
    results: list[TippingPointStatus] = []
    for cluster_id, series in cluster_series.items():
        if len(series) < window:
            logger.debug(
                f"[TIPPING] Cluster '{cluster_id}' has {len(series)} points "
                f"(need {window}) — skipping"
            )
            continue

        # Use the most recent 'window' values for CSD analysis
        recent = series[-window:] if len(series) > window else series
        full_series = series  # Use full series for autocorrelation

        vt = compute_variance_trend(full_series)
        ac = compute_autocorrelation(full_series, lag=1)
        fl = detect_flickering(full_series)

        alert = _determine_alert_level(vt, ac)

        # Upgrade to RED if flickering + ORANGE
        if fl and alert == "ORANGE":
            alert = "RED"
        # Upgrade to ORANGE if flickering + YELLOW
        elif fl and alert == "YELLOW":
            alert = "ORANGE"

        evidence_parts = []
        if vt > 0.1:
            evidence_parts.append(f"Variance trend={vt:.3f}")
        if ac > 0.3:
            evidence_parts.append(f"Autocorrelation={ac:.3f}")
        if fl:
            evidence_parts.append("Flickering detected")
        evidence = ". ".join(evidence_parts) if evidence_parts else "No significant indicators"

        results.append(TippingPointStatus(
            signal_id=cluster_id,
            alert_level=alert,
            variance_trend=vt,
            autocorrelation=ac,
            flickering=fl,
            evidence=evidence,
        ))

    # Overall alert = worst across all clusters
    alert_priority = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}
    overall = "GREEN"
    for r in results:
        if alert_priority.get(r.alert_level, 0) > alert_priority.get(overall, 0):
            overall = r.alert_level

    alert_dist = Counter(r.alert_level for r in results)

    return {
        "overall_alert": overall,
        "clusters": [r.to_dict() for r in results],
        "summary": {
            "total_clusters_analyzed": len(results),
            "window_size": window,
            "alert_distribution": {
                "GREEN": alert_dist.get("GREEN", 0),
                "YELLOW": alert_dist.get("YELLOW", 0),
                "ORANGE": alert_dist.get("ORANGE", 0),
                "RED": alert_dist.get("RED", 0),
            },
        },
    }


# ──────────────────────────────────────────────────────────────────────
# Anomaly Detection
# ──────────────────────────────────────────────────────────────────────

@dataclass
class AnomalyFlag:
    """Anomaly detection result for a signal."""
    signal_id: str
    anomaly_type: str   # z_score | cross_domain | single_source
    severity: str       # Low | Medium | High
    z_score: float = 0.0
    detail: str = ""

    def to_dict(self) -> dict:
        result: dict = {
            "signal_id": self.signal_id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "detail": self.detail,
        }
        if self.anomaly_type == "z_score":
            result["z_score"] = round(self.z_score, 3)
        return result


def detect_anomaly(signal_counts: dict, window: int = 14) -> list[dict]:
    """Detect statistical anomalies via z-score > 3 threshold.

    Performs three types of anomaly detection:
    1. Z-score analysis: flags signals whose category count deviates
       >3 standard deviations from the rolling mean.
    2. Cross-domain anomaly: flags signals appearing in unexpected
       STEEPs categories.
    3. Single-source concentration: flags when one source contributes
       >70% of signals.

    Args:
        signal_counts: Dict with the following structure:
            {
                "category_counts": {"S": [...], "T": [...], ...},
                    — daily counts per STEEPs category (list of floats)
                "signals": [...],
                    — list of signal dicts for structural analysis
                "source_distribution": {"SourceA": 10, "SourceB": 5, ...}
                    — count of signals per source name
            }
        window: Rolling window size for z-score baseline (default 14).

    Returns:
        List of anomaly flag dicts.
    """
    anomalies: list[AnomalyFlag] = []

    # --- 1. Z-score analysis per category ---
    category_counts = signal_counts.get("category_counts", {})
    for cat, counts in category_counts.items():
        if not isinstance(counts, list) or len(counts) < window:
            continue

        baseline = counts[-window:-1]  # All but the latest
        latest = counts[-1]

        mean = sum(baseline) / len(baseline)
        std = _stddev(baseline)

        if std == 0.0:
            # If zero variance baseline and latest is non-zero, flag it
            if latest > 0:
                anomalies.append(AnomalyFlag(
                    signal_id=f"CATEGORY-{cat}",
                    anomaly_type="z_score",
                    severity="High",
                    z_score=float("inf"),
                    detail=(
                        f"Category '{cat}' had zero variance baseline "
                        f"but latest count={latest}"
                    ),
                ))
            continue

        z = (latest - mean) / std
        if abs(z) > 3.0:
            severity = "High" if abs(z) > 5.0 else "Medium"
            direction = "spike" if z > 0 else "drop"
            anomalies.append(AnomalyFlag(
                signal_id=f"CATEGORY-{cat}",
                anomaly_type="z_score",
                severity=severity,
                z_score=round(z, 3),
                detail=(
                    f"Category '{cat}' {direction}: z={z:.2f} "
                    f"(mean={mean:.1f}, std={std:.2f}, latest={latest})"
                ),
            ))

    # --- 2. Cross-domain anomaly ---
    signals = signal_counts.get("signals", [])
    for signal in signals:
        sid = signal.get("id", "")
        prelim = signal.get("preliminary_category", "")
        content = signal.get("content", {})
        abstract = content.get("abstract", "") if isinstance(content, dict) else ""

        if prelim and abstract:
            # Check if content mentions categories different from assigned
            steeps_mentions = _detect_steeps_in_text(abstract)
            if steeps_mentions and prelim not in steeps_mentions:
                anomalies.append(AnomalyFlag(
                    signal_id=sid,
                    anomaly_type="cross_domain",
                    severity="Low",
                    detail=(
                        f"Signal classified as '{prelim}' but content "
                        f"mentions domains: {steeps_mentions}"
                    ),
                ))

    # --- 3. Single-source concentration ---
    source_dist = signal_counts.get("source_distribution", {})
    total_signals = sum(source_dist.values()) if source_dist else 0
    if total_signals > 0:
        for source_name, count in source_dist.items():
            ratio = count / total_signals
            if ratio > 0.7:
                anomalies.append(AnomalyFlag(
                    signal_id="AGGREGATE",
                    anomaly_type="single_source",
                    severity="Medium",
                    detail=(
                        f"Source '{source_name}' dominates with "
                        f"{ratio:.0%} ({count}/{total_signals}) of signals"
                    ),
                ))

    return [a.to_dict() for a in anomalies]


# ──────────────────────────────────────────────────────────────────────
# Alert Trigger Evaluation
# ──────────────────────────────────────────────────────────────────────

ALERT_ACTIONS: dict[str, str] = {
    "CRITICAL": "URGENT — immediate strategic review required",
    "HIGH": "Elevated attention — monitor closely and consider escalation",
    "MEDIUM": "Track closely — potential strategic significance",
}


def evaluate_alert_triggers(signals: list[dict]) -> list[dict]:
    """Evaluate 5 alert trigger conditions, return severity levels.

    Trigger conditions:
        a. RED tipping point alert → CRITICAL
        b. Wild Card + impact > 0.7 → HIGH
        c. Discontinuity + impact > 0.7 → HIGH
        d. H3 + Weak Signal + cross-STEEPs → MEDIUM
        e. 3+ anomalies in same STEEPs category → MEDIUM

    Args:
        signals: List of processed signal dicts. Each signal may contain:
            - fssf_type: str (FSSF classification)
            - impact_score: float (0.0 to 1.0)
            - tipping_level: str (GREEN/YELLOW/ORANGE/RED)
            - three_horizons: str (H1/H2/H3)
            - cross_steeps_count: int
            - anomaly_flags: list[dict]
            - preliminary_category: str

    Returns:
        List of alert dicts with signal_id, signal_title, condition,
        severity (CRITICAL/HIGH/MEDIUM), and action.
    """
    alerts: list[dict] = []

    # Pre-compute: anomaly count per STEEPs category
    category_anomaly_counts: dict[str, int] = defaultdict(int)
    for signal in signals:
        cat = signal.get("preliminary_category", "")
        anomaly_flags = signal.get("anomaly_flags", [])
        if anomaly_flags:
            category_anomaly_counts[cat] += len(anomaly_flags)

    # Categories with 3+ anomalies
    high_anomaly_categories: set[str] = {
        cat for cat, count in category_anomaly_counts.items() if count >= 3
    }

    for signal in signals:
        sid = signal.get("id", "")
        title = signal.get("title", "")
        fssf = signal.get("fssf_type", "")
        impact = signal.get("impact_score", 0.0)
        tipping = signal.get("tipping_level", "GREEN")
        horizon = signal.get("three_horizons", "")
        cross_steeps = signal.get("cross_steeps_count", 0)
        cat = signal.get("preliminary_category", "")

        triggered = False

        # Condition a: RED tipping point alert → CRITICAL
        if tipping == "RED":
            alerts.append({
                "signal_id": sid,
                "signal_title": title,
                "condition": "tipping_point_red",
                "severity": "CRITICAL",
                "action": (
                    "URGENT — tipping point imminent. "
                    "Immediate strategic response recommended."
                ),
            })
            triggered = True

        # Condition b: Wild Card + impact > 0.7 → HIGH
        if fssf == "Wild Card" and impact > 0.7:
            alerts.append({
                "signal_id": sid,
                "signal_title": title,
                "condition": "wild_card_high_impact",
                "severity": "HIGH",
                "action": (
                    "Low-probability high-impact event detected. "
                    "Monitor closely and prepare contingency."
                ),
            })
            triggered = True

        # Condition c: Discontinuity + impact > 0.7 → HIGH
        if fssf == "Discontinuity" and impact > 0.7:
            alerts.append({
                "signal_id": sid,
                "signal_title": title,
                "condition": "discontinuity_high_impact",
                "severity": "HIGH",
                "action": (
                    "Pattern break with high impact confirmed. "
                    "Review strategic assumptions."
                ),
            })
            triggered = True

        # Condition d: H3 + Weak Signal + cross-STEEPs → MEDIUM
        if horizon == "H3" and fssf == "Weak Signal" and cross_steeps >= 2:
            alerts.append({
                "signal_id": sid,
                "signal_title": title,
                "condition": "h3_weak_signal_cross_steeps",
                "severity": "MEDIUM",
                "action": (
                    "Future system seed detected across multiple domains. "
                    "Track evolution closely."
                ),
            })
            triggered = True

        # Condition e: 3+ anomalies in same STEEPs category → MEDIUM
        if cat in high_anomaly_categories and not triggered:
            anomaly_flags = signal.get("anomaly_flags", [])
            if anomaly_flags:
                alerts.append({
                    "signal_id": sid,
                    "signal_title": title,
                    "condition": "anomaly_cluster",
                    "severity": "MEDIUM",
                    "action": (
                        f"Multiple anomalies ({category_anomaly_counts[cat]}) "
                        f"in STEEPs category '{cat}'. Investigate pattern."
                    ),
                })

    return alerts


# ──────────────────────────────────────────────────────────────────────
# Internal Helpers (stdlib math only — no numpy)
# ──────────────────────────────────────────────────────────────────────

def _variance(values: list[float]) -> float:
    """Compute population variance."""
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)


def _stddev(values: list[float]) -> float:
    """Compute population standard deviation."""
    return math.sqrt(_variance(values))


def _detect_steeps_in_text(text: str) -> list[str]:
    """Detect which STEEPs domains are mentioned in text.

    Returns list of STEEPs codes found.
    """
    text_lower = text.lower()
    steeps_keywords: dict[str, list[str]] = {
        "S": ["social", "demographic", "education", "labor",
              "사회", "인구", "교육", "노동"],
        "T": ["technology", "AI", "digital", "quantum",
              "기술", "디지털", "양자"],
        "E": ["economy", "finance", "market", "trade",
              "경제", "금융", "시장", "무역"],
        "Env": ["climate", "environment", "carbon", "energy",
                "기후", "환경", "탄소", "에너지"],
        "P": ["policy", "regulation", "government", "law",
              "정책", "규제", "정부", "법"],
        "s": ["ethics", "values", "psychology", "culture",
              "윤리", "가치관", "심리", "문화"],
    }
    found = []
    for code, keywords in steeps_keywords.items():
        if any(kw in text_lower for kw in keywords):
            found.append(code)
    return found


# ──────────────────────────────────────────────────────────────────────
# CLI Entry Point (4 subcommands)
# ──────────────────────────────────────────────────────────────────────

def _load_json(path: str) -> dict:
    """Load a JSON file and return its contents."""
    file_path = Path(path)
    if not file_path.exists():
        logger.error(f"File not found: {path}")
        sys.exit(1)
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    """Write data to a JSON file, creating parent directories."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"[SAVE] Output written: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "News Signal Processor — "
            "FSSF / Tipping Point / Anomaly / Alert for WF4"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", help="Processing mode")
    subparsers.required = True

    # ── fssf-hints ──
    fssf_parser = subparsers.add_parser(
        "fssf-hints",
        help="Compute FSSF classification hints from signal statistics",
    )
    fssf_parser.add_argument(
        "--input", "-i", required=True,
        help="Classified signals JSON file",
    )
    fssf_parser.add_argument(
        "--history",
        help="Historical signals JSON (for frequency/novelty computation)",
    )
    fssf_parser.add_argument(
        "--output", "-o", required=True,
        help="Output JSON file path for FSSF hints",
    )

    # ── tipping-point ──
    tp_parser = subparsers.add_parser(
        "tipping-point",
        help="Detect tipping point indicators via CSD analysis",
    )
    tp_parser.add_argument(
        "--input", "-i", required=True,
        help="Signals database JSON (with daily counts history)",
    )
    tp_parser.add_argument(
        "--window", type=int, default=7,
        help="Rolling window size for CSD computation (default: 7)",
    )
    tp_parser.add_argument(
        "--output", "-o", required=True,
        help="Output JSON file path for tipping point status",
    )

    # ── anomaly ──
    anomaly_parser = subparsers.add_parser(
        "anomaly",
        help="Statistical anomaly detection (z-score, cross-domain, concentration)",
    )
    anomaly_parser.add_argument(
        "--input", "-i", required=True,
        help="Classified signals JSON file",
    )
    anomaly_parser.add_argument(
        "--window", type=int, default=14,
        help="Rolling window for z-score baseline (default: 14)",
    )
    anomaly_parser.add_argument(
        "--output", "-o", required=True,
        help="Output JSON file path for anomaly flags",
    )

    # ── alert-eval ──
    alert_parser = subparsers.add_parser(
        "alert-eval",
        help="Evaluate 5 alert trigger conditions with severity levels",
    )
    alert_parser.add_argument(
        "--input", "-i", required=True,
        help="Processed signals JSON (with FSSF, tipping, anomaly fields)",
    )
    alert_parser.add_argument(
        "--output", "-o", required=True,
        help="Output JSON file path for alert evaluation",
    )

    args = parser.parse_args()
    scan_date = datetime.now().strftime("%Y-%m-%d")

    try:
        if args.command == "fssf-hints":
            _cmd_fssf_hints(args, scan_date)
        elif args.command == "tipping-point":
            _cmd_tipping_point(args, scan_date)
        elif args.command == "anomaly":
            _cmd_anomaly(args, scan_date)
        elif args.command == "alert-eval":
            _cmd_alert_eval(args, scan_date)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        logger.error(f"[ERROR] {args.command} failed: {e}")
        sys.exit(1)

    sys.exit(0)


def _cmd_fssf_hints(args: argparse.Namespace, scan_date: str) -> None:
    """Execute fssf-hints subcommand."""
    data = _load_json(args.input)
    signals = data.get("items", data.get("signals", []))

    historical: list[dict] = []
    if args.history:
        hist_path = Path(args.history)
        if hist_path.exists():
            hist_data = _load_json(args.history)
            historical = hist_data.get("signals", hist_data.get("items", []))
        else:
            logger.warning(f"History file not found: {args.history} — using empty history")

    logger.info(
        f"[FSSF] Computing hints for {len(signals)} signals "
        f"({len(historical)} historical)"
    )

    hints = []
    for signal in signals:
        hint = compute_fssf_hints(signal, historical)
        hints.append(hint)

    output = {
        "analysis_date": scan_date,
        "workflow": "wf4-news",
        "mode": "fssf-hints",
        "total_signals": len(signals),
        "historical_signals_used": len(historical),
        "fssf_hints": hints,
    }
    _write_json(args.output, output)
    logger.info(f"[FSSF] {len(hints)} hints computed")


def _cmd_tipping_point(args: argparse.Namespace, scan_date: str) -> None:
    """Execute tipping-point subcommand."""
    data = _load_json(args.input)

    # Support multiple input formats
    daily_counts: list[dict] = []

    if "daily_counts" in data:
        daily_counts = data["daily_counts"]
    elif "signals" in data:
        # Build daily counts from signals database
        daily_counts = _build_daily_counts_from_db(data["signals"])
    elif "items" in data:
        daily_counts = _build_daily_counts_from_db(data["items"])
    else:
        logger.error("[TIPPING] Input must contain 'daily_counts', 'signals', or 'items'")
        sys.exit(1)

    logger.info(
        f"[TIPPING] Analyzing {len(daily_counts)} daily entries "
        f"(window={args.window})"
    )

    result = compute_tipping_point(daily_counts, window=args.window)
    result["analysis_date"] = scan_date
    result["workflow"] = "wf4-news"
    result["mode"] = "tipping-point"

    _write_json(args.output, result)
    logger.info(f"[TIPPING] Overall alert: {result['overall_alert']}")


def _cmd_anomaly(args: argparse.Namespace, scan_date: str) -> None:
    """Execute anomaly subcommand."""
    data = _load_json(args.input)
    signals = data.get("items", data.get("signals", []))

    # Build signal_counts structure from the input
    signal_counts = _build_signal_counts(signals, window=args.window)

    logger.info(
        f"[ANOMALY] Analyzing {len(signals)} signals "
        f"(window={args.window})"
    )

    anomaly_flags = detect_anomaly(signal_counts, window=args.window)

    type_counts = Counter(a["anomaly_type"] for a in anomaly_flags)
    severity_counts = Counter(a["severity"] for a in anomaly_flags)

    output = {
        "analysis_date": scan_date,
        "workflow": "wf4-news",
        "mode": "anomaly",
        "total_signals_analyzed": len(signals),
        "anomaly_flags": anomaly_flags,
        "summary": {
            "total_anomalies": len(anomaly_flags),
            "by_type": dict(type_counts),
            "by_severity": dict(severity_counts),
        },
    }
    _write_json(args.output, output)
    logger.info(f"[ANOMALY] {len(anomaly_flags)} anomalies detected")


def _cmd_alert_eval(args: argparse.Namespace, scan_date: str) -> None:
    """Execute alert-eval subcommand."""
    data = _load_json(args.input)
    signals = data.get("items", data.get("signals", []))

    logger.info(f"[ALERT] Evaluating {len(signals)} signals")

    alerts = evaluate_alert_triggers(signals)

    severity_counts = Counter(a["severity"] for a in alerts)
    condition_counts = Counter(a["condition"] for a in alerts)

    output = {
        "alert_date": scan_date,
        "workflow": "wf4-news",
        "mode": "alert-eval",
        "alerts_dispatched": len(alerts),
        "alerts": alerts,
        "summary": {
            "total_signals_evaluated": len(signals),
            "signals_triggered": len(alerts),
            "signals_below_threshold": len(signals) - len(alerts),
            "by_severity": dict(severity_counts),
            "by_condition": dict(condition_counts),
        },
    }
    _write_json(args.output, output)
    logger.info(
        f"[ALERT] {len(alerts)} alerts dispatched "
        f"(CRITICAL={severity_counts.get('CRITICAL', 0)}, "
        f"HIGH={severity_counts.get('HIGH', 0)}, "
        f"MEDIUM={severity_counts.get('MEDIUM', 0)})"
    )


# ──────────────────────────────────────────────────────────────────────
# CLI Helper: Build structures from raw signal data
# ──────────────────────────────────────────────────────────────────────

def _build_daily_counts_from_db(signals: list[dict]) -> list[dict]:
    """Build daily count time series per STEEPs category from signals list.

    Returns list of dicts: [{"date": "2026-02-01", "S": 3, "T": 2, ...}, ...]
    """
    date_cat_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for signal in signals:
        # Try multiple date field locations
        date = (
            signal.get("date")
            or signal.get("last_seen")
            or signal.get("collected_at", "")[:10]
            or ""
        )
        if not date:
            continue
        date = date[:10]  # Truncate to YYYY-MM-DD

        cat = signal.get("category", signal.get("preliminary_category", "X"))
        date_cat_counts[date][cat] += 1

    if not date_cat_counts:
        return []

    sorted_dates = sorted(date_cat_counts.keys())
    result = []
    for d in sorted_dates:
        entry: dict = {"date": d}
        entry.update(date_cat_counts[d])
        result.append(entry)

    return result


def _build_signal_counts(signals: list[dict], window: int = 14) -> dict:
    """Build the signal_counts structure expected by detect_anomaly.

    Creates:
        - category_counts: daily counts per STEEPs category
        - signals: passthrough
        - source_distribution: count per source name
    """
    # Build per-category daily counts
    date_cat: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    source_counts: dict[str, int] = defaultdict(int)

    for signal in signals:
        date = (
            signal.get("date")
            or signal.get("last_seen")
            or signal.get("collected_at", "")[:10]
            or ""
        )
        if date:
            date = date[:10]
            cat = signal.get("category", signal.get("preliminary_category", "X"))
            date_cat[date][cat] += 1

        source = signal.get("source", {})
        if isinstance(source, dict):
            name = source.get("name", "Unknown")
        else:
            name = "Unknown"
        source_counts[name] += 1

    # Convert to category_counts: {cat: [count_day1, count_day2, ...]}
    all_categories: set[str] = set()
    for counts in date_cat.values():
        all_categories.update(counts.keys())

    sorted_dates = sorted(date_cat.keys())
    category_counts: dict[str, list[float]] = {}
    for cat in all_categories:
        category_counts[cat] = [
            float(date_cat[d].get(cat, 0)) for d in sorted_dates
        ]

    return {
        "category_counts": category_counts,
        "signals": signals,
        "source_distribution": dict(source_counts),
    }


if __name__ == "__main__":
    main()
