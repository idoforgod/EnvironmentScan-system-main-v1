#!/usr/bin/env python3
"""
Pipeline Gate 2 Output Validator
=================================
8 deterministic checks that validate Phase 2 outputs before Phase 3 begins.

This script is the Python enforcement of Pipeline Gate 2 (Phase 2 → Phase 3).
Previously, PG2 was documented in orchestrator-protocol.md but had NO programmatic
enforcement. LLM hallucinations in Phase 2 (invalid STEEPs codes, out-of-range
scores, invalid FSSF types) could propagate silently into final reports.

Design Principle (Python 원천봉쇄):
    "계산은 Python이, 판단은 LLM이"
    All enumeration checks and range validations are deterministic Python code.
    No LLM judgment is involved.

Checks:
    PG2-001: STEEPs Classification Validity — category ∈ valid codes          — CRITICAL
    PG2-002: Impact Score Range — impact_score ∈ [-10.0, +10.0]              — CRITICAL
    PG2-003: Priority Score Range — priority_score ∈ [0.0, 10.0]             — CRITICAL
    PG2-004: FSSF Type Validity (WF3/WF4 only) — ∈ 8 canonical types        — CRITICAL
    PG2-005: Three Horizons Validity (WF3/WF4 only) — ∈ {H1, H2, H3}        — CRITICAL
    PG2-006: Tipping Point Color Validity (WF3/WF4 only) — ∈ 4 alert colors  — ERROR
    PG2-007: Signal Count Consistency — classified ≈ impact ≈ ranked          — ERROR
    PG2-008: Required Fields Exist — mandatory fields in priority-ranked       — CRITICAL

Usage:
    python3 env-scanning/scripts/validate_phase2_output.py \
        --sot env-scanning/config/workflow-registry.yaml \
        --workflow wf1-general \
        --date 2026-03-07

    python3 env-scanning/scripts/validate_phase2_output.py \
        --sot env-scanning/config/workflow-registry.yaml \
        --workflow wf3-naver \
        --date 2026-03-07 --json

Exit codes:
    0 = PASS (all checks passed or WARN-only)
    1 = FAIL (one or more CRITICAL checks failed)
    2 = WARN (ERROR-level issues found, no CRITICAL failures)

Version: 1.0.0
Origin: Created 2026-03-09 as part of hallucination prevention initiative.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

VERSION = "1.0.0"
GATE_ID = "validate_phase2_output.py"

# ══════════════════════════════════════════════════════════════════════
# Canonical Enumerations (from core-invariants.yaml + signal processors)
# ══════════════════════════════════════════════════════════════════════

# Valid STEEPs codes — base codes from core-invariants.yaml plus extended forms
# used across different workflow data structures.
STEEPS_VALID: set[str] = {
    # Base codes (6 categories)
    "S", "T", "E", "P", "s",
    # Extended forms (used in classified-signals)
    "S_Social", "T_Technological", "E_Economic", "E_Environmental",
    "P_Political", "s_spiritual",
    # Lowercase-variant forms (seen in WF3 data)
    "E_economic", "E_environmental", "P_political", "S_social",
    "T_technological", "s_Spiritual",
}

# FSSF 8 types — canonical values from naver_signal_processor.py and
# news_signal_processor.py. Both space-separated and underscore variants
# are accepted because WF3 data uses underscores, WF4 uses spaces.
FSSF_CANONICAL: set[str] = {
    "Weak Signal", "Emerging Issue", "Trend", "Megatrend",
    "Driver", "Wild Card", "Discontinuity", "Precursor Event",
}
FSSF_UNDERSCORE: set[str] = {t.replace(" ", "_") for t in FSSF_CANONICAL}
FSSF_VALID: set[str] = FSSF_CANONICAL | FSSF_UNDERSCORE

# Three Horizons
THREE_HORIZONS_VALID: set[str] = {"H1", "H2", "H3"}

# Tipping Point alert colors
TIPPING_COLORS_VALID: set[str] = {"GREEN", "YELLOW", "ORANGE", "RED"}

# Workflows that use FSSF / Three Horizons / Tipping Point frameworks
FSSF_WORKFLOWS: set[str] = {"wf3-naver", "wf4-multiglobal-news"}


# ══════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════

def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file. Requires PyYAML."""
    if yaml is None:
        raise ImportError("PyYAML required: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _extract_signals(data: Dict[str, Any], *keys: str) -> List[Dict[str, Any]]:
    """Extract signal array from data, trying multiple possible key names.

    Handles both list-type (WF1/WF2/WF4) and dict-type (WF3 impact) structures.
    Dict entries are converted to list with signal_id injected from the key.
    """
    for key in keys:
        val = data.get(key)
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            # Dict-type: {signal_id: {...}, ...} → [{signal_id: id, ...}, ...]
            result = []
            for sig_id, sig_data in val.items():
                if isinstance(sig_data, dict):
                    entry = dict(sig_data)
                    entry.setdefault("signal_id", sig_id)
                    entry.setdefault("id", sig_id)
                    result.append(entry)
            if result:
                return result
    return []


def _get_steeps(signal: Dict[str, Any]) -> Optional[str]:
    """Extract STEEPs category from a signal, trying multiple field names."""
    for field in ("steeps_category", "category", "steeps",
                  "steeps_classification", "steeps_primary",
                  "preliminary_category"):
        val = signal.get(field)
        if val and isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _get_fssf(signal: Dict[str, Any]) -> Optional[str]:
    """Extract FSSF type from a signal."""
    val = signal.get("fssf_type")
    if val and isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _get_horizon(signal: Dict[str, Any]) -> Optional[str]:
    """Extract Three Horizons value from a signal."""
    for field in ("three_horizons", "horizon"):
        val = signal.get(field)
        if val and isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _get_tipping_color(signal: Dict[str, Any]) -> Optional[str]:
    """Extract tipping point alert color from a signal."""
    # Direct field (WF4 structure)
    val = signal.get("tipping_point_alert")
    if val and isinstance(val, str):
        return val.strip().upper()
    # Nested object (WF3 structure)
    tp = signal.get("tipping_point")
    if isinstance(tp, dict):
        for field in ("status", "alert_level", "color"):
            val = tp.get(field)
            if val and isinstance(val, str):
                return val.strip().upper()
    return None


def _sig_id(signal: Dict[str, Any]) -> str:
    """Get signal ID with fallback."""
    return signal.get("id", signal.get("signal_id", "unknown"))


# ══════════════════════════════════════════════════════════════════════
# Main Validation
# ══════════════════════════════════════════════════════════════════════

def validate_phase2_output(
    sot_path: str,
    workflow: str,
    scan_date: str,
) -> Dict[str, Any]:
    """
    Validate Phase 2 output files for a specific workflow.

    Args:
        sot_path: Path to workflow-registry.yaml
        workflow: Workflow name (e.g., "wf1-general", "wf3-naver")
        scan_date: Scan date (YYYY-MM-DD)

    Returns:
        Result dict with checks, status, exit_code, and summary.
    """
    sot = _load_yaml(Path(sot_path))
    checks: List[Dict[str, Any]] = []
    is_fssf = workflow in FSSF_WORKFLOWS

    # ── Resolve workflow data root from SOT ──
    wf_cfg = sot.get("workflows", {}).get(workflow, {})
    if not wf_cfg:
        return _fail_result(scan_date, workflow,
                            f"Workflow '{workflow}' not found in SOT")

    if not wf_cfg.get("enabled", False):
        return _fail_result(scan_date, workflow,
                            f"Workflow '{workflow}' is disabled in SOT")

    project_root = Path(sot_path).resolve().parent.parent.parent
    data_root = project_root / wf_cfg.get("data_root", f"env-scanning/{workflow}")

    # ── Resolve Phase 2 file paths ──
    classified_path = data_root / f"structured/classified-signals-{scan_date}.json"
    impact_path = data_root / f"analysis/impact-assessment-{scan_date}.json"
    ranked_path = data_root / f"analysis/priority-ranked-{scan_date}.json"

    # ── Load files ──
    classified_data, classified_signals = _safe_load(
        classified_path, "signals", "items")
    impact_data, impact_signals = _safe_load(
        impact_path, "impact_matrix", "assessments", "signal_impact_scores",
        "items", "signals")
    ranked_data, ranked_signals = _safe_load(
        ranked_path, "ranked_signals", "signals", "items")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PG2-001: STEEPs Classification Validity
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if classified_signals is not None:
        invalid = []
        for sig in classified_signals:
            sid = _sig_id(sig)
            steeps = _get_steeps(sig)
            if steeps is None:
                invalid.append(f"{sid}: no STEEPs field")
            elif steeps not in STEEPS_VALID:
                invalid.append(f"{sid}: '{steeps}'")

        checks.append({
            "id": "PG2-001",
            "description": "STEEPs classification validity",
            "passed": len(invalid) == 0,
            "severity": "CRITICAL",
            "detail": _violation_detail(invalid, len(classified_signals),
                                        "signals have valid STEEPs"),
        })
    else:
        checks.append(_file_missing_check(
            "PG2-001", "STEEPs classification validity",
            classified_path, classified_data))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PG2-002: Impact Score Range [-5.0, +5.0]
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if impact_signals is not None:
        invalid = []
        for sig in impact_signals:
            sid = _sig_id(sig)
            score = sig.get("impact_score")
            if score is None:
                invalid.append(f"{sid}: missing impact_score")
            elif not isinstance(score, (int, float)):
                invalid.append(f"{sid}: non-numeric '{score}'")
            elif score < -10.0 or score > 10.0:
                invalid.append(f"{sid}: {score}")

        checks.append({
            "id": "PG2-002",
            "description": "Impact score range [-10.0, +10.0]",
            "passed": len(invalid) == 0,
            "severity": "CRITICAL",
            "detail": _violation_detail(invalid, len(impact_signals),
                                        "impact scores in range"),
        })
    else:
        checks.append(_file_missing_check(
            "PG2-002", "Impact score range [-10.0, +10.0]",
            impact_path, impact_data))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PG2-003: Priority Score Range [0.0, 10.0]
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if ranked_signals is not None:
        invalid = []
        for sig in ranked_signals:
            sid = _sig_id(sig)
            score = sig.get("priority_score")
            if score is None:
                invalid.append(f"{sid}: missing priority_score")
            elif not isinstance(score, (int, float)):
                invalid.append(f"{sid}: non-numeric '{score}'")
            elif score < 0.0 or score > 10.0:
                invalid.append(f"{sid}: {score}")

        checks.append({
            "id": "PG2-003",
            "description": "Priority score range [0.0, 10.0]",
            "passed": len(invalid) == 0,
            "severity": "CRITICAL",
            "detail": _violation_detail(invalid, len(ranked_signals),
                                        "priority scores in range"),
        })
    else:
        checks.append(_file_missing_check(
            "PG2-003", "Priority score range [0.0, 10.0]",
            ranked_path, ranked_data))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PG2-004: FSSF Type Validity (WF3/WF4 only)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if is_fssf and classified_signals is not None:
        invalid = []
        missing_count = 0
        for sig in classified_signals:
            sid = _sig_id(sig)
            fssf = _get_fssf(sig)
            if fssf is None or fssf == "":
                missing_count += 1
            elif fssf not in FSSF_VALID:
                invalid.append(f"{sid}: '{fssf}'")

        parts = []
        if invalid:
            parts.append(f"{len(invalid)} invalid: {'; '.join(invalid[:5])}")
        if missing_count > 0:
            parts.append(f"{missing_count} missing fssf_type")

        checks.append({
            "id": "PG2-004",
            "description": "FSSF type validity (WF3/WF4)",
            "passed": len(invalid) == 0,
            "severity": "CRITICAL",
            "detail": "; ".join(parts) if parts
                      else f"All {len(classified_signals)} FSSF types valid",
        })
    elif is_fssf:
        checks.append(_file_missing_check(
            "PG2-004", "FSSF type validity (WF3/WF4)",
            classified_path, classified_data))
    else:
        checks.append(_skip_check(
            "PG2-004", "FSSF type validity (WF3/WF4)", workflow))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PG2-005: Three Horizons Validity (WF3/WF4 only)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if is_fssf and classified_signals is not None:
        invalid = []
        missing_count = 0
        for sig in classified_signals:
            sid = _sig_id(sig)
            horizon = _get_horizon(sig)
            if horizon is None or horizon == "":
                missing_count += 1
            elif horizon not in THREE_HORIZONS_VALID:
                invalid.append(f"{sid}: '{horizon}'")

        parts = []
        if invalid:
            parts.append(f"{len(invalid)} invalid: {'; '.join(invalid[:5])}")
        if missing_count > 0:
            parts.append(f"{missing_count} missing three_horizons")

        checks.append({
            "id": "PG2-005",
            "description": "Three Horizons validity (WF3/WF4)",
            "passed": len(invalid) == 0,
            "severity": "CRITICAL",
            "detail": "; ".join(parts) if parts
                      else f"All {len(classified_signals)} Three Horizons valid",
        })
    elif is_fssf:
        checks.append(_file_missing_check(
            "PG2-005", "Three Horizons validity (WF3/WF4)",
            classified_path, classified_data))
    else:
        checks.append(_skip_check(
            "PG2-005", "Three Horizons validity (WF3/WF4)", workflow))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PG2-006: Tipping Point Color Validity (WF3/WF4 only)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if is_fssf and classified_signals is not None:
        invalid = []
        signals_with_tp = 0
        for sig in classified_signals:
            sid = _sig_id(sig)
            color = _get_tipping_color(sig)
            if color is not None:
                signals_with_tp += 1
                if color not in TIPPING_COLORS_VALID:
                    invalid.append(f"{sid}: '{color}'")

        checks.append({
            "id": "PG2-006",
            "description": "Tipping Point color validity (WF3/WF4)",
            "passed": len(invalid) == 0,
            "severity": "ERROR",
            "detail": f"{len(invalid)} invalid: {'; '.join(invalid[:5])}"
                      if invalid
                      else f"All {signals_with_tp} tipping point colors valid",
        })
    elif is_fssf:
        checks.append(_file_missing_check(
            "PG2-006", "Tipping Point color validity (WF3/WF4)",
            classified_path, classified_data, severity="ERROR"))
    else:
        checks.append(_skip_check(
            "PG2-006", "Tipping Point color validity (WF3/WF4)", workflow))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PG2-007: Signal Count Consistency
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    n_classified = len(classified_signals) if classified_signals is not None else -1
    n_impact = len(impact_signals) if impact_signals is not None else -1
    n_ranked = len(ranked_signals) if ranked_signals is not None else -1

    present = [n for n in (n_classified, n_impact, n_ranked) if n >= 0]
    count_str = (f"classified={n_classified if n_classified >= 0 else 'N/A'}, "
                 f"impact={n_impact if n_impact >= 0 else 'N/A'}, "
                 f"ranked={n_ranked if n_ranked >= 0 else 'N/A'}")

    if len(present) >= 2:
        all_equal = len(set(present)) == 1
        checks.append({
            "id": "PG2-007",
            "description": "Signal count consistency across Phase 2 files",
            "passed": all_equal,
            "severity": "ERROR",
            "detail": count_str + ("" if all_equal else " — MISMATCH"),
        })
    else:
        checks.append({
            "id": "PG2-007",
            "description": "Signal count consistency across Phase 2 files",
            "passed": False,
            "severity": "ERROR",
            "detail": f"Cannot compare: only {len(present)}/3 files have signals ({count_str})",
        })

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PG2-008: Required Fields in Priority-Ranked Signals
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    REQUIRED_RANKED_FIELDS = ("id", "title", "priority_score", "rank")

    if ranked_signals is not None:
        defective = []
        for sig in ranked_signals:
            sid = _sig_id(sig)
            missing = [f for f in REQUIRED_RANKED_FIELDS
                       if f not in sig or sig[f] is None]
            if missing:
                defective.append(f"{sid}: missing {', '.join(missing)}")

        checks.append({
            "id": "PG2-008",
            "description": "Required fields in priority-ranked signals",
            "passed": len(defective) == 0,
            "severity": "CRITICAL",
            "detail": _violation_detail(defective, len(ranked_signals),
                                        "ranked signals have required fields"),
        })
    else:
        checks.append(_file_missing_check(
            "PG2-008", "Required fields in priority-ranked signals",
            ranked_path, ranked_data))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Compute Summary
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    critical_fails = sum(
        1 for c in checks if not c["passed"] and c["severity"] == "CRITICAL")
    error_fails = sum(
        1 for c in checks if not c["passed"] and c["severity"] == "ERROR")
    total = len(checks)
    passed = sum(1 for c in checks if c["passed"])

    if critical_fails > 0:
        status = "FAIL"
        exit_code = 1
    elif error_fails > 0:
        status = "WARN"
        exit_code = 2
    else:
        status = "PASS"
        exit_code = 0

    suffix = ""
    if critical_fails + error_fails > 0:
        parts = []
        if critical_fails:
            parts.append(f"{critical_fails} CRITICAL")
        if error_fails:
            parts.append(f"{error_fails} ERROR")
        suffix = f" ({', '.join(parts)})"

    return {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "scan_date": scan_date,
        "workflow": workflow,
        "is_fssf_workflow": is_fssf,
        "files": {
            "classified": str(classified_path),
            "impact": str(impact_path),
            "ranked": str(ranked_path),
        },
        "signal_counts": {
            "classified": n_classified if n_classified >= 0 else None,
            "impact": n_impact if n_impact >= 0 else None,
            "ranked": n_ranked if n_ranked >= 0 else None,
        },
        "status": status,
        "exit_code": exit_code,
        "summary": f"{passed}/{total} checks passed{suffix}",
        "critical_failures": critical_fails,
        "error_failures": error_fails,
        "checks": checks,
    }


# ══════════════════════════════════════════════════════════════════════
# Internal Helpers
# ══════════════════════════════════════════════════════════════════════

def _safe_load(
    path: Path, *signal_keys: str,
) -> tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
    """
    Load a JSON file and extract signal array.

    Returns:
        (raw_data, signal_list) — raw_data is None if file doesn't exist,
        signal_list is None if file doesn't exist or has no signal array.
    """
    if not path.exists():
        return None, None
    try:
        data = _load_json(path)
        signals = _extract_signals(data, *signal_keys)
        return data, signals if signals else None
    except Exception:
        return None, None


def _violation_detail(
    violations: List[str], total: int, ok_msg: str,
) -> str:
    """Format violation detail string."""
    if violations:
        truncated = violations[:5]
        extra = f" (+{len(violations) - 5} more)" if len(violations) > 5 else ""
        return f"{len(violations)} invalid: {'; '.join(truncated)}{extra}"
    return f"All {total} {ok_msg}"


def _file_missing_check(
    check_id: str,
    description: str,
    path: Path,
    data: Optional[Dict[str, Any]],
    severity: str = "CRITICAL",
) -> Dict[str, Any]:
    """Create a check result for a missing or empty file."""
    if data is not None:
        detail = "File loaded but contains no signal array"
    else:
        detail = f"File not found: {path.name}"
    return {
        "id": check_id,
        "description": description,
        "passed": False,
        "severity": severity,
        "detail": detail,
    }


def _skip_check(
    check_id: str, description: str, workflow: str,
) -> Dict[str, Any]:
    """Create a SKIP result for non-applicable checks."""
    return {
        "id": check_id,
        "description": description,
        "passed": True,
        "severity": "SKIP",
        "detail": f"Skipped: {workflow} does not use this framework",
    }


def _fail_result(
    scan_date: str, workflow: str, summary: str,
) -> Dict[str, Any]:
    """Create an early-exit failure result."""
    return {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "scan_date": scan_date,
        "workflow": workflow,
        "status": "FAIL",
        "exit_code": 1,
        "summary": summary,
        "critical_failures": 1,
        "error_failures": 0,
        "checks": [],
    }


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline Gate 2: Validate Phase 2 output before Phase 3",
    )
    parser.add_argument(
        "--sot", required=True,
        help="Path to workflow-registry.yaml",
    )
    parser.add_argument(
        "--workflow", required=True,
        help="Workflow name (e.g., wf1-general, wf3-naver)",
    )
    parser.add_argument(
        "--date", required=True,
        help="Scan date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable",
    )
    args = parser.parse_args()

    result = validate_phase2_output(args.sot, args.workflow, args.date)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        status = result["status"]
        icon = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}[status]
        print(f"\n[{icon}] Pipeline Gate 2: {result['summary']}")
        print(f"  Workflow: {result['workflow']}  |  Date: {result['scan_date']}")
        print()

        for check in result["checks"]:
            mark = "PASS" if check["passed"] else (
                "SKIP" if check["severity"] == "SKIP" else "FAIL")
            sev = check["severity"]
            print(f"  [{mark}] {check['id']} [{sev}] {check['description']}")
            if check.get("detail"):
                print(f"         {check['detail']}")
        print()

    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
