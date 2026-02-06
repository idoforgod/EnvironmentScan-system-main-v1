#!/usr/bin/env python3
"""
Context Summary Generator v2.0 — SOT-Bound
Creates a detailed summary of current project state for context preservation.

Key changes from v1.0:
  - Reads workflow-registry.yaml (SOT) to discover state file paths dynamically
  - Reads master-status.json and workflow-status.json (READ-ONLY)
  - Reads task-state.json for implementation context
  - Eliminates manual-update placeholder sections
  - All workflow paths resolved from SOT, never hardcoded
"""
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())


# ── SOT Binding ────────────────────────────────────────────

def load_sot_paths():
    """Read workflow-registry.yaml (SOT) and extract state file paths.

    Returns dict of resolved absolute paths, or None if SOT not found.
    All workflow state file locations come from SOT — never hardcoded.
    """
    try:
        project_root = Path(get_project_root())
        registry_path = project_root / 'env-scanning' / 'config' / 'workflow-registry.yaml'

        if not registry_path.exists():
            return None

        # Use simple YAML parsing to avoid external dependency
        registry = _parse_yaml_simple(registry_path)
        if not registry:
            return None

        # Extract paths from SOT
        int_output_root = registry.get('integration', {}).get('output_root', '')
        wf1_data_root = registry.get('workflows', {}).get('wf1-general', {}).get('data_root', '')
        wf2_data_root = registry.get('workflows', {}).get('wf2-arxiv', {}).get('data_root', '')

        paths = {}

        if int_output_root:
            int_root = project_root / int_output_root
            paths['master_status'] = int_root / 'logs' / 'master-status.json'
            paths['int_output_root'] = int_root

        if wf1_data_root:
            wf1_root = project_root / wf1_data_root
            paths['wf1_data_root'] = wf1_root
            paths['wf1_signals_db'] = wf1_root / 'signals' / 'database.json'

        if wf2_data_root:
            wf2_root = project_root / wf2_data_root
            paths['wf2_data_root'] = wf2_root
            paths['wf2_signals_db'] = wf2_root / 'signals' / 'database.json'

        # Global workflow status (outside individual workflow data roots)
        paths['workflow_status'] = project_root / 'env-scanning' / 'logs' / 'workflow-status.json'

        # Registry metadata
        paths['registry_version'] = registry.get('system', {}).get('version', 'unknown')

        return paths

    except Exception:
        return None


def _parse_yaml_simple(yaml_path):
    """Parse YAML file. Try PyYAML first, fall back to basic parser."""
    try:
        import yaml
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        pass

    # Fallback: extract key fields with basic parsing
    try:
        content = yaml_path.read_text(encoding='utf-8')
        result = {'integration': {}, 'workflows': {'wf1-general': {}, 'wf2-arxiv': {}}, 'system': {}}

        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('output_root:') and 'integration' in content[:content.index(line)].split('workflows')[0]:
                val = stripped.split(':', 1)[1].strip().strip('"').strip("'")
                result['integration']['output_root'] = val
            elif stripped.startswith('data_root:') and 'wf1-general' in content[:content.index(line)]:
                val = stripped.split(':', 1)[1].strip().strip('"').strip("'")
                result['workflows']['wf1-general']['data_root'] = val
            elif stripped.startswith('data_root:') and 'wf2-arxiv' in content[:content.index(line)]:
                val = stripped.split(':', 1)[1].strip().strip('"').strip("'")
                result['workflows']['wf2-arxiv']['data_root'] = val
            elif stripped.startswith('version:') and 'system' in content[:content.index(line)][:200]:
                val = stripped.split(':', 1)[1].strip().strip('"').strip("'")
                result['system']['version'] = val

        return result
    except Exception:
        return None


# ── Workflow State Readers (READ-ONLY) ──────────────────────

def get_workflow_state(sot_paths):
    """Read master-status.json and workflow-status.json. READ-ONLY."""
    state = {}

    if not sot_paths:
        return state

    # Master status
    master_path = sot_paths.get('master_status')
    if master_path and master_path.exists():
        try:
            ms = json.loads(master_path.read_text(encoding='utf-8'))
            state['master'] = {
                'master_id': ms.get('master_id', ''),
                'status': ms.get('status', ''),
                'started_at': ms.get('started_at', ''),
                'completed_at': ms.get('completed_at', ''),
                'registry_version': ms.get('registry_version', ''),
                'sot_validation': ms.get('sot_validation', {}).get('status', ''),
            }

            # WF results
            wf_results = ms.get('workflow_results', {})
            for wf_key, wf_data in wf_results.items():
                state[f'wf_{wf_key}'] = {
                    'status': wf_data.get('status', ''),
                    'signals': wf_data.get('signals_collected', wf_data.get('signal_count', '')),
                    'report_path': wf_data.get('report_path', ''),
                    'validation': wf_data.get('validation', ''),
                }

            # Integration result
            int_result = ms.get('integration_result', {})
            if int_result:
                state['integration'] = {
                    'status': int_result.get('status', ''),
                    'total_signals': int_result.get('total_signals', ''),
                    'report_path': int_result.get('report_path', ''),
                }

            # Human decisions summary
            decisions = ms.get('human_decisions', {})
            state['approvals'] = {k: v.get('decision', '') for k, v in decisions.items()}

            # Master gates
            gates = ms.get('master_gates', {})
            state['master_gates'] = {k: v.get('status', '') for k, v in gates.items()}

        except Exception:
            pass

    # Workflow status
    wf_status_path = sot_paths.get('workflow_status')
    if wf_status_path and wf_status_path.exists():
        try:
            ws = json.loads(wf_status_path.read_text(encoding='utf-8'))
            state['workflow_progress'] = {
                'workflow_id': ws.get('workflow_id', ''),
                'status': ws.get('status', ''),
                'current_phase': ws.get('current_phase', ''),
                'current_step': ws.get('current_step', ''),
                'completed_steps': ws.get('completed_steps', []),
                'blocked_on': ws.get('blocked_on'),
                'errors': ws.get('errors', []),
                'last_updated': ws.get('last_updated', ''),
            }
        except Exception:
            pass

    return state


