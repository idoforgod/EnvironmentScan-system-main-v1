#!/usr/bin/env python3
"""
Report Statistics Engine — Python이 센다 (Python Counts)
========================================================
classified-signals JSON에서 통계를 프로그래매틱으로 계산하여
보고서 스켈레톤 플레이스홀더를 사전 주입할 값을 생성한다.

핵심 원칙: "LLM이 분류하고, Python이 센다"
    - LLM은 STEEPs 분류, FSSF 유형, Tipping Point 레벨을 결정
    - Python은 그 결과를 정확하게 집계 → 플레이스홀더 값 생성
    - 이를 통해 보고서 통계 할루시네이션을 원천 차단

Pipeline Position:
    temporal_anchor.py → scan-window.json
    report_statistics_engine.py (THIS) → report-statistics.json
                    ↓                           ↓
    report_metadata_injector.py (temporal + statistics) → skeleton-prepared.md
                    ↓
    LLM report-generator (fills ONLY analytical/narrative placeholders)

Usage (CLI):
    python3 env-scanning/core/report_statistics_engine.py \\
        --input classified-signals-{date}.json \\
        --workflow-type naver \\
        --output report-statistics-{date}.json

Usage (importable):
    from core.report_statistics_engine import compute_statistics, build_placeholder_map

Exit codes:
    0 = SUCCESS
    1 = ERROR (missing files, invalid data)
"""

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("report_statistics_engine")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.3.0"
ENGINE_ID = "report_statistics_engine.py"

# STEEPs code → Korean label mapping
STEEPS_LABELS = {
    "S": "사회(S)",
    "T": "기술(T)",
    "E": "경제(E)",
    "E_Environmental": "환경(E)",
    "P": "정치(P)",
    "s": "정신적(s)",
}

# STEEPs code → English label mapping (v1.3.0 bilingual)
STEEPS_LABELS_EN = {
    "S": "Social(S)",
    "T": "Technological(T)",
    "E": "Economic(E)",
    "E_Environmental": "Environmental(E)",
    "P": "Political(P)",
    "s": "Spiritual(s)",
}

# Bilingual text constants — {key: {"ko": ..., "en": ...}}
_BILINGUAL = {
    "not_applicable":       {"ko": "해당 없음", "en": "N/A"},
    "none":                 {"ko": "없음", "en": "None"},
    "disabled":             {"ko": "비활성", "en": "Disabled"},
    "counter_items":        {"ko": "건", "en": ""},
    "counter_signals":      {"ko": "개", "en": ""},
    "counter_days":         {"ko": "일", "en": "d"},
    "counter_times":        {"ko": "회", "en": "x"},
    "simultaneous":         {"ko": "동시", "en": "same day"},
    "no_cross_evo":         {"ko": "시간축 교차 데이터 없음", "en": "No cross-evolution data"},
    "no_cross_corr":        {"ko": "워크플로우 간 시간축 교차 상관 없음",
                             "en": "No cross-workflow temporal correlations"},
    "and_more":             {"ko": "외", "en": "and"},
    # Evolution table headers
    "evo_header_thread":    {"ko": "추적 스레드", "en": "Tracking Thread"},
    "evo_header_days":      {"ko": "추적일수", "en": "Days Tracked"},
    "evo_header_appear":    {"ko": "등장횟수", "en": "Appearances"},
    "evo_header_psst":      {"ko": "pSST 변화", "en": "pSST Change"},
    "evo_header_velocity":  {"ko": "속도", "en": "Velocity"},
    "evo_header_expansion": {"ko": "확장도", "en": "Expansion"},
    # Direction arrows
    "dir_accelerating":     {"ko": "▲ 가속", "en": "▲ Accel"},
    "dir_stable":           {"ko": "→ 안정", "en": "→ Stable"},
    "dir_decelerating":     {"ko": "▼ 감속", "en": "▼ Decel"},
    "dir_volatile":         {"ko": "↕ 변동", "en": "↕ Volatile"},
    # Weekly velocity table
    "weekly_accel_label":   {"ko": "가속", "en": "Accelerating"},
    "weekly_decel_label":   {"ko": "감속", "en": "Decelerating"},
    "wv_header_thread":     {"ko": "스레드", "en": "Thread"},
    "wv_header_days":       {"ko": "추적일수", "en": "Days Tracked"},
    "wv_header_velocity":   {"ko": "속도(velocity)", "en": "Velocity"},
    "wv_header_direction":  {"ko": "방향", "en": "Direction"},
    # Cross-evolution table headers
    "ce_src_wf":            {"ko": "소스 WF", "en": "Source WF"},
    "ce_src_thread":        {"ko": "소스 스레드", "en": "Source Thread"},
    "ce_tgt_wf":            {"ko": "대상 WF", "en": "Target WF"},
    "ce_tgt_thread":        {"ko": "대상 스레드", "en": "Target Thread"},
    "ce_similarity":        {"ko": "유사도", "en": "Similarity"},
    "ce_lead_time":         {"ko": "리드타임", "en": "Lead Time"},
    # WF labels
    "wf1_label":            {"ko": "WF1(일반)", "en": "WF1(General)"},
    "wf2_label":            {"ko": "WF2(arXiv)", "en": "WF2(arXiv)"},
    "wf3_label":            {"ko": "WF3(네이버)", "en": "WF3(Naver)"},
    "wf4_label":            {"ko": "WF4(멀티글로벌)", "en": "WF4(Multi&Global)"},
}


def _t(key: str, lang: str = "ko") -> str:
    """Look up a bilingual text constant. Falls back to Korean if key/lang missing."""
    entry = _BILINGUAL.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get("ko", key))

# Canonical order for STEEPs display
STEEPS_ORDER = ["E", "T", "S", "P", "E_Environmental", "s"]

# FSSF 8 types (canonical order: CRITICAL → HIGH → MEDIUM)
FSSF_TYPES = [
    "Weak Signal",
    "Wild Card",
    "Discontinuity",
    "Driver",
    "Emerging Issue",
    "Precursor Event",
    "Trend",
    "Megatrend",
]

# FSSF type → placeholder abbreviation code
FSSF_ABBREV = {
    "Weak Signal": "WS",
    "Wild Card": "WC",
    "Discontinuity": "DC",
    "Driver": "DR",
    "Emerging Issue": "EI",
    "Precursor Event": "PE",
    "Trend": "TR",
    "Megatrend": "MT",
}

