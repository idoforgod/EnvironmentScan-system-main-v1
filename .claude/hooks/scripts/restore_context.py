#!/usr/bin/env python3
"""
Context Restoration System for Claude Code
Auto-loads previous context when session starts/resumes after compression.
"""
import json
import sys
import os
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

def get_latest_context_file():
    """Get the path to the latest context file"""
    project_root = get_project_root()
    context_file = Path(project_root) / '.claude' / 'context-backups' / 'latest-context.md'
    return context_file

def restore_context():
    """Print context restoration message for Claude to read"""
    try:
        context_file = get_latest_context_file()

        if not context_file.exists():
            # No context file exists yet - this is normal for first run
            return 0

        # Print message that will appear in Claude's session
        print("\n" + "="*60)
        print("🔄 CONTEXT RESTORATION REQUIRED")
        print("="*60)
        print(f"\nPrevious context detected at: {context_file}")
        print("\n📋 Action Required:")
        print(f"Please read the file: {context_file}")
        print("\nThis file contains:")
        print("  • Recent work summary")
        print("  • Active tasks and their status")
        print("  • Key decisions and context")
        print("  • Modified files list")
        print("\nThis ensures workflow continuity after context compression.")
        print("="*60 + "\n")

        return 0

    except Exception as e:
        print(f"Warning: Could not restore context: {e}", file=sys.stderr)
        return 0  # Don't fail the hook

if __name__ == '__main__':
    sys.exit(restore_context())
