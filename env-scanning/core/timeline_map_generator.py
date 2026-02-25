#!/usr/bin/env python3
"""
Timeline Map Generator — Signal Evolution Timeline Visualization
================================================================
evolution-map과 evolution-index에서 테마별 시간축 추적, pSST 궤적,
에스컬레이션 탐지, 교차 WF 시그널을 추출하여 한국어 마크다운 타임라인 맵을 생성한다.

핵심 원칙:
    - evolution-index는 READ-ONLY (파생 출력만 생성)
    - SOT Direct Reading: --registry에서 설정 직접 읽기
    - 모듈 독립성: core/ 내 다른 모듈 import 없음
    - Graceful Degradation: 개별 입력 파일 없으면 해당 WF 건너뜀

Pipeline Position (Step 3.1.4):
    Step 3.1.2: Cross-Workflow Evolution Correlation → cross-evolution-map
    Step 3.1.3: Compute Integrated Evolution Statistics → report-statistics
    → timeline_map_generator.py (THIS) → timeline-map-{date}.md
    Step 3.1.5: Pre-fill Integrated Skeleton

Usage (CLI):
    python3 env-scanning/core/timeline_map_generator.py generate \\
        --registry env-scanning/config/workflow-registry.yaml \\
        --wf1-evolution-map {WF1}/analysis/evolution/evolution-map-{date}.json \\
        --wf2-evolution-map {WF2}/analysis/evolution/evolution-map-{date}.json \\
        --wf3-evolution-map {WF3}/analysis/evolution/evolution-map-{date}.json \\
        --cross-evolution-map {INT}/analysis/evolution/cross-evolution-map-{date}.json \\
        --wf1-index {WF1}/signals/evolution-index.json \\
        --wf2-index {WF2}/signals/evolution-index.json \\
        --wf3-index {WF3}/signals/evolution-index.json \\
        --scan-date 2026-02-11 \\
        --output {INT}/reports/daily/timeline-map-{date}.md

Exit codes:
    0 = SUCCESS
    1 = ERROR (invalid arguments, write failure)
"""

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("timeline_map_generator")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
ENGINE_ID = "timeline_map_generator.py"

# STEEPs code → Korean label mapping
STEEPS_LABELS = {
    "S": "사회(S)",
    "T": "기술(T)",
    "E": "경제(E)",
    "E_Environmental": "환경(Env)",
    "P": "정치(P)",
    "s": "정신적(s)",
}

STEEPS_ORDER = ["S", "T", "E", "E_Environmental", "P", "s"]

