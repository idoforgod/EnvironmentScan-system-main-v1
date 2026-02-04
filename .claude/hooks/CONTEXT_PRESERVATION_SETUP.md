# Context Preservation Hook System

## Overview

This system automatically saves and restores Claude Code's working context to prevent critical memory loss during token compression or session clears.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                  Context Preservation Flow                   │
└─────────────────────────────────────────────────────────────┘

1. During Work (PostToolUse Hook)
   └─> Incrementally logs activities to work-log.jsonl

2. Before Compression (PreCompact Hook - 75% token threshold)
   └─> Saves full context snapshot to latest-context.md
   └─> Creates timestamped backup

3. After Clear (SessionStart Hook)
   └─> Detects existing context file
   └─> Alerts Claude to read the file
   └─> Claude reads and rebuilds context

4. Periodic Backup (Stop Hook - every response)
   └─> Updates context summary
   └─> Maintains incremental backups
```

## Files Created

```
.claude/
├── hooks/
│   ├── scripts/
│   │   ├── save_context.py           # Main context saver
│   │   ├── restore_context.py        # Session restoration
│   │   ├── update_work_log.py        # Incremental activity logger
│   │   └── generate_context_summary.py # Comprehensive summary generator
│   └── CONTEXT_PRESERVATION_SETUP.md  # This file
│
└── context-backups/
    ├── latest-context.md              # Most recent context snapshot
    ├── work-log.jsonl                 # Incremental activity log
    └── context-backup-YYYYMMDD_HHMMSS.md  # Timestamped backups (last 10 kept)
```

## Installation

### Option 1: Automatic Setup (Recommended)

Run the setup command:

```bash
python3 .claude/hooks/scripts/generate_context_summary.py
```

Then manually add hooks to your Claude Code settings.

### Option 2: Manual Setup

Add the following configuration to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/save_context.py",
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
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/restore_context.py",
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
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/update_work_log.py",
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
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/generate_context_summary.py > /dev/null 2>&1",
            "description": "Generate context summary periodically"
          }
        ]
      }
    ]
  }
}
```

### Option 3: Project-Specific Setup

Add to `.claude/config.json` in your project (if supported):

```json
{
  "hooks": {
    // Same configuration as above
  }
}
```

## Usage

### Automatic Usage (No Action Required)

Once installed, the system works automatically:

1. ✅ **During Normal Work**: Activities are logged incrementally
2. ✅ **Before Compression**: Full context is saved automatically
3. ✅ **After Clear**: Claude is prompted to read context file
4. ✅ **Periodic Updates**: Context summary regenerates after each response

### Manual Context Save

Generate a context summary at any time:

```bash
python3 .claude/hooks/scripts/generate_context_summary.py
```

### View Current Context

```bash
cat .claude/context-backups/latest-context.md
```

### View Activity Log

```bash
tail -20 .claude/context-backups/work-log.jsonl
```

### View All Backups

```bash
ls -lht .claude/context-backups/context-backup-*.md
```

## Context File Structure

The `latest-context.md` file contains:

```markdown
# Claude Code Context Summary

## Current Project State
- Git branch and status
- Modified files
- Recent commits

## Recent Activities
- Last 10 tool uses with timestamps
- Activity summaries

## Project Files Overview
- File counts by type
- Key directories status
- Critical files modification times

## Workflow State Tracking
- Current phase (manually updated)
- Active tasks
- Blockers and issues
- Key decisions made
```

## Best Practices

### 1. Manual Context Updates

During critical work, manually update the workflow state section:

```bash
# Edit the context file
code .claude/context-backups/latest-context.md

# Add current phase, tasks, decisions
```

### 2. Review Before Clearing

Before manually clearing context:

```bash
# Generate fresh snapshot
python3 .claude/hooks/scripts/generate_context_summary.py

# Review what will be saved
cat .claude/context-backups/latest-context.md
```

### 3. Post-Restoration Workflow

After Claude reads the context file:

1. ✅ Scan the recent activities
2. ✅ Review modified files
3. ✅ Check workflow phase and next steps
4. ✅ Read any critical files mentioned

### 4. Backup Management

The system automatically:
- Keeps last 10 timestamped backups
- Keeps last 100 activity log entries
- Overwrites `latest-context.md` with fresh snapshots

## Troubleshooting

### Hook Not Running

Check if hooks are enabled:

```bash
cat ~/.claude/settings.json | grep -A 5 "hooks"
```

### Permission Errors

Ensure scripts are executable:

```bash
chmod +x .claude/hooks/scripts/*.py
```

### Missing Context File

Generate manually:

```bash
python3 .claude/hooks/scripts/generate_context_summary.py
```

### Context Not Restoring

Check SessionStart hook output in Claude Code console.

## Advanced Configuration

### Adjust Backup Retention

Edit `.claude/hooks/scripts/save_context.py`:

```python
# Keep last 20 backups instead of 10
for old_backup in backups[20:]:  # Change from [10:]
```

### Customize Activity Logging

Edit `.claude/hooks/scripts/update_work_log.py`:

```python
# Log more entries (default 100)
if len(lines) > 200:  # Change from > 100
```

### Add Custom Context Sections

Edit `.claude/hooks/scripts/generate_context_summary.py` to add custom sections.

## Testing

### Test Context Save

```bash
echo '{"event": "test"}' | python3 .claude/hooks/scripts/save_context.py
```

Expected output:
```
✓ Context saved to .claude/context-backups/latest-context.md
✓ Backup created: context-backup-YYYYMMDD_HHMMSS.md
```

### Test Context Restore

```bash
python3 .claude/hooks/scripts/restore_context.py
```

Expected output:
```
============================================================
🔄 CONTEXT RESTORATION REQUIRED
============================================================
...
```

### Test Activity Logging

```bash
echo '{"tool_name": "Edit", "tool_input": {"file_path": "test.py"}}' | python3 .claude/hooks/scripts/update_work_log.py
```

Then check:
```bash
tail -1 .claude/context-backups/work-log.jsonl
```

## Security & Privacy

### What Gets Saved

✅ **Saved**:
- File paths and names
- Tool names and activities
- Git status and commits
- Timestamps and counts

❌ **NOT Saved**:
- File contents (unless you manually add)
- Credentials or secrets
- Full conversation text
- API keys or tokens

### Sensitive Projects

For sensitive projects, you can:

1. **Disable automatic logging**:
   - Remove PostToolUse hook

2. **Manual context only**:
   - Keep only PreCompact and SessionStart hooks
   - Manually curate what goes into context file

3. **Gitignore context files**:
   ```bash
   echo ".claude/context-backups/" >> .gitignore
   ```

## Version History

- **v1.0.0** (2026-01-30): Initial release
  - PreCompact, SessionStart, PostToolUse, Stop hooks
  - Incremental activity logging
  - Automated backup rotation
  - Context summary generation

## Support

If you encounter issues:

1. Check hook logs in Claude Code output
2. Verify scripts are executable: `ls -la .claude/hooks/scripts/`
3. Test individual scripts manually
4. Review `~/.claude/settings.json` for hook configuration

---

**System Version**: 1.0.0
**Last Updated**: 2026-01-30
**Purpose**: Prevent context loss during token compression in Claude Code workflows