def get_task_state():
    """Read task-state.json for implementation context."""
    try:
        project_root = Path(get_project_root())
        task_file = project_root / '.claude' / 'context-backups' / 'task-state.json'

        if not task_file.exists():
            return None

        return json.loads(task_file.read_text(encoding='utf-8'))
    except Exception:
        return None


# ── Git Status ──────────────────────────────────────────────

def get_git_status():
    """Get current git status."""
    try:
        project_root = get_project_root()

        branch = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=project_root, capture_output=True, text=True, timeout=5
        ).stdout.strip()

        modified = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=project_root, capture_output=True, text=True, timeout=5
        ).stdout

        recent_commits = subprocess.run(
            ['git', 'log', '--oneline', '-5'],
            cwd=project_root, capture_output=True, text=True, timeout=5
        ).stdout

        return {
            'branch': branch,
            'modified_files': modified,
            'recent_commits': recent_commits
        }
    except Exception as e:
        return {'error': str(e)}


# ── Activity Log ────────────────────────────────────────────

def get_recent_activities():
    """Read recent work log entries."""
    try:
        project_root = get_project_root()
        log_file = Path(project_root) / '.claude' / 'context-backups' / 'work-log.jsonl'

        if not log_file.exists():
            return []

        activities = []
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-20:]:
                try:
                    activities.append(json.loads(line))
                except Exception:
                    pass

        return activities
    except Exception:
        return []


# ── Summary Generator ───────────────────────────────────────