# Three Horizons (canonical order)
HORIZONS = ["H1", "H2", "H3"]

# Tipping Point alert levels (canonical order: most severe first)
ALERT_LEVELS = ["RED", "ORANGE", "YELLOW", "GREEN"]

# pSST grade boundaries
PSST_GRADE_BOUNDARIES = [
    ("A", 90, 100),
    ("B", 70, 89),
    ("C", 50, 69),
    ("D", 0, 49),
]

# Exploration placeholder names (v2.5.0)
EXPLORATION_PLACEHOLDERS = {
    "EXPLORATION_GAPS",
    "EXPLORATION_METHOD",
    "EXPLORATION_DISCOVERED",
    "EXPLORATION_VIABLE",
    "EXPLORATION_SIGNALS",
    "EXPLORATION_PENDING",
}


# ---------------------------------------------------------------------------
# Core Computation Functions
# ---------------------------------------------------------------------------

def compute_statistics(
    classified_data: dict,
    workflow_type: str,
    evolution_map: Optional[dict] = None,
    cross_evolution_map: Optional[dict] = None,
    exploration_candidates_path: Optional[str] = None,
    raw_crawl_data: Optional[dict] = None,
    language: str = "ko",
) -> dict:
    """Master function: classified-signals JSON → statistics dict.

    Args:
        classified_data: Full classified-signals JSON (with classified_signals array)
        workflow_type: "standard", "naver", "arxiv", or "integrated"
        evolution_map: Optional evolution-map JSON from signal_evolution_tracker
        cross_evolution_map: Optional cross-evolution-map JSON (integrated only)
        exploration_candidates_path: Optional path to exploration-candidates.json (WF1)
        language: Output language — "ko" (Korean, default) or "en" (English)

    Returns:
        Statistics dict with raw_distributions and placeholders
    """
    # Key-variant fallback: production data uses "classified_signals" (v2.1.0+)
    # or "signals" (v2.0.x, some v2.1 runs) or "items" (v1.x raw format)
    signals = (classified_data.get("classified_signals")
               or classified_data.get("signals")
               or classified_data.get("items", []))
    total = len(signals)

    stats: dict[str, Any] = {
        "engine_version": VERSION,
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_file": classified_data.get("classification_metadata", {}).get("date", ""),
        "workflow_type": workflow_type,
        "total_signals": total,
        "raw_distributions": {},
    }

    # Universal distributions
    stats["raw_distributions"]["steeps"] = compute_steeps_distribution(signals)

    # WF3/WF4-specific distributions (FSSF-enabled workflows)
    if workflow_type in ("naver", "multiglobal-news"):
        stats["raw_distributions"]["fssf"] = compute_fssf_distribution(signals)
        stats["raw_distributions"]["horizons"] = compute_three_horizons_distribution(signals)
        stats["raw_distributions"]["tipping_point_alerts"] = compute_tipping_point_distribution(signals)

    # pSST grades (universal, when scores are available)
    stats["raw_distributions"]["psst_grades"] = compute_psst_grade_distribution(signals)

    # Evolution distributions (when evolution_map is provided)
    if evolution_map:
        stats["raw_distributions"]["evolution"] = _extract_evolution_distribution(evolution_map)

    # WF4-specific: crawl and translation statistics
    if workflow_type == "multiglobal-news" and raw_crawl_data:
        stats["raw_distributions"]["crawl"] = raw_crawl_data.get("crawl_stats", {})

    # Build placeholder map (includes evolution + exploration placeholders when data available)
    stats["placeholders"] = build_placeholder_map(
        stats, workflow_type, evolution_map, cross_evolution_map,
        exploration_candidates_path=exploration_candidates_path,
        raw_crawl_data=raw_crawl_data,
        language=language,
    )

    return stats


def compute_steeps_distribution(signals: list[dict]) -> dict[str, int]:
    """STEEPs 카테고리별 count. 모든 6개 카테고리를 0으로 초기화."""
    dist = {code: 0 for code in STEEPS_ORDER}
    for signal in signals:
        cat = signal.get("final_category", signal.get("preliminary_category", ""))
        if cat in dist:
            dist[cat] += 1
    return dist


def compute_fssf_distribution(signals: list[dict]) -> dict[str, int]:
    """FSSF 8-type count. 없는 유형은 0으로 채움."""
    dist = {ftype: 0 for ftype in FSSF_TYPES}
    for signal in signals:
        fssf = signal.get("fssf_type", "")
        if fssf in dist:
            dist[fssf] += 1
    return dist


def compute_three_horizons_distribution(signals: list[dict]) -> dict[str, int]:
    """H1/H2/H3 count."""
    dist = {h: 0 for h in HORIZONS}
    for signal in signals:
        horizon = signal.get("horizon", "")
        if horizon in dist:
            dist[horizon] += 1
    return dist


def compute_tipping_point_distribution(signals: list[dict]) -> dict[str, Any]:
    """RED/ORANGE/YELLOW/GREEN count + 해당 신호 제목 목록."""
    dist: dict[str, Any] = {}
    for level in ALERT_LEVELS:
        dist[level] = {"count": 0, "signals": []}

    for signal in signals:
        tp = signal.get("tipping_point", {})
        if not isinstance(tp, dict):
            continue
        level = tp.get("alert_level", "GREEN")
        if level in dist:
            dist[level]["count"] += 1
            dist[level]["signals"].append(signal.get("title", ""))

    return dist


def compute_psst_grade_distribution(signals: list[dict]) -> dict[str, int]:
    """A/B/C/D count. psst_grade 필드 우선, 없으면 psst_score로 계산."""
    dist = {"A": 0, "B": 0, "C": 0, "D": 0}

    for signal in signals:
        grade = signal.get("psst_grade", "")
        if grade in dist:
            dist[grade] += 1
            continue

        score = signal.get("psst_score")
        if score is not None:
            try:
                score_val = float(score)
            except (TypeError, ValueError):
                continue
            computed_grade = _score_to_grade(score_val)
            dist[computed_grade] += 1

    return dist


# ---------------------------------------------------------------------------
# Evolution Statistics (v1.1.0)
# ---------------------------------------------------------------------------

def _extract_evolution_distribution(evolution_map: dict) -> dict:
    """Extract evolution state counts from evolution-map JSON."""
    summary = evolution_map.get("summary", {})
    return {
        "new": summary.get("new_signals", 0),
        "recurring": summary.get("recurring_signals", 0),
        "strengthening": summary.get("strengthening_signals", 0),
        "weakening": summary.get("weakening_signals", 0),
        "faded": summary.get("faded_threads", 0),
        "transformed": summary.get("transformed_signals", 0),
        "active_threads": summary.get("active_threads", 0),
    }


