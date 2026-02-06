#!/usr/bin/env python3
"""
Incremental Work Logger v2.0 for Claude Code
Logs tool usage and maintains task-state.json for context preservation.

Key changes from v1.0:
  - Activity description expanded from 50 to 200 chars
  - Edit/Write records relative path (not just basename)
  - TaskCreate/TaskUpdate detection → updates task-state.json
  - Increased log retention from 100 to 200 entries
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())


def get_work_log_file():
    """Get the incremental work log file."""
    project_root = get_project_root()
    log_dir = Path(project_root) / '.claude' / 'context-backups'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / 'work-log.jsonl'


def get_task_state_file():
    """Get the task state file."""
    project_root = get_project_root()
    return Path(project_root) / '.claude' / 'context-backups' / 'task-state.json'


def log_activity():
    """Log the current tool activity."""
    try:
        # Read hook input from stdin (PostToolUse provides tool_name and tool_input)
        hook_data = json.load(sys.stdin) if not sys.stdin.isatty() else {}

        tool_name = hook_data.get('tool_name', 'unknown')
        tool_input = hook_data.get('tool_input', {})

        # Create log entry
        entry = {
            'timestamp': datetime.now().isoformat(),
            'tool': tool_name,
            'activity': summarize_activity(tool_name, tool_input)
        }

        # Append to work log
        log_file = get_work_log_file()
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        # Update task-state.json if this is a task management operation
        update_task_state(tool_name, tool_input)

        # Keep log size manageable
        cleanup_work_log(log_file)

        return 0

    except Exception as e:
        # Non-critical — never fail the hook
        print(f"Warning: Could not log activity: {e}", file=sys.stderr)
        return 0


def summarize_activity(tool_name, tool_input):
    """Create a human-readable activity summary (up to 200 chars)."""
    project_root = get_project_root()

    if tool_name == 'Edit':
        file_path = tool_input.get('file_path', '')
        try:
            rel_path = os.path.relpath(file_path, project_root)
        except ValueError:
            rel_path = os.path.basename(file_path)
        return f"Edited {rel_path}"

    elif tool_name == 'Write':
        file_path = tool_input.get('file_path', '')
        try:
            rel_path = os.path.relpath(file_path, project_root)
        except ValueError:
            rel_path = os.path.basename(file_path)
        return f"Wrote {rel_path}"

    elif tool_name == 'Bash':
        command = tool_input.get('command', '')[:200]
        return f"Ran: {command}"

    elif tool_name == 'Task':
        desc = tool_input.get('description', '')[:100]
        prompt_snippet = tool_input.get('prompt', '')[:100]
        if prompt_snippet:
            return f"Task: {desc} | {prompt_snippet}"
        return f"Task: {desc}"

    elif tool_name == 'TaskCreate':
        subject = tool_input.get('subject', '')[:120]
        return f"TaskCreate: {subject}"

    elif tool_name == 'TaskUpdate':
        task_id = tool_input.get('taskId', '')
        status = tool_input.get('status', '')
        subject = tool_input.get('subject', '')
        return f"TaskUpdate: #{task_id} → {status}" + (f" ({subject})" if subject else "")

    else:
        return f"Used {tool_name}"


def update_task_state(tool_name, tool_input):
    """Update task-state.json when TaskCreate/TaskUpdate is detected.

    This captures the semantic context of what the user/Claude is working on,
    which is the most critical information for context restoration after /clear.
    """
    if tool_name not in ('TaskCreate', 'TaskUpdate'):
        return

    try:
        task_state_file = get_task_state_file()

        # Load existing state
        state = {}
        if task_state_file.exists():
            try:
                state = json.loads(task_state_file.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError):
                state = {}

        state['last_updated'] = datetime.now().isoformat()

        if tool_name == 'TaskCreate':
            subject = tool_input.get('subject', '')
            description = tool_input.get('description', '')[:500]
            active_form = tool_input.get('activeForm', '')

            tasks = state.get('tasks', [])
            tasks.append({
                'subject': subject,
                'description': description,
                'activeForm': active_form,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            })
            state['tasks'] = tasks

            # Set session_goal from the first task if not set
            if not state.get('session_goal') and subject:
                state['session_goal'] = subject

        elif tool_name == 'TaskUpdate':
            task_id = tool_input.get('taskId', '')
            new_status = tool_input.get('status', '')
            new_subject = tool_input.get('subject', '')

            # Record the update
            updates = state.get('task_updates', [])
            update_entry = {
                'task_id': task_id,
                'timestamp': datetime.now().isoformat()
            }
            if new_status:
                update_entry['new_status'] = new_status
            if new_subject:
                update_entry['new_subject'] = new_subject
            updates.append(update_entry)
            # Keep last 50 updates
            state['task_updates'] = updates[-50:]

            # Try to update the matching task in our tasks list
            if new_status and task_id:
                tasks = state.get('tasks', [])
                # task_id is a string number like "1", "2", etc.
                # Match by index (task_id "1" → index 0)
                try:
                    idx = int(task_id) - 1
                    if 0 <= idx < len(tasks):
                        tasks[idx]['status'] = new_status
                        tasks[idx]['updated_at'] = datetime.now().isoformat()
                        if new_subject:
                            tasks[idx]['subject'] = new_subject
                except (ValueError, IndexError):
                    pass

        # Write updated state
        task_state_file.parent.mkdir(parents=True, exist_ok=True)
        task_state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    except Exception:
        pass  # Non-critical — never fail the hook


def cleanup_work_log(log_file):
    """Keep only the last 200 log entries."""
    try:
        if not log_file.exists():
            return

        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if len(lines) > 200:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.writelines(lines[-200:])

    except Exception:
        pass


if __name__ == '__main__':
    sys.exit(log_activity())
