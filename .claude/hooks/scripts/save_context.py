#!/usr/bin/env python3
"""
Context Preservation System for Claude Code
Saves conversation context and work history to prevent memory loss during compression.
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

def get_context_dir():
    """Get the context backups directory"""
    project_root = get_project_root()
    context_dir = Path(project_root) / '.claude' / 'context-backups'
    context_dir.mkdir(parents=True, exist_ok=True)
    return context_dir

def get_latest_context_file():
    """Get the path to the latest context file"""
    context_dir = get_context_dir()
    return context_dir / 'latest-context.md'

def get_timestamped_backup():
    """Get a timestamped backup file path"""
    context_dir = get_context_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return context_dir / f'context-backup-{timestamp}.md'

def create_context_snapshot():
    """Create a context snapshot file"""
    try:
        # Read hook input
        hook_data = json.load(sys.stdin) if not sys.stdin.isatty() else {}

        project_root = get_project_root()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Build context summary
        context_content = f"""# Claude Code Context Backup
**Project**: {project_root}
**Timestamp**: {timestamp}
**Event**: {hook_data.get('event', 'manual-save')}

## ⚠️ CONTEXT PRESERVATION NOTICE
This file was auto-generated to prevent context loss during token compression.
When Claude Code resumes, it should read this file to restore working memory.

## Current Working State

### Active Tasks
<!-- List current tasks, their status, and next steps -->
- Task tracking should be added here during workflow

### Recent Work Summary
<!-- Auto-populated by Stop hook with recent activities -->

### Key Decisions & Context
<!-- Important decisions, architectural choices, and context -->

### Files Modified Recently
"""

        # Add recently modified files
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                context_content += "\n```\n"
                context_content += result.stdout.strip()
                context_content += "\n```\n"
            else:
                context_content += "\n(No modified files detected)\n"
        except Exception as e:
            context_content += f"\n(Could not detect modified files: {e})\n"

        # Add project structure snapshot
        context_content += """
### Project Structure Context
"""

        # Save to latest context file
        latest_file = get_latest_context_file()
        with open(latest_file, 'w', encoding='utf-8') as f:
            f.write(context_content)

        # Also save timestamped backup
        backup_file = get_timestamped_backup()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(context_content)

        # Keep only last 10 backups
        cleanup_old_backups()

        print(f"✓ Context saved to {latest_file}")
        print(f"✓ Backup created: {backup_file.name}")

        return 0

    except Exception as e:
        print(f"❌ Error saving context: {e}", file=sys.stderr)
        return 1

def cleanup_old_backups():
    """Keep only the last 10 backup files"""
    try:
        context_dir = get_context_dir()
        backups = sorted(
            [f for f in context_dir.glob('context-backup-*.md')],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        # Remove backups beyond the 10 most recent
        for old_backup in backups[10:]:
            old_backup.unlink()

    except Exception as e:
        print(f"Warning: Could not cleanup old backups: {e}", file=sys.stderr)

if __name__ == '__main__':
    sys.exit(create_context_snapshot())