def compute_evolution_statistics(evolution_map: dict, language: str = "ko") -> dict[str, str]:
    """Evolution map → placeholder key→value mapping for skeleton injection.

    Generates:
        EVOLUTION_ACTIVE_THREADS, EVOLUTION_STRENGTHENING_COUNT/PCT,
        EVOLUTION_WEAKENING_COUNT/PCT, EVOLUTION_FADED_COUNT,
        EVOLUTION_NEW_COUNT/PCT, EVOLUTION_RECURRING_COUNT/PCT,
        EVOLUTION_TABLE_STRENGTHENING, EVOLUTION_TABLE_WEAKENING
    """
    summary = evolution_map.get("summary", {})
    entries = evolution_map.get("evolution_entries", [])
    faded = evolution_map.get("faded_threads", [])
    total = summary.get("total_signals_today", 0)

    placeholders: dict[str, str] = {}

    # Counts — NEW/RECURRING/STRENGTHENING/WEAKENING are subsets of today's signals (sum = total)
    placeholders["EVOLUTION_ACTIVE_THREADS"] = str(summary.get("active_threads", 0))
    placeholders["EVOLUTION_NEW_COUNT"] = str(summary.get("new_signals", 0))
    placeholders["EVOLUTION_NEW_PCT"] = _pct(summary.get("new_signals", 0), total)
    placeholders["EVOLUTION_RECURRING_COUNT"] = str(summary.get("recurring_signals", 0))
    placeholders["EVOLUTION_RECURRING_PCT"] = _pct(summary.get("recurring_signals", 0), total)
    placeholders["EVOLUTION_STRENGTHENING_COUNT"] = str(summary.get("strengthening_signals", 0))
    placeholders["EVOLUTION_STRENGTHENING_PCT"] = _pct(summary.get("strengthening_signals", 0), total)
    placeholders["EVOLUTION_WEAKENING_COUNT"] = str(summary.get("weakening_signals", 0))
    placeholders["EVOLUTION_WEAKENING_PCT"] = _pct(summary.get("weakening_signals", 0), total)
    # FADED threads are NOT a subset of today's signals — they are absent history threads.
    # Using today's signal count as denominator produces a meaningless percentage (H1 fix).
    # Show count only; percentage is "—" to avoid population mixing error.
    placeholders["EVOLUTION_FADED_COUNT"] = str(summary.get("faded_threads", 0))
    placeholders["EVOLUTION_FADED_PCT"] = "—"

    # Strengthening table
    strengthening_entries = [e for e in entries if e.get("state") == "STRENGTHENING"]
    placeholders["EVOLUTION_TABLE_STRENGTHENING"] = _format_evolution_table(strengthening_entries, language=language)

    # Weakening table
    weakening_entries = [e for e in entries if e.get("state") == "WEAKENING"]
    placeholders["EVOLUTION_TABLE_WEAKENING"] = _format_evolution_table(weakening_entries, language=language)

    return placeholders


def _format_evolution_table(entries: list, language: str = "ko") -> str:
    """Format evolution entries as a markdown table for skeleton injection.

    | Tracking Thread | Days Tracked | Appearances | pSST Change | Velocity | Expansion |
    """
    if not entries:
        return _t("not_applicable", language)

    h = [_t("evo_header_thread", language), _t("evo_header_days", language),
         _t("evo_header_appear", language), _t("evo_header_psst", language),
         _t("evo_header_velocity", language), _t("evo_header_expansion", language)]
    rows = [f"| {h[0]} | {h[1]} | {h[2]} | {h[3]} | {h[4]} | {h[5]} |",
            "|------------|---------|---------|----------|------|-------|"]

    direction_arrows = {
        "ACCELERATING": _t("dir_accelerating", language),
        "STABLE": _t("dir_stable", language),
        "DECELERATING": _t("dir_decelerating", language),
        "VOLATILE": _t("dir_volatile", language),
    }

    d_suffix = _t("counter_days", language)
    t_suffix = _t("counter_times", language)

    for entry in entries:
        metrics = entry.get("metrics", {})
        # C1 fix: Use canonical_title (human-readable) instead of thread_id fallback
        title = entry.get("canonical_title", "")
        if not title:
            # Fallback chain: history title → thread_id → signal_id
            history = entry.get("thread_history_summary", [])
            title = history[-1].get("title", "") if history else ""
        if not title:
            title = entry.get("thread_id", entry.get("signal_id", ""))

        days = metrics.get("days_tracked", 0)
        appearances = entry.get("appearance_count", 0)
        psst_prev = metrics.get("psst_previous", 0)
        psst_curr = metrics.get("psst_current", 0)
        delta = metrics.get("psst_delta", "0")
        direction = direction_arrows.get(metrics.get("direction", "STABLE"), "→")
        expansion = metrics.get("expansion", 0.0)

        rows.append(
            f"| {title} | {days}{d_suffix} | {appearances}{t_suffix} | {psst_prev}→{psst_curr} ({delta}) | {direction} | {expansion:.2f} |"
        )

    return "\n".join(rows)


def _empty_evolution_placeholders(language: str = "ko") -> dict[str, str]:
    """Return evolution placeholders with empty/zero values (graceful degradation).

    Used when signal_evolution is disabled or no evolution data available.
    """
    na = _t("not_applicable", language)
    return {
        "EVOLUTION_ACTIVE_THREADS": "0",
        "EVOLUTION_NEW_COUNT": "0",
        "EVOLUTION_NEW_PCT": "—",
        "EVOLUTION_RECURRING_COUNT": "0",
        "EVOLUTION_RECURRING_PCT": "—",
        "EVOLUTION_STRENGTHENING_COUNT": "0",
        "EVOLUTION_STRENGTHENING_PCT": "—",
        "EVOLUTION_WEAKENING_COUNT": "0",
        "EVOLUTION_WEAKENING_PCT": "—",
        "EVOLUTION_FADED_COUNT": "0",
        "EVOLUTION_FADED_PCT": "—",
        "EVOLUTION_TABLE_STRENGTHENING": na,
        "EVOLUTION_TABLE_WEAKENING": na,
    }