# Default theme definitions — validated from manual timeline map
DEFAULT_THEMES = {
    "trade_tariff": {
        "label_ko": "무역·관세 전쟁",
        "label_en": "Trade & Tariffs",
        "keywords_en": [
            "tariff", "trade war", "customs", "import duty",
            "export control", "trade policy", "trade tension",
            "export restriction", "import restriction",
        ],
        "keywords_ko": [
            "관세", "무역", "수출", "수입", "통상", "무역전쟁",
            "수출규제", "수입규제",
        ],
        "steeps": ["E", "P"],
        "priority": "CRITICAL",
    },
    "geopolitics": {
        "label_ko": "지정학적 긴장",
        "label_en": "Geopolitics",
        "keywords_en": [
            "geopolitics", "geopolitical", "us-china", "china-us",
            "nato", "alliance", "sanctions", "diplomacy", "conflict",
            "military", "defense", "security", "arms race",
        ],
        "keywords_ko": [
            "지정학", "미중", "중국", "안보", "동맹", "군사",
            "제재", "외교", "갈등", "분쟁",
        ],
        "steeps": ["P"],
        "priority": "CRITICAL",
    },
    "energy_climate": {
        "label_ko": "에너지·기후 전환",
        "label_en": "Energy & Climate",
        "keywords_en": [
            "climate", "renewable", "solar", "wind", "nuclear",
            "fusion", "carbon", "emission", "energy transition",
            "greenhouse", "sustainability", "esg",
        ],
        "keywords_ko": [
            "기후", "재생에너지", "태양", "풍력", "원전", "핵융합",
            "탄소", "온실가스", "에너지", "지속가능",
        ],
        "steeps": ["E_Environmental", "T"],
        "priority": "HIGH",
    },
    "ai_technology": {
        "label_ko": "AI·기술 진화",
        "label_en": "AI & Technology",
        "keywords_en": [
            "artificial intelligence", "machine learning", "deep learning",
            "llm", "gpt", "agentic", "autonomous", "robotics",
            "quantum computing", "quantum", "6g", "cybersecurity",
        ],
        "keywords_ko": [
            "인공지능", "머신러닝", "딥러닝", "에이전트", "로봇",
            "양자", "사이버", "자율", "생성형",
        ],
        "steeps": ["T"],
        "priority": "HIGH",
    },
    "semiconductor": {
        "label_ko": "반도체 전쟁",
        "label_en": "Semiconductor",
        "keywords_en": [
            "semiconductor", "chip", "hbm", "dram", "nand",
            "tsmc", "samsung", "foundry", "wafer", "lithography",
        ],
        "keywords_ko": [
            "반도체", "칩", "메모리", "파운드리", "웨이퍼",
            "삼성전자", "하이닉스", "시총",
        ],
        "steeps": ["T", "E"],
        "priority": "MEDIUM",
    },
    "demographics": {
        "label_ko": "인구·사회 위기",
        "label_en": "Demographics",
        "keywords_en": [
            "demographics", "demographic", "population", "birth rate",
            "fertility", "aging", "migration", "labor shortage",
            "youth", "housing",
        ],
        "keywords_ko": [
            "인구", "출산", "고령화", "저출생", "청년", "주거",
            "노동", "이민", "인구절벽",
        ],
        "steeps": ["S"],
        "priority": "MEDIUM",
    },
    "biotech_health": {
        "label_ko": "바이오·의료",
        "label_en": "Biotech & Health",
        "keywords_en": [
            "biotech", "crispr", "gene editing", "genomics",
            "pharmaceutical", "vaccine", "medical", "health",
            "pandemic", "drug discovery",
        ],
        "keywords_ko": [
            "바이오", "유전자", "의료", "의대", "제약", "백신",
            "헬스", "건강", "크리스퍼",
        ],
        "steeps": ["T", "S"],
        "priority": "MEDIUM",
    },
    "nuclear_security": {
        "label_ko": "핵무기·전략 균형",
        "label_en": "Nuclear Security",
        "keywords_en": [
            "nuclear weapon", "nuclear arms", "nuclear proliferation",
            "new start", "arms control", "icbm", "warhead",
            "nuclear treaty", "deterrence",
        ],
        "keywords_ko": [
            "핵무기", "핵군비", "핵확산", "군축", "전략무기",
            "억제력", "핵전략",
        ],
        "steeps": ["P"],
        "priority": "MEDIUM",
    },
}

# Priority level ordering
PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
PRIORITY_ICONS = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}


# ---------------------------------------------------------------------------
# 1. load_timeline_config — SOT에서 설정 읽기
# ---------------------------------------------------------------------------

def load_timeline_config(registry_path: str) -> dict:
    """Read timeline_map configuration from SOT (workflow-registry.yaml).

    Args:
        registry_path: Path to workflow-registry.yaml

    Returns:
        Dict with timeline_map settings. Empty dict if disabled or missing.
    """
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to read registry: {e}")
        return {}

    system = registry.get("system", {})
    sig_evo = system.get("signal_evolution", {})

    # Check if signal_evolution itself is enabled
    if not sig_evo.get("enabled", False):
        logger.info("signal_evolution.enabled=false — returning empty config")
        return {}

    tl_cfg = sig_evo.get("timeline_map", {})
    if not tl_cfg.get("enabled", False):
        logger.info("timeline_map.enabled=false — returning empty config")
        return {}

    return {
        "enabled": True,
        "lookback_days": tl_cfg.get("lookback_days", 7),
        "min_signals_for_theme": tl_cfg.get("min_signals_for_theme", 2),
        "top_n_psst": tl_cfg.get("top_n_psst", 10),
        "generator_script": tl_cfg.get("generator_script", ""),
        "output_filename_pattern": tl_cfg.get("output_filename_pattern", "timeline-map-{date}.md"),
    }


# ---------------------------------------------------------------------------
# 2. discover_evolution_history — evolution-index에서 lookback 범위 내 thread history 추출
# ---------------------------------------------------------------------------

