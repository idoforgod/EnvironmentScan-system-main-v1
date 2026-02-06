"""
Naver Signal Processor (WF3 Core Module)

Utility functions for WF3-exclusive analysis:
    - FSSF 8-type classification support
    - Three Horizons time classification
    - Tipping Point detection (CSD, Flickering)
    - Anomaly detection (Statistical, Structural)

These functions are called by WF3 worker agents:
    - naver-signal-detector (Phase 2, Step 2.1)
    - naver-pattern-detector (Phase 2, Step 2.2)
    - naver-alert-dispatcher (Phase 3, Step 3.3)

CLI Usage:
    python3 env-scanning/core/naver_signal_processor.py \\
        --mode tipping-point \\
        --input env-scanning/wf3-naver/structured/classified-signals-2026-02-06.json \\
        --history env-scanning/wf3-naver/context/previous-signals.json \\
        --output env-scanning/wf3-naver/analysis/tipping-point-indicators-2026-02-06.json
"""

import argparse
import json
import logging
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("naver_signal_processor")


# ──────────────────────────────────────────────────────────────────────
# FSSF Classification Support
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


@dataclass
class FSSFHints:
    """Heuristic hints for FSSF classification.

    These are pre-computed features that help the AI agent
    make better classification decisions.
    """
    source_count: int = 1         # How many sources report this
    historical_frequency: float = 0.0  # 7-day average mentions
    pattern_match: bool = False   # Matches known trend pattern
    is_event: bool = False        # Specific datable event
    is_first_occurrence: bool = False  # No historical precedent
    breaks_pattern: bool = False  # Contradicts existing trends
    cross_steeps_count: int = 1   # Number of STEEPs domains
    impact_breadth: str = "narrow"  # narrow | broad | global

    def suggest_fssf_type(self) -> tuple[str, float]:
        """Apply decision tree to suggest FSSF type with confidence.

        Returns (fssf_type, confidence).
        The AI agent should use this as a HINT, not a final answer.
        """
        # Decision tree from naver-signal-detector.md
        if self.is_event:
            if self.is_first_occurrence:
                return ("Precursor Event", 0.7)
            if self.breaks_pattern:
                return ("Discontinuity", 0.7)

        if self.source_count <= 2 and self.historical_frequency < 1.0:
            return ("Weak Signal", 0.6)
        if 3 <= self.source_count <= 10:
            return ("Emerging Issue", 0.6)
        if self.source_count > 10:
            if self.cross_steeps_count >= 3 and self.impact_breadth == "global":
                return ("Megatrend", 0.6)
            return ("Trend", 0.6)

        return ("Emerging Issue", 0.4)  # Default with low confidence


def compute_fssf_hints(
    signal: dict,
    historical_signals: list[dict],
    lookback_days: int = 7,
) -> FSSFHints:
    """Compute heuristic FSSF classification hints from data.

    Args:
        signal: Current signal dict (standard format)
        historical_signals: Previous signals from database
        lookback_days: Days to look back for frequency calculation
    """
    title = signal.get("title", "")
    title_lower = title.lower()

    # Count similar historical signals (title keyword overlap)
    title_words = set(title_lower.split())
    similar_count = 0
    for hist in historical_signals:
        hist_words = set(hist.get("title", "").lower().split())
        overlap = len(title_words & hist_words)
        if overlap >= 2:
            similar_count += 1

    freq = similar_count / max(lookback_days, 1)

    # Detect if it's a specific event
    event_keywords = [
        "발표", "출시", "선언", "합의", "체결", "발생", "사고",
        "시행", "개최", "통과", "승인", "결정", "폭발", "붕괴",
    ]
    is_event = any(kw in title for kw in event_keywords)

    # Detect pattern breaks
    break_keywords = [
        "최초", "전례 없", "역사적", "예상 밖", "돌발", "반전",
        "급변", "전환", "처음으로", "이례적",
    ]
    breaks_pattern = any(kw in title for kw in break_keywords)

    # Cross-STEEPs count from content
    content = signal.get("content", {})
    abstract = content.get("abstract", "") if isinstance(content, dict) else ""
    steeps_indicators = {
        "S": ["사회", "인구", "교육", "건강", "세대"],
        "T": ["기술", "AI", "디지털", "로봇", "양자"],
        "E_econ": ["경제", "금융", "투자", "시장", "무역"],
        "E_env": ["기후", "환경", "탄소", "오염", "에너지"],
        "P": ["정책", "규제", "법안", "정부", "국제"],
        "s": ["가치관", "윤리", "심리", "종교", "문화"],
    }
    cross_count = sum(
        1 for domain_kws in steeps_indicators.values()
        if any(kw in abstract for kw in domain_kws)
    )

    return FSSFHints(
        source_count=1,  # Single source (Naver)
        historical_frequency=freq,
        pattern_match=similar_count > 3,
        is_event=is_event,
        is_first_occurrence=similar_count == 0 and is_event,
        breaks_pattern=breaks_pattern,
        cross_steeps_count=max(cross_count, 1),
        impact_breadth="broad" if cross_count >= 3 else "narrow",
    )