def compute_weekly_evolution_stats(evolution_maps: list[dict], language: str = "ko") -> dict[str, str]:
    """Aggregate multiple daily evolution-maps into weekly evolution placeholders.

    Args:
        evolution_maps: list of evolution-map-{date}.json dicts from 7 days
        language: Output language — "ko" or "en"

    Returns:
        dict mapping WEEKLY_EVOLUTION_* placeholder names to values.
    """
    if not evolution_maps:
        return _empty_weekly_evolution_placeholders(language)

    # Aggregate counts across all days
    total_threads_set: set[str] = set()
    new_threads: set[str] = set()
    faded_threads: set[str] = set()
    # Track velocity for top accelerating/decelerating
    thread_velocities: dict[str, dict] = {}  # thread_id -> latest entry info

    for evo_map in evolution_maps:
        for entry in evo_map.get("evolution_entries", []):
            tid = entry.get("thread_id", "")
            if tid:
                total_threads_set.add(tid)
            if entry.get("state") == "NEW":
                new_threads.add(tid)
            metrics = entry.get("metrics", {})
            vel = metrics.get("velocity", 0.0)
            history = entry.get("thread_history_summary", [])
            title = history[-1].get("title", tid) if history else tid
            thread_velocities[tid] = {
                "title": title,
                "velocity": vel,
                "direction": metrics.get("direction", "STABLE"),
                "days_tracked": metrics.get("days_tracked", 0),
            }
        for ft in evo_map.get("faded_threads", []):
            faded_threads.add(ft.get("thread_id", ""))

    # Sort by velocity for top accelerating/decelerating tables
    sorted_entries = sorted(thread_velocities.items(), key=lambda x: x[1]["velocity"], reverse=True)
    top_accel = sorted_entries[:5]
    top_decel = sorted_entries[-5:][::-1] if len(sorted_entries) >= 5 else sorted_entries[::-1]
    # Filter: only include genuinely accelerating (vel > 0) / decelerating (vel < 0)
    top_accel = [(tid, info) for tid, info in top_accel if info["velocity"] > 0]
    top_decel = [(tid, info) for tid, info in top_decel if info["velocity"] < 0]

    direction_arrows = {
        "ACCELERATING": _t("dir_accelerating", language),
        "STABLE": _t("dir_stable", language),
        "DECELERATING": _t("dir_decelerating", language),
        "VOLATILE": _t("dir_volatile", language),
    }

    d_suffix = _t("counter_days", language)
    h_thread = _t("wv_header_thread", language)
    h_days = _t("wv_header_days", language)
    h_vel = _t("wv_header_velocity", language)
    h_dir = _t("wv_header_direction", language)

    def _format_velocity_table(items: list, label: str) -> str:
        if not items:
            return _t("not_applicable", language)
        rows = [f"| {label} {h_thread} | {h_days} | {h_vel} | {h_dir} |",
                "|------------|---------|--------------|------|"]
        for _, info in items:
            arrow = direction_arrows.get(info["direction"], "→")
            rows.append(f"| {info['title']} | {info['days_tracked']}{d_suffix} | {info['velocity']:+.2f} | {arrow} |")
        return "\n".join(rows)

    accel_label = _t("weekly_accel_label", language)
    decel_label = _t("weekly_decel_label", language)

    return {
        "WEEKLY_EVOLUTION_TOTAL_THREADS": str(len(total_threads_set)),
        "WEEKLY_EVOLUTION_NEW_THREADS": str(len(new_threads)),
        "WEEKLY_EVOLUTION_FADED_THREADS": str(len(faded_threads)),
        "WEEKLY_EVOLUTION_TOP_ACCELERATING": _format_velocity_table(top_accel, accel_label),
        "WEEKLY_EVOLUTION_TOP_DECELERATING": _format_velocity_table(top_decel, decel_label),
    }


def _empty_weekly_evolution_placeholders(language: str = "ko") -> dict[str, str]:
    """Return weekly evolution placeholders with empty/zero values."""
    na = _t("not_applicable", language)
    return {
        "WEEKLY_EVOLUTION_TOTAL_THREADS": "0",
        "WEEKLY_EVOLUTION_NEW_THREADS": "0",
        "WEEKLY_EVOLUTION_FADED_THREADS": "0",
        "WEEKLY_EVOLUTION_TOP_ACCELERATING": na,
        "WEEKLY_EVOLUTION_TOP_DECELERATING": na,
    }


def merge_evolution_maps(evolution_maps: list[dict]) -> dict:
    """Merge multiple per-WF evolution-maps into a single aggregated map.

    Used by the integrated pipeline to combine WF1+WF2+WF3 evolution data
    into a single data structure that compute_evolution_statistics() can process.
    """
    merged_entries: list = []
    merged_faded: list = []
    totals = {"total_signals_today": 0, "new_signals": 0, "recurring_signals": 0,
              "strengthening_signals": 0, "weakening_signals": 0, "faded_threads": 0,
              "active_threads": 0}

    for evo_map in evolution_maps:
        if not evo_map:
            continue
        summary = evo_map.get("summary", {})
        for key in totals:
            totals[key] += summary.get(key, 0)
        merged_entries.extend(evo_map.get("evolution_entries", []))
        merged_faded.extend(evo_map.get("faded_threads", []))

    return {
        "summary": totals,
        "evolution_entries": merged_entries,
        "faded_threads": merged_faded,
    }


def compute_cross_evolution_table(cross_evolution_map: dict, language: str = "ko") -> str:
    """Format cross-evolution correlations as a markdown table.

    Args:
        cross_evolution_map: output of cross_correlate_threads()
        language: Output language — "ko" or "en"

    Returns:
        Markdown table string for {{INT_EVOLUTION_CROSS_TABLE}}.
    """
    correlations = cross_evolution_map.get("correlations", [])
    if not correlations:
        return _t("no_cross_corr", language)

    wf_labels = {
        "wf1": _t("wf1_label", language),
        "wf2": _t("wf2_label", language),
        "wf3": _t("wf3_label", language),
        "wf4": _t("wf4_label", language),
    }
    h = [_t("ce_src_wf", language), _t("ce_src_thread", language),
         _t("ce_tgt_wf", language), _t("ce_tgt_thread", language),
         _t("ce_similarity", language), _t("ce_lead_time", language)]
    rows = [f"| {h[0]} | {h[1]} | {h[2]} | {h[3]} | {h[4]} | {h[5]} |",
            "|---------|-----------|---------|-----------|--------|---------|"]

    d_suffix = _t("counter_days", language)
    simul = _t("simultaneous", language)

    for corr in correlations[:15]:  # max 15 rows
        src_wf = wf_labels.get(corr.get("source_wf", ""), corr.get("source_wf", ""))
        tgt_wf = wf_labels.get(corr.get("target_wf", ""), corr.get("target_wf", ""))
        src_title = corr.get("source_title", "")[:30]
        tgt_title = corr.get("target_title", "")[:30]
        # v1.3.0+: prefer combined_score; fallback to max() for pre-v1.3.0 data
        sim = corr.get("combined_score", max(corr.get("title_similarity", 0), corr.get("keyword_similarity", 0)))
        lead = corr.get("lead_days", 0)
        lead_str = f"{lead}{d_suffix}" if lead != 0 else simul
        rows.append(f"| {src_wf} | {src_title} | {tgt_wf} | {tgt_title} | {sim:.2f} | {lead_str} |")

    return "\n".join(rows)


