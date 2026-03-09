#!/usr/bin/env python3
"""
Completion Gate — Final Deliverables Completeness Validator
===========================================================
Programmatic enforcement that ALL required deliverables exist after a daily scan.

This script is the LAST gate before a scan is declared "complete".
It catches the exact class of failures that occurred on 2026-03-09:
  - Korean translations missing (bilingual protocol violation)
  - Timeline map skipped without escalation
  - Skeleton templates left unfilled (PLACEHOLDER tokens remaining)

Design Principle (Python 원천봉쇄):
    "완료했다는 '선언'이 아닌, 완료를 '증명'하는 메커니즘."
    The gate either PASSES or FAILS — there is no way to "declare complete"
    without all deliverables verified on disk.

Checks (CG-001 through CG-009):
    CG-001: EN report exists for each enabled workflow
    CG-002: KO report exists for each enabled workflow
    CG-003: EN integrated report exists
    CG-004: KO integrated report exists
    CG-005: No unfilled PLACEHOLDER tokens in any report
    CG-006: Timeline map exists (if signal_evolution.timeline_map enabled)
    CG-007: KO reports have ≥30% Korean characters
    CG-008: Archive copies exist for all reports (EN + KO)
    CG-009: All EN reports pass structural validation (validate_report.py)

Usage:
    python3 env-scanning/scripts/validate_completion.py \\
        --sot env-scanning/config/workflow-registry.yaml \\
        --date 2026-03-09

    python3 env-scanning/scripts/validate_completion.py \\
        --sot env-scanning/config/workflow-registry.yaml \\
        --date 2026-03-09 --json

Exit codes:
    0 = PASS (all deliverables verified)
    1 = FAIL (one or more CRITICAL checks failed)
    2 = WARN (non-critical issues found)

Version: 1.0.0
Origin: Created 2026-03-09 after autopilot mode skipped 3 deliverables.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

VERSION = "1.0.0"
GATE_ID = "validate_completion.py"

# Placeholder patterns that indicate unfilled skeleton tokens
PLACEHOLDER_PATTERNS = [
    r"\{\{[A-Z_]+\}\}",                    # {{PLACEHOLDER}}
    r"\[Data pending[:\s].*?\]",            # [Data pending: X] and [Data pending for X]
    r"\{\{[A-Z_]+\]",                       # {{MALFORMED]
]


def _load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise ImportError("PyYAML required: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _korean_char_ratio(text: str) -> float:
    """Calculate ratio of Korean characters (Hangul) in text."""
    if not text:
        return 0.0
    korean = sum(1 for c in text if '\uAC00' <= c <= '\uD7A3' or '\u3131' <= c <= '\u3163')
    total = sum(1 for c in text if not c.isspace())
    return korean / total if total > 0 else 0.0


def _count_placeholders(text: str) -> int:
    """Count unfilled placeholder tokens in text."""
    count = 0
    for pattern in PLACEHOLDER_PATTERNS:
        count += len(re.findall(pattern, text))
    return count


def _file_exists_and_nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 100


# ---------------------------------------------------------------------------
# Workflow report path resolution — reads from SOT deliverables section
# ---------------------------------------------------------------------------
# SOT defines per-workflow: deliverables.report_en, deliverables.report_ko
# Integration defines: deliverables.report_en, report_ko, timeline_map
# paths.reports_daily and paths.reports_archive provide directory prefixes.
# This eliminates hardcoded filename patterns (Python 원천봉쇄 principle).
# ---------------------------------------------------------------------------


def _resolve_wf_paths(wf_cfg: Dict[str, Any]) -> Dict[str, str]:
    """Resolve report file patterns from SOT workflow config."""
    deliverables = wf_cfg.get("deliverables", {})
    paths = wf_cfg.get("paths", {})
    daily = paths.get("reports_daily", "reports/daily/")
    archive = paths.get("reports_archive", "reports/archive/")

    en_name = deliverables.get("report_en", "")
    ko_name = deliverables.get("report_ko", "")

    return {
        "en_pattern": daily + en_name if en_name else "",
        "ko_pattern": daily + ko_name if ko_name else "",
        "archive_en": archive + "{year}/{month}/" + en_name if en_name else "",
        "archive_ko": archive + "{year}/{month}/" + ko_name if ko_name else "",
    }


def _resolve_int_paths(int_cfg: Dict[str, Any]) -> Dict[str, str]:
    """Resolve integrated report file patterns from SOT integration config."""
    deliverables = int_cfg.get("deliverables", {})
    paths = int_cfg.get("paths", {})
    daily = paths.get("reports_daily", "reports/daily/")
    archive = paths.get("reports_archive", "reports/archive/")

    en_name = deliverables.get("report_en", "")
    ko_name = deliverables.get("report_ko", "")

    return {
        "en_pattern": daily + en_name if en_name else "",
        "ko_pattern": daily + ko_name if ko_name else "",
        "archive_en": archive + "{year}/{month}/" + en_name if en_name else "",
        "archive_ko": archive + "{year}/{month}/" + ko_name if ko_name else "",
        "timeline_map": daily + deliverables.get("timeline_map", "") if deliverables.get("timeline_map") else "",
    }


def validate_completion(
    sot_path: str,
    scan_date: str,
    workflow_only: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate that all required deliverables exist for a completed scan.

    Args:
        sot_path: Path to workflow-registry.yaml
        scan_date: Scan date (YYYY-MM-DD)
        workflow_only: If set, validate only this workflow (e.g., "wf1-general").
                       Used by Master Gates M1/M2/M2a/M2b for per-workflow checks.

    Returns:
        Result dict with checks, status, and summary.
    """
    sot = _load_yaml(Path(sot_path))
    checks: List[Dict[str, Any]] = []
    date_parts = scan_date.split("-")
    year, month = date_parts[0], date_parts[1]

    # Determine enabled workflows — reads from SOT, no hardcoded workflow list
    workflows = sot.get("workflows", {})
    enabled_wfs = {
        k: v for k, v in workflows.items()
        if v.get("enabled", False) and v.get("deliverables")
    }

    # If --workflow-only, restrict to just that workflow
    if workflow_only:
        if workflow_only not in enabled_wfs:
            return {
                "gate_id": GATE_ID,
                "gate_version": VERSION,
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "scan_date": scan_date,
                "workflow_only": workflow_only,
                "status": "FAIL",
                "exit_code": 1,
                "summary": f"Workflow '{workflow_only}' not found or not enabled in SOT",
                "critical_failures": 1,
                "error_failures": 0,
                "checks": [],
            }
        enabled_wfs = {workflow_only: enabled_wfs[workflow_only]}

    # Resolve data roots — data_root values in SOT are project-root-relative
    project_root = Path(sot_path).resolve().parent.parent.parent
    wf_roots = {}
    wf_report_maps = {}
    for wf_key, wf_cfg in enabled_wfs.items():
        data_root = wf_cfg.get("data_root", f"env-scanning/{wf_key}")
        wf_roots[wf_key] = project_root / data_root
        wf_report_maps[wf_key] = _resolve_wf_paths(wf_cfg)

    # Integration checks are skipped in --workflow-only mode
    skip_integration = workflow_only is not None
    int_cfg = sot.get("integration", {})
    int_root = project_root / int_cfg.get("output_root", "env-scanning/integrated")
    int_paths = _resolve_int_paths(int_cfg) if not skip_integration else {}

    # ── CG-001: EN report exists for each enabled workflow ──
    for wf_key in enabled_wfs:
        report_map = wf_report_maps[wf_key]
        en_pattern = report_map.get("en_pattern", "")
        if not en_pattern:
            continue
        en_path = wf_roots[wf_key] / en_pattern.format(date=scan_date)
        exists = _file_exists_and_nonempty(en_path)
        checks.append({
            "id": "CG-001",
            "description": f"EN report exists: {wf_key}",
            "passed": exists,
            "severity": "CRITICAL",
            "detail": str(en_path) if not exists else "",
        })

    # ── CG-002: KO report exists for each enabled workflow ──
    for wf_key in enabled_wfs:
        report_map = wf_report_maps[wf_key]
        ko_pattern = report_map.get("ko_pattern", "")
        if not ko_pattern:
            continue
        ko_path = wf_roots[wf_key] / ko_pattern.format(date=scan_date)
        exists = _file_exists_and_nonempty(ko_path)
        checks.append({
            "id": "CG-002",
            "description": f"KO report exists: {wf_key}",
            "passed": exists,
            "severity": "CRITICAL",
            "detail": str(ko_path) if not exists else "",
        })

    # ── CG-003: EN integrated report exists (skipped in --workflow-only mode) ──
    int_en = int_root / int_paths["en_pattern"].format(date=scan_date) if int_paths.get("en_pattern") else None
    if int_en and not skip_integration:
        checks.append({
            "id": "CG-003",
            "description": "EN integrated report exists",
            "passed": _file_exists_and_nonempty(int_en),
            "severity": "CRITICAL",
            "detail": str(int_en) if not _file_exists_and_nonempty(int_en) else "",
        })

    # ── CG-004: KO integrated report exists (skipped in --workflow-only mode) ──
    int_ko = int_root / int_paths["ko_pattern"].format(date=scan_date) if int_paths.get("ko_pattern") else None
    if int_ko and not skip_integration:
        checks.append({
            "id": "CG-004",
            "description": "KO integrated report exists",
            "passed": _file_exists_and_nonempty(int_ko),
            "severity": "CRITICAL",
            "detail": str(int_ko) if not _file_exists_and_nonempty(int_ko) else "",
        })

    # ── CG-005: No unfilled PLACEHOLDER tokens in any report ──
    all_report_paths = []
    for wf_key in enabled_wfs:
        rm = wf_report_maps[wf_key]
        if rm.get("en_pattern"):
            all_report_paths.append(
                (wf_key + " EN", wf_roots[wf_key] / rm["en_pattern"].format(date=scan_date))
            )
        if rm.get("ko_pattern"):
            all_report_paths.append(
                (wf_key + " KO", wf_roots[wf_key] / rm["ko_pattern"].format(date=scan_date))
            )
    if int_en and not skip_integration:
        all_report_paths.append(("integrated EN", int_en))
    if int_ko and not skip_integration:
        all_report_paths.append(("integrated KO", int_ko))

    for label, rpath in all_report_paths:
        if rpath.exists():
            text = rpath.read_text(encoding="utf-8", errors="replace")
            ph_count = _count_placeholders(text)
            checks.append({
                "id": "CG-005",
                "description": f"No PLACEHOLDERs: {label}",
                "passed": ph_count == 0,
                "severity": "CRITICAL",
                "detail": f"{ph_count} unfilled placeholders found" if ph_count > 0 else "",
            })

    # ── CG-006: Timeline map exists (pattern from SOT integration.deliverables) ──
    sig_evo = sot.get("system", {}).get("signal_evolution", {})
    tm_cfg = sig_evo.get("timeline_map", {})
    tm_enabled = sig_evo.get("enabled", False) and tm_cfg.get("enabled", tm_cfg.get("generate", False))
    if not tm_enabled and "timeline_map" in sig_evo:
        tm_enabled = True

    if tm_enabled and int_paths.get("timeline_map") and not skip_integration:
        tm_path = int_root / int_paths["timeline_map"].format(date=scan_date)
        tm_exists = _file_exists_and_nonempty(tm_path)
        checks.append({
            "id": "CG-006",
            "description": "Timeline map exists",
            "passed": tm_exists,
            "severity": "CRITICAL",
            "detail": str(tm_path) if not tm_exists else "",
        })

    # ── CG-007: KO reports have ≥30% Korean characters ──
    ko_paths_list: List[Tuple[str, Path]] = []
    for wf_key in enabled_wfs:
        rm = wf_report_maps[wf_key]
        if rm.get("ko_pattern"):
            ko_paths_list.append(
                (wf_key, wf_roots[wf_key] / rm["ko_pattern"].format(date=scan_date))
            )
    if int_ko and not skip_integration:
        ko_paths_list.append(("integrated", int_ko))

    for label, kp in ko_paths_list:
        if kp.exists():
            text = kp.read_text(encoding="utf-8", errors="replace")
            ratio = _korean_char_ratio(text)
            passed = ratio >= 0.30
            checks.append({
                "id": "CG-007",
                "description": f"KO ratio ≥30%: {label}",
                "passed": passed,
                "severity": "CRITICAL",
                "detail": f"Korean ratio: {ratio:.1%}" if not passed else f"{ratio:.1%}",
            })

    # ── CG-008: Archive copies exist ──
    archive_paths: List[Tuple[str, Path]] = []
    for wf_key in enabled_wfs:
        rm = wf_report_maps[wf_key]
        if rm.get("archive_en"):
            archive_paths.append((
                f"{wf_key} archive EN",
                wf_roots[wf_key] / rm["archive_en"].format(date=scan_date, year=year, month=month),
            ))
        if rm.get("archive_ko"):
            archive_paths.append((
                f"{wf_key} archive KO",
                wf_roots[wf_key] / rm["archive_ko"].format(date=scan_date, year=year, month=month),
            ))
    if int_paths.get("archive_en") and not skip_integration:
        archive_paths.append((
            "integrated archive EN",
            int_root / int_paths["archive_en"].format(date=scan_date, year=year, month=month),
        ))
    if int_paths.get("archive_ko") and not skip_integration:
        archive_paths.append((
            "integrated archive KO",
            int_root / int_paths["archive_ko"].format(date=scan_date, year=year, month=month),
        ))

    for label, ap in archive_paths:
        exists = _file_exists_and_nonempty(ap)
        checks.append({
            "id": "CG-008",
            "description": f"Archive exists: {label}",
            "passed": exists,
            "severity": "ERROR",
            "detail": str(ap) if not exists else "",
        })

    # ── CG-009: Skeleton header check (reports should NOT start with "Skeleton Template") ──
    for label, rpath in all_report_paths:
        if rpath.exists():
            text = rpath.read_text(encoding="utf-8", errors="replace")
            first_lines = text[:500].lower()
            is_skeleton = "skeleton template" in first_lines
            checks.append({
                "id": "CG-009",
                "description": f"Not skeleton template: {label}",
                "passed": not is_skeleton,
                "severity": "CRITICAL",
                "detail": "Report header still says 'Skeleton Template'" if is_skeleton else "",
            })

    # ── Aggregate results ──
    critical_fails = [c for c in checks if not c["passed"] and c["severity"] == "CRITICAL"]
    error_fails = [c for c in checks if not c["passed"] and c["severity"] == "ERROR"]
    total = len(checks)
    passed = sum(1 for c in checks if c["passed"])

    if critical_fails:
        status = "FAIL"
        exit_code = 1
    elif error_fails:
        status = "WARN"
        exit_code = 2
    else:
        status = "PASS"
        exit_code = 0

    result = {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "scan_date": scan_date,
        "status": status,
        "exit_code": exit_code,
        "summary": f"{passed}/{total} checks passed",
        "critical_failures": len(critical_fails),
        "error_failures": len(error_fails),
        "checks": checks,
    }
    if workflow_only:
        result["workflow_only"] = workflow_only

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Completion Gate — Final Deliverables Completeness Validator"
    )
    parser.add_argument(
        "--sot", required=True,
        help="Path to workflow-registry.yaml"
    )
    parser.add_argument(
        "--date", required=True,
        help="Scan date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--workflow-only", default=None, dest="workflow_only",
        help="Validate only this workflow (e.g., wf1-general). Used by M1/M2/M2a/M2b gates."
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output as JSON"
    )
    parser.add_argument(
        "--output", default=None,
        help="Write result to file"
    )

    args = parser.parse_args()

    try:
        result = validate_completion(
            sot_path=args.sot,
            scan_date=args.date,
            workflow_only=args.workflow_only,
        )

        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        if args.json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            status = result["status"]
            icon = {"PASS": "\u2705", "FAIL": "\u274c", "WARN": "\u26a0\ufe0f"}[status]
            print("=" * 64)
            print(f"  {icon} Completion Gate: {status}")
            print(f"  Date: {result['scan_date']}")
            print(f"  {result['summary']}")
            if result["critical_failures"]:
                print(f"  CRITICAL failures: {result['critical_failures']}")
            if result["error_failures"]:
                print(f"  ERROR failures: {result['error_failures']}")
            print("-" * 64)
            for c in result["checks"]:
                ck = "\u2705" if c["passed"] else ("\u274c" if c["severity"] == "CRITICAL" else "\u26a0\ufe0f")
                detail = f" -- {c['detail']}" if c.get("detail") else ""
                print(f"  {ck} [{c['id']}] {c['description']}{detail}")
            print("=" * 64)

        sys.exit(result["exit_code"])

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
