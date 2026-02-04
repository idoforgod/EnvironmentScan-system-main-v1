# Context Preservation Quick Start Guide

## What This Does

Automatically saves your Claude Code conversation and work history to prevent memory loss when tokens reach 75% capacity or when the session is cleared/compressed.

## 3-Step Installation

### Step 1: Run Tests (Verify Everything Works)

```bash
python3 .claude/hooks/scripts/test_hooks.py
```

Expected output: ✅ All tests passed!

### Step 2: Install Hooks

```bash
python3 .claude/hooks/scripts/setup_hooks.py
```

When prompted, type `y` to install.

### Step 3: Restart Claude Code

Restart Claude Code to load the new hooks.

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│         Context Preservation Automatic Flow              │
└─────────────────────────────────────────────────────────┘

During Your Work:
┌──────────────────────────────────────────────────────────┐
│ You: Edit file.py                                         │
│ Hook: Logs "Edited file.py" to work-log.jsonl ✓         │
│                                                           │
│ You: Run tests                                            │
│ Hook: Logs "Ran: pytest" to work-log.jsonl ✓            │
│                                                           │
│ Claude: Generates response                                │
│ Hook: Updates context summary ✓                          │
└──────────────────────────────────────────────────────────┘

When Tokens Reach 75%:
┌──────────────────────────────────────────────────────────┐
│ System: About to compress context...                      │
│ Hook: Saves full snapshot to latest-context.md ✓        │
│ Hook: Creates timestamped backup ✓                       │
└──────────────────────────────────────────────────────────┘

After Session Clear:
┌──────────────────────────────────────────────────────────┐
│ System: Session starting...                               │
│ Hook: 🔄 CONTEXT RESTORATION REQUIRED                    │
│       Please read: .claude/context-backups/              │
│                    latest-context.md                      │
│                                                           │
│ Claude: [Reads file and rebuilds context] ✓             │
└──────────────────────────────────────────────────────────┘
```

## Manual Usage

### View Current Context

```bash
cat .claude/context-backups/latest-context.md
```

### Save Context Manually

```bash
python3 .claude/hooks/scripts/generate_context_summary.py
```

### View Recent Activities

```bash
tail -20 .claude/context-backups/work-log.jsonl
```

### View All Backups

```bash
ls -lht .claude/context-backups/
```

## What Gets Saved

✅ **Automatically Saved**:
- Git status and modified files
- Recent tool activities (Edit, Write, Bash, etc.)
- Project file overview
- Recent commits
- Timestamps of all activities

❌ **NOT Saved** (Privacy Safe):
- Conversation text
- File contents
- API keys or secrets
- Credentials

## Files Created

```
.claude/context-backups/
├── latest-context.md           # Most recent snapshot
├── work-log.jsonl              # Incremental activity log
└── context-backup-*.md         # Timestamped backups (last 10)
```

## Updating During Critical Work

Edit the context file to add important notes:

```bash
code .claude/context-backups/latest-context.md
```

Add to the "Workflow State Tracking" section:
- Current phase of work
- Active tasks
- Important decisions
- Blockers

## Verification

After installation, verify hooks are working:

```bash
# Check hooks are registered
cat ~/.claude/settings.json | grep -A 10 "PreCompact"

# Make a change and check logging
echo "test" > test.txt
cat .claude/context-backups/work-log.jsonl | tail -1
```

## Troubleshooting

### Hooks Not Running?

Check settings file:
```bash
cat ~/.claude/settings.json
```

Should contain `"hooks": { ... }`

### Scripts Not Executable?

```bash
chmod +x .claude/hooks/scripts/*.py
```

### Context Not Saving?

Test manually:
```bash
echo '{"event": "test"}' | python3 .claude/hooks/scripts/save_context.py
```

## Advanced Features

### Change Backup Retention

Edit `.claude/hooks/scripts/save_context.py`:
```python
# Line 88: Change 10 to desired number
for old_backup in backups[10:]:  # Keep last 10
```

### Customize Activity Log Size

Edit `.claude/hooks/scripts/update_work_log.py`:
```python
# Line 76: Change 100 to desired number
if len(lines) > 100:  # Keep last 100 entries
```

### Disable Specific Hooks

Remove from `~/.claude/settings.json`:
- Remove `PostToolUse` - Stops activity logging
- Remove `Stop` - Stops periodic summaries
- Remove `PreCompact` - Stops auto-save before compression
- Remove `SessionStart` - Stops restoration alerts

## Important Notes

1. **First Run**: Won't show restoration message (no prior context)
2. **Backup Rotation**: Only last 10 backups are kept
3. **Gitignore**: Add `.claude/context-backups/` to `.gitignore` if needed
4. **Manual Updates**: Update context file during important milestones

## Support

For detailed documentation:
```bash
cat .claude/hooks/CONTEXT_PRESERVATION_SETUP.md
```

For testing:
```bash
python3 .claude/hooks/scripts/test_hooks.py
```

---

**Version**: 1.0.0
**Purpose**: Prevent critical context loss in Claude Code workflows
**Created**: 2026-01-30