def _empty_cross_evolution_placeholder(language: str = "ko") -> str:
    """Return empty cross-evolution table string."""
    return _t("no_cross_evo", language)


# ---------------------------------------------------------------------------
# Exploration Statistics (v2.5.0)
# ---------------------------------------------------------------------------

def compute_exploration_statistics(candidates_path: str, language: str = "ko") -> dict[str, str]:
    """Compute exploration statistics from candidates JSON.

    Reads exploration-candidates-{date}.json produced by SourceExplorer
    and returns placeholder key→value mapping for skeleton injection.

    Args:
        candidates_path: Path to exploration-candidates-{date}.json
        language: Output language — "ko" or "en"

    Returns:
        Dict mapping EXPLORATION_* placeholder names to values
    """
    p = Path(candidates_path)
    if not p.exists():
        return _empty_exploration_placeholders(language)

    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _empty_exploration_placeholders(language)

    viable = data.get("viable_candidates", [])
    non_viable = data.get("non_viable_candidates", [])
    total_signals = data.get("total_exploration_signals", 0)
    method = data.get("method_used", "unknown")

    # Extract gap categories from scan results or viable candidates
    gap_categories: set[str] = set()
    for c in viable + non_viable:
        steeps = c.get("target_steeps", [])
        if isinstance(steeps, list):
            gap_categories.update(steeps)

    # Count pending (viable but not yet decided)
    decided = set()
    for c in viable:
        if c.get("user_decision"):
            decided.add(c.get("name", ""))
    pending = len(viable) - len(decided)

    discovered = len(viable) + len(non_viable)
    viable_count = len(viable)
    sig_suffix = _t("counter_signals", language)
    none_text = _t("none", language)

    return {
        "EXPLORATION_GAPS": ", ".join(sorted(gap_categories)) if gap_categories else none_text,
        "EXPLORATION_METHOD": method,
        "EXPLORATION_DISCOVERED": f"{discovered}{sig_suffix}",
        "EXPLORATION_VIABLE": f"{viable_count}{sig_suffix}",
        "EXPLORATION_SIGNALS": f"{total_signals}{sig_suffix}",
        "EXPLORATION_PENDING": f"{pending}{sig_suffix}",
    }


def _empty_exploration_placeholders(language: str = "ko") -> dict[str, str]:
    """Return exploration placeholders with empty values (exploration disabled)."""
    none_text = _t("none", language)
    disabled_text = _t("disabled", language)
    sig_suffix = _t("counter_signals", language)
    return {
        "EXPLORATION_GAPS": none_text,
        "EXPLORATION_METHOD": disabled_text,
        "EXPLORATION_DISCOVERED": f"0{sig_suffix}",
        "EXPLORATION_VIABLE": f"0{sig_suffix}",
        "EXPLORATION_SIGNALS": f"0{sig_suffix}",
        "EXPLORATION_PENDING": f"0{sig_suffix}",
    }


# ---------------------------------------------------------------------------
# WF4 Crawl & Translation Statistics (v2.10.0)
# ---------------------------------------------------------------------------