def discover_evolution_history(
    index_data: dict,
    lookback_days: int,
    scan_date: str,
) -> List[dict]:
    """Extract thread history entries within the lookback window from an evolution-index.

    Args:
        index_data: Parsed evolution-index.json dict
        lookback_days: Number of days to look back from scan_date
        scan_date: Current scan date (YYYY-MM-DD)

    Returns:
        List of flattened appearance dicts with thread metadata.
    """
    if not index_data:
        return []

    try:
        end_date = datetime.strptime(scan_date, "%Y-%m-%d")
        start_date = end_date - timedelta(days=lookback_days)
    except ValueError:
        logger.warning(f"Invalid scan_date: {scan_date}")
        return []

    entries = []
    threads = index_data.get("threads", {})
    for thread_id, thread in threads.items():
        canonical_title = thread.get("canonical_title", "")
        primary_category = thread.get("primary_category", "")
        keywords = thread.get("keywords", [])

        for appearance in thread.get("appearances", []):
            app_date_str = appearance.get("scan_date", "")
            try:
                app_date = datetime.strptime(app_date_str, "%Y-%m-%d")
            except ValueError:
                continue

            if start_date <= app_date <= end_date:
                entries.append({
                    "thread_id": thread_id,
                    "canonical_title": canonical_title,
                    "primary_category": primary_category,
                    "keywords": keywords,
                    "scan_date": app_date_str,
                    "signal_id": appearance.get("signal_id", ""),
                    "title": appearance.get("title", canonical_title),
                    "psst_score": appearance.get("psst_score", 0) or 0,
                    "source": appearance.get("source", ""),
                })

    return entries


# ---------------------------------------------------------------------------
# 3. load_evolution_maps — 3개 WF evolution-map JSON 로딩
# ---------------------------------------------------------------------------

def load_evolution_maps(wf_map_paths: Dict[str, str]) -> Dict[str, dict]:
    """Load evolution-map JSON files for each workflow.

    Args:
        wf_map_paths: Dict mapping workflow label to file path.
            e.g. {"wf1": "/path/to/evolution-map.json", "wf2": "...", "wf3": "..."}

    Returns:
        Dict mapping workflow label to parsed JSON. Missing files return empty dict.
    """
    result = {}
    for label, path in wf_map_paths.items():
        if not path:
            result[label] = {}
            continue
        p = Path(path)
        if not p.exists():
            logger.warning(f"Evolution map not found for {label}: {path}")
            result[label] = {}
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                result[label] = json.load(f)
            logger.info(f"Loaded evolution map for {label}: {path}")
        except Exception as e:
            logger.warning(f"Failed to load evolution map for {label}: {e}")
            result[label] = {}
    return result


# ---------------------------------------------------------------------------
# 4. cluster_by_theme — 테마별 키워드 기반 클러스터링
# ---------------------------------------------------------------------------

def cluster_by_theme(
    all_entries: List[dict],
    themes_config: Optional[Dict[str, dict]] = None,
    min_signals: int = 2,
) -> Dict[str, dict]:
    """Cluster signal entries by theme using bilingual keyword matching.

    Args:
        all_entries: List of flattened signal/appearance dicts with
            'title', 'canonical_title', 'keywords', 'psst_score', 'scan_date', 'source_wf'
        themes_config: Theme definitions dict (defaults to DEFAULT_THEMES)
        min_signals: Minimum signals required to include a theme

    Returns:
        Dict mapping theme_id to {label_ko, label_en, priority, signals: [...], count: N}.
        Only themes with count >= min_signals are included.
    """
    if themes_config is None:
        themes_config = DEFAULT_THEMES

    clusters = {}
    for theme_id, theme_def in themes_config.items():
        clusters[theme_id] = {
            "label_ko": theme_def["label_ko"],
            "label_en": theme_def["label_en"],
            "priority": theme_def.get("priority", "MEDIUM"),
            "signals": [],
        }

    # Build keyword patterns for efficient matching
    theme_patterns = {}
    for theme_id, theme_def in themes_config.items():
        all_kws = []
        for kw in theme_def.get("keywords_en", []):
            all_kws.append(kw.lower())
        for kw in theme_def.get("keywords_ko", []):
            all_kws.append(kw.lower())
        theme_patterns[theme_id] = all_kws

    for entry in all_entries:
        # Build searchable text from entry
        title = (entry.get("title", "") or "").lower()
        canonical = (entry.get("canonical_title", "") or "").lower()
        keywords_list = entry.get("keywords", [])
        keywords_text = " ".join(
            kw.lower() if isinstance(kw, str) else "" for kw in keywords_list
        )
        search_text = f"{title} {canonical} {keywords_text}"

        matched_themes = set()
        for theme_id, kw_list in theme_patterns.items():
            for kw in kw_list:
                if kw in search_text:
                    matched_themes.add(theme_id)
                    break

        for theme_id in matched_themes:
            clusters[theme_id]["signals"].append(entry)

    # Filter by min_signals and sort by priority
    result = {}
    for theme_id, cluster in clusters.items():
        cluster["count"] = len(cluster["signals"])
        if cluster["count"] >= min_signals:
            result[theme_id] = cluster

    # Sort by priority then by count (descending)
    result = dict(
        sorted(
            result.items(),
            key=lambda x: (PRIORITY_ORDER.get(x[1]["priority"], 99), -x[1]["count"]),
        )
    )

    return result


