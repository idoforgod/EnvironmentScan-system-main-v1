#!/usr/bin/env python3
"""
Exploration Merge Gate — Atomic Signal Merge + Exhaustive Verification
======================================================================
Merges exploration signals into raw/daily-scan and classified-signals JSON
files ATOMICALLY. Then verifies the merge result with 100% coverage.

This replaces the LLM-instruction-based merge in env-scan-orchestrator.md
with a deterministic Python operation. The script either succeeds (both
files updated) or fails (neither file updated) — there is no partial state.

Design Principle:
    "합치라는 '지시'가 아닌, 합침을 '강제'하는 메커니즘."
    The script either MERGES BOTH files or NONE — no way to update only one.

Pipeline Position:
    exploration-orchestrator → exploration-results.json
                                      ↓
    exploration_merge_gate.py merge (THIS) → raw + classified updated
    exploration_merge_gate.py verify (THIS) → 100% verification
                                      ↓
    Step 1.3a: dedup reads the merged files

Usage (CLI):
    # Merge exploration signals into pipeline files
    python3 env-scanning/core/exploration_merge_gate.py merge \\
        --exploration-signals exploration-signals.json \\
        --target-raw wf1-general/raw/daily-scan-2026-02-10.json \\
        --target-classified wf1-general/structured/classified-signals-2026-02-10.json

    # Verify merge integrity
    python3 env-scanning/core/exploration_merge_gate.py verify \\
        --target-raw wf1-general/raw/daily-scan-2026-02-10.json \\
        --target-classified wf1-general/structured/classified-signals-2026-02-10.json \\
        --excluded-sources wf1-general/exploration/excluded-sources.json \\
        --max-exploration-signals 50

Usage (importable):
    from core.exploration_merge_gate import merge_exploration_signals, verify_exploration_signals

Exit codes:
    0 = SUCCESS
    1 = ERROR (merge or verification failed)
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
GATE_ID = "exploration_merge_gate.py"


# ---------------------------------------------------------------------------
# Signal Extraction (reuse patterns from temporal_gate.py)
# ---------------------------------------------------------------------------

def _extract_items(data: Any) -> list[dict]:
    """Extract signal list from a JSON file, supporting various key names."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "classified_signals", "signals"):
            if key in data:
                return data[key]
    return []


def _get_items_key(data: dict) -> str | None:
    """Identify which key holds the signal array in the JSON structure."""
    for key in ("items", "classified_signals", "signals"):
        if key in data:
            return key
    return None


# ---------------------------------------------------------------------------
# Core: Merge
# ---------------------------------------------------------------------------

