#!/usr/bin/env python3
"""
Incremental Work Logger for Claude Code
Updates context file with recent tool usage and activities.
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

def get_latest_context_file():
    """Get the path to the latest context file"""
    project_root = get_project_root()
    context_file = Path(project_root) / '.claude' / 'context-backups' / 'latest-context.md'
    return context_file

def get_work_log_file():
    """Get the incremental work log file"""
    project_root = get_project_root()
    log_file = Path(project_root) / '.claude' / 'context-backups' / 'work-log.jsonl'
    return log_file

def log_activity():
    """Log the current tool activity"""
    try:
        # Read hook input
        hook_data = json.load(sys.stdin) if not sys.stdin.isatty() else {}

        # Extract relevant information
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
            f.write(json.dumps(entry) + '\n')

        # Keep log size manageable (last 100 entries)
        cleanup_work_log(log_file)

        return 0

    except Exception as e:
        # Don't fail - this is a non-critical logging operation
        print(f"Warning: Could not log activity: {e}", file=sys.stderr)
        return 0

def summarize_activity(tool_name, tool_input):
    """Create a human-readable activity summary"""
    if tool_name == 'Edit':
        file_path = tool_input.get('file_path', '')
        return f"Edited {os.path.basename(file_path)}"
    elif tool_name == 'Write':
        file_path = tool_input.get('file_path', '')
        return f"Wrote {os.path.basename(file_path)}"
    elif tool_name == 'Bash':
        command = tool_input.get('command', '')[:50]
        return f"Ran: {command}"
    elif tool_name == 'Task':
        desc = tool_input.get('description', '')[:50]
        return f"Task: {desc}"
    else:
        return f"Used {tool_name}"

def cleanup_work_log(log_file):
    """Keep only the last 100 log entries"""
    try:
        if not log_file.exists():
            return

        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if len(lines) > 100:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.writelines(lines[-100:])

    except Exception:
        pass  # Ignore cleanup errors

if __name__ == '__main__':
    sys.exit(log_activity())