# ──────────────────────────────────────────────────────────────────────
# Three Horizons Classification
# ──────────────────────────────────────────────────────────────────────

HORIZON_LABELS = {"H1": "0-2년", "H2": "2-7년", "H3": "7년+"}


def suggest_horizon(signal: dict) -> tuple[str, float]:
    """Suggest Three Horizons classification from signal content.

    Returns (horizon, confidence).
    """
    title = signal.get("title", "")
    content = signal.get("content", {})
    abstract = content.get("abstract", "") if isinstance(content, dict) else ""
    text = title + " " + abstract

    h3_keywords = [
        "패러다임", "혁명", "근본적", "문명", "탈인간", "특이점",
        "양자", "핵융합", "유전자편집", "범용인공지능", "AGI",
        "뇌-컴퓨터", "우주식민", "인공생명",
    ]
    h2_keywords = [
        "실험", "시범", "파일럿", "스타트업", "초기",
        "규제 논의", "표준화", "도입 검토", "시제품", "베타",
    ]
    h1_keywords = [
        "시행", "적용", "현재", "올해", "이번", "당장",
        "내년", "예산", "집행", "개정", "시장 점유",
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
# Tipping Point Detection
# ──────────────────────────────────────────────────────────────────────

@dataclass
class TippingPointResult:
    """Result of tipping point detection for a topic cluster."""
    cluster_id: str
    representative_signal_id: str
    representative_title: str
    alert_level: str  # GREEN | YELLOW | ORANGE | RED
    detection_type: str  # critical_slowing_down | flickering | none
    indicators: dict = field(default_factory=dict)
    evidence: str = ""
    recommended_action: str = ""

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "signal_id": self.representative_signal_id,
            "signal_title": self.representative_title,
            "alert_level": self.alert_level,
            "detection_type": self.detection_type,
            "indicators": self.indicators,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action,
        }


def compute_variance_change(
    daily_counts: list[float],
    baseline_window: int = 30,
    recent_window: int = 7,
) -> float:
    """Compute variance change ratio (recent vs baseline).

    Returns ratio > 1.0 means variance is increasing (CSD indicator).
    Returns 0.0 if insufficient data.
    """
    if len(daily_counts) < baseline_window:
        return 0.0

    baseline = daily_counts[-baseline_window:-recent_window]
    recent = daily_counts[-recent_window:]

    if not baseline or not recent:
        return 0.0

    baseline_var = _variance(baseline)
    recent_var = _variance(recent)

    if baseline_var == 0:
        return 0.0 if recent_var == 0 else 2.0

    return recent_var / baseline_var


def compute_autocorrelation(daily_counts: list[float], lag: int = 1) -> float:
    """Compute lag-1 autocorrelation coefficient.

    High autocorrelation (> 0.7) indicates Critical Slowing Down.
    Returns 0.0 if insufficient data.
    """
    n = len(daily_counts)
    if n < lag + 3:
        return 0.0

    mean = sum(daily_counts) / n
    denominator = sum((x - mean) ** 2 for x in daily_counts)
    if denominator == 0:
        return 0.0

    numerator = sum(
        (daily_counts[i] - mean) * (daily_counts[i + lag] - mean)
        for i in range(n - lag)
    )
    return numerator / denominator


