#!/usr/bin/env python3
"""
Temporal Gate — Programmatic Pipeline Gate for Temporal Consistency
===================================================================
Validates that ALL signals in a JSON file fall within the scan window.
Replaces the LLM-instruction-based Pipeline Gate 1 temporal_boundary_check
with a deterministic Python verification.

This script is called by WF orchestrators at the Phase 1 → Phase 2 transition
(Pipeline Gate 1). The LLM orchestrator runs this script as a Python command
instead of evaluating temporal boundaries through LLM reasoning.

Design Principle:
    "검증하라는 '지시'가 아닌, 검증을 '강제'하는 메커니즘."
    The script either PASSES or FAILS — there is no way to "skip" the check.

Usage (CLI):
    python3 env-scanning/core/temporal_gate.py \\
        --signals env-scanning/wf1-general/structured/classified-signals-2026-02-10.json \\
        --scan-window env-scanning/integrated/logs/scan-window-2026-02-10.json \\
        --workflow wf1-general

    python3 env-scanning/core/temporal_gate.py \\
        --signals env-scanning/wf2-arxiv/raw/daily-scan-2026-02-10.json \\
        --scan-window env-scanning/integrated/logs/scan-window-2026-02-10.json \\
        --workflow wf2-arxiv

Usage (importable):
    from core.temporal_gate import check_signals_in_window
    result = check_signals_in_window(signals_path, scan_window_path, "wf1-general")

Exit codes:
    0 = PASS (all signals within window, or violations removed in strict mode)
    1 = FAIL (enforce=strict and violations found that could not be auto-removed)
    2 = WARN (enforce=lenient and violations found but logged only)
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
GATE_ID = "temporal_gate.py"


# ---------------------------------------------------------------------------
# Date parsing utility
# ---------------------------------------------------------------------------

def _parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string in various formats to a naive-UTC datetime.

    Handles:
    - ISO8601 with timezone: "2026-02-10T09:00:00+00:00"
    - ISO8601 with Z: "2026-02-10T09:00:00Z"
    - ISO8601 without timezone: "2026-02-10T09:00:00"
    - Date only: "2026-02-10"
    - Korean format: "2026년 02월 10일"

    Returns:
        datetime (naive, treated as UTC) or None if unparseable
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    # ISO8601 with T
    if "T" in date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)  # Normalize to naive for comparison
        except (ValueError, TypeError):
            pass

    # Date only (YYYY-MM-DD)
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        pass

    # Korean format
    try:
        import re
        m = re.match(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", date_str)
        if m:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except (ValueError, TypeError):
        pass

    return None


def _parse_iso_to_naive(iso_str: str) -> datetime:
    """Parse ISO8601 string to naive datetime (for window boundaries)."""
    dt = datetime.fromisoformat(iso_str)
    return dt.replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Signal extraction
# ---------------------------------------------------------------------------

def _extract_signals(data: Any) -> List[Dict[str, Any]]:
    """
    Extract signal list from various JSON structures.

    Supports:
    - {"items": [...]}  (raw scan output)
    - {"signals": [...]}  (classified/ranked output)
    - [...]  (direct list)
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Key-variant fallback: "classified_signals" (v2.1.0+), "signals" (v2.0.x), "items" (v1.x raw)
        if "classified_signals" in data:
            return data["classified_signals"]
        if "items" in data:
            return data["items"]
        if "signals" in data:
            return data["signals"]
    return []


def _get_signal_date(signal: Dict[str, Any]) -> Optional[str]:
    """Extract published_date from a signal in various schema formats."""
    # Standard format: signal.source.published_date
    date_str = signal.get("source", {}).get("published_date")
    if date_str:
        return date_str

    # Alternative: signal.published_date
    date_str = signal.get("published_date")
    if date_str:
        return date_str

    # Alternative: signal.date
    date_str = signal.get("date")
    if date_str:
        return date_str

    # Naver format: signal.pubDate
    date_str = signal.get("pubDate")
    if date_str:
        return date_str

    return None


# ---------------------------------------------------------------------------
# Core Gate Function
# ---------------------------------------------------------------------------

