#!/usr/bin/env python3
"""
Automated Hook Setup for Context Preservation System
Helps configure Claude Code hooks in settings.json
"""
import json
import os
import sys
from pathlib import Path

def get_settings_path():
    """Get Claude Code settings file path"""
    home = Path.home()
    return home / '.claude' / 'settings.json'

def get_hook_configuration():
    """Generate hook configuration"""
    return {
        "hooks": {
            "PreCompact": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/scripts/save_context.py',
                            "description": "Save context before compression"
                        }
                    ]
                }
            ],
            "SessionStart": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/scripts/restore_context.py',
                            "description": "Alert to restore context on session start"
                        }
                    ]
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Edit|Write|Bash|Task",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/scripts/update_work_log.py',
                            "description": "Log tool activity incrementally"
                        }
                    ]
                }
            ],
            "Stop": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/scripts/generate_context_summary.py > /dev/null 2>&1',
                            "description": "Generate context summary periodically"
                        }
                    ]
                }
            ]
        }
    }

def merge_configurations(existing, new):
    """Merge new hooks with existing configuration"""
    if 'hooks' not in existing:
        return new

    # Deep merge hooks
    for event, hooks in new['hooks'].items():
        if event not in existing['hooks']:
            existing['hooks'][event] = hooks
        else:
            # Append new hooks to existing event hooks
            existing['hooks'][event].extend(hooks)

    return existing

def setup_hooks(dry_run=False):
    """Setup hooks in Claude Code settings"""
    settings_path = get_settings_path()

    print("="*60)
    print("Claude Code Context Preservation Hook Setup")
    print("="*60)
    print()

    # Check if settings file exists
    if settings_path.exists():
        print(f"✓ Found settings file: {settings_path}")
        with open(settings_path, 'r') as f:
            try:
                settings = json.load(f)
                print("✓ Loaded existing settings")
            except json.JSONDecodeError:
                print("❌ Error: Invalid JSON in settings file")
                return 1
    else:
        print(f"⚠ Settings file not found: {settings_path}")
        print("⚠ Will create new settings file")
        settings = {}

    # Get new hook configuration
    new_config = get_hook_configuration()

    # Merge configurations
    merged = merge_configurations(settings.copy(), new_config)

    print()
    print("Hook Configuration to Install:")
    print("-" * 60)
    print(json.dumps(new_config['hooks'], indent=2))
    print("-" * 60)

    if dry_run:
        print()
        print("DRY RUN MODE - No changes made")
        print()
        print("To install, run without --dry-run flag:")
        print("  python3 .claude/hooks/scripts/setup_hooks.py")
        return 0

    print()

    # Check for auto-install flag
    auto_install = '--yes' in sys.argv or '-y' in sys.argv

    if auto_install:
        print("Auto-install mode: Installing hooks...")
        response = 'y'
    else:
        try:
            response = input("Install these hooks? [y/N]: ")
        except EOFError:
            # Non-interactive mode - default to yes
            print("\nNon-interactive mode detected: Installing hooks...")
            response = 'y'

    if response.lower() != 'y':
        print("Installation cancelled")
        return 0

    # Backup existing settings
    if settings_path.exists():
        backup_path = settings_path.with_suffix('.json.backup')
        with open(backup_path, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"✓ Backed up existing settings to: {backup_path}")

    # Write merged configuration
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, 'w') as f:
        json.dump(merged, f, indent=2)

    print(f"✓ Hooks installed to: {settings_path}")
    print()
    print("="*60)
    print("Installation Complete!")
    print("="*60)
    print()
    print("Next Steps:")
    print("  1. Restart Claude Code to load new hooks")
    print("  2. Test with: python3 .claude/hooks/scripts/test_hooks.py")
    print("  3. View setup guide: .claude/hooks/CONTEXT_PRESERVATION_SETUP.md")
    print()
    print("The system will now automatically:")
    print("  • Save context before token compression")
    print("  • Alert you to restore context after clearing")
    print("  • Log activities incrementally")
    print("  • Generate periodic context summaries")
    print()

    return 0

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    sys.exit(setup_hooks(dry_run=dry_run))