def merge_exploration_signals(
    exploration_signals_path: str,
    target_raw_path: str,
    target_classified_path: str,
    output_report_path: str | None = None,
) -> dict[str, Any]:
    """
    Atomically merge exploration signals into both raw and classified files.

    Guarantees:
        - BOTH files are updated, or NEITHER is updated (atomic pair)
        - Existing signals are preserved (append-only)
        - Duplicate signal IDs are prevented (idempotent merge)
        - Original files are backed up before modification

    Args:
        exploration_signals_path: JSON file with exploration signals
            (list or {"signals": [...]} or {"items": [...]})
        target_raw_path: raw/daily-scan-{date}.json
        target_classified_path: structured/classified-signals-{date}.json
        output_report_path: Optional path to write merge report JSON

    Returns:
        Merge report dictionary

    Raises:
        FileNotFoundError: If any input file doesn't exist
        ValueError: If exploration signals are invalid
    """
    # 1. Load exploration signals
    exp_path = Path(exploration_signals_path)
    if not exp_path.exists():
        raise FileNotFoundError(f"Exploration signals file not found: {exploration_signals_path}")

    with open(exp_path, "r", encoding="utf-8") as f:
        exp_data = json.load(f)

    exp_signals = _extract_items(exp_data)
    if not exp_signals:
        return _build_report("SKIPPED", "No exploration signals to merge", 0, 0, 0)

    # 2. Load both target files
    raw_path = Path(target_raw_path)
    cls_path = Path(target_classified_path)

    if not raw_path.exists():
        raise FileNotFoundError(f"Target raw file not found: {target_raw_path}")
    if not cls_path.exists():
        raise FileNotFoundError(f"Target classified file not found: {target_classified_path}")

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    with open(cls_path, "r", encoding="utf-8") as f:
        cls_data = json.load(f)

    raw_key = _get_items_key(raw_data)
    cls_key = _get_items_key(cls_data)

    if raw_key is None:
        raise ValueError(f"Cannot find signal array in {target_raw_path} (expected 'items', 'classified_signals', or 'signals')")
    if cls_key is None:
        raise ValueError(f"Cannot find signal array in {target_classified_path} (expected 'items', 'classified_signals', or 'signals')")

    # 3. Deduplicate: collect existing IDs from both files
    existing_raw_ids = {sig.get("id") for sig in raw_data[raw_key] if sig.get("id")}
    existing_cls_ids = {sig.get("id") for sig in cls_data[cls_key] if sig.get("id")}
    all_existing_ids = existing_raw_ids | existing_cls_ids

    # Filter out signals already present (idempotent merge)
    new_signals = [sig for sig in exp_signals if sig.get("id") not in all_existing_ids]
    skipped = len(exp_signals) - len(new_signals)

    if not new_signals:
        report = _build_report("SKIPPED", "All exploration signals already present", len(exp_signals), 0, skipped)
        if output_report_path:
            _write_json(output_report_path, report)
        return report

    # 4. Create backups (BOTH files, before any modification)
    raw_backup = raw_path.with_suffix(".json.merge-bak")
    cls_backup = cls_path.with_suffix(".json.merge-bak")
    shutil.copy2(raw_path, raw_backup)
    shutil.copy2(cls_path, cls_backup)

    try:
        # 5. Append to both in-memory
        raw_before = len(raw_data[raw_key])
        cls_before = len(cls_data[cls_key])

        raw_data[raw_key].extend(new_signals)
        cls_data[cls_key].extend(new_signals)

        # 6. Write to temporary files (not overwriting originals yet)
        raw_tmp = raw_path.with_suffix(".json.merge-tmp")
        cls_tmp = cls_path.with_suffix(".json.merge-tmp")

        _write_json(str(raw_tmp), raw_data)
        _write_json(str(cls_tmp), cls_data)

        # 7. Verify temp files are valid JSON with correct counts
        with open(raw_tmp, "r", encoding="utf-8") as f:
            raw_verify = json.load(f)
        with open(cls_tmp, "r", encoding="utf-8") as f:
            cls_verify = json.load(f)

        raw_after = len(_extract_items(raw_verify))
        cls_after = len(_extract_items(cls_verify))

        if raw_after != raw_before + len(new_signals):
            raise ValueError(
                f"Raw file count mismatch: expected {raw_before + len(new_signals)}, got {raw_after}"
            )
        if cls_after != cls_before + len(new_signals):
            raise ValueError(
                f"Classified file count mismatch: expected {cls_before + len(new_signals)}, got {cls_after}"
            )

        # 8. Atomic replace: BOTH files or NEITHER
        os.replace(raw_tmp, raw_path)
        os.replace(cls_tmp, cls_path)

        # 9. Cleanup backups (merge successful)
        raw_backup.unlink(missing_ok=True)
        cls_backup.unlink(missing_ok=True)

        report = _build_report(
            "SUCCESS",
            f"Merged {len(new_signals)} exploration signals into both files",
            len(exp_signals),
            len(new_signals),
            skipped,
            raw_before=raw_before,
            raw_after=raw_after,
            cls_before=cls_before,
            cls_after=cls_after,
        )

        if output_report_path:
            _write_json(output_report_path, report)

        return report

    except Exception as e:
        # ROLLBACK: restore both files from backup
        if raw_backup.exists():
            shutil.copy2(raw_backup, raw_path)
        if cls_backup.exists():
            shutil.copy2(cls_backup, cls_path)
        # Cleanup temp files
        for tmp in [raw_path.with_suffix(".json.merge-tmp"),
                     cls_path.with_suffix(".json.merge-tmp")]:
            if tmp.exists():
                tmp.unlink()
        raise ValueError(f"Merge failed, both files restored from backup: {e}") from e


# ---------------------------------------------------------------------------
# Core: Verify
# ---------------------------------------------------------------------------