def compute_crawl_statistics(raw_data: dict, language: str = "ko") -> dict[str, str]:
    """Compute per-site crawling statistics from raw crawl data.

    Reads the raw/daily-crawl-{date}.json produced by news_direct_crawler.py
    and generates deterministic placeholder values for the WF4 skeleton.

    Args:
        raw_data: Parsed raw crawl JSON (with items[], crawl_stats, language_stats)
        language: Output language — "ko" or "en"

    Returns:
        Dict mapping placeholder names to computed values.
    """
    items = raw_data.get("items", [])
    crawl_stats = raw_data.get("crawl_stats", {})
    site_stats = crawl_stats.get("per_site", {})
    language_stats = crawl_stats.get("per_language", {})
    strategy_stats = crawl_stats.get("per_strategy", {})

    total_sites = crawl_stats.get("total_sites", len(site_stats))
    succeeded = crawl_stats.get("sites_succeeded", 0)
    failed = crawl_stats.get("sites_failed", 0)
    total_articles = len(items)

    # If crawl_stats not present, compute from items
    if not site_stats and items:
        sites_seen: dict[str, int] = {}
        langs_seen: dict[str, int] = {}
        for item in items:
            src = item.get("scan_metadata", {}).get("site_name", "unknown")
            sites_seen[src] = sites_seen.get(src, 0) + 1
            lang = item.get("content", {}).get("original_language",
                   item.get("content", {}).get("language", "unknown"))
            langs_seen[lang] = langs_seen.get(lang, 0) + 1
        site_stats = sites_seen
        language_stats = langs_seen
        total_sites = len(sites_seen)
        succeeded = total_sites
        failed = 0

    placeholders: dict[str, str] = {}
    placeholders["TOTAL_SITES_CRAWLED"] = str(total_sites)
    placeholders["TOTAL_SITES_SUCCEEDED"] = str(succeeded)
    placeholders["TOTAL_SITES_FAILED"] = str(failed)
    placeholders["TOTAL_ARTICLES"] = str(total_articles)

    # Crawl datetime from execution proof
    exec_proof = raw_data.get("scan_metadata", {}).get("execution_proof", {})
    crawl_dt = exec_proof.get("started_at", raw_data.get("collected_at", "N/A"))
    placeholders["CRAWL_DATETIME"] = str(crawl_dt)

    # Signal-to-noise ratio (articles collected / articles after dedup)
    dedup_count = raw_data.get("dedup_stats", {}).get("after_dedup", total_articles)
    sn_ratio = f"{total_articles}:{dedup_count}" if dedup_count else "N/A"
    placeholders["SN_RATIO"] = sn_ratio

    # Defense log table (from crawler's defense stats)
    defense_stats = crawl_stats.get("defense_log", {})
    if defense_stats:
        counter = _t("counter_items", language)
        d_rows = ["| Block Type | Count | Strategy Used | Success Rate |",
                  "|------------|-------|---------------|--------------|"]
        for block_type, info in sorted(defense_stats.items()):
            count = info.get("count", 0)
            strategy = info.get("strategy", "—")
            rate = info.get("success_rate", "—")
            d_rows.append(f"| {block_type} | {count}{counter} | {strategy} | {rate} |")
        placeholders["DEFENSE_LOG_TABLE"] = "\n".join(d_rows)
    else:
        placeholders["DEFENSE_LOG_TABLE"] = _t("not_applicable", language)

    # Per-language counts
    lang_map = {
        "ko": "BY_LANGUAGE_KO", "en": "BY_LANGUAGE_EN",
        "zh": "BY_LANGUAGE_ZH", "ja": "BY_LANGUAGE_JA",
        "de": "BY_LANGUAGE_DE", "fr": "BY_LANGUAGE_FR",
        "ru": "BY_LANGUAGE_RU",
    }
    other_count = 0
    for lang_code, count in language_stats.items():
        ph_key = lang_map.get(lang_code)
        if ph_key:
            placeholders[ph_key] = str(count)
        else:
            other_count += count
    # Fill missing language placeholders with "0"
    for ph_key in lang_map.values():
        placeholders.setdefault(ph_key, "0")
    placeholders["BY_LANGUAGE_OTHER"] = str(other_count)

    # Crawl site table (markdown)
    if site_stats:
        counter = _t("counter_items", language)
        rows = ["| Site | Language | Articles | Strategy | Success Rate |",
                "|------|----------|----------|----------|--------------|"]
        for site_name, count in sorted(site_stats.items(), key=lambda x: -x[1]):
            # Try to extract language/strategy from raw data
            site_lang = "—"
            site_strategy = "—"
            site_rate = "100%"
            for item in items:
                if item.get("scan_metadata", {}).get("site_name") == site_name:
                    site_lang = item.get("content", {}).get("original_language", "—")
                    site_strategy = item.get("scan_metadata", {}).get("crawl_strategy_used", "—")
                    break
            rows.append(f"| {site_name} | {site_lang} | {count}{counter} | {site_strategy} | {site_rate} |")
        placeholders["CRAWL_SITE_TABLE"] = "\n".join(rows)
    else:
        placeholders["CRAWL_SITE_TABLE"] = _t("not_applicable", language)

    return placeholders


def compute_translation_statistics(raw_data: dict, language: str = "ko") -> dict[str, str]:
    """Compute translation statistics from raw crawl data.

    Examines content.original_language and content.translation_confidence
    to produce deterministic placeholder values for the WF4 skeleton.

    Args:
        raw_data: Parsed raw crawl JSON (with items[])
        language: Output language — "ko" or "en"

    Returns:
        Dict mapping TRANSLATION_* placeholder names to computed values.
    """
    items = raw_data.get("items", [])

    total_translated = 0
    total_failed = 0
    lang_translation_stats: dict[str, dict] = {}  # lang -> {count, confidence_sum, failed}

    for item in items:
        content = item.get("content", {})
        orig_lang = content.get("original_language", content.get("language", "en"))
        confidence = content.get("translation_confidence", 1.0)

        if orig_lang not in lang_translation_stats:
            lang_translation_stats[orig_lang] = {"count": 0, "confidence_sum": 0.0, "failed": 0}

        stats = lang_translation_stats[orig_lang]
        stats["count"] += 1

        if orig_lang != "en":  # English articles don't need translation
            if confidence and confidence > 0:
                total_translated += 1
                stats["confidence_sum"] += confidence
            else:
                total_failed += 1
                stats["failed"] += 1

    placeholders: dict[str, str] = {}
    placeholders["TRANSLATION_TOTAL"] = str(total_translated)
    placeholders["TRANSLATION_FAILED"] = str(total_failed)

    # Translation stats table (markdown)
    if lang_translation_stats:
        counter = _t("counter_items", language)
        rows = ["| Language | Total | Translated | Failed | Avg Confidence |",
                "|----------|-------|------------|--------|----------------|"]
        for lang_code, stats in sorted(lang_translation_stats.items()):
            count = stats["count"]
            translated = count - stats["failed"] if lang_code != "en" else 0
            failed = stats["failed"]
            avg_conf = (stats["confidence_sum"] / translated) if translated > 0 else 0.0
            conf_str = f"{avg_conf:.2f}" if lang_code != "en" else "N/A"
            rows.append(f"| {lang_code} | {count}{counter} | {translated}{counter} | {failed}{counter} | {conf_str} |")
        placeholders["TRANSLATION_STATS_TABLE"] = "\n".join(rows)
    else:
        placeholders["TRANSLATION_STATS_TABLE"] = _t("not_applicable", language)

    return placeholders


def _empty_crawl_placeholders(language: str = "ko") -> dict[str, str]:
    """Return crawl statistics placeholders with zero/empty values."""
    na = _t("not_applicable", language)
    return {
        "TOTAL_SITES_CRAWLED": "0", "TOTAL_SITES_SUCCEEDED": "0",
        "TOTAL_SITES_FAILED": "0", "TOTAL_ARTICLES": "0",
        "CRAWL_DATETIME": "N/A", "SN_RATIO": "N/A",
        "DEFENSE_LOG_TABLE": na,
        "BY_LANGUAGE_KO": "0", "BY_LANGUAGE_EN": "0", "BY_LANGUAGE_ZH": "0",
        "BY_LANGUAGE_JA": "0", "BY_LANGUAGE_DE": "0", "BY_LANGUAGE_FR": "0",
        "BY_LANGUAGE_RU": "0", "BY_LANGUAGE_OTHER": "0",
        "CRAWL_SITE_TABLE": na,
        "TRANSLATION_TOTAL": "0", "TRANSLATION_FAILED": "0",
        "TRANSLATION_STATS_TABLE": na,
    }


# ---------------------------------------------------------------------------
# Placeholder Map Builder
# ---------------------------------------------------------------------------

