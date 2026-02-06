#!/usr/bin/env python3
"""
Context Preservation System v2.0 for Claude Code
Saves context before token compression (PreCompact hook).

Key changes from v1.0:
  - No longer generates empty skeleton that overwrites rich content
  - Copies existing latest-context.md to timestamped backup first (preserve)
  - Then calls generate_context_summary.py to refresh with latest state
  - Fixed variable name bug in cleanup_old_backups()
"""
import json
import shutil
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())


def get_context_dir():
    """Get the context backups directory."""
    project_root = get_project_root()
    context_dir = Path(project_root) / '.claude' / 'context-backups'
    context_dir.mkdir(parents=True, exist_ok=True)
    return context_dir


def get_latest_context_file():
    """Get the path to the latest context file."""
    return get_context_dir() / 'latest-context.md'


def get_timestamped_backup():
    """Get a timestamped backup file path."""
    context_dir = get_context_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return context_dir / f'context-backup-{timestamp}.md'


def create_context_snapshot():
    """Create a context snapshot before token compression.

    Strategy:
      1. Copy existing latest-context.md → timestamped backup (preserve rich content)
      2. Call generate_context_summary.py to refresh latest-context.md with current state
      3. Clean up old backups (keep last 10)
    """
    try:
        # Read hook input (PreCompact provides event data via stdin)
        hook_data = json.load(sys.stdin) if not sys.stdin.isatty() else {}

        latest_file = get_latest_context_file()

        # Step 1: Preserve existing rich content as timestamped backup
        if latest_file.exists() and latest_file.stat().st_size > 100:
            backup_file = get_timestamped_backup()
            shutil.copy2(latest_file, backup_file)
            print(f"✓ Backup created: {backup_file.name}")

        # Step 2: Refresh latest-context.md with current state
        # Call generate_context_summary.py which reads SOT + workflow state
        generator_script = Path(__file__).parent / 'generate_context_summary.py'
        if generator_script.exists():
            result = subprocess.run(
                [sys.executable, str(generator_script)],
                cwd=get_project_root(),
                capture_output=True,
                text=True,
                timeout=15,
                env={**os.environ, 'CLAUDE_PROJECT_DIR': get_project_root()}
            )
            if result.returncode == 0:
                print(f"✓ Context refreshed: {latest_file}")
            else:
                # If generator fails, latest-context.md still has previous content
                print(f"Warning: Context refresh failed, backup preserved", file=sys.stderr)
        else:
            print(f"Warning: generate_context_summary.py not found", file=sys.stderr)

        # Step 3: Clean up old backups
        cleanup_old_backups()

        return 0

    except Exception as e:
        print(f"Error saving context: {e}", file=sys.stderr)
        return 1


def cleanup_old_backups():
    """Keep only the last 10 backup files."""
    try:
        context_dir = get_context_dir()
        backups = sorted(
            [f for f in context_dir.glob('context-backup-*.md')],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        for old_backup in backups[10:]:
            old_backup.unlink()

    except Exception as e:
        print(f"Warning: Could not cleanup old backups: {e}", file=sys.stderr)


if __name__ == '__main__':
    sys.exit(create_context_snapshot())
