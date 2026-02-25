#!/usr/bin/env python3
"""
Exploration Gate — Programmatic Pipeline Gate for Source Exploration (Stage C)
==============================================================================
Deterministic enforcement of Source Exploration execution within WF1.

This script is called by the WF1 orchestrator at three points:
  1. BEFORE exploration: `check` — decides if exploration MUST run
  2. AFTER exploration:  `post`  — records proof + updates history
  3. At PG1 gate:        `verify` — validates proof file integrity

Design Principle:
    "검증하라는 '지시'가 아닌, 검증을 '강제'하는 메커니즘."
    The gate either PASSES or FAILS — there is no way to "skip" the check.
    This is the programmatic safety net for Stage C, which was previously
    unreliable due to LLM instruction-following within a 51K-token spec.

Usage (CLI):
    # 1. Check (before exploration)
    python3 env-scanning/core/exploration_gate.py check \\
        --sot env-scanning/config/workflow-registry.yaml \\
        --classified env-scanning/wf1-general/structured/classified-signals-2026-02-13.json \\
        --date 2026-02-13 \\
        --output env-scanning/wf1-general/exploration/gate-decision-2026-02-13.json

    # 2. Post (after exploration)
    python3 env-scanning/core/exploration_gate.py post \\
        --decision env-scanning/wf1-general/exploration/gate-decision-2026-02-13.json \\
        --candidates env-scanning/wf1-general/exploration/candidates/exploration-candidates-2026-02-13.json \\
        --signals env-scanning/wf1-general/exploration/exploration-signals-2026-02-13.json \\
        --method single-agent \\
        --data-root env-scanning/wf1-general \\
        --output env-scanning/wf1-general/exploration/exploration-proof-2026-02-13.json

    # 3. Verify (at PG1)
    python3 env-scanning/core/exploration_gate.py verify \\
        --proof env-scanning/wf1-general/exploration/exploration-proof-2026-02-13.json \\
        --decision env-scanning/wf1-general/exploration/gate-decision-2026-02-13.json

Usage (importable):
    from core.exploration_gate import gate_check, gate_post, gate_verify

Exit codes:
    0 = PASS
    1 = FAIL (critical validation error)
    2 = WARN (non-critical issue logged)

Version: 1.0.0
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
GATE_ID = "exploration_gate.py"

# Decision values (deterministic outcomes)
DECISION_MUST_RUN = "MUST_RUN"
DECISION_SKIP_DISABLED = "SKIP_DISABLED"
DECISION_SKIP_BASE_ONLY = "SKIP_BASE_ONLY"


# ---------------------------------------------------------------------------
# Helper: load YAML (with graceful fallback)
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file, raising clear errors."""
    if yaml is None:
        raise ImportError("PyYAML is required: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_json(path: Path) -> Any:
    """Load a JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: Any) -> None:
    """Write JSON atomically: write to .tmp then rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    # Verify before rename
    with open(tmp, encoding="utf-8") as f:
        json.load(f)  # integrity check
    import os
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Command 1: CHECK — Determine if exploration must run
# ---------------------------------------------------------------------------

def gate_check(
    sot_path: str,
    classified_path: Optional[str] = None,
    date: str = "",
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Deterministic gate decision for source exploration.

    Logic:
        1. Read SOT → wf1-general.parameters.source_exploration
        2. If exploration.enabled == false → SKIP_DISABLED
        3. If base_only_flag == true → SKIP_BASE_ONLY
        4. Otherwise → MUST_RUN (with gap analysis summary if classified_path given)

    Args:
        sot_path: Path to workflow-registry.yaml
        classified_path: Optional path to classified signals JSON (for gap preview)
        date: Scan date (YYYY-MM-DD)
        output_path: Path to write gate decision JSON

    Returns:
        Gate decision dict
    """
    sot = _load_yaml(Path(sot_path))

    wf1_cfg = sot.get("workflows", {}).get("wf1-general", {})
    wf1_enabled = wf1_cfg.get("enabled", False)
    params = wf1_cfg.get("parameters", {})
    exp_cfg = params.get("source_exploration", {})
    exp_enabled = exp_cfg.get("enabled", False)
    base_only = params.get("base_only_flag", False)

    scan_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Decision logic
    if not wf1_enabled or not exp_enabled:
        decision = DECISION_SKIP_DISABLED
        reason = "source_exploration.enabled=false or wf1-general.enabled=false"
    elif base_only:
        decision = DECISION_SKIP_BASE_ONLY
        reason = "base_only_flag=true — exploration skipped to focus on base sources"
    else:
        decision = DECISION_MUST_RUN
        reason = "source_exploration.enabled=true and base_only_flag=false"

    # Optional gap analysis preview
    gap_preview = None
    if classified_path and decision == DECISION_MUST_RUN:
        try:
            cls_data = _load_json(Path(classified_path))
            signals = cls_data if isinstance(cls_data, list) else (
                cls_data.get("classified_signals", []) or
                cls_data.get("items", []) or
                cls_data.get("signals", [])
            )
            total = len(signals)
            from collections import Counter
            cat_counts: Counter = Counter()
            for sig in signals:
                cat = sig.get("category") or sig.get("preliminary_category", "")
                if cat:
                    cat_counts[cat] += 1
            threshold = exp_cfg.get("coverage_gap_threshold", 0.15)
            distribution = {cat: cnt / total for cat, cnt in cat_counts.items()} if total > 0 else {}
            expected_cats = {"S_Social", "T_Technological", "E_Economic",
                            "E_Environmental", "P_Political", "s_spiritual"}
            gaps = [cat for cat in expected_cats if distribution.get(cat, 0.0) < threshold]
            gap_preview = {
                "total_signals": total,
                "distribution": {k: round(v, 3) for k, v in distribution.items()},
                "gaps": sorted(gaps),
                "threshold": threshold,
            }
        except Exception as e:
            gap_preview = {"error": str(e)[:200]}

    result = {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "command": "check",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "date": scan_date,
        "decision": decision,
        "reason": reason,
        "exploration_config": {
            "enabled": exp_enabled,
            "method": exp_cfg.get("exploration_method", "unknown"),
            "max_candidates": exp_cfg.get("max_candidates_per_scan", 5),
            "coverage_gap_threshold": exp_cfg.get("coverage_gap_threshold", 0.15),
        },
        "base_only_flag": base_only,
        "gap_preview": gap_preview,
    }

    if output_path:
        _write_json(Path(output_path), result)

    return result


# ---------------------------------------------------------------------------
# Command 2: POST — Record exploration proof + update history
# ---------------------------------------------------------------------------

def gate_post(
    decision_path: str,
    data_root: str,
    candidates_path: Optional[str] = None,
    signals_path: Optional[str] = None,
    method_used: str = "unknown",
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record exploration proof and update history as safety net.

    This is called AFTER exploration completes (or after SKIP decision).
    It creates an exploration-proof-{date}.json and records the scan
    in ExplorationHistory (with duplicate prevention).

    Args:
        decision_path: Path to gate-decision-{date}.json (from check command)
        data_root: WF1 data_root path
        candidates_path: Path to exploration-candidates-{date}.json (if exploration ran)
        signals_path: Path to exploration-signals-{date}.json (if exploration ran)
        method_used: "agent-team" | "single-agent" | "skipped"
        output_path: Path to write exploration-proof-{date}.json

    Returns:
        Proof dict
    """
    decision = _load_json(Path(decision_path))
    gate_decision = decision.get("decision", "unknown")
    scan_date = decision.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    # Determine actual exploration results
    candidates_discovered = 0
    viable_count = 0
    signals_collected = 0
    gaps_analyzed = []
    frontier_selection_file: Optional[str] = None

    if gate_decision == DECISION_MUST_RUN:
        # Load candidates if available
        if candidates_path and Path(candidates_path).exists():
            try:
                cand_data = _load_json(Path(candidates_path))
                candidates_discovered = cand_data.get("total_candidates_discovered",
                                                       len(cand_data.get("viable_candidates", [])) +
                                                       len(cand_data.get("non_viable_candidates", [])))
                viable_count = len(cand_data.get("viable_candidates", []))
                gaps_analyzed = cand_data.get("gap_analysis_result", {}).get("pre_exploration_gaps", [])
            except Exception:
                pass

        # Load signals if available
        if signals_path and Path(signals_path).exists():
            try:
                sig_data = _load_json(Path(signals_path))
                if isinstance(sig_data, list):
                    signals_collected = len(sig_data)
                elif isinstance(sig_data, dict):
                    items = sig_data.get("items", sig_data.get("signals", []))
                    signals_collected = len(items)
            except Exception:
                pass

        # VP-5 evidence: frontier_selector.py writes this file before any discovery runs.
        # Its existence proves the orchestrator executed past gap analysis — not short-circuited.
        # Convention: {data_root}/exploration/frontier-selection-{scan_date}.json
        _fs_path = Path(data_root) / "exploration" / f"frontier-selection-{scan_date}.json"
        frontier_selection_file = str(_fs_path) if _fs_path.exists() else None

    execution_status = "executed" if gate_decision == DECISION_MUST_RUN else "skipped"

    proof = {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "command": "post",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "date": scan_date,
        "gate_decision": gate_decision,
        "execution_status": execution_status,
        "method_used": method_used if gate_decision == DECISION_MUST_RUN else "n/a",
        "results": {
            "candidates_discovered": candidates_discovered,
            "viable_count": viable_count,
            "signals_collected": signals_collected,
            "gaps_analyzed": gaps_analyzed,
        },
        "files": {
            "decision": decision_path,
            "candidates": candidates_path if candidates_path and Path(candidates_path).exists() else None,
            "signals": signals_path if signals_path and Path(signals_path).exists() else None,
            "frontier_selection": frontier_selection_file,
        },
    }

    # Write proof file
    proof_path = Path(output_path) if output_path else (
        Path(data_root) / "exploration" / f"exploration-proof-{scan_date}.json"
    )
    _write_json(proof_path, proof)
    proof["proof_file"] = str(proof_path)

    # Safety net: record in ExplorationHistory (with duplicate prevention)
    if gate_decision == DECISION_MUST_RUN:
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from source_explorer import ExplorationHistory
            history = ExplorationHistory(str(Path(data_root) / "exploration" / "history"))
            history_data = history.load()

            # Duplicate prevention: check if scan for this date already recorded
            existing_dates = {
                s.get("date") for s in history_data.get("scans", [])
            }
            if scan_date not in existing_dates:
                history_data.setdefault("scans", []).append({
                    "date": scan_date,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "method_used": method_used,
                    "candidates_discovered": candidates_discovered,
                    "viable_count": viable_count,
                    "signals_collected": signals_collected,
                    "gaps_analyzed": gaps_analyzed,
                    "recorded_by": "exploration_gate.py (safety net)",
                })
                # Keep only last 30 scans
                if len(history_data["scans"]) > 30:
                    history_data["scans"] = history_data["scans"][-30:]
                history.save(history_data)
                proof["history_updated"] = True
            else:
                proof["history_updated"] = False
                proof["history_note"] = f"Scan for {scan_date} already in history (no duplicate)"
        except Exception as e:
            proof["history_updated"] = False
            proof["history_error"] = str(e)[:200]

    return proof


# ---------------------------------------------------------------------------
# Command 3: VERIFY — Validate proof file integrity
# ---------------------------------------------------------------------------

def gate_verify(
    proof_path: str,
    decision_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify exploration proof file integrity. Called at PG1.

    Checks (VP-1 through VP-5):
        VP-1: Proof file exists and is valid JSON
        VP-2: gate_decision field matches decision file (if provided)
        VP-3: If decision was MUST_RUN, execution_status must be "executed"
        VP-4: If executed, signals_collected must be >= 0 (proof of actual execution)
        VP-5: If MUST_RUN+executed, frontier-selection file must exist on disk
              (Python-enforced proof that frontier_selector.py ran past gap analysis)

    Args:
        proof_path: Path to exploration-proof-{date}.json
        decision_path: Optional path to gate-decision-{date}.json for cross-check

    Returns:
        Verification result dict
    """
    checks = []

    # VP-1: Proof file exists and is valid JSON
    proof = None
    try:
        proof = _load_json(Path(proof_path))
        checks.append({
            "id": "VP-1",
            "description": "Proof file exists and is valid JSON",
            "passed": True,
        })
    except FileNotFoundError:
        checks.append({
            "id": "VP-1",
            "description": "Proof file exists and is valid JSON",
            "passed": False,
            "detail": f"File not found: {proof_path}",
        })
    except json.JSONDecodeError as e:
        checks.append({
            "id": "VP-1",
            "description": "Proof file exists and is valid JSON",
            "passed": False,
            "detail": f"Invalid JSON: {e}",
        })

    if proof is None:
        # Cannot proceed without proof file
        return {
            "gate_id": GATE_ID,
            "gate_version": VERSION,
            "command": "verify",
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "status": "FAIL",
            "message": "Proof file missing or invalid — exploration gate verification failed",
            "checks": checks,
            "all_passed": False,
        }

    # VP-2: gate_decision matches decision file
    proof_decision = proof.get("gate_decision", "unknown")
    if decision_path:
        try:
            decision_data = _load_json(Path(decision_path))
            file_decision = decision_data.get("decision", "unknown")
            match = proof_decision == file_decision
            checks.append({
                "id": "VP-2",
                "description": "Proof gate_decision matches decision file",
                "passed": match,
                "detail": "" if match else f"proof={proof_decision}, file={file_decision}",
            })
        except Exception as e:
            checks.append({
                "id": "VP-2",
                "description": "Proof gate_decision matches decision file",
                "passed": False,
                "detail": f"Could not load decision file: {e}",
            })
    else:
        # No decision file to cross-check — skip VP-2
        checks.append({
            "id": "VP-2",
            "description": "Proof gate_decision matches decision file",
            "passed": True,
            "detail": "No decision file provided — skipped",
        })

    # VP-3: If MUST_RUN, execution_status must be "executed"
    execution_status = proof.get("execution_status", "unknown")
    if proof_decision == DECISION_MUST_RUN:
        vp3_passed = execution_status == "executed"
        checks.append({
            "id": "VP-3",
            "description": "MUST_RUN decision has execution_status='executed'",
            "passed": vp3_passed,
            "detail": "" if vp3_passed else f"execution_status='{execution_status}' (expected 'executed')",
        })
    else:
        # SKIP decisions: execution_status should be "skipped"
        vp3_passed = execution_status == "skipped"
        checks.append({
            "id": "VP-3",
            "description": f"{proof_decision} has execution_status='skipped'",
            "passed": vp3_passed,
            "detail": "" if vp3_passed else f"execution_status='{execution_status}' (expected 'skipped')",
        })

    # VP-4: If executed, results must have non-negative signals_collected
    if execution_status == "executed":
        results = proof.get("results", {})
        signals_collected = results.get("signals_collected", -1)
        vp4_passed = isinstance(signals_collected, (int, float)) and signals_collected >= 0
        checks.append({
            "id": "VP-4",
            "description": "Executed exploration has valid signals_collected count",
            "passed": vp4_passed,
            "detail": "" if vp4_passed else f"signals_collected={signals_collected}",
        })
    else:
        checks.append({
            "id": "VP-4",
            "description": "Skipped exploration — no signals count check needed",
            "passed": True,
        })

    # VP-5: If MUST_RUN+executed, frontier-selection file must exist on disk.
    # frontier_selector.py writes this file at the START of exploration (Step 2.5),
    # before any discovery agents run. Its existence is Python-enforced proof that:
    #   (a) the orchestrator did NOT short-circuit after gap analysis, AND
    #   (b) frontier keyword selection actually executed (enabling beta agent discovery).
    # A null or missing file means the orchestrator bypassed Step 2.5 — HALT.
    if proof_decision == DECISION_MUST_RUN and execution_status == "executed":
        files_dict = proof.get("files", {})
        frontier_file = files_dict.get("frontier_selection")
        if frontier_file is None:
            vp5_passed = False
            vp5_detail = (
                "frontier_selection not recorded in proof — "
                "frontier_selector.py may not have run (possible early-exit bypass)"
            )
        elif not Path(frontier_file).exists():
            vp5_passed = False
            vp5_detail = f"frontier-selection file not found on disk: {frontier_file}"
        else:
            vp5_passed = True
            vp5_detail = ""
        checks.append({
            "id": "VP-5",
            "description": "Frontier selection file exists (proof exploration ran past gap analysis)",
            "passed": vp5_passed,
            "detail": vp5_detail,
        })
    else:
        checks.append({
            "id": "VP-5",
            "description": "Skipped/disabled exploration — no frontier selection check needed",
            "passed": True,
        })

    all_passed = all(c["passed"] for c in checks)
    status = "PASS" if all_passed else "FAIL"

    result = {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "command": "verify",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "proof_file": proof_path,
        "status": status,
        "message": f"All {len(checks)} verification checks passed" if all_passed else
                   f"{sum(1 for c in checks if not c['passed'])}/{len(checks)} checks FAILED",
        "checks": checks,
        "all_passed": all_passed,
    }

    return result


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Exploration Gate — Programmatic Pipeline Gate for Source Exploration"
    )
    subparsers = parser.add_subparsers(dest="command", required=True,
                                        help="Gate command")

    # --- check subcommand ---
    check_parser = subparsers.add_parser(
        "check", help="Determine if exploration must run"
    )
    check_parser.add_argument(
        "--sot", required=True,
        help="Path to workflow-registry.yaml"
    )
    check_parser.add_argument(
        "--classified", default=None,
        help="Path to classified signals JSON (for gap preview)"
    )
    check_parser.add_argument(
        "--date", default="",
        help="Scan date (YYYY-MM-DD)"
    )
    check_parser.add_argument(
        "--output", default=None,
        help="Output path for gate decision JSON"
    )
    check_parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Print result as JSON to stdout"
    )

    # --- post subcommand ---
    post_parser = subparsers.add_parser(
        "post", help="Record exploration proof and update history"
    )
    post_parser.add_argument(
        "--decision", required=True,
        help="Path to gate-decision-{date}.json"
    )
    post_parser.add_argument(
        "--data-root", required=True,
        help="WF1 data_root path"
    )
    post_parser.add_argument(
        "--candidates", default=None,
        help="Path to exploration-candidates-{date}.json"
    )
    post_parser.add_argument(
        "--signals", default=None,
        help="Path to exploration-signals-{date}.json"
    )
    post_parser.add_argument(
        "--method", default="unknown",
        choices=["agent-team", "single-agent", "unknown"],
        help="Exploration method actually used"
    )
    post_parser.add_argument(
        "--output", default=None,
        help="Output path for exploration proof JSON"
    )
    post_parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Print result as JSON to stdout"
    )

    # --- verify subcommand ---
    verify_parser = subparsers.add_parser(
        "verify", help="Verify exploration proof integrity (for PG1)"
    )
    verify_parser.add_argument(
        "--proof", required=True,
        help="Path to exploration-proof-{date}.json"
    )
    verify_parser.add_argument(
        "--decision", default=None,
        help="Path to gate-decision-{date}.json (for cross-check)"
    )
    verify_parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Print result as JSON to stdout"
    )

    args = parser.parse_args()

    try:
        if args.command == "check":
            result = gate_check(
                sot_path=args.sot,
                classified_path=args.classified,
                date=args.date,
                output_path=args.output,
            )
            if args.json_output:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                decision = result["decision"]
                icon = {"MUST_RUN": "🔍", "SKIP_DISABLED": "⏭️",
                        "SKIP_BASE_ONLY": "⏭️"}.get(decision, "❓")
                print("=" * 60)
                print(f"  {icon} Exploration Gate: {decision}")
                print(f"  Date: {result['date']}")
                print(f"  Reason: {result['reason']}")
                if result.get("gap_preview") and "error" not in result["gap_preview"]:
                    gaps = result["gap_preview"].get("gaps", [])
                    print(f"  STEEPs gaps: {gaps if gaps else 'none detected'}")
                print("=" * 60)
            sys.exit(0)

        elif args.command == "post":
            result = gate_post(
                decision_path=args.decision,
                data_root=args.data_root,
                candidates_path=args.candidates,
                signals_path=args.signals,
                method_used=args.method,
                output_path=args.output,
            )
            if args.json_output:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                status = result["execution_status"]
                icon = "✅" if status == "executed" else "⏭️"
                print("=" * 60)
                print(f"  {icon} Exploration Proof Recorded: {status}")
                print(f"  Date: {result['date']}")
                print(f"  Decision: {result['gate_decision']}")
                if status == "executed":
                    r = result["results"]
                    print(f"  Candidates: {r['candidates_discovered']} "
                          f"(viable: {r['viable_count']})")
                    print(f"  Signals: {r['signals_collected']}")
                hist = result.get("history_updated")
                if hist is True:
                    print("  History: updated (safety net)")
                elif hist is False:
                    note = result.get("history_note", result.get("history_error", ""))
                    print(f"  History: not updated ({note})")
                print("=" * 60)
            sys.exit(0)

        elif args.command == "verify":
            result = gate_verify(
                proof_path=args.proof,
                decision_path=args.decision,
            )
            status = result["status"]
            if args.json_output:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                icon = "✅" if status == "PASS" else "❌"
                print("=" * 60)
                print(f"  {icon} Exploration Gate Verify: {status}")
                print(f"  {result['message']}")
                for c in result["checks"]:
                    ck = "✅" if c["passed"] else "❌"
                    detail = f" — {c['detail']}" if c.get("detail") else ""
                    print(f"    {ck} {c['id']}: {c['description']}{detail}")
                print("=" * 60)
            if status == "PASS":
                sys.exit(0)
            else:
                sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