def build_placeholder_map(
    stats: dict,
    workflow_type: str,
    evolution_map: Optional[dict] = None,
    cross_evolution_map: Optional[dict] = None,
    exploration_candidates_path: Optional[str] = None,
    raw_crawl_data: Optional[dict] = None,
    language: str = "ko",
) -> dict[str, str]:
    """Raw stats → skeleton placeholder key→value mapping.

    Universal (all workflows):
        TOTAL_NEW_SIGNALS, DOMAIN_DISTRIBUTION, EVOLUTION_*

    WF1 (standard) additional (when exploration active):
        EXPLORATION_GAPS, EXPLORATION_METHOD, EXPLORATION_DISCOVERED,
        EXPLORATION_VIABLE, EXPLORATION_SIGNALS, EXPLORATION_PENDING

    WF3 (naver) additional:
        FSSF_*_COUNT/PCT, H*_COUNT/PCT, FSSF_DIST_*_COUNT, TIPPING_POINT_ALERT_SUMMARY

    Integrated additional:
        INT_EVOLUTION_CROSS_TABLE
    """
    total = stats["total_signals"]
    raw = stats["raw_distributions"]
    placeholders: dict[str, str] = {}

    # --- Universal ---
    placeholders["TOTAL_NEW_SIGNALS"] = str(total)
    placeholders["DOMAIN_DISTRIBUTION"] = format_domain_distribution(raw["steeps"], language=language)

    # --- WF3/WF4-specific (FSSF-enabled workflows) ---
    if workflow_type in ("naver", "multiglobal-news"):
        fssf = raw.get("fssf", {})
        horizons = raw.get("horizons", {})
        tp = raw.get("tipping_point_alerts", {})

        # FSSF Summary (Section 1)
        for ftype in FSSF_TYPES:
            count = fssf.get(ftype, 0)
            pct = _pct(count, total)
            prefix = _fssf_placeholder_prefix(ftype)
            placeholders[f"{prefix}_COUNT"] = str(count)
            placeholders[f"{prefix}_PCT"] = pct

        # FSSF Section 4.3 counts
        for ftype, abbrev in FSSF_ABBREV.items():
            count = fssf.get(ftype, 0)
            placeholders[f"FSSF_DIST_{abbrev}_COUNT"] = str(count)

        # Three Horizons
        for h in HORIZONS:
            count = horizons.get(h, 0)
            pct = _pct(count, total)
            placeholders[f"{h}_COUNT"] = str(count)
            placeholders[f"{h}_PCT"] = pct

        # Tipping Point summary table
        placeholders["TIPPING_POINT_ALERT_SUMMARY"] = format_tipping_point_summary_table(tp, language=language)

    # --- Evolution (universal, when evolution data available) ---
    if evolution_map:
        placeholders.update(compute_evolution_statistics(evolution_map, language=language))
    else:
        placeholders.update(_empty_evolution_placeholders(language=language))

    # --- Cross-evolution table (integrated only) ---
    if cross_evolution_map:
        placeholders["INT_EVOLUTION_CROSS_TABLE"] = compute_cross_evolution_table(cross_evolution_map, language=language)
    elif workflow_type == "integrated":
        placeholders["INT_EVOLUTION_CROSS_TABLE"] = _empty_cross_evolution_placeholder(language=language)

    # --- Exploration statistics (standard WF1 only, when candidates file provided) ---
    if exploration_candidates_path:
        placeholders.update(compute_exploration_statistics(exploration_candidates_path, language=language))

    # --- WF4 crawl & translation statistics ---
    if workflow_type == "multiglobal-news":
        if raw_crawl_data:
            placeholders.update(compute_crawl_statistics(raw_crawl_data, language=language))
            placeholders.update(compute_translation_statistics(raw_crawl_data, language=language))
        else:
            placeholders.update(_empty_crawl_placeholders(language=language))

    return placeholders


# ---------------------------------------------------------------------------
# Format Functions
# ---------------------------------------------------------------------------

def format_domain_distribution(steeps: dict[str, int], language: str = "ko") -> str:
    """Format STEEPs distribution as comma-separated string.

    KO: '경제(E) 4건, 기술(T) 3건, 사회(S) 3건, ...'
    EN: 'Economic(E) 4, Technological(T) 3, Social(S) 3, ...'

    Categories with 0 count are excluded. Sorted by count descending.
    """
    labels = STEEPS_LABELS_EN if language == "en" else STEEPS_LABELS
    counter = _t("counter_items", language)
    items = []
    for code in STEEPS_ORDER:
        count = steeps.get(code, 0)
        if count > 0:
            label = labels.get(code, code)
            items.append((label, count))

    # Sort by count descending
    items.sort(key=lambda x: x[1], reverse=True)
    return ", ".join(f"{label} {count}{counter}" for label, count in items)


def format_tipping_point_summary_table(tp: dict[str, Any], language: str = "ko") -> str:
    """Generate markdown table rows for tipping point summary (Alert Level | Count | Key Signals).

    Shows up to 3 signal titles per level. Levels with 0 count are excluded.
    """
    rows = []
    more_word = _t("and_more", language)
    counter = _t("counter_items", language)
    for level in ALERT_LEVELS:
        data = tp.get(level, {"count": 0, "signals": []})
        count = data["count"]
        if count == 0:
            continue
        signals = data["signals"]
        # Max 3 signal titles
        if len(signals) > 3:
            titles = ", ".join(signals[:3]) + f" {more_word} {len(signals) - 3}{counter}"
        else:
            titles = ", ".join(signals) if signals else "-"
        rows.append(f"| {level} | {count} | {titles} |")

    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _pct(count: int, total: int) -> str:
    """Compute percentage string. Returns '0%' if total is 0."""
    if total == 0:
        return "0%"
    return f"{round(count / total * 100)}%"


def _score_to_grade(score: float) -> str:
    """Convert pSST score to grade letter."""
    for grade, low, high in PSST_GRADE_BOUNDARIES:
        if low <= score <= high:
            return grade
    return "D"


