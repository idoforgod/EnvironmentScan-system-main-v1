#!/usr/bin/env python3
"""
PostToolUse hook for Agent tool: Task Completion Guard (v2.0.0).

When an Agent tool call completes, this script checks master-status.json
to determine if the workflow has finished. If completed, it runs
master_task_manager.py --action sync to compute EXACT TaskUpdate instructions.

This replaces LLM memory with a deterministic trigger:
  "계산은 Python이, 판단은 LLM이" — the CHECK is Python, the UPDATE is LLM.

v2.0.0 (2026-03-15): Enhanced with master_task_manager.py integration.
  - Calls --action sync for specific, deterministic TaskUpdate instructions
  - Falls back to generic message if master_task_manager.py unavailable
  - Reads task_management.master_script path from SOT (workflow-registry.yaml)
"""
import json
import subprocess
import sys
import os
from pathlib import Path


def get_project_root():
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())


def find_master_status_file(project_root):
    """Find the most recent master-status JSON file."""
    logs_dir = Path(project_root) / 'env-scanning' / 'integrated' / 'logs'

    # Try master-status.json (legacy/symlink)
    legacy = logs_dir / 'master-status.json'
    if legacy.exists():
        return legacy

    # Try dated files, pick most recent
    dated_files = sorted(logs_dir.glob('master-status-*.json'), reverse=True)
    if dated_files:
        return dated_files[0]

    return None


def read_master_status(status_file):
    """Read and parse master-status JSON."""
    try:
        with open(status_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _read_sot_task_script(sot_path):
    """Extract task_management.master_script from SOT YAML.

    Strategy: PyYAML (precise) → regex fallback (best-effort).
    """
    try:
        import yaml
        with open(sot_path, 'r') as f:
            registry = yaml.safe_load(f)
        return registry.get('system', {}).get('task_management', {}).get('master_script')
    except Exception:
        pass

    # Regex fallback — handles simple `key: value` lines only
    try:
        import re
        text = Path(sot_path).read_text()
        match = re.search(r'master_script:\s*["\']?([^"\'#\n]+)', text)
        if match:
            return match.group(1).strip()
    except Exception:
        pass

    return None


def find_task_manager_script(project_root):
    """Find master_task_manager.py, preferring SOT-declared path."""
    sot_path = Path(project_root) / 'env-scanning' / 'config' / 'workflow-registry.yaml'
    if sot_path.exists():
        script_rel = _read_sot_task_script(sot_path)
        if script_rel:
            script_path = Path(project_root) / script_rel
            if script_path.exists():
                return script_path

    # Fallback to known path
    fallback = Path(project_root) / 'env-scanning' / 'core' / 'master_task_manager.py'
    if fallback.exists():
        return fallback

    return None


def run_sync(task_manager_script, status_file):
    """Run master_task_manager.py --action sync and return parsed result."""
    try:
        result = subprocess.run(
            [sys.executable, str(task_manager_script),
             '--action', 'sync',
             '--status-file', str(status_file)],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        pass
    return None


def format_sync_instructions(sync_result):
    """Format sync result into actionable LLM instructions."""
    if not sync_result or sync_result.get('action') != 'SYNC':
        return None

    updates = sync_result.get('updates', [])
    completable = [u for u in updates
                   if u.get('expected_status') == 'completed' and u.get('task_id')]

    if not completable:
        return None

    lines = [
        "TASK COMPLETION GUARD: master-status.json shows workflow completed.",
        f"Python computed {len(completable)} task(s) that should be marked completed:",
        ""
    ]
    for u in completable:
        lines.append(
            f"  TaskUpdate(taskId='{u['task_id']}', status='completed')  "
            f"# {u['name']}"
        )
    lines.append("")
    lines.append("Execute these TaskUpdate calls now (non-critical — do not halt on failure).")

    return "\n".join(lines)


def main():
    try:
        hook_data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (json.JSONDecodeError, EOFError):
        hook_data = {}

    # Only act on Agent tool completions
    tool_name = hook_data.get('tool_name', '')
    if tool_name != 'Agent':
        return 0

    # Check if the agent was scan/orchestrator related
    tool_input = hook_data.get('tool_input', {})
    agent_type = tool_input.get('subagent_type', '')
    description = tool_input.get('description', '').lower()
    prompt = tool_input.get('prompt', '').lower()

    scan_keywords = [
        'orchestrator', 'env-scan', 'env scan', 'autopilot',
        'quadruple', 'environmental scanning', 'workflow',
        'wf1', 'wf2', 'wf3', 'wf4', 'integration',
    ]

    is_scan_agent = (
        'orchestrator' in agent_type
        or any(kw in description for kw in scan_keywords)
        or any(kw in prompt[:200] for kw in scan_keywords)
    )

    if not is_scan_agent:
        return 0

    project_root = get_project_root()

    # Find and read master-status
    status_file = find_master_status_file(project_root)
    if not status_file:
        return 0

    data = read_master_status(status_file)
    if not data:
        return 0

    status = data.get('status', data.get('overall_status'))
    if status != 'completed':
        return 0

    # Try enhanced path: master_task_manager.py --action sync
    try:
        task_manager = find_task_manager_script(project_root)
        if task_manager:
            sync_result = run_sync(task_manager, status_file)
            instructions = format_sync_instructions(sync_result)
            if instructions:
                print(instructions)
                return 0
    except Exception:
        pass  # Fall through to generic message

    # Fallback: generic message (L2 defense — still better than nothing)
    print(
        "TASK COMPLETION GUARD: master-status.json shows 'completed'. "
        "You MUST now update ALL in_progress tasks to 'completed' using TaskUpdate "
        "BEFORE responding to the user. This is a mandatory post-workflow action."
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