def detect_flickering(sentiment_sequence: list[float]) -> dict:
    """Detect flickering pattern (sentiment oscillation).

    Args:
        sentiment_sequence: Daily sentiment scores (-1.0 to 1.0)

    Returns dict with detection result and polarity switch count.
    """
    if len(sentiment_sequence) < 3:
        return {"detected": False, "polarity_switches": 0, "oscillation_rate": 0.0}

    switches = 0
    for i in range(1, len(sentiment_sequence)):
        if sentiment_sequence[i] * sentiment_sequence[i - 1] < 0:
            switches += 1

    oscillation_rate = switches / (len(sentiment_sequence) - 1)
    return {
        "detected": switches >= 3,
        "polarity_switches": switches,
        "oscillation_rate": round(oscillation_rate, 3),
    }


def compute_alert_level(
    variance_ratio: float,
    autocorrelation: float,
    flickering_detected: bool,
) -> str:
    """Determine tipping point alert level.

    GREEN: No indicators
    YELLOW: 1 CSD indicator OR mild flickering
    ORANGE: 2+ CSD indicators OR strong flickering
    RED: 3+ CSD indicators AND flickering confirmed
    """
    csd_count = 0
    if variance_ratio > 1.5:
        csd_count += 1
    if autocorrelation > 0.7:
        csd_count += 1
    if variance_ratio > 2.0:
        csd_count += 1  # Extra point for extreme variance

    if csd_count >= 3 and flickering_detected:
        return "RED"
    if csd_count >= 2 or (csd_count >= 1 and flickering_detected):
        return "ORANGE"
    if csd_count >= 1 or flickering_detected:
        return "YELLOW"
    return "GREEN"


ALERT_ACTIONS: dict[str, str] = {
    "GREEN": "Standard monitoring",
    "YELLOW": "Increase monitoring frequency for this topic cluster",
    "ORANGE": "Immediate attention required — consider escalation to strategic review",
    "RED": "URGENT — tipping point imminent. Recommend immediate strategic response",
}


def detect_tipping_points(
    signals: list[dict],
    historical_signals: list[dict],
) -> list[TippingPointResult]:
    """Run tipping point detection across all signal topic clusters.

    Groups signals by topic (keyword overlap), then checks each cluster
    for CSD and Flickering indicators against historical data.
    """
    if not historical_signals:
        logger.info("[TIPPING] No historical data — all signals default to GREEN")
        return []

    # Group signals by preliminary_category + title keyword clusters
    clusters = _cluster_signals(signals)
    results = []

    for cluster_id, cluster in clusters.items():
        if not cluster:
            continue

        # Build daily count time series from history
        daily_counts = _build_daily_counts(cluster_id, historical_signals)

        if len(daily_counts) < 7:
            continue  # Need at least 7 days of data

        # CSD detection
        var_ratio = compute_variance_change(daily_counts)
        autocorr = compute_autocorrelation(daily_counts)

        # Flickering (placeholder sentiment: use title sentiment polarity)
        sentiments = _extract_sentiment_proxy(cluster_id, historical_signals)
        flicker = detect_flickering(sentiments)

        alert = compute_alert_level(var_ratio, autocorr, flicker["detected"])

        if alert != "GREEN":
            rep = cluster[0]
            results.append(TippingPointResult(
                cluster_id=cluster_id,
                representative_signal_id=rep.get("id", ""),
                representative_title=rep.get("title", ""),
                alert_level=alert,
                detection_type="critical_slowing_down" if var_ratio > 1.5 else "flickering",
                indicators={
                    "variance_change": round(var_ratio, 3),
                    "autocorrelation": round(autocorr, 3),
                    "sentiment_oscillation": flicker["polarity_switches"],
                    "oscillation_rate": flicker["oscillation_rate"],
                },
                evidence=_build_evidence(var_ratio, autocorr, flicker),
                recommended_action=ALERT_ACTIONS[alert],
            ))

    return results


