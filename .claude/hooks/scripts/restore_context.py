#!/usr/bin/env python3
"""
Context Restoration System v2.0 for Claude Code
Outputs key state info directly on session start, then guides Claude to read full context.

Key changes from v1.0:
  - Reads task-state.json and outputs task progress directly
  - Reads master-status.json (via SOT path) and outputs workflow state directly
  - Shows concrete data, not just "please read file" message
  - Checks latest-context.md has actual content (not empty skeleton)
"""
import json
import sys
import os
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())


def get_latest_context_file():
    """Get the path to the latest context file."""
    project_root = get_project_root()
    return Path(project_root) / '.claude' / 'context-backups' / 'latest-context.md'


def restore_context():
    """Output key state info and guide Claude to read full context."""
    try:
        project_root = Path(get_project_root())
        context_file = get_latest_context_file()

        if not context_file.exists():
            return 0

        # Check if context file has real content (not empty skeleton)
        file_size = context_file.stat().st_size
        has_content = file_size > 500  # Rich content is typically > 1KB

        print("\n" + "=" * 60)
        if has_content:
            print("CONTEXT RESTORATION REQUIRED")
        else:
            print("WARNING: Context file exists but has minimal content.")
            print("Previous context may not have been captured properly.")
        print("=" * 60)

        # ── Task State (most critical for implementation continuity) ──
        task_state_file = project_root / '.claude' / 'context-backups' / 'task-state.json'
        if task_state_file.exists():
            try:
                state = json.loads(task_state_file.read_text(encoding='utf-8'))

                if state.get('session_goal'):
                    print(f"\nCurrent Goal: {state['session_goal']}")

                tasks = state.get('tasks', [])
                if tasks:
                    completed = [t for t in tasks if t.get('status') == 'completed']
                    in_progress = [t for t in tasks if t.get('status') == 'in_progress']
                    pending = [t for t in tasks if t.get('status') == 'pending']
                    print(f"Task Progress: {len(completed)} done / {len(in_progress)} active / {len(pending)} pending")

                    if in_progress:
                        print(f"Active Task: {in_progress[0].get('subject', '')}")
                    elif pending:
                        print(f"Next Task: {pending[0].get('subject', '')}")

                if state.get('last_updated'):
                    print(f"Last Updated: {state['last_updated']}")

            except Exception:
                pass

        # ── Workflow State (from SOT → master-status.json) ──
        try:
            registry_path = project_root / 'env-scanning' / 'config' / 'workflow-registry.yaml'
            if registry_path.exists():
                master_path = _find_master_status(project_root, registry_path)
                if master_path and master_path.exists():
                    ms = json.loads(master_path.read_text(encoding='utf-8'))
                    status = ms.get('status', 'unknown')
                    master_id = ms.get('master_id', '')
                    print(f"\nWorkflow: {status} ({master_id})")

                    wf_results = ms.get('workflow_results', {})
                    for wf_key, wf_data in wf_results.items():
                        signals = wf_data.get('signals_collected', wf_data.get('signal_count', '?'))
                        print(f"  {wf_key}: {wf_data.get('status', '?')} ({signals} signals)")
        except Exception:
            pass

        # ── Guide to full context ──
        print(f"\nAction Required:")
        print(f"Please read the file: {context_file}")
        print("\nThis file contains:")
        print("  - Implementation state (goals, tasks, progress)")
        print("  - Workflow execution state (SOT-bound)")
        print("  - Git repository status")
        print("  - Recent tool activity log")
        print("\nThis ensures workflow continuity after context compression.")
        print("=" * 60 + "\n")

        return 0

    except Exception as e:
        print(f"Warning: Could not restore context: {e}", file=sys.stderr)
        return 0


def _find_master_status(project_root, registry_path):
    """Find master-status.json path from SOT registry."""
    try:
        # Try PyYAML
        try:
            import yaml
            with open(registry_path, 'r', encoding='utf-8') as f:
                reg = yaml.safe_load(f)
            output_root = reg.get('integration', {}).get('output_root', '')
            if output_root:
                return project_root / output_root / 'logs' / 'master-status.json'
        except ImportError:
            pass

        # Fallback: simple text search for output_root in integration section
        content = registry_path.read_text(encoding='utf-8')
        in_integration = False
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('integration:'):
                in_integration = True
            elif not line.startswith(' ') and not line.startswith('\t') and ':' in stripped and not stripped.startswith('#'):
                if in_integration:
                    in_integration = False
            if in_integration and stripped.startswith('output_root:'):
                val = stripped.split(':', 1)[1].strip().strip('"').strip("'")
                return project_root / val / 'logs' / 'master-status.json'
    except Exception:
        pass

    return None


if __name__ == '__main__':
    sys.exit(restore_context())