def verify_exploration_signals(
    target_raw_path: str,
    target_classified_path: str,
    excluded_sources_path: str | None = None,
    max_exploration_signals: int = 50,
    output_report_path: str | None = None,
) -> dict[str, Any]:
    """
    Exhaustively verify ALL exploration signals in both pipeline files.

    Checks (100% coverage — every signal is checked):
        V1: Every exploration signal has source.tier == "exploration"
        V2: Every exploration signal ID starts with "explore-"
        V3: No exploration source name appears in excluded-sources.json
        V4: Exploration signal count <= max_exploration_signals
        V5: Both files contain the same exploration signal IDs (consistency)

    Args:
        target_raw_path: raw/daily-scan-{date}.json
        target_classified_path: structured/classified-signals-{date}.json
        excluded_sources_path: Optional path to excluded-sources.json
        max_exploration_signals: Maximum allowed exploration signals
        output_report_path: Optional path to write verification report

    Returns:
        Verification report dictionary
    """
    # Load files
    raw_path = Path(target_raw_path)
    cls_path = Path(target_classified_path)

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw file not found: {target_raw_path}")
    if not cls_path.exists():
        raise FileNotFoundError(f"Classified file not found: {target_classified_path}")

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_signals = _extract_items(json.load(f))
    with open(cls_path, "r", encoding="utf-8") as f:
        cls_signals = _extract_items(json.load(f))

    # Extract exploration signals from both files
    raw_explore = [s for s in raw_signals if _is_exploration_signal(s)]
    cls_explore = [s for s in cls_signals if _is_exploration_signal(s)]

    # Load excluded sources
    excluded_names: set[str] = set()
    if excluded_sources_path:
        ex_path = Path(excluded_sources_path)
        if ex_path.exists():
            with open(ex_path, "r", encoding="utf-8") as f:
                ex_data = json.load(f)
            excluded_names = {n.lower() for n in ex_data.get("excluded_sources", [])}

    # Run all checks
    violations: list[dict] = []

    # V1: source.tier == "exploration"
    for sig in raw_explore + cls_explore:
        tier = sig.get("source", {}).get("tier", "")
        if tier != "exploration":
            violations.append({
                "check": "V1_tier_tag",
                "signal_id": sig.get("id", "unknown"),
                "expected": "exploration",
                "actual": tier,
            })

    # V2: signal ID starts with "explore-"
    for sig in raw_explore + cls_explore:
        sig_id = sig.get("id", "")
        if not sig_id.startswith("explore-"):
            violations.append({
                "check": "V2_id_prefix",
                "signal_id": sig_id,
                "expected": "explore-*",
                "actual": sig_id[:20],
            })

    # V3: No exploration source in excluded list
    for sig in raw_explore:
        source_name = (sig.get("exploration_source", "")
                       or sig.get("source", {}).get("name", ""))
        if source_name.lower() in excluded_names:
            violations.append({
                "check": "V3_excluded_source",
                "signal_id": sig.get("id", "unknown"),
                "source_name": source_name,
            })

    # V4: Count <= max
    total_explore = len(raw_explore)
    if total_explore > max_exploration_signals:
        violations.append({
            "check": "V4_count_limit",
            "count": total_explore,
            "max": max_exploration_signals,
        })

    # V5: Both files have same exploration signal IDs
    raw_ids = {s.get("id") for s in raw_explore}
    cls_ids = {s.get("id") for s in cls_explore}
    if raw_ids != cls_ids:
        only_raw = raw_ids - cls_ids
        only_cls = cls_ids - raw_ids
        violations.append({
            "check": "V5_consistency",
            "only_in_raw": sorted(only_raw),
            "only_in_classified": sorted(only_cls),
        })

    # Build result
    passed = len(violations) == 0
    status = "PASS" if passed else "FAIL"
    message = (
        f"All {total_explore} exploration signals verified"
        if passed else
        f"{len(violations)} violation(s) found in {total_explore} exploration signals"
    )

    report = {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "command": "verify",
        "status": status,
        "message": message,
        "statistics": {
            "raw_total_signals": len(raw_signals),
            "raw_exploration_signals": len(raw_explore),
            "classified_total_signals": len(cls_signals),
            "classified_exploration_signals": len(cls_explore),
            "max_exploration_signals": max_exploration_signals,
        },
        "violations": violations,
    }

    if output_report_path:
        _write_json(output_report_path, report)

    return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_exploration_signal(signal: dict) -> bool:
    """Detect exploration signals by tier tag OR ID prefix."""
    if signal.get("source", {}).get("tier") == "exploration":
        return True
    sig_id = signal.get("id", "")
    if isinstance(sig_id, str) and sig_id.startswith("explore-"):
        return True
    return False