# ---------------------------------------------------------------------------
# 5. compute_steeps_timeline — 날짜별 STEEPs 분포 집계
# ---------------------------------------------------------------------------

def compute_steeps_timeline(all_entries: List[dict]) -> Dict[str, Dict[str, int]]:
    """Compute per-date STEEPs distribution matrix.

    Args:
        all_entries: List of signal entries with 'scan_date' and 'primary_category'

    Returns:
        Dict mapping date_str → {steeps_code: count}. Sorted by date ascending.
    """
    timeline = defaultdict(lambda: defaultdict(int))

    for entry in all_entries:
        date = entry.get("scan_date", "")
        category = entry.get("primary_category", "")
        if date and category:
            timeline[date][category] += 1

    # Sort by date
    return dict(sorted(timeline.items()))


# ---------------------------------------------------------------------------
# 6. compute_psst_rankings — pSST 기준 Top-N 시그널 추출
# ---------------------------------------------------------------------------

def compute_psst_rankings(all_entries: List[dict], top_n: int = 10) -> List[dict]:
    """Extract top-N signals by pSST score.

    Args:
        all_entries: List of signal entries with 'psst_score'
        top_n: Number of top signals to return

    Returns:
        List of top-N entries sorted by pSST descending.
    """
    # Filter entries with valid pSST
    scored = [e for e in all_entries if (e.get("psst_score") or 0) > 0]

    # Sort by pSST descending, then by date descending for ties
    scored.sort(key=lambda x: (-(x.get("psst_score") or 0), x.get("scan_date", "")))

    # Deduplicate by title (keep highest pSST)
    seen_titles = set()
    unique = []
    for entry in scored:
        title_key = (entry.get("title") or entry.get("canonical_title", "")).lower().strip()
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique.append(entry)

    return unique[:top_n]


# ---------------------------------------------------------------------------
# 7. detect_escalations — 테마별 pSST 상승 추이로 에스컬레이션 탐지
# ---------------------------------------------------------------------------

def detect_escalations(
    theme_clusters: Dict[str, dict],
    min_signals: int = 2,
) -> List[dict]:
    """Detect escalation patterns in theme clusters.

    An escalation is detected when a theme's average pSST increases over time,
    or when signal count grows across dates.

    Args:
        theme_clusters: Output from cluster_by_theme()
        min_signals: Minimum signals across ≥2 dates needed for escalation detection

    Returns:
        List of escalation dicts with theme info, trajectory, and current pSST.
    """
    escalations = []

    for theme_id, cluster in theme_clusters.items():
        signals = cluster.get("signals", [])
        if len(signals) < min_signals:
            continue

        # Group by date
        by_date = defaultdict(list)
        for sig in signals:
            date = sig.get("scan_date", "")
            if date:
                by_date[date].append(sig.get("psst_score", 0) or 0)

        if len(by_date) < 2:
            continue

        sorted_dates = sorted(by_date.keys())

        # Compute per-date stats
        date_stats = []
        for d in sorted_dates:
            scores = by_date[d]
            avg = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            date_stats.append({
                "date": d,
                "count": len(scores),
                "avg_psst": round(avg, 1),
                "max_psst": max_score,
            })

        # Detect escalation: avg_psst trending up or count increasing
        first_avg = date_stats[0]["avg_psst"]
        last_avg = date_stats[-1]["avg_psst"]
        first_count = date_stats[0]["count"]
        last_count = date_stats[-1]["count"]
        current_max = date_stats[-1]["max_psst"]

        is_escalating = (last_avg > first_avg) or (last_count > first_count)

        if is_escalating:
            trajectory_parts = []
            for ds in date_stats:
                trajectory_parts.append(f"{ds['date'][-5:]}({ds['avg_psst']})")
            trajectory = " → ".join(trajectory_parts)

            direction = "↑" if last_avg > first_avg else "→"
            escalations.append({
                "theme_id": theme_id,
                "label_ko": cluster["label_ko"],
                "priority": cluster["priority"],
                "trajectory": trajectory,
                "current_psst": current_max,
                "direction": direction,
                "date_stats": date_stats,
                "signal_count": len(signals),
            })

    # Sort by current_psst descending
    escalations.sort(key=lambda x: -(x.get("current_psst") or 0))

    return escalations