def generate_summary():
    """Generate comprehensive context summary with SOT-bound workflow state."""
    project_root = get_project_root()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Load SOT paths and workflow state
    sot_paths = load_sot_paths()
    wf_state = get_workflow_state(sot_paths)
    task_state = get_task_state()

    summary = f"""# Claude Code Context Summary
**Project**: {project_root}
**Generated**: {timestamp}
**Version**: 2.0.0 (SOT-bound)

---
"""

    # ── Section 1: Implementation State (task-state.json) ──
    summary += "\n## Implementation State\n\n"
    if task_state:
        if task_state.get('session_goal'):
            summary += f"**Current Goal**: {task_state['session_goal']}\n\n"

        tasks = task_state.get('tasks', [])
        if tasks:
            completed = [t for t in tasks if t.get('status') == 'completed']
            in_progress = [t for t in tasks if t.get('status') == 'in_progress']
            pending = [t for t in tasks if t.get('status') == 'pending']

            summary += f"**Progress**: {len(completed)} completed / {len(in_progress)} in progress / {len(pending)} pending\n\n"

            if completed:
                summary += "**Completed**:\n"
                for t in completed:
                    summary += f"- [x] {t.get('subject', t.get('description', '')[:80])}\n"
                summary += "\n"

            if in_progress:
                summary += "**In Progress**:\n"
                for t in in_progress:
                    summary += f"- [ ] {t.get('subject', t.get('description', '')[:80])}\n"
                summary += "\n"

            if pending:
                summary += "**Pending**:\n"
                for t in pending:
                    summary += f"- [ ] {t.get('subject', t.get('description', '')[:80])}\n"
                summary += "\n"

        decisions = task_state.get('key_decisions', [])
        if decisions:
            summary += "**Key Decisions**:\n"
            for d in decisions[-5:]:
                summary += f"- {d.get('decision', '')} ({d.get('reason', '')})\n"
            summary += "\n"

        next_actions = task_state.get('next_actions', [])
        if next_actions:
            summary += "**Next Actions**:\n"
            for a in next_actions:
                summary += f"- {a}\n"
            summary += "\n"

        errors = task_state.get('recent_errors', [])
        if errors:
            summary += "**Recent Errors**:\n"
            for e in errors[-3:]:
                summary += f"- {e.get('description', '')} -> {e.get('resolution', 'unresolved')}\n"
            summary += "\n"

        if task_state.get('last_updated'):
            summary += f"*Last updated: {task_state['last_updated']}*\n\n"
    else:
        summary += "(No task-state.json found — task state will be captured when TaskCreate/TaskUpdate is used)\n\n"

    # ── Section 2: Workflow Execution State (from SOT → master-status.json) ──
    summary += "---\n\n## Workflow Execution State\n\n"

    if sot_paths:
        summary += f"**SOT Version**: {sot_paths.get('registry_version', 'unknown')}\n\n"

    if wf_state.get('master'):
        ms = wf_state['master']
        summary += f"**Master**: {ms['master_id']} | Status: **{ms['status']}**\n"
        if ms.get('completed_at'):
            summary += f"**Completed**: {ms['completed_at']}\n"
        summary += f"**SOT Validation**: {ms.get('sot_validation', 'N/A')}\n\n"

        # WF results table
        summary += "| Workflow | Status | Signals | Validation |\n"
        summary += "|----------|--------|---------|------------|\n"
        for key in ['wf_wf1-general', 'wf_wf2-arxiv']:
            if key in wf_state:
                wf = wf_state[key]
                name = key.replace('wf_', '')
                summary += f"| {name} | {wf['status']} | {wf['signals']} | {wf.get('validation', 'N/A')} |\n"
        if wf_state.get('integration'):
            intg = wf_state['integration']
            summary += f"| integrated | {intg['status']} | {intg['total_signals']} | - |\n"
        summary += "\n"

        # Master gates
        gates = wf_state.get('master_gates', {})
        if gates:
            summary += "**Master Gates**: "
            summary += " | ".join([f"{k}: {v}" for k, v in gates.items()])
            summary += "\n\n"

        # Approvals
        approvals = wf_state.get('approvals', {})
        if approvals:
            summary += "**Human Approvals**: "
            summary += " | ".join([f"{k}: {v}" for k, v in approvals.items()])
            summary += "\n\n"

    elif sot_paths:
        summary += "(master-status.json not found — workflow has not been executed yet)\n\n"
    else:
        summary += "(workflow-registry.yaml not found — SOT binding unavailable)\n\n"

    # Workflow progress detail
    wp = wf_state.get('workflow_progress')
    if wp:
        summary += f"**Current Phase**: {wp.get('current_phase', 'N/A')} | "
        summary += f"**Step**: {wp.get('current_step', 'N/A')} | "
        summary += f"**Status**: {wp.get('status', 'N/A')}\n\n"

        steps = wp.get('completed_steps', [])
        if steps:
            summary += f"**Completed Steps** ({len(steps)}):\n"
            for s in steps:
                summary += f"- {s}\n"
            summary += "\n"

        if wp.get('blocked_on'):
            summary += f"**BLOCKED ON**: {wp['blocked_on']}\n\n"

        errors = wp.get('errors', [])
        if errors:
            summary += f"**Errors**: {errors}\n\n"

    # ── Section 3: Git Repository Status ──
    summary += "---\n\n## Git Repository Status\n\n"
    git_status = get_git_status()
    if 'error' not in git_status:
        summary += f"**Branch**: `{git_status['branch']}`\n\n"
        summary += "**Modified Files**:\n```\n"
        summary += git_status['modified_files'] or '(No changes)'
        summary += "\n```\n\n"
        summary += "**Recent Commits**:\n```\n"
        summary += git_status['recent_commits']
        summary += "```\n"
    else:
        summary += f"(Git status unavailable: {git_status['error']})\n"

    # ── Section 4: Recent Activities ──
    summary += "\n---\n\n## Recent Activities\n\n"
    activities = get_recent_activities()
    if activities:
        summary += "| Time | Tool | Activity |\n"
        summary += "|------|------|----------|\n"
        for act in activities[-15:]:
            try:
                time_str = datetime.fromisoformat(act['timestamp']).strftime('%m-%d %H:%M')
            except Exception:
                time_str = act.get('timestamp', '')[:16]
            activity_text = act.get('activity', '')[:120]
            summary += f"| {time_str} | {act.get('tool', '')} | {activity_text} |\n"
    else:
        summary += "(No recent activities logged)\n"

    # ── Section 5: Restoration Instructions ──
    summary += """
---

## Restoration Instructions

**For Claude Code**: When you read this file after /clear or compression:

1. **Read Implementation State** above — understand what task was in progress
2. **Read Workflow Execution State** — understand scan status
3. **Check Git Status** — understand file changes
4. **Review Recent Activities** — understand what tools were used
5. **Read task-state.json** for detailed task breakdown if available
6. **Continue from the in-progress task** — do not restart completed work

---

**Auto-generated by**: Context Preservation System v2.0.0 (SOT-bound)
"""

    return summary


if __name__ == '__main__':
    try:
        summary = generate_summary()

        # Save to context file
        project_root = get_project_root()
        context_file = Path(project_root) / '.claude' / 'context-backups' / 'latest-context.md'
        context_file.parent.mkdir(parents=True, exist_ok=True)

        with open(context_file, 'w', encoding='utf-8') as f:
            f.write(summary)

    except Exception as e:
        # Silent failure — this runs in Stop hook, must not disrupt workflow
        import sys
        print(f"Context summary error: {e}", file=sys.stderr)