def _fssf_placeholder_prefix(fssf_type: str) -> str:
    """Convert FSSF type name to placeholder prefix.

    'Weak Signal' → 'FSSF_WEAK_SIGNAL'
    'Emerging Issue' → 'FSSF_EMERGING_ISSUE'
    'Precursor Event' → 'FSSF_PRECURSOR'  (skeleton uses shortened form)
    """
    mapping = {
        "Weak Signal": "FSSF_WEAK_SIGNAL",
        "Wild Card": "FSSF_WILD_CARD",
        "Discontinuity": "FSSF_DISCONTINUITY",
        "Driver": "FSSF_DRIVER",
        "Emerging Issue": "FSSF_EMERGING_ISSUE",
        "Precursor Event": "FSSF_PRECURSOR",
        "Trend": "FSSF_TREND",
        "Megatrend": "FSSF_MEGATREND",
    }
    return mapping.get(fssf_type, f"FSSF_{fssf_type.upper().replace(' ', '_')}")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def _load_json_file(path_str: str, label: str = "file") -> Optional[dict]:
    """Load a JSON file, return None with warning if not found."""
    p = Path(path_str)
    if not p.exists():
        logger.warning(f"{label} not found: {path_str} (proceeding without)")
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Report Statistics Engine — compute statistics from classified signals"
    )
    parser.add_argument(
        "--input", "-i", default=None,
        help="Path to classified-signals JSON file (required for standard/naver/arxiv)",
    )
    parser.add_argument(
        "--workflow-type", required=True,
        choices=["standard", "naver", "multiglobal-news", "arxiv", "integrated", "weekly"],
        help="Workflow type (determines which distributions to compute)",
    )
    parser.add_argument(
        "--output", "-o", required=True,
        help="Output path for report-statistics JSON",
    )
    parser.add_argument(
        "--evolution-map",
        default=None,
        help="Path to evolution-map JSON (single WF, for standard/naver/arxiv)",
    )
    parser.add_argument(
        "--evolution-maps",
        nargs="+", default=None,
        help="Paths to multiple evolution-map JSONs (for integrated mode: 1 per WF)",
    )
    parser.add_argument(
        "--cross-evolution-map",
        default=None,
        help="Path to cross-evolution-map JSON (for integrated mode)",
    )
    parser.add_argument(
        "--weekly-evolution-maps",
        nargs="+", default=None,
        help="Paths to daily evolution-map JSONs (for weekly mode: 1 per day)",
    )
    parser.add_argument(
        "--exploration-candidates",
        default=None,
        help="Path to exploration-candidates JSON (for WF1 standard mode)",
    )
    parser.add_argument(
        "--raw-crawl-data",
        default=None,
        help="Path to raw crawl data JSON (for multiglobal-news mode: crawl/translation stats)",
    )
    parser.add_argument(
        "--language", default="ko", choices=["ko", "en"],
        help="Output language for human-readable strings (default: ko)",
    )
    args = parser.parse_args()
    lang = args.language

    # ── Integrated mode: merge evolution-maps + cross-evolution ──
    if args.workflow_type == "integrated":
        evo_maps = []
        for evo_path in (args.evolution_maps or []):
            data = _load_json_file(evo_path, "evolution-map")
            if data:
                evo_maps.append(data)
        merged_evo = merge_evolution_maps(evo_maps) if evo_maps else None

        cross_evo = None
        if args.cross_evolution_map:
            cross_evo = _load_json_file(args.cross_evolution_map, "cross-evolution-map")

        placeholders: dict[str, str] = {}
        if merged_evo:
            placeholders.update(compute_evolution_statistics(merged_evo, language=lang))
        else:
            placeholders.update(_empty_evolution_placeholders(language=lang))

        if cross_evo:
            placeholders["INT_EVOLUTION_CROSS_TABLE"] = compute_cross_evolution_table(cross_evo, language=lang)
        else:
            placeholders["INT_EVOLUTION_CROSS_TABLE"] = _empty_cross_evolution_placeholder(language=lang)

        stats = {
            "engine_version": VERSION,
            "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "workflow_type": "integrated",
            "mode": "integrated_evolution",
            "evolution_maps_loaded": len(evo_maps),
            "cross_evolution_loaded": cross_evo is not None,
            "placeholders": placeholders,
        }

    # ── Weekly mode: aggregate daily evolution-maps ──
    elif args.workflow_type == "weekly":
        evo_maps = []
        for evo_path in (args.weekly_evolution_maps or []):
            data = _load_json_file(evo_path, "weekly-evolution-map")
            if data:
                evo_maps.append(data)

        placeholders = compute_weekly_evolution_stats(evo_maps, language=lang)

        stats = {
            "engine_version": VERSION,
            "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "workflow_type": "weekly",
            "mode": "weekly_evolution",
            "evolution_maps_loaded": len(evo_maps),
            "placeholders": placeholders,
        }

    # ── Standard mode (standard/naver/arxiv): requires --input ──
    else:
        if not args.input:
            logger.error("--input is required for standard/naver/arxiv workflow types")
            sys.exit(1)

        input_path = Path(args.input)
        if not input_path.exists():
            logger.error(f"Input file not found: {args.input}")
            sys.exit(1)

        with open(input_path, "r", encoding="utf-8") as f:
            classified_data = json.load(f)

        # Load evolution map if provided
        evolution_map = None
        if args.evolution_map:
            evolution_map = _load_json_file(args.evolution_map, "evolution-map")
            if evolution_map:
                logger.info(f"Loaded evolution map: {args.evolution_map}")

        # Load raw crawl data if provided (WF4 multiglobal-news)
        raw_crawl = None
        if args.raw_crawl_data:
            raw_crawl = _load_json_file(args.raw_crawl_data, "raw-crawl-data")

        stats = compute_statistics(
            classified_data, args.workflow_type, evolution_map,
            exploration_candidates_path=args.exploration_candidates,
            raw_crawl_data=raw_crawl,
            language=lang,
        )
        stats["source_file"] = str(input_path)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Print summary
    ph_count = len(stats.get("placeholders", {}))
    print("=" * 60)
    print(f"  Report Statistics Engine v{VERSION}")
    print(f"  Workflow: {args.workflow_type}")
    if "total_signals" in stats:
        print(f"  Total signals: {stats['total_signals']}")
    print(f"  Placeholders generated: {ph_count}")
    if stats.get("raw_distributions", {}).get("tipping_point_alerts"):
        tp_raw = stats["raw_distributions"]["tipping_point_alerts"]
        tp_summary = ", ".join(
            f"{level}={tp_raw[level]['count']}" for level in ALERT_LEVELS
            if tp_raw.get(level, {}).get("count", 0) > 0
        )
        print(f"  Tipping Point: {tp_summary}")
    print(f"  Output: {args.output}")
    print("=" * 60)

    sys.exit(0)


if __name__ == "__main__":
    main()
