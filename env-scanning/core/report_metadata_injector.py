#!/usr/bin/env python3
"""
Report Metadata Injector — Pre-populate Deterministic Placeholders
==================================================================
Before the LLM fills analytical/narrative content into a skeleton template,
this script fills all DETERMINISTIC placeholders (timestamps, scan windows,
statistics) from the scan-window state file produced by temporal_anchor.py
and the report-statistics file produced by report_statistics_engine.py.

Separation Principle:
    Python fills: timestamps, window boundaries, lookback hours, signal counts,
                  distribution tables — anything that has exactly ONE correct value
                  computable from the state/statistics files.
    LLM fills:    analysis, narrative, signal descriptions, strategic implications —
                  anything that requires judgment, reasoning, or creative synthesis.

Supported Temporal Placeholders:
    {{SCAN_WINDOW_START}}      → Window start (Korean formatted datetime)
    {{SCAN_WINDOW_END}}        → Window end (Korean formatted datetime)
    {{SCAN_ANCHOR_TIMESTAMP}}  → T₀ (Korean formatted datetime)
    {{LOOKBACK_HOURS}}         → Per-WF lookback hours (numeric)
    {{WF1_LOOKBACK_HOURS}}     → WF1 lookback hours (integrated report)
    {{WF2_LOOKBACK_HOURS}}     → WF2 lookback hours (integrated report)
    {{WF3_LOOKBACK_HOURS}}     → WF3 lookback hours (integrated report)
    {{DAILY_LOOKBACK_HOURS}}   → Default lookback hours (weekly report)

Supported Statistical Placeholders (from report_statistics_engine.py):
    {{TOTAL_NEW_SIGNALS}}               → Total signal count
    {{DOMAIN_DISTRIBUTION}}             → STEEPs distribution string
    {{FSSF_*_COUNT}} / {{FSSF_*_PCT}}   → FSSF 8-type counts/percentages (WF3)
    {{H*_COUNT}} / {{H*_PCT}}           → Three Horizons counts/percentages (WF3)
    {{FSSF_DIST_*_COUNT}}               → FSSF Section 4.3 counts (WF3)
    {{TIPPING_POINT_ALERT_SUMMARY}}     → Tipping Point alert table (WF3)

Usage (CLI):
    python3 env-scanning/core/report_metadata_injector.py \\
        --skeleton .claude/skills/env-scanner/references/report-skeleton-en.md \\
        --scan-window env-scanning/integrated/logs/scan-window-2026-02-10.json \\
        --statistics env-scanning/wf1-general/reports/report-statistics-2026-02-10.json \\
        --workflow wf1-general \\
        --language en \\
        --output env-scanning/wf1-general/reports/skeleton-prepared-2026-02-10.md

Usage (importable):
    from core.report_metadata_injector import inject_temporal_metadata
    content, report = inject_temporal_metadata(
        skeleton_path, scan_window_path, "wf3-naver",
        statistics_path="report-statistics.json",
    )

Exit codes:
    0 = SUCCESS (all deterministic placeholders replaced)
    1 = ERROR (missing files, missing fields)
    2 = WARN (some placeholders could not be resolved)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.2.0"
INJECTOR_ID = "report_metadata_injector.py"

# All temporal placeholders this injector handles
TEMPORAL_PLACEHOLDERS = {
    "SCAN_WINDOW_START",
    "SCAN_WINDOW_END",
    "SCAN_ANCHOR_TIMESTAMP",
    "LOOKBACK_HOURS",
    "WF1_LOOKBACK_HOURS",
    "WF2_LOOKBACK_HOURS",
    "WF3_LOOKBACK_HOURS",
    "WF4_LOOKBACK_HOURS",
    "DAILY_LOOKBACK_HOURS",
}

# Statistical placeholders (from report_statistics_engine.py)
STATISTICAL_PLACEHOLDERS = {
    "TOTAL_NEW_SIGNALS", "DOMAIN_DISTRIBUTION",
    # FSSF Summary (Section 1)
    "FSSF_WEAK_SIGNAL_COUNT", "FSSF_WEAK_SIGNAL_PCT",
    "FSSF_EMERGING_ISSUE_COUNT", "FSSF_EMERGING_ISSUE_PCT",
    "FSSF_TREND_COUNT", "FSSF_TREND_PCT",
    "FSSF_MEGATREND_COUNT", "FSSF_MEGATREND_PCT",
    "FSSF_DRIVER_COUNT", "FSSF_DRIVER_PCT",
    "FSSF_WILD_CARD_COUNT", "FSSF_WILD_CARD_PCT",
    "FSSF_DISCONTINUITY_COUNT", "FSSF_DISCONTINUITY_PCT",
    "FSSF_PRECURSOR_COUNT", "FSSF_PRECURSOR_PCT",
    # FSSF Section 4.3 counts
    "FSSF_DIST_WS_COUNT", "FSSF_DIST_EI_COUNT", "FSSF_DIST_TR_COUNT",
    "FSSF_DIST_MT_COUNT", "FSSF_DIST_DR_COUNT", "FSSF_DIST_WC_COUNT",
    "FSSF_DIST_DC_COUNT", "FSSF_DIST_PE_COUNT",
    # Three Horizons
    "H1_COUNT", "H1_PCT", "H2_COUNT", "H2_PCT", "H3_COUNT", "H3_PCT",
    # Tipping Point summary
    "TIPPING_POINT_ALERT_SUMMARY",
}

# Evolution placeholders (from signal_evolution_tracker → report_statistics_engine)
EVOLUTION_PLACEHOLDERS = {
    "EVOLUTION_ACTIVE_THREADS",
    "EVOLUTION_NEW_COUNT", "EVOLUTION_NEW_PCT",
    "EVOLUTION_RECURRING_COUNT", "EVOLUTION_RECURRING_PCT",
    "EVOLUTION_STRENGTHENING_COUNT", "EVOLUTION_STRENGTHENING_PCT",
    "EVOLUTION_WEAKENING_COUNT", "EVOLUTION_WEAKENING_PCT",
    "EVOLUTION_FADED_COUNT", "EVOLUTION_FADED_PCT",
    "EVOLUTION_TABLE_STRENGTHENING", "EVOLUTION_TABLE_WEAKENING",
    # Integrated report cross-evolution table
    "INT_EVOLUTION_CROSS_TABLE",
}

# Weekly evolution placeholders (aggregated across 7 daily evolution maps)
WEEKLY_EVOLUTION_PLACEHOLDERS = {
    "WEEKLY_EVOLUTION_TOTAL_THREADS",
    "WEEKLY_EVOLUTION_NEW_THREADS",
    "WEEKLY_EVOLUTION_FADED_THREADS",
    "WEEKLY_EVOLUTION_TOP_ACCELERATING",
    "WEEKLY_EVOLUTION_TOP_DECELERATING",
}

# Exploration placeholders (from report_statistics_engine v2.5.0)
EXPLORATION_PLACEHOLDERS = {
    "EXPLORATION_GAPS",
    "EXPLORATION_METHOD",
    "EXPLORATION_DISCOVERED",
    "EXPLORATION_VIABLE",
    "EXPLORATION_SIGNALS",
    "EXPLORATION_PENDING",
}

# WF4 crawl/translation placeholders (from report_statistics_engine v2.10.0)
CRAWL_TRANSLATION_PLACEHOLDERS = {
    "TOTAL_SITES_CRAWLED", "TOTAL_SITES_SUCCEEDED", "TOTAL_SITES_FAILED",
    "TOTAL_ARTICLES",
    "BY_LANGUAGE_KO", "BY_LANGUAGE_EN", "BY_LANGUAGE_ZH",
    "BY_LANGUAGE_JA", "BY_LANGUAGE_DE", "BY_LANGUAGE_FR",
    "BY_LANGUAGE_RU", "BY_LANGUAGE_OTHER",
    "CRAWL_SITE_TABLE",
    "CRAWL_DATETIME",
    "DEFENSE_LOG_TABLE",
    "SN_RATIO",
    "TRANSLATION_TOTAL", "TRANSLATION_FAILED",
    "TRANSLATION_STATS_TABLE",
}

# All deterministic placeholders this injector can handle
ALL_DETERMINISTIC_PLACEHOLDERS = (
    TEMPORAL_PLACEHOLDERS | STATISTICAL_PLACEHOLDERS
    | EVOLUTION_PLACEHOLDERS | WEEKLY_EVOLUTION_PLACEHOLDERS
    | EXPLORATION_PLACEHOLDERS | CRAWL_TRANSLATION_PLACEHOLDERS
)


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def build_replacement_map(
    scan_window_state: Dict[str, Any],
    workflow_name: Optional[str] = None,
    language: str = "ko",
) -> Dict[str, str]:
    """
    Build a mapping from placeholder names to replacement values.

    Args:
        scan_window_state: Loaded scan-window state (from temporal_anchor.py)
        workflow_name: Target workflow (e.g., "wf1-general"). Required for
                       single-WF reports. Not required for integrated/weekly.
        language: Output language — "ko" (Korean, default) or "en" (English).
                  Controls which date format strings are selected from
                  the scan-window state (e.g., window_start_ko vs window_start_en).

    Returns:
        Dict mapping placeholder names (without braces) to replacement strings
    """
    replacements = {}

    # Language-aware field suffix: "_ko" or "_en"
    suffix = f"_{language}"

    # Global values
    replacements["SCAN_ANCHOR_TIMESTAMP"] = scan_window_state.get(
        f"anchor_time{suffix}",
        scan_window_state.get("anchor_timestamp", ""),
    )
    replacements["DAILY_LOOKBACK_HOURS"] = str(
        scan_window_state.get("default_lookback_hours", 24)
    )

    # Per-WF values (for standard/naver single-WF reports)
    if workflow_name:
        wf = scan_window_state.get("workflows", {}).get(workflow_name, {})
        if wf:
            replacements["SCAN_WINDOW_START"] = wf.get(
                f"window_start{suffix}", wf.get("window_start", "")
            )
            replacements["SCAN_WINDOW_END"] = wf.get(
                f"window_end{suffix}", wf.get("window_end", "")
            )
            replacements["LOOKBACK_HOURS"] = str(wf.get("lookback_hours", ""))

    # Integrated report: all 3 WF lookback hours
    workflows = scan_window_state.get("workflows", {})
    for wf_key, placeholder_key in [
        ("wf1-general", "WF1_LOOKBACK_HOURS"),
        ("wf2-arxiv", "WF2_LOOKBACK_HOURS"),
        ("wf3-naver", "WF3_LOOKBACK_HOURS"),
        ("wf4-multiglobal-news", "WF4_LOOKBACK_HOURS"),
    ]:
        wf = workflows.get(wf_key, {})
        if wf:
            replacements[placeholder_key] = str(wf.get("lookback_hours", ""))

    # For integrated reports, use the broadest window
    if not workflow_name or workflow_name == "integrated":
        # Find earliest start and latest end across all WFs
        all_starts: List[Tuple[str, str]] = []
        all_ends: List[Tuple[str, str]] = []
        for wf in workflows.values():
            start_fmt = wf.get(f"window_start{suffix}", "")
            end_fmt = wf.get(f"window_end{suffix}", "")
            if start_fmt:
                all_starts.append((wf.get("window_start", ""), start_fmt))
            if end_fmt:
                all_ends.append((wf.get("window_end", ""), end_fmt))

        if all_starts:
            earliest = min(all_starts, key=lambda x: x[0])
            replacements.setdefault("SCAN_WINDOW_START", earliest[1])
        if all_ends:
            latest = max(all_ends, key=lambda x: x[0])
            replacements.setdefault("SCAN_WINDOW_END", latest[1])

    return replacements


def inject_temporal_metadata(
    skeleton_path: str,
    scan_window_path: str,
    workflow_name: Optional[str] = None,
    output_path: Optional[str] = None,
    statistics_path: Optional[str] = None,
    language: str = "ko",
) -> Tuple[str, Dict[str, Any]]:
    """
    Inject deterministic metadata into a skeleton template.

    Replaces temporal placeholders from scan-window state and (optionally)
    statistical placeholders from report-statistics JSON.
    All other {{PLACEHOLDER}} tokens are left intact for LLM to fill.

    Args:
        skeleton_path: Path to skeleton template (.md)
        scan_window_path: Path to scan-window state file (from temporal_anchor.py)
        workflow_name: Target workflow (None for integrated/weekly)
        output_path: Optional path to write the prepared skeleton
        statistics_path: Optional path to report-statistics JSON
                         (from report_statistics_engine.py)
        language: Output language — "ko" (Korean, default) or "en" (English).
                  Controls date format selection in temporal placeholders.

    Returns:
        Tuple of (prepared_content, injection_report)
    """
    # 1. Read skeleton
    skel_path = Path(skeleton_path)
    if not skel_path.exists():
        raise FileNotFoundError(f"Skeleton not found: {skeleton_path}")

    content = skel_path.read_text(encoding="utf-8")

    # 2. Read scan window state
    sw_path = Path(scan_window_path)
    if not sw_path.exists():
        raise FileNotFoundError(f"Scan window state not found: {scan_window_path}")

    with open(sw_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    # 3. Build temporal replacement map (language-aware: v1.2.0)
    replacements = build_replacement_map(state, workflow_name, language=language)

    # 4. Load and merge statistical placeholders if provided
    statistical_replacements: Dict[str, str] = {}
    if statistics_path:
        stats_path = Path(statistics_path)
        if stats_path.exists():
            with open(stats_path, "r", encoding="utf-8") as f:
                stats_data = json.load(f)
            statistical_replacements = stats_data.get("placeholders", {})
            replacements.update(statistical_replacements)

    # 5. Find all placeholders in the skeleton
    all_placeholders = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", content))
    temporal_found = all_placeholders & TEMPORAL_PLACEHOLDERS
    statistical_found = all_placeholders & STATISTICAL_PLACEHOLDERS
    evolution_found = all_placeholders & EVOLUTION_PLACEHOLDERS
    exploration_found = all_placeholders & EXPLORATION_PLACEHOLDERS
    crawl_translation_found = all_placeholders & CRAWL_TRANSLATION_PLACEHOLDERS
    deterministic_found = temporal_found | statistical_found | evolution_found | exploration_found | crawl_translation_found
    non_deterministic = all_placeholders - ALL_DETERMINISTIC_PLACEHOLDERS

    # 6. Replace deterministic placeholders (temporal + statistical)
    replaced = []
    unresolved = []

    for placeholder in deterministic_found:
        value = replacements.get(placeholder)
        if value:
            token = "{{" + placeholder + "}}"
            content = content.replace(token, value)
            replaced.append(placeholder)
        else:
            unresolved.append(placeholder)

    # 7. Write output if requested
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")

    # 8. Build injection report
    report = {
        "injector": INJECTOR_ID,
        "injector_version": VERSION,
        "skeleton": str(skeleton_path),
        "scan_window": str(scan_window_path),
        "statistics": str(statistics_path) if statistics_path else None,
        "workflow": workflow_name,
        "language": language,
        "temporal_placeholders_found": len(temporal_found),
        "temporal_placeholders_replaced": len([p for p in replaced if p in TEMPORAL_PLACEHOLDERS]),
        "temporal_placeholders_unresolved": [p for p in unresolved if p in TEMPORAL_PLACEHOLDERS],
        "statistical_placeholders_found": len(statistical_found),
        "statistical_placeholders_replaced": len([p for p in replaced if p in STATISTICAL_PLACEHOLDERS]),
        "statistical_placeholders_unresolved": [p for p in unresolved if p in STATISTICAL_PLACEHOLDERS],
        "evolution_placeholders_found": len(evolution_found),
        "evolution_placeholders_replaced": len([p for p in replaced if p in EVOLUTION_PLACEHOLDERS]),
        "evolution_placeholders_unresolved": [p for p in unresolved if p in EVOLUTION_PLACEHOLDERS],
        "exploration_placeholders_found": len(exploration_found),
        "exploration_placeholders_replaced": len([p for p in replaced if p in EXPLORATION_PLACEHOLDERS]),
        "exploration_placeholders_unresolved": [p for p in unresolved if p in EXPLORATION_PLACEHOLDERS],
        "non_deterministic_placeholders_preserved": len(non_deterministic),
        "replaced": sorted(replaced),
        "status": "SUCCESS" if not unresolved else "PARTIAL",
    }

    return content, report


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Inject deterministic temporal metadata into skeleton templates"
    )
    parser.add_argument(
        "--skeleton",
        required=True,
        help="Path to skeleton template (.md)",
    )
    parser.add_argument(
        "--scan-window",
        required=True,
        help="Path to scan-window state file (from temporal_anchor.py)",
    )
    parser.add_argument(
        "--workflow",
        default=None,
        help="Target workflow (e.g., wf1-general). Omit for integrated/weekly.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for prepared skeleton",
    )
    parser.add_argument(
        "--statistics",
        default=None,
        help="Path to report-statistics JSON (from report_statistics_engine.py)",
    )
    parser.add_argument(
        "--language",
        default="ko",
        choices=["ko", "en"],
        help="Output language for date format selection (default: ko)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print injection report as JSON to stdout",
    )
    args = parser.parse_args()

    try:
        content, report = inject_temporal_metadata(
            skeleton_path=args.skeleton,
            scan_window_path=args.scan_window,
            workflow_name=args.workflow,
            output_path=args.output,
            statistics_path=args.statistics,
            language=args.language,
        )

        if args.json_output:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            status = report["status"]
            icon = "✅" if status == "SUCCESS" else "⚠️"
            print("=" * 60)
            print(f"  {icon} Metadata Injector: {status}")
            print(f"  Skeleton: {report['skeleton']}")
            print(f"  Workflow: {report['workflow'] or 'integrated/weekly'}")
            print("-" * 60)
            print(f"  Temporal placeholders replaced: {report['temporal_placeholders_replaced']}/{report['temporal_placeholders_found']}")
            stat_found = report.get('statistical_placeholders_found', 0)
            stat_replaced = report.get('statistical_placeholders_replaced', 0)
            if stat_found > 0:
                print(f"  Statistical placeholders replaced: {stat_replaced}/{stat_found}")
            evo_found = report.get('evolution_placeholders_found', 0)
            evo_replaced = report.get('evolution_placeholders_replaced', 0)
            if evo_found > 0:
                print(f"  Evolution placeholders replaced: {evo_replaced}/{evo_found}")
            exp_found = report.get('exploration_placeholders_found', 0)
            exp_replaced = report.get('exploration_placeholders_replaced', 0)
            if exp_found > 0:
                print(f"  Exploration placeholders replaced: {exp_replaced}/{exp_found}")
            print(f"  Non-deterministic preserved for LLM: {report.get('non_deterministic_placeholders_preserved', report.get('non_temporal_placeholders_preserved', 0))}")
            all_unresolved = report.get("temporal_placeholders_unresolved", []) + report.get("statistical_placeholders_unresolved", []) + report.get("evolution_placeholders_unresolved", []) + report.get("exploration_placeholders_unresolved", [])
            if all_unresolved:
                print(f"  ⚠️ Unresolved: {all_unresolved}")
            if report["replaced"]:
                print(f"  Replaced: {report['replaced']}")
            print("=" * 60)
            if args.output:
                print(f"  Output: {args.output}")

        sys.exit(0 if report["status"] == "SUCCESS" else 2)

    except (FileNotFoundError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