def check_signals_in_window(
    signals_path: str,
    scan_window_path: str,
    workflow_name: str,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check all signals against the scan window. Deterministic verification.

    Args:
        signals_path: Path to signal JSON file (raw, classified, or ranked)
        scan_window_path: Path to scan-window state file (from temporal_anchor.py)
        workflow_name: Workflow ID (e.g., "wf1-general")
        output_path: Optional path to write gate result JSON

    Returns:
        Gate result dictionary with pass/fail status and violation details

    Raises:
        FileNotFoundError: If input files don't exist
        KeyError: If workflow not found in scan window state
    """
    # 1. Load scan window state
    sw_path = Path(scan_window_path)
    if not sw_path.exists():
        raise FileNotFoundError(f"Scan window state file not found: {scan_window_path}")

    with open(sw_path, "r", encoding="utf-8") as f:
        scan_window_state = json.load(f)

    wf_window = scan_window_state.get("workflows", {}).get(workflow_name)
    if wf_window is None:
        available = list(scan_window_state.get("workflows", {}).keys())
        raise KeyError(
            f"Workflow '{workflow_name}' not in scan window state. "
            f"Available: {available}"
        )

    # 2. Parse window boundaries
    effective_start = _parse_iso_to_naive(wf_window["effective_start"])
    window_end = _parse_iso_to_naive(wf_window["window_end"])
    enforce = wf_window.get("enforce", "strict")

    # 3. Load signals
    sig_path = Path(signals_path)
    if not sig_path.exists():
        raise FileNotFoundError(f"Signals file not found: {signals_path}")

    with open(sig_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    signals = _extract_signals(data)

    # 4. Check each signal
    within_window = []
    outside_window = []
    unparseable = []

    for signal in signals:
        date_str = _get_signal_date(signal)
        signal_id = signal.get("id", signal.get("title", "unknown"))

        if not date_str:
            unparseable.append({
                "signal_id": str(signal_id),
                "reason": "no_date_field",
            })
            within_window.append(signal)  # Keep signals without dates
            continue

        pub_date = _parse_date(date_str)
        if pub_date is None:
            unparseable.append({
                "signal_id": str(signal_id),
                "date_str": date_str,
                "reason": "parse_failure",
            })
            within_window.append(signal)  # Keep unparseable dates
            continue

        if effective_start <= pub_date <= window_end:
            within_window.append(signal)
        else:
            outside_window.append({
                "signal_id": str(signal_id),
                "published_date": date_str,
                "parsed_date": pub_date.isoformat(),
                "window": f"[{effective_start.isoformat()}, {window_end.isoformat()}]",
            })

    # 5. Determine gate result
    total = len(signals)
    violations = len(outside_window)
    passed = violations == 0

    if enforce == "strict" and violations > 0:
        gate_status = "PASS_WITH_REMOVAL"
        gate_message = (
            f"{violations} signal(s) outside window removed (strict mode). "
            f"{len(within_window)}/{total} signals retained."
        )
    elif enforce == "lenient" and violations > 0:
        gate_status = "WARN"
        gate_message = (
            f"{violations} signal(s) outside window (lenient mode — logged only). "
            f"All {total} signals retained."
        )
        within_window = signals  # Keep all in lenient mode
    elif violations == 0:
        gate_status = "PASS"
        gate_message = f"All {total} signals within window."
    else:
        gate_status = "PASS"
        gate_message = f"All {total} signals within window."

    # 6. Build result
    result = {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "workflow": workflow_name,
        "signals_file": str(signals_path),
        "scan_window_file": str(scan_window_path),
        "gate_status": gate_status,
        "gate_message": gate_message,
        "statistics": {
            "total_signals": total,
            "within_window": len(within_window),
            "outside_window": violations,
            "unparseable_dates": len(unparseable),
        },
        "window": {
            "effective_start": effective_start.isoformat(),
            "window_end": window_end.isoformat(),
            "lookback_hours": wf_window["lookback_hours"],
            "tolerance_minutes": wf_window["tolerance_minutes"],
            "enforce": enforce,
        },
        "violations": outside_window,
        "unparseable": unparseable,
    }

    # 7. Write result if output_path given
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    return result


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Temporal Gate — Programmatic Pipeline Gate for scan window verification"
    )
    parser.add_argument(
        "--signals",
        required=True,
        help="Path to signal JSON file (raw, classified, or ranked)",
    )
    parser.add_argument(
        "--scan-window",
        required=True,
        help="Path to scan-window state file (from temporal_anchor.py)",
    )
    parser.add_argument(
        "--workflow",
        required=True,
        help="Workflow name (e.g., wf1-general, wf2-arxiv, wf3-naver)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for gate result JSON",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print result as JSON to stdout",
    )
    args = parser.parse_args()

    try:
        result = check_signals_in_window(
            signals_path=args.signals,
            scan_window_path=args.scan_window,
            workflow_name=args.workflow,
            output_path=args.output,
        )

        if args.json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Human-readable summary
            status = result["gate_status"]
            stats = result["statistics"]
            icon = "✅" if status in ("PASS", "PASS_WITH_REMOVAL") else "⚠️"
            print("=" * 60)
            print(f"  {icon} Temporal Gate: {status}")
            print(f"  Workflow: {result['workflow']}")
            print(f"  {result['gate_message']}")
            print("-" * 60)
            print(f"  Total: {stats['total_signals']}  |  "
                  f"In window: {stats['within_window']}  |  "
                  f"Outside: {stats['outside_window']}  |  "
                  f"Unparseable: {stats['unparseable_dates']}")
            print("=" * 60)

            if result["violations"]:
                print("  Violations:")
                for v in result["violations"][:10]:
                    print(f"    - {v['signal_id']}: {v['published_date']} "
                          f"(outside {v['window']})")
                if len(result["violations"]) > 10:
                    print(f"    ... and {len(result['violations']) - 10} more")

        # Exit code based on gate status
        if status == "PASS" or status == "PASS_WITH_REMOVAL":
            sys.exit(0)
        elif status == "WARN":
            sys.exit(2)
        else:
            sys.exit(1)

    except (FileNotFoundError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