# ──────────────────────────────────────────────────────────────────────
# Anomaly Detection
# ──────────────────────────────────────────────────────────────────────

@dataclass
class AnomalyResult:
    """Result of anomaly detection for a signal."""
    signal_id: str
    anomaly_type: str  # statistical | structural
    subtype: str       # z_score | new_cluster | volume_spike | cross_domain | single_source
    severity: str      # Low | Medium | High
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "type": self.anomaly_type,
            "subtype": self.subtype,
            "severity": self.severity,
            "detail": self.detail,
        }


def detect_anomalies(
    signals: list[dict],
    historical_signals: list[dict],
    z_threshold: float = 3.0,
) -> list[AnomalyResult]:
    """Detect statistical and structural anomalies in the signal set.

    Statistical: z-score of topic frequency, new keyword clusters, volume spikes
    Structural: cross-domain signals, single-source dominance, temporal clustering
    """
    anomalies: list[AnomalyResult] = []

    # Build historical keyword frequency baseline
    hist_keywords = _build_keyword_baseline(historical_signals)

    for signal in signals:
        sid = signal.get("id", "")
        content = signal.get("content", {})
        abstract = content.get("abstract", "") if isinstance(content, dict) else ""
        keywords = content.get("keywords", []) if isinstance(content, dict) else []

        # Statistical: new keyword cluster
        if keywords:
            new_kws = [kw for kw in keywords if kw not in hist_keywords]
            if len(new_kws) >= 3:
                anomalies.append(AnomalyResult(
                    signal_id=sid,
                    anomaly_type="statistical",
                    subtype="new_cluster",
                    severity="Medium",
                    detail=f"New keyword cluster: {new_kws[:5]}",
                ))

        # Structural: cross-domain (check if STEEPs doesn't match section)
        prelim = signal.get("preliminary_category", "")
        source = signal.get("source", {})
        section = source.get("section", "") if isinstance(source, dict) else ""
        if prelim and section:
            expected = _expected_steeps(section)
            if expected and prelim != expected:
                anomalies.append(AnomalyResult(
                    signal_id=sid,
                    anomaly_type="structural",
                    subtype="cross_domain",
                    severity="Low",
                    detail=f"Section {section} classified as {prelim} (expected {expected})",
                ))

    # Structural: single source dominance
    press_counts: dict[str, int] = Counter()
    for signal in signals:
        source = signal.get("source", {})
        press = source.get("press", "Unknown") if isinstance(source, dict) else "Unknown"
        press_counts[press] += 1

    total_signals = len(signals)
    if total_signals > 0:
        for press, count in press_counts.items():
            ratio = count / total_signals
            if ratio > 0.7:
                anomalies.append(AnomalyResult(
                    signal_id="AGGREGATE",
                    anomaly_type="structural",
                    subtype="single_source",
                    severity="Medium",
                    detail=f"Press '{press}' dominates with {ratio:.0%} of articles",
                ))

    return anomalies


# ──────────────────────────────────────────────────────────────────────
# Alert Trigger Evaluation
# ──────────────────────────────────────────────────────────────────────

