#!/usr/bin/env python3
"""
Master Task Manager — Deterministic Task Decision Engine (원천봉쇄)
===================================================================
Eliminates LLM hallucination in master-level task state management by
computing EXACT task instructions based on master-status.json state.

This module is the SINGLE PROGRAMMATIC AUTHORITY for deciding:
  - Whether to create master tasks (duplicate prevention)
  - Which step can be marked completed (gate-based verification)
  - What task updates are needed for synchronization
  - How to handle degraded mode (WF skip metadata)

The LLM's role is reduced to EXECUTION ONLY — calling TaskCreate/TaskUpdate
with the exact parameters this module outputs. No judgment required.

Design Principle:
    "계산은 Python이, 판단은 LLM이."
    Task state decisions (gate checks, duplicate detection) = Python.
    Tool invocation (TaskCreate/TaskUpdate API calls) = LLM.

Usage (CLI):
    # Check if master tasks need creation
    python3 env-scanning/core/master_task_manager.py \\
        --action init \\
        --status-file env-scanning/integrated/logs/master-status-2026-03-15.json

    # Check if step N can be marked completed
    python3 env-scanning/core/master_task_manager.py \\
        --action step-complete --step 5 \\
        --status-file env-scanning/integrated/logs/master-status-2026-03-15.json

    # Generate full sync instructions
    python3 env-scanning/core/master_task_manager.py \\
        --action sync \\
        --status-file env-scanning/integrated/logs/master-status-2026-03-15.json

    # Handle WF skip (degraded mode)
    python3 env-scanning/core/master_task_manager.py \\
        --action wf-skip --step 3 \\
        --status-file env-scanning/integrated/logs/master-status-2026-03-15.json

Exit codes:
    0 = SUCCESS (instructions written to stdout as JSON)
    1 = ERROR (file read failure, invalid arguments, etc.)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
GENERATOR_ID = "master_task_manager.py"

# Master-level step definitions with gate mappings.
# CRITICAL: Step 5 uses M4 (deliverable completeness), NOT M3 (approval only).
# This mapping is the SINGLE SOURCE OF TRUTH for gate→step associations.
#
# ⚠️ DRIFT WARNING: If you add/remove a workflow (e.g. WF5) or rename a gate,
# you MUST update this dict AND the following coupled files:
#   - .claude/agents/master-orchestrator.md (execution flow, gate sections, error handling)
#   - env-scanning/config/workflow-registry.yaml (workflow definitions)
#   - .claude/agents/TASK_MANAGEMENT_EXECUTION_GUIDE.md (master task docs)
# SOT-062 validates file existence only, NOT content consistency.
MASTER_STEPS = {
    0: {
        "key": "master_step0",
        "subject": "Step 0: SOT Validation & Setup",
        "description": "Read SOT, validate registry, initialize master state",
        "activeForm": "Validating SOT",
        "gate": None,
        "wf_key": None,
    },
    1: {
        "key": "master_step1",
        "subject": "Step 1: WF1 General Environmental Scanning",
        "description": "Execute WF1 (general multi-source scanning) via env-scan-orchestrator",
        "activeForm": "Running WF1",
        "gate": "M1",
        "wf_key": "wf1-general",
    },
    2: {
        "key": "master_step2",
        "subject": "Step 2: WF2 arXiv Academic Deep Scanning",
        "description": "Execute WF2 (arXiv-only academic scanning) via arxiv-scan-orchestrator",
        "activeForm": "Running WF2",
        "gate": "M2",
        "wf_key": "wf2-arxiv",
    },
    3: {
        "key": "master_step3",
        "subject": "Step 3: WF3 Naver News Environmental Scanning",
        "description": "Execute WF3 (Naver News scanning with FSSF/Tipping Point) via naver-scan-orchestrator",
        "activeForm": "Running WF3",
        "gate": "M2a",
        "wf_key": "wf3-naver",
    },
    4: {
        "key": "master_step4",
        "subject": "Step 4: WF4 Multi&Global-News Environmental Scanning",
        "description": "Execute WF4 (43 direct news sites, multilingual) via multiglobal-news-scan-orchestrator",
        "activeForm": "Running WF4",
        "gate": "M2b",
        "wf_key": "wf4-multiglobal-news",
    },
    5: {
        "key": "master_step5",
        "subject": "Step 5: Integration — Report Merge + Timeline Map",
        "description": "Merge 4 independent reports, generate timeline map, validate via M3+M4 gates",
        "activeForm": "Integrating reports",
        # CRITICAL: M4 (deliverable completeness), NOT M3 (approval only).
        # M4 = validate_completion.py (CG-001~009). If M4 FAIL, HALT_AND_REMEDIATE.
        # Step 5 task must remain in_progress during remediation.
        "gate": "M4",
        "wf_key": None,
    },
    6: {
        "key": "master_step6",
        "subject": "Step 6: Finalization",
        "description": "Update master status, display completion summary, archive",
        "activeForm": "Finalizing",
        "gate": None,
        "wf_key": None,
    },
}


# ---------------------------------------------------------------------------
# Core Decision Functions
# ---------------------------------------------------------------------------

def action_init(master_status: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide whether master tasks need creation or should be skipped.

    Prevents duplicate task creation on session resume by checking
    master_task_mapping in master-status.json.

    Returns:
        {"action": "CREATE", "tasks": [...]}  -- tasks need creation
        {"action": "SKIP", "reason": "...", "existing_mapping": {...}}  -- already exist
    """
    existing_mapping = master_status.get("master_task_mapping")

    if existing_mapping and len(existing_mapping) > 0:
        return {
            "action": "SKIP",
            "reason": "master_task_mapping already exists in master-status.json "
                      f"({len(existing_mapping)} tasks). Reuse existing task IDs.",
            "existing_mapping": existing_mapping,
        }

    tasks = []
    for step_num in sorted(MASTER_STEPS.keys()):
        step = MASTER_STEPS[step_num]
        blocked_by = f"master_step{step_num - 1}" if step_num > 0 else None
        tasks.append({
            "step_num": step_num,
            "key": step["key"],
            "subject": step["subject"],
            "description": step["description"],
            "activeForm": step["activeForm"],
            "blocked_by": blocked_by,
        })

    return {
        "action": "CREATE",
        "task_count": len(tasks),
        "tasks": tasks,
        "instruction": (
            "Execute TaskCreate for each task in order. "
            "Set blockedBy dependencies as specified. "
            "Store returned task IDs in master-status.json under master_task_mapping."
        ),
    }