def _build_report(
    status: str,
    message: str,
    total_input: int,
    merged: int,
    skipped: int,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build a merge report dictionary."""
    report = {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "command": "merge",
        "status": status,
        "message": message,
        "statistics": {
            "total_input_signals": total_input,
            "merged": merged,
            "skipped_duplicate": skipped,
        },
    }
    report["statistics"].update(kwargs)
    return report


def _write_json(path: str, data: Any) -> None:
    """Write JSON with proper encoding."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Exploration Merge Gate — atomic signal merge + exhaustive verification"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- merge ---
    merge_parser = subparsers.add_parser("merge", help="Merge exploration signals into pipeline files")
    merge_parser.add_argument("--exploration-signals", required=True,
                              help="Path to exploration signals JSON")
    merge_parser.add_argument("--target-raw", required=True,
                              help="Path to raw/daily-scan-{date}.json")
    merge_parser.add_argument("--target-classified", required=True,
                              help="Path to structured/classified-signals-{date}.json")
    merge_parser.add_argument("--output", default=None,
                              help="Path to write merge report JSON")
    merge_parser.add_argument("--json", action="store_true", dest="json_output",
                              help="Print result as JSON to stdout")

    # --- verify ---
    verify_parser = subparsers.add_parser("verify", help="Verify exploration signal integrity")
    verify_parser.add_argument("--target-raw", required=True,
                               help="Path to raw/daily-scan-{date}.json")
    verify_parser.add_argument("--target-classified", required=True,
                               help="Path to structured/classified-signals-{date}.json")
    verify_parser.add_argument("--excluded-sources", default=None,
                               help="Path to excluded-sources.json")
    verify_parser.add_argument("--max-exploration-signals", type=int, default=50,
                               help="Maximum allowed exploration signals")
    verify_parser.add_argument("--output", default=None,
                               help="Path to write verification report JSON")
    verify_parser.add_argument("--json", action="store_true", dest="json_output",
                               help="Print result as JSON to stdout")

    args = parser.parse_args()

    try:
        if args.command == "merge":
            result = merge_exploration_signals(
                exploration_signals_path=args.exploration_signals,
                target_raw_path=args.target_raw,
                target_classified_path=args.target_classified,
                output_report_path=args.output,
            )
        elif args.command == "verify":
            result = verify_exploration_signals(
                target_raw_path=args.target_raw,
                target_classified_path=args.target_classified,
                excluded_sources_path=args.excluded_sources,
                max_exploration_signals=args.max_exploration_signals,
                output_report_path=args.output,
            )
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

        if args.json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            status = result["status"]
            icon = "PASS" if status in ("SUCCESS", "PASS", "SKIPPED") else "FAIL"
            print("=" * 60)
            print(f"  [{icon}] Exploration Merge Gate: {args.command}")
            print(f"  {result['message']}")
            stats = result.get("statistics", {})
            if args.command == "merge":
                print(f"  Input: {stats.get('total_input_signals', 0)}  |  "
                      f"Merged: {stats.get('merged', 0)}  |  "
                      f"Skipped: {stats.get('skipped_duplicate', 0)}")
            else:
                print(f"  Raw exploration: {stats.get('raw_exploration_signals', 0)}  |  "
                      f"Classified exploration: {stats.get('classified_exploration_signals', 0)}")
                if result.get("violations"):
                    print(f"  Violations: {len(result['violations'])}")
                    for v in result["violations"][:5]:
                        print(f"    - {v['check']}: {v.get('signal_id', v.get('count', ''))}")
            print("=" * 60)

        if result["status"] in ("SUCCESS", "PASS", "SKIPPED"):
            sys.exit(0)
        else:
            sys.exit(1)

    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