# ---------------------------------------------------------------------------
# 8. find_cross_wf_signals — cross-evolution-map에서 교차 WF 시그널 추출
# ---------------------------------------------------------------------------

def find_cross_wf_signals(cross_map: dict) -> List[dict]:
    """Extract cross-workflow signal correlations from cross-evolution-map.

    Args:
        cross_map: Parsed cross-evolution-map JSON

    Returns:
        List of correlation dicts for display in the timeline map.
    """
    if not cross_map:
        return []

    correlations = cross_map.get("correlations", [])
    if not correlations:
        return []

    # Sort by combined_score descending
    sorted_corrs = sorted(correlations, key=lambda x: -(x.get("combined_score", 0)))

    return sorted_corrs


# ---------------------------------------------------------------------------
# 9. format_timeline_markdown — 전체 데이터를 한국어 마크다운으로 포맷팅
# ---------------------------------------------------------------------------

def format_timeline_markdown(
    scan_date: str,
    lookback_days: int,
    wf_counts: Dict[str, int],
    theme_clusters: Dict[str, dict],
    steeps_timeline: Dict[str, Dict[str, int]],
    psst_rankings: List[dict],
    cross_wf_signals: List[dict],
    escalations: List[dict],
) -> str:
    """Format all timeline data into a Korean markdown document.

    Args:
        scan_date: Current scan date (YYYY-MM-DD)
        lookback_days: Number of days the map covers
        wf_counts: {wf_label: signal_count}
        theme_clusters: Output from cluster_by_theme()
        steeps_timeline: Output from compute_steeps_timeline()
        psst_rankings: Output from compute_psst_rankings()
        cross_wf_signals: Output from find_cross_wf_signals()
        escalations: Output from detect_escalations()

    Returns:
        Complete markdown string.
    """
    lines = []

    # Compute date range
    try:
        end = datetime.strptime(scan_date, "%Y-%m-%d")
        start = end - timedelta(days=lookback_days - 1)
        start_str = start.strftime("%Y-%m-%d")
    except ValueError:
        start_str = scan_date

    total_signals = sum(wf_counts.values())

    # Header
    lines.append("# 시그널 진화 타임라인 맵")
    lines.append("## Signal Evolution Timeline Map")
    lines.append("")
    lines.append(f"**기간**: {start_str} ~ {scan_date} ({lookback_days}일간)")
    lines.append(f"**생성일**: {scan_date}")
    lines.append(f"**엔진**: Timeline Map Generator v{VERSION}")

    wf_parts = []
    for label in ["wf1", "wf2", "wf3", "wf4"]:
        c = wf_counts.get(label, 0)
        if c > 0:
            wf_display = {"wf1": "WF1(일반)", "wf2": "WF2(arXiv)", "wf3": "WF3(네이버)", "wf4": "WF4(멀티글로벌)"}.get(label, label)
            wf_parts.append(f"{wf_display} {c}개")
    lines.append(f"**데이터 소스**: {' | '.join(wf_parts) if wf_parts else '데이터 없음'} = 총 {total_signals}개 시그널")
    lines.append("")
    lines.append("---")

    # Section 0: 타임라인 개관
    lines.append("")
    lines.append("## 타임라인 개관")
    lines.append("")

    sorted_dates = sorted(steeps_timeline.keys()) if steeps_timeline else []
    if sorted_dates:
        date_labels = [d[-5:] for d in sorted_dates]  # MM-DD format
        lines.append("```")
        lines.append("  " + "        ".join(date_labels))

        # Show per-date total signal counts
        for wf_label in ["wf1", "wf2", "wf3", "wf4"]:
            wf_display = {"wf1": "WF1", "wf2": "WF2", "wf3": "WF3", "wf4": "WF4"}.get(wf_label, wf_label)
            # We don't have per-date per-WF counts in steeps_timeline, so show totals
            date_totals = []
            for d in sorted_dates:
                total = sum(steeps_timeline[d].values())
                date_totals.append(str(total))
            lines.append(f"  {wf_display}: " + "  ".join(f"{t:>5}" for t in date_totals))

        lines.append("```")
    else:
        lines.append("*데이터 없음*")

    lines.append("")
    lines.append("---")

    # Section 1: 핵심 테마별 시간축 추적
    lines.append("")
    lines.append("## 1. 핵심 테마별 시간축 추적")
    lines.append("")

    if theme_clusters:
        for theme_id, cluster in theme_clusters.items():
            priority = cluster.get("priority", "MEDIUM")
            icon = PRIORITY_ICONS.get(priority, "🟡")
            label_ko = cluster["label_ko"]
            label_en = cluster["label_en"]
            count = cluster["count"]

            lines.append(f"### {icon} {priority}: {label_ko} ({label_en}) — {count}개 시그널")
            lines.append("")

            # Group signals by date for this theme
            by_date = defaultdict(list)
            for sig in cluster["signals"]:
                d = sig.get("scan_date", "unknown")
                by_date[d].append(sig)

            theme_dates = sorted(by_date.keys())

            # ASCII timeline
            if theme_dates:
                lines.append("```")
                date_header = " ────── ".join(d[-5:] for d in theme_dates)
                lines.append(f"  {date_header}")

                for d in theme_dates:
                    sigs = by_date[d]
                    psst_scores = [s.get("psst_score", 0) for s in sigs if s.get("psst_score")]
                    psst_range = ""
                    if psst_scores:
                        psst_range = f"pSST: {min(psst_scores)}~{max(psst_scores)}"
                    sig_titles = [_truncate(s.get("title", ""), 30) for s in sigs[:3]]
                    lines.append(f"  [{d[-5:]}] {len(sigs)}개 | {psst_range}")
                    for t in sig_titles:
                        lines.append(f"    ▪ {t}")

                lines.append("```")
            lines.append("")

            # Signal table
            lines.append("| 날짜 | WF | pSST | 시그널 |")
            lines.append("|------|-----|------|--------|")

            # Sort by date then pSST descending
            sorted_sigs = sorted(
                cluster["signals"],
                key=lambda x: (x.get("scan_date", ""), -(x.get("psst_score", 0) or 0)),
            )
            for sig in sorted_sigs[:15]:  # Limit to 15 per theme
                d = sig.get("scan_date", "")[-5:]
                wf = sig.get("source_wf", "—")
                psst = sig.get("psst_score", 0) or "—"
                title = sig.get("title", sig.get("canonical_title", ""))
                lines.append(f"| {d} | {wf} | {psst} | {title} |")

            lines.append("")
            lines.append("---")
            lines.append("")
    else:
        lines.append("*테마 클러스터 데이터 없음*")
        lines.append("")

    # Section 2: STEEPs 도메인별 시간축 분포
    lines.append("## 2. STEEPs 도메인별 시간축 분포")
    lines.append("")

    if steeps_timeline:
        dates = sorted(steeps_timeline.keys())
        date_headers = [d[-5:] for d in dates]

        lines.append("```")
        header_line = "         " + "  ".join(f"{h:>8}" for h in date_headers)
        lines.append(header_line)

        for steeps_code in STEEPS_ORDER:
            label = STEEPS_LABELS.get(steeps_code, steeps_code)
            vals = []
            for d in dates:
                count = steeps_timeline[d].get(steeps_code, 0)
                vals.append(f"{count:>8}")
            lines.append(f"  {label:<6}" + "  ".join(vals))

        lines.append("```")
    else:
        lines.append("*STEEPs 분포 데이터 없음*")

    lines.append("")
    lines.append("---")

    # Section 3: pSST 우선순위 Top-N 궤적
    lines.append("")
    lines.append("## 3. pSST 우선순위 Top-10 궤적")
    lines.append("")

    if psst_rankings:
        lines.append("| 순위 | pSST | 날짜 | WF | 시그널 |")
        lines.append("|------|------|------|-----|--------|")

        for i, entry in enumerate(psst_rankings, 1):
            psst = entry.get("psst_score", 0)
            date = entry.get("scan_date", "")[-5:]
            wf = entry.get("source_wf", "—")
            title = entry.get("title", entry.get("canonical_title", ""))
            psst_str = f"**{psst}**" if psst >= 90 else str(psst)
            lines.append(f"| {i} | {psst_str} | {date} | {wf} | {title} |")
    else:
        lines.append("*pSST 데이터 없음*")

    lines.append("")
    lines.append("---")

    # Section 4: 교차 워크플로우 시그널 궤적
    lines.append("")
    lines.append("## 4. 교차 워크플로우 시그널 궤적")
    lines.append("")

    if cross_wf_signals:
        lines.append("| 소스 WF | 시그널 (소스) | 대상 WF | 시그널 (대상) | 유사도 |")
        lines.append("|---------|-------------|---------|-------------|--------|")

        for corr in cross_wf_signals[:20]:  # Limit to 20
            src_wf = corr.get("source_wf", "")
            src_title = _truncate(corr.get("source_title", ""), 40)
            tgt_wf = corr.get("target_wf", "")
            tgt_title = _truncate(corr.get("target_title", ""), 40)
            score = corr.get("combined_score", 0)
            lines.append(
                f"| {src_wf} | {src_title} | {tgt_wf} | {tgt_title} | {score:.2f} |"
            )
    else:
        lines.append("*교차 워크플로우 시그널 없음 (개별 WF evolution-index 필요)*")

    lines.append("")
    lines.append("---")

    # Section 5: 에스컬레이션 모니터링
    lines.append("")
    lines.append("## 5. 에스컬레이션 모니터링")
    lines.append("")

    if escalations:
        lines.append("| # | 테마 | 에스컬레이션 궤적 | 현재 pSST | 방향 |")
        lines.append("|---|------|-------------------|----------|------|")

        for i, esc in enumerate(escalations, 1):
            label = esc["label_ko"]
            trajectory = esc["trajectory"]
            current = esc["current_psst"]
            direction = esc["direction"]
            lines.append(f"| {i} | {label} | {trajectory} | {current} | {direction} |")
    else:
        lines.append("*에스컬레이션 탐지 데이터 없음*")

    lines.append("")
    lines.append("---")

    # Section 6: 메타데이터
    lines.append("")
    lines.append("## 6. 메타데이터")
    lines.append("")
    lines.append("```yaml")
    lines.append(f"engine: Timeline Map Generator v{VERSION}")
    lines.append(f"scan_date: {scan_date}")
    lines.append(f"lookback_days: {lookback_days}")
    lines.append(f"period: {start_str} ~ {scan_date}")

    lines.append("data_sources:")
    for label in ["wf1", "wf2", "wf3", "wf4"]:
        lines.append(f"  {label}: {wf_counts.get(label, 0)} signals")

    lines.append(f"total_signals: {total_signals}")
    lines.append(f"themes_detected: {len(theme_clusters)}")
    lines.append(f"escalations_detected: {len(escalations)}")
    lines.append(f"cross_wf_correlations: {len(cross_wf_signals)}")
    lines.append(f"generated_at: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 10. generate_timeline_map — 메인 진입점
# ---------------------------------------------------------------------------

def generate_timeline_map(
    registry_path: str,
    wf_evolution_map_paths: Dict[str, str],
    wf_index_paths: Dict[str, str],
    cross_evolution_map_path: str,
    scan_date: str,
    output_path: str,
) -> str:
    """Main entry point: load → cluster → format → write.

    Args:
        registry_path: Path to workflow-registry.yaml
        wf_evolution_map_paths: {"wf1": path, "wf2": path, "wf3": path}
        wf_index_paths: {"wf1": path, "wf2": path, "wf3": path}
        cross_evolution_map_path: Path to cross-evolution-map JSON
        scan_date: Current scan date (YYYY-MM-DD)
        output_path: Output markdown file path

    Returns:
        Generated markdown string.
    """
    # 1. Load config from SOT
    config = load_timeline_config(registry_path)
    if not config:
        # Even if disabled, generate a minimal map
        config = {
            "enabled": False,
            "lookback_days": 7,
            "min_signals_for_theme": 2,
            "top_n_psst": 10,
        }
        logger.info("Timeline map config disabled or not found — using defaults")

    lookback_days = config.get("lookback_days", 7)
    min_signals = config.get("min_signals_for_theme", 2)
    top_n = config.get("top_n_psst", 10)

    # 2. Load evolution maps (current day)
    evo_maps = load_evolution_maps(wf_evolution_map_paths)

    # 3. Extract entries from evolution maps
    all_entries = []
    wf_counts = {}

    for wf_label, evo_map in evo_maps.items():
        entries = evo_map.get("evolution_entries", [])
        wf_name = evo_map.get("workflow", wf_label)

        for entry in entries:
            entry["source_wf"] = wf_label.upper()
            # Ensure scan_date is set
            if not entry.get("scan_date"):
                entry["scan_date"] = evo_map.get("scan_date", scan_date)

        all_entries.extend(entries)
        wf_counts[wf_label] = len(entries)

    # 4. Discover historical entries from evolution indices
    for wf_label, idx_path in wf_index_paths.items():
        if not idx_path:
            continue
        p = Path(idx_path)
        if not p.exists():
            logger.warning(f"Evolution index not found for {wf_label}: {idx_path}")
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            historical = discover_evolution_history(index_data, lookback_days, scan_date)
            # Tag with source_wf and add only entries not already present
            existing_ids = {e.get("signal_id") for e in all_entries}
            new_historical = 0
            for h_entry in historical:
                h_entry["source_wf"] = wf_label.upper()
                if h_entry.get("signal_id") not in existing_ids:
                    all_entries.append(h_entry)
                    existing_ids.add(h_entry.get("signal_id"))
                    new_historical += 1
            if new_historical > 0:
                wf_counts[wf_label] = wf_counts.get(wf_label, 0) + new_historical
                logger.info(f"Added {new_historical} historical entries from {wf_label} index")
        except Exception as e:
            logger.warning(f"Failed to read evolution index for {wf_label}: {e}")

    logger.info(f"Total entries collected: {len(all_entries)} across {len(wf_counts)} workflows")

    # 5. Cluster by theme
    theme_clusters = cluster_by_theme(all_entries, min_signals=min_signals)
    logger.info(f"Theme clusters: {len(theme_clusters)} themes detected")

    # 6. Compute STEEPs timeline
    steeps_timeline = compute_steeps_timeline(all_entries)

    # 7. Compute pSST rankings
    psst_rankings = compute_psst_rankings(all_entries, top_n=top_n)

    # 8. Load cross-evolution-map
    cross_map = {}
    if cross_evolution_map_path:
        cp = Path(cross_evolution_map_path)
        if cp.exists():
            try:
                with open(cp, "r", encoding="utf-8") as f:
                    cross_map = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cross-evolution-map: {e}")

    cross_wf_signals = find_cross_wf_signals(cross_map)

    # 9. Detect escalations
    escalations = detect_escalations(theme_clusters, min_signals=min_signals)
    logger.info(f"Escalations detected: {len(escalations)}")

    # 10. Format markdown
    markdown = format_timeline_markdown(
        scan_date=scan_date,
        lookback_days=lookback_days,
        wf_counts=wf_counts,
        theme_clusters=theme_clusters,
        steeps_timeline=steeps_timeline,
        psst_rankings=psst_rankings,
        cross_wf_signals=cross_wf_signals,
        escalations=escalations,
    )

    # 11. Write output
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    logger.info(f"Timeline map written: {output_path} ({len(markdown)} chars)")
    return markdown


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, max_len: int = 50) -> str:
    """Truncate text to max_len with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Timeline Map Generator — Signal Evolution Timeline Visualization"
    )
    subparsers = parser.add_subparsers(dest="command")

    gen_parser = subparsers.add_parser("generate", help="Generate timeline map")
    gen_parser.add_argument(
        "--registry",
        default="env-scanning/config/workflow-registry.yaml",
        help="Path to workflow-registry.yaml (SOT)",
    )
    gen_parser.add_argument("--wf1-evolution-map", default="", help="WF1 evolution-map JSON")
    gen_parser.add_argument("--wf2-evolution-map", default="", help="WF2 evolution-map JSON")
    gen_parser.add_argument("--wf3-evolution-map", default="", help="WF3 evolution-map JSON")
    gen_parser.add_argument("--wf4-evolution-map", default="", help="WF4 evolution-map JSON")
    gen_parser.add_argument(
        "--cross-evolution-map", default="", help="Cross-evolution-map JSON"
    )
    gen_parser.add_argument("--wf1-index", default="", help="WF1 evolution-index JSON")
    gen_parser.add_argument("--wf2-index", default="", help="WF2 evolution-index JSON")
    gen_parser.add_argument("--wf3-index", default="", help="WF3 evolution-index JSON")
    gen_parser.add_argument("--wf4-index", default="", help="WF4 evolution-index JSON")
    gen_parser.add_argument(
        "--scan-date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Scan date (YYYY-MM-DD)",
    )
    gen_parser.add_argument("--output", "-o", required=True, help="Output markdown path")

    args = parser.parse_args()

    if args.command != "generate":
        parser.print_help()
        sys.exit(1)

    try:
        generate_timeline_map(
            registry_path=args.registry,
            wf_evolution_map_paths={
                "wf1": args.wf1_evolution_map,
                "wf2": args.wf2_evolution_map,
                "wf3": args.wf3_evolution_map,
                "wf4": args.wf4_evolution_map,
            },
            wf_index_paths={
                "wf1": args.wf1_index,
                "wf2": args.wf2_index,
                "wf3": args.wf3_index,
                "wf4": args.wf4_index,
            },
            cross_evolution_map_path=args.cross_evolution_map,
            scan_date=args.scan_date,
            output_path=args.output,
        )
        sys.exit(0)
    except Exception as e:
        logger.error(f"Timeline map generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