def action_step_complete(master_status: Dict[str, Any], step_num: int) -> Dict[str, Any]:
    """
    Decide if a step can be marked as completed.

    Checks the required gate status in master-status.json.
    Step 5 specifically requires M4 PASS (not M3).

    Returns:
        {"action": "COMPLETE", ...}  -- safe to mark completed
        {"action": "WAIT", "reason": ...}  -- gate not passed yet
    """
    if step_num not in MASTER_STEPS:
        return {
            "action": "ERROR",
            "reason": f"Invalid step number: {step_num}. Valid range: 0-6.",
        }

    step = MASTER_STEPS[step_num]
    gate = step["gate"]
    task_key = step["key"]
    task_id = master_status.get("master_task_mapping", {}).get(task_key)

    # No gate required (Step 0, Step 6)
    if gate is None:
        return {
            "action": "COMPLETE",
            "step_num": step_num,
            "task_key": task_key,
            "task_id": task_id,
            "reason": f"Step {step_num} has no gate requirement.",
            "instruction": (
                f"TaskUpdate(taskId='{task_id}', status='completed')"
                if task_id else
                f"TaskUpdate for {task_key} — resolve task_id from master_task_mapping"
            ),
        }

    # Check gate status
    gates = master_status.get("master_gates", {})
    gate_entry = gates.get(gate, {})
    gate_status = gate_entry.get("status")

    if gate_status == "PASS":
        return {
            "action": "COMPLETE",
            "step_num": step_num,
            "task_key": task_key,
            "task_id": task_id,
            "gate": gate,
            "gate_status": "PASS",
            "reason": f"Gate {gate} has PASS status. Step {step_num} can be marked completed.",
            "instruction": (
                f"TaskUpdate(taskId='{task_id}', status='completed')"
                if task_id else
                f"TaskUpdate for {task_key} — resolve task_id from master_task_mapping"
            ),
        }
    else:
        return {
            "action": "WAIT",
            "step_num": step_num,
            "task_key": task_key,
            "gate": gate,
            "gate_status": gate_status,
            "reason": (
                f"Gate {gate} status is '{gate_status}', not 'PASS'. "
                f"Step {step_num} task must remain in_progress until {gate} passes."
            ),
        }