def evaluate_alert_triggers(signal: dict) -> Optional[dict]:
    """Evaluate all 5 alert trigger conditions for a signal.

    Returns trigger info dict if any condition is met, None otherwise.
    """
    fssf = signal.get("fssf_type", "")
    fssf_conf = signal.get("fssf_confidence", 0)
    horizon = signal.get("three_horizons", "")
    priority = signal.get("priority_score", 0)
    tipping = signal.get("tipping_level", "GREEN")
    cross_steeps = signal.get("cross_steeps_count", 0)
    anomaly_count = signal.get("anomaly_count", 0)
    anomaly_high = signal.get("anomaly_high_severity", False)

    # Condition 1: Tipping Point RED
    if tipping == "RED":
        return {
            "condition": "tipping_point_red",
            "urgency": "CRITICAL",
            "action": "URGENT — tipping point imminent. Immediate strategic review needed.",
        }

    # Condition 2: Wild Card + High Priority
    if fssf == "Wild Card" and priority >= 7.0:
        return {
            "condition": "wild_card_high",
            "urgency": "HIGH",
            "action": "Low-probability high-impact event detected. Monitor closely.",
        }

    # Condition 3: Discontinuity + High Confidence
    if fssf == "Discontinuity" and fssf_conf >= 0.7:
        return {
            "condition": "discontinuity_confirmed",
            "urgency": "HIGH",
            "action": "Pattern break confirmed. Review strategic assumptions.",
        }

    # Condition 4: H3 + Weak Signal + cross-STEEPs
    if horizon == "H3" and fssf == "Weak Signal" and cross_steeps >= 2:
        return {
            "condition": "h3_weak_signal_cross",
            "urgency": "MEDIUM",
            "action": "Future system seed detected across multiple domains. Track closely.",
        }

    # Condition 5: Anomaly cluster
    if anomaly_count >= 3 and anomaly_high:
        return {
            "condition": "anomaly_cluster",
            "urgency": "MEDIUM",
            "action": "Multiple anomalies in related signals. Investigate pattern.",
        }

    return None


# ──────────────────────────────────────────────────────────────────────
# Internal Helpers
# ──────────────────────────────────────────────────────────────────────

def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)


def _cluster_signals(signals: list[dict]) -> dict[str, list[dict]]:
    """Group signals by preliminary category + keyword overlap."""
    clusters: dict[str, list[dict]] = defaultdict(list)
    for signal in signals:
        cat = signal.get("preliminary_category", "X")
        # Simple clustering by category (full NLP clustering is AI-driven)
        clusters[cat].append(signal)
    return dict(clusters)


def _build_daily_counts(cluster_id: str, historical: list[dict]) -> list[float]:
    """Build daily signal count time series from history."""
    date_counts: dict[str, int] = Counter()
    for sig in historical:
        cat = sig.get("category", sig.get("preliminary_category", ""))
        if cat == cluster_id:
            date = sig.get("date", sig.get("last_seen", ""))
            if date:
                date_counts[date] += 1

    if not date_counts:
        return []

    sorted_dates = sorted(date_counts.keys())
    return [date_counts[d] for d in sorted_dates]


def _extract_sentiment_proxy(cluster_id: str, historical: list[dict]) -> list[float]:
    """Extract proxy sentiment values from historical signals.

    Uses a very simple heuristic: positive keywords = +1, negative = -1.
    Real sentiment analysis would be done by the AI agent.
    """
    positive = {"성장", "증가", "호조", "개선", "발전", "혁신", "성공", "확대"}
    negative = {"하락", "감소", "위기", "악화", "실패", "축소", "붕괴", "침체"}

    sentiments = []
    for sig in historical:
        cat = sig.get("category", sig.get("preliminary_category", ""))
        if cat != cluster_id:
            continue
        title = sig.get("title", "")
        pos = sum(1 for kw in positive if kw in title)
        neg = sum(1 for kw in negative if kw in title)
        if pos + neg > 0:
            sentiments.append((pos - neg) / (pos + neg))
        else:
            sentiments.append(0.0)

    return sentiments


def _build_evidence(var_ratio: float, autocorr: float, flicker: dict) -> str:
    parts = []
    if var_ratio > 1.5:
        parts.append(f"Variance increased {var_ratio:.1f}x vs baseline")
    if autocorr > 0.7:
        parts.append(f"Autocorrelation at {autocorr:.2f} (threshold 0.7)")
    if flicker["detected"]:
        parts.append(
            f"Flickering detected: {flicker['polarity_switches']} polarity switches"
        )
    return ". ".join(parts) if parts else "No significant indicators"


def _build_keyword_baseline(historical: list[dict]) -> set[str]:
    """Build set of all keywords seen in historical data."""
    keywords: set[str] = set()
    for sig in historical:
        content = sig.get("content", {})
        if isinstance(content, dict):
            for kw in content.get("keywords", []):
                keywords.add(kw)
    return keywords


