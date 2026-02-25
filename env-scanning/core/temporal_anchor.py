#!/usr/bin/env python3
"""
Temporal Anchor — Deterministic T₀ and Scan Window Calculator
==============================================================
Eliminates LLM hallucination in timestamp generation, datetime arithmetic,
and parameter propagation by producing a pre-computed JSON state file.

This module is the SINGLE PROGRAMMATIC AUTHORITY for all temporal parameters
during a scan execution. All downstream agents and scripts READ the output
state file instead of performing datetime arithmetic themselves.

Design Principle:
    "계산은 Python이, 판단은 LLM이."
    Deterministic operations (timestamps, arithmetic, window boundaries) = Python.
    Analytical operations (signal assessment, narrative writing) = LLM.

Usage (CLI):
    python3 env-scanning/core/temporal_anchor.py \\
        --registry env-scanning/config/workflow-registry.yaml \\
        --output env-scanning/integrated/logs/scan-window-2026-02-10.json

Usage (importable):
    from core.temporal_anchor import generate_scan_window
    result = generate_scan_window("env-scanning/config/workflow-registry.yaml")

Exit codes:
    0 = SUCCESS (state file written)
    1 = ERROR (SOT read failure, missing fields, etc.)
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.1.0"
GENERATOR_ID = "temporal_anchor.py"

# Allowed enforce values (mirroring SOT-030 validation)
VALID_ENFORCE_MODES = {"strict", "lenient"}

# Lookback bounds (from core-invariants.yaml tunable_parameters)
MIN_LOOKBACK_HOURS = 1
MAX_LOOKBACK_HOURS = 168  # 7 days


# ---------------------------------------------------------------------------
# Core Function
# ---------------------------------------------------------------------------

def generate_scan_window(
    registry_path: str,
    output_path: Optional[str] = None,
    anchor: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Generate deterministic scan window from SOT.

    This function:
    1. Reads workflow-registry.yaml (SOT)
    2. Generates T₀ (anchor timestamp) — deterministic Python datetime.now(UTC)
    3. Reads per-WF lookback_hours, tolerance_minutes, enforce from SOT
    4. Calculates all scan windows via Python datetime arithmetic (zero hallucination)
    5. Optionally writes the result to a JSON state file

    Args:
        registry_path: Path to workflow-registry.yaml (SOT)
        output_path: Where to write the scan-window JSON (optional)
        anchor: Override T₀ for testing (default: datetime.now(UTC))

    Returns:
        Scan window dictionary containing all computed temporal parameters

    Raises:
        FileNotFoundError: If registry_path does not exist
        KeyError: If required SOT fields are missing
        ValueError: If SOT values are out of valid range
    """
    registry_file = Path(registry_path)
    if not registry_file.exists():
        raise FileNotFoundError(f"SOT not found: {registry_path}")

    # 1. Read SOT
    with open(registry_file, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    # 2. Generate T₀ (deterministic)
    t0 = anchor or datetime.now(timezone.utc)
    # Ensure T₀ is timezone-aware (UTC)
    if t0.tzinfo is None:
        t0 = t0.replace(tzinfo=timezone.utc)

    # 3. Read global temporal consistency settings
    tc = registry.get("system", {}).get("temporal_consistency", {})
    tc_enabled = tc.get("enabled", True)
    default_lookback = tc.get("default_lookback_hours", 24)
    default_tolerance = tc.get("default_tolerance_minutes", 30)
    default_enforce = tc.get("default_enforce", "strict")

    # 4. Calculate per-WF windows
    workflows = registry.get("workflows", {})
    wf_windows = {}

    for wf_name, wf_config in workflows.items():
        if not wf_config.get("enabled", True):
            continue

        sw = wf_config.get("parameters", {}).get("scan_window", {})
        lookback_hours = sw.get("lookback_hours", default_lookback)
        tolerance_minutes = sw.get("tolerance_minutes", default_tolerance)
        enforce = sw.get("enforce", default_enforce)

        # Validate ranges
        if not (MIN_LOOKBACK_HOURS <= lookback_hours <= MAX_LOOKBACK_HOURS):
            raise ValueError(
                f"{wf_name}: lookback_hours={lookback_hours} out of range "
                f"[{MIN_LOOKBACK_HOURS}, {MAX_LOOKBACK_HOURS}]"
            )
        if enforce not in VALID_ENFORCE_MODES:
            raise ValueError(
                f"{wf_name}: enforce='{enforce}' not in {VALID_ENFORCE_MODES}"
            )

        # Deterministic datetime arithmetic (NO LLM involved)
        window_end = t0
        window_start = t0 - timedelta(hours=lookback_hours)
        effective_start = window_start - timedelta(minutes=tolerance_minutes)

        wf_windows[wf_name] = {
            "lookback_hours": lookback_hours,
            "tolerance_minutes": tolerance_minutes,
            "enforce": enforce,
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat(),
            "effective_start": effective_start.isoformat(),
            # Human-readable Korean format (for report metadata injection)
            "window_start_ko": window_start.strftime("%Y년 %m월 %d일 %H:%M UTC"),
            "window_end_ko": window_end.strftime("%Y년 %m월 %d일 %H:%M UTC"),
            # Human-readable English format (v1.1.0 — bilingual support)
            "window_start_en": window_start.strftime("%B %d, %Y %H:%M UTC"),
            "window_end_en": window_end.strftime("%B %d, %Y %H:%M UTC"),
            # Date-only (for file naming)
            "window_start_date": window_start.strftime("%Y-%m-%d"),
            "window_end_date": window_end.strftime("%Y-%m-%d"),
        }

    # 5. Build result
    result = {
        "generator": GENERATOR_ID,
        "generator_version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        # ── T₀ (Anchor Timestamp) ──
        "anchor_timestamp": t0.isoformat(),
        "anchor_date": t0.strftime("%Y-%m-%d"),
        "anchor_time_ko": t0.strftime("%Y년 %m월 %d일 %H:%M:%S UTC"),
        "anchor_time_en": t0.strftime("%B %d, %Y %H:%M:%S UTC"),
        # ── Global Settings ──
        "temporal_consistency_enabled": tc_enabled,
        "default_lookback_hours": default_lookback,
        "default_tolerance_minutes": default_tolerance,
        "default_enforce": default_enforce,
        # ── Per-Workflow Windows ──
        "workflows": wf_windows,
        # ── Provenance ──
        "registry_path": str(registry_path),
        "registry_version": registry.get("system", {}).get("version", "unknown"),
    }

    # 6. Write to file if output_path given
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def load_scan_window(state_file_path: str) -> Dict[str, Any]:
    """
    Load a previously generated scan-window state file.

    This is the function that downstream agents/scripts should call
    to get temporal parameters — NOT datetime arithmetic.

    Args:
        state_file_path: Path to the scan-window JSON file

    Returns:
        Scan window dictionary

    Raises:
        FileNotFoundError: If state file does not exist
        json.JSONDecodeError: If state file is malformed
    """
    path = Path(state_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Scan window state file not found: {state_file_path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_workflow_window(
    state: Dict[str, Any], workflow_name: str
) -> Dict[str, Any]:
    """
    Extract a specific workflow's window from the state file.

    Args:
        state: Loaded scan-window state dictionary
        workflow_name: e.g., "wf1-general", "wf2-arxiv", "wf3-naver"

    Returns:
        Workflow-specific window dictionary

    Raises:
        KeyError: If workflow not found in state
    """
    wf = state.get("workflows", {}).get(workflow_name)
    if wf is None:
        available = list(state.get("workflows", {}).keys())
        raise KeyError(
            f"Workflow '{workflow_name}' not in state file. "
            f"Available: {available}"
        )
    return wf


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate deterministic scan window from SOT (temporal_anchor.py)"
    )
    parser.add_argument(
        "--registry",
        default="env-scanning/config/workflow-registry.yaml",
        help="Path to workflow-registry.yaml (SOT)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for scan-window JSON state file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print result as JSON to stdout",
    )
    args = parser.parse_args()

    try:
        result = generate_scan_window(
            registry_path=args.registry,
            output_path=args.output,
        )

        if args.json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Human-readable summary
            print("=" * 60)
            print(f"  Temporal Anchor: SUCCESS")
            print(f"  T₀: {result['anchor_timestamp']}")
            print(f"  Registry: {result['registry_path']} (v{result['registry_version']})")
            print("=" * 60)
            for wf_name, wf in result["workflows"].items():
                print(
                    f"  {wf_name}: [{wf['window_start']}] → [{wf['window_end']}] "
                    f"({wf['lookback_hours']}h, ±{wf['tolerance_minutes']}min, {wf['enforce']})"
                )
            print("=" * 60)
            if args.output:
                print(f"  State file: {args.output}")

        sys.exit(0)

    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