def action_sync(master_status: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate full synchronization instructions for all master tasks.

    Compares expected state (derived from master-status.json gates/results)
    with the assumption that tasks may be stale. Outputs exact TaskUpdate
    calls for any tasks that should be completed.

    This is called by the PostToolUse hook (check_task_completion.py)
    after the master orchestrator agent returns.
    """
    overall_status = master_status.get("status")
    task_mapping = master_status.get("master_task_mapping", {})
    updates = []

    for step_num in sorted(MASTER_STEPS.keys()):
        step = MASTER_STEPS[step_num]
        expected = _determine_expected_status(master_status, step_num, step)
        task_id = task_mapping.get(step["key"])

        entry = {
            "step_num": step_num,
            "task_key": step["key"],
            "name": step["subject"],
            "expected_status": expected,
            "task_id": task_id,
        }

        # Only include tasks that should be completed
        # (we can't know current task state from Python,
        # so we output all that SHOULD be completed)
        if expected == "completed" and task_id:
            entry["instruction"] = (
                f"TaskUpdate(taskId='{task_id}', status='completed')"
            )

        updates.append(entry)

    # Count tasks that should be completed
    completable = [u for u in updates if u["expected_status"] == "completed" and u.get("task_id")]

    return {
        "action": "SYNC",
        "overall_status": overall_status,
        "total_steps": len(MASTER_STEPS),
        "completable_count": len(completable),
        "updates": updates,
        "instruction": (
            "For each update with expected_status='completed', "
            "execute the TaskUpdate instruction. Skip tasks without task_id."
        ),
    }


def action_wf_skip(master_status: Dict[str, Any], step_num: int) -> Dict[str, Any]:
    """
    Generate task update instructions for a skipped workflow (degraded mode).

    When a WF fails and the user chooses to skip, the corresponding step task
    should be marked completed with metadata indicating it was skipped.
    """
    if step_num not in MASTER_STEPS:
        return {
            "action": "ERROR",
            "reason": f"Invalid step number: {step_num}. Valid range: 0-6.",
        }

    step = MASTER_STEPS[step_num]
    task_key = step["key"]
    task_id = master_status.get("master_task_mapping", {}).get(task_key)
    wf_key = step.get("wf_key")

    return {
        "action": "SKIP_WF",
        "step_num": step_num,
        "task_key": task_key,
        "task_id": task_id,
        "wf_key": wf_key,
        "instruction": (
            f"TaskUpdate(taskId='{task_id}', status='completed', "
            f"metadata={{\"skipped\": true, \"reason\": \"user_choice\", \"wf\": \"{wf_key}\"}})"
            if task_id else
            f"TaskUpdate for {task_key} — resolve task_id from master_task_mapping, "
            f"set status='completed' with metadata={{skipped: true}}"
        ),
    }


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _determine_expected_status(
    master_status: Dict[str, Any],
    step_num: int,
    step: Dict[str, Any],
) -> str:
    """
    Determine the expected task status for a step based on master-status.json.

    This is the core deterministic logic that eliminates LLM guesswork.
    """
    overall = master_status.get("status")

    # If overall workflow is completed, ALL steps should be completed
    if overall == "completed":
        return "completed"

    # Step 0: completed if SOT validation passed
    if step_num == 0:
        sot_status = master_status.get("sot_validation", {}).get("status")
        if sot_status == "PASS":
            return "completed"
        return "pending"

    # Steps 1-4: check corresponding WF result and gate
    wf_key = step.get("wf_key")
    if wf_key:
        wf_result = master_status.get("workflow_results", {}).get(wf_key, {})
        wf_status = wf_result.get("status")

        if wf_status == "completed":
            return "completed"
        elif wf_status == "skipped":
            return "completed"  # skipped WFs are marked completed with metadata
        elif wf_status in ("running", "in_progress"):
            return "in_progress"
        else:
            return "pending"

    # Step 5: check M4 gate (NOT M3)
    if step_num == 5:
        gate = step.get("gate")  # "M4"
        if gate:
            gate_result = master_status.get("master_gates", {}).get(gate, {}).get("status")
            if gate_result == "PASS":
                return "completed"

        # Check if integration is running
        int_status = master_status.get("integration_result", {}).get("status")
        if int_status in ("running", "in_progress"):
            return "in_progress"
        elif int_status == "completed":
            # Integration completed but M4 may not have passed yet
            # (remediation could be in progress)
            return "in_progress"

        return "pending"

    # Step 6: only completed when overall status is completed
    if step_num == 6:
        return "pending"

    return "pending"


def _read_status_file(path: str) -> Dict[str, Any]:
    """Read and parse master-status.json."""
    status_path = Path(path)

    if not status_path.exists():
        return {}

    try:
        with open(status_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(json.dumps({
            "action": "ERROR",
            "reason": f"Failed to read status file: {e}",
        }), file=sys.stdout)
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Master Task Manager — Deterministic Task Decision Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["init", "step-complete", "sync", "wf-skip"],
        help="Action to perform",
    )
    parser.add_argument(
        "--status-file",
        required=True,
        help="Path to master-status-{date}.json",
    )
    parser.add_argument(
        "--step",
        type=int,
        choices=range(0, 7),
        help="Step number (required for step-complete and wf-skip)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Validate step argument for actions that require it
    if args.action in ("step-complete", "wf-skip") and args.step is None:
        parser.error(f"--step is required for --action {args.action}")

    # Read master-status.json
    master_status = _read_status_file(args.status_file)

    # Dispatch action
    if args.action == "init":
        result = action_init(master_status)
    elif args.action == "step-complete":
        result = action_step_complete(master_status, args.step)
    elif args.action == "sync":
        result = action_sync(master_status)
    elif args.action == "wf-skip":
        result = action_wf_skip(master_status, args.step)
    else:
        result = {"action": "ERROR", "reason": f"Unknown action: {args.action}"}

    # Add metadata
    result["_meta"] = {
        "generator": GENERATOR_ID,
        "version": VERSION,
        "status_file": args.status_file,
    }

    # Output JSON to stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Exit code
    if result.get("action") == "ERROR":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