def _expected_steeps(section: str) -> str:
    """Map Naver section name to expected STEEPs category."""
    mapping = {
        "정치": "P", "경제": "E", "사회": "S",
        "생활문화": "S", "세계": "P", "IT과학": "T",
    }
    return mapping.get(section, "")


# ──────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Naver Signal Processor — FSSF / Tipping Point / Anomaly Detection"
    )
    parser.add_argument(
        "--mode", required=True,
        choices=["fssf-hints", "tipping-point", "anomaly", "alert-eval"],
        help="Processing mode",
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Input signals JSON file",
    )
    parser.add_argument(
        "--history",
        help="Historical signals JSON (for tipping point / FSSF)",
    )
    parser.add_argument(
        "--output", "-o", required=True,
        help="Output JSON file path",
    )
    args = parser.parse_args()

    # Load input signals
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    signals = data.get("items", data.get("signals", []))

    # Load historical data if provided
    historical = []
    if args.history:
        hist_path = Path(args.history)
        if hist_path.exists():
            with open(hist_path, encoding="utf-8") as f:
                hist_data = json.load(f)
            historical = hist_data.get("signals", hist_data.get("items", []))

    # Process
    output: dict = {}
    scan_date = datetime.now().strftime("%Y-%m-%d")

    if args.mode == "fssf-hints":
        hints = []
        for signal in signals:
            h = compute_fssf_hints(signal, historical)
            suggestion, confidence = h.suggest_fssf_type()
            horizon, h_conf = suggest_horizon(signal)
            hints.append({
                "signal_id": signal.get("id", ""),
                "suggested_fssf": suggestion,
                "fssf_confidence": confidence,
                "suggested_horizon": horizon,
                "horizon_confidence": h_conf,
                "hints": {
                    "source_count": h.source_count,
                    "historical_frequency": h.historical_frequency,
                    "is_event": h.is_event,
                    "is_first_occurrence": h.is_first_occurrence,
                    "breaks_pattern": h.breaks_pattern,
                    "cross_steeps_count": h.cross_steeps_count,
                },
            })
        output = {"analysis_date": scan_date, "fssf_hints": hints}

    elif args.mode == "tipping-point":
        results = detect_tipping_points(signals, historical)
        alert_dist = Counter(r.alert_level for r in results)
        overall = "RED" if alert_dist.get("RED") else \
                  "ORANGE" if alert_dist.get("ORANGE") else \
                  "YELLOW" if alert_dist.get("YELLOW") else "GREEN"
        output = {
            "analysis_date": scan_date,
            "tipping_point_indicators": [r.to_dict() for r in results],
            "overall_alert_status": overall,
            "summary": {
                "total_signals_analyzed": len(signals),
                "tipping_indicators_found": len(results),
                "alert_distribution": {
                    "GREEN": len(signals) - len(results),
                    "YELLOW": alert_dist.get("YELLOW", 0),
                    "ORANGE": alert_dist.get("ORANGE", 0),
                    "RED": alert_dist.get("RED", 0),
                },
            },
        }

    elif args.mode == "anomaly":
        results = detect_anomalies(signals, historical)
        type_counts = Counter(r.anomaly_type for r in results)
        sev_counts = Counter(r.severity for r in results)
        output = {
            "analysis_date": scan_date,
            "anomalies": [r.to_dict() for r in results],
            "summary": {
                "total_anomalies": len(results),
                "by_type": dict(type_counts),
                "by_severity": dict(sev_counts),
            },
        }

    elif args.mode == "alert-eval":
        alerts = []
        for signal in signals:
            trigger = evaluate_alert_triggers(signal)
            if trigger:
                alerts.append({
                    "signal_id": signal.get("id", ""),
                    "signal_title": signal.get("title", ""),
                    **trigger,
                })
        output = {
            "alert_date": scan_date,
            "alerts_dispatched": len(alerts),
            "alerts": alerts,
            "non_triggered_summary": {
                "total_signals_evaluated": len(signals),
                "signals_below_threshold": len(signals) - len(alerts),
            },
        }

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logger.info(f"[SAVE] {args.mode} output written: {output_path}")


if __name__ == "__main__":
    main()
