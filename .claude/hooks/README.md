# Claude Code Hooks System

## 🎯 Quick Start - Context Preservation

**NEW**: Automatic context backup to prevent memory loss during token compression!

```bash
# Install in 3 commands
python3 .claude/hooks/scripts/test_hooks.py
python3 .claude/hooks/scripts/setup_hooks.py
# Restart Claude Code
```

**See**: [QUICK_START.md](./QUICK_START.md) for complete installation guide.

---

## Overview

This directory contains two hook systems:

### 1. Context Preservation Hooks (NEW) 🔄

**Purpose**: Prevent critical context loss when Claude Code compresses/clears conversation.

**Features**:
- Auto-saves context when tokens reach 75%
- Incremental activity logging
- Auto-restoration alerts on session start
- Periodic context summaries

**Files**:
- `QUICK_START.md` - Installation guide
- `CONTEXT_PRESERVATION_SETUP.md` - Complete documentation
- `scripts/save_context.py` - Main context saver
- `scripts/restore_context.py` - Session restoration
- `scripts/update_work_log.py` - Activity logger
- `scripts/generate_context_summary.py` - Summary generator
- `scripts/setup_hooks.py` - Automated setup
- `scripts/test_hooks.py` - Test suite

### 2. Environmental Scanning Workflow Hooks

**Purpose**: Validation logic for the environmental scanning workflow.

Hooks allow automatic execution of validation logic at key workflow events:
- Pre-agent execution validation
- Post-agent output verification
- Human review management
- Quality metrics tracking

## Hook Events

### pre-agent-execution

Triggered before any worker agent runs.

**Purpose**: Validate inputs and prerequisites

```yaml
hooks:
  pre-agent-execution:
    - name: "validate-inputs"
      command: "python tests/validate_agent_inputs.py ${AGENT_NAME}"
      description: "Check required input files exist"

    - name: "check-api-keys"
      command: "python tests/check_api_keys.py"
      description: "Verify API credentials for scanner"
      agents: ["multi-source-scanner"]
```

### post-agent-execution

Triggered after worker agent completes.

**Purpose**: Verify outputs and run unit tests

```yaml
hooks:
  post-agent-execution:
    - name: "verify-output"
      command: "python tests/unit/test_${AGENT_NAME}.py"
      description: "Run TDD unit tests for agent output"

    - name: "log-metrics"
      command: "python scripts/log_metrics.py ${AGENT_NAME} ${EXECUTION_TIME}"
      description: "Record performance metrics"
```

### on-human-review

Triggered when workflow reaches human checkpoint.

**Purpose**: Notify user and wait for input

```yaml
hooks:
  on-human-review:
    - name: "notify-user"
      command: "python scripts/send_notification.py ${STEP_ID}"
      description: "Send Slack/email notification"

    - name: "block-workflow"
      command: "python scripts/update_status.py ${STEP_ID} blocked"
      description: "Mark task as blocked"
```

## Implementation

### 1. Create hook scripts

```bash
mkdir -p .claude/hooks/scripts
```

### 2. Define hooks in claude.json (if supported)

Or use external task runner (Make, Shell scripts).

### 3. Hook execution flow

```
Agent Execution Request
    ↓
Run pre-agent-execution hooks
    ↓ (Pass)
Execute Agent
    ↓ (Complete)
Run post-agent-execution hooks
    ↓ (Pass)
Continue Workflow
```

## Example Hook Scripts

### validate_agent_inputs.py

```python
import sys
import os

agent_name = sys.argv[1]

input_map = {
    "archive-loader": ["signals/database.json"],
    "multi-source-scanner": ["config/sources.yaml"],
    "deduplication-filter": ["raw/daily-scan-*.json", "context/previous-signals.json"]
}

required_files = input_map.get(agent_name, [])
missing = [f for f in required_files if not os.path.exists(f)]

if missing:
    print(f"ERROR: Missing input files: {missing}")
    sys.exit(1)

print(f"✓ All inputs present for {agent_name}")
sys.exit(0)
```

### test_agent_output.py

```python
import sys
import json

agent_name = sys.argv[1]

output_map = {
    "archive-loader": "context/previous-signals.json",
    "deduplication-filter": "filtered/new-signals-*.json"
}

output_file = output_map.get(agent_name)

# Validate output exists
assert os.path.exists(output_file), f"Output file not found: {output_file}"

# Validate JSON structure
with open(output_file) as f:
    data = json.load(f)

# Agent-specific validation
if agent_name == "archive-loader":
    assert "signals" in data
    assert "index" in data
    assert "metadata" in data

print(f"✓ {agent_name} output validation passed")
sys.exit(0)
```

## Integration with Orchestrator

The orchestrator should invoke hooks at appropriate points:

```python
def execute_agent(agent_name, inputs):
    # Pre-execution hooks
    run_hooks("pre-agent-execution", agent=agent_name)

    # Execute agent
    result = invoke_agent(agent_name, inputs)

    # Post-execution hooks
    run_hooks("post-agent-execution", agent=agent_name, time=result.duration)

    return result
```

## Configuration Example

If Claude Code supports hooks in configuration:

```yaml
# .claude/hooks/config.yaml
hooks:
  pre-agent-execution:
    enabled: true
    scripts:
      - path: ".claude/hooks/scripts/validate_inputs.py"
        agents: ["all"]

  post-agent-execution:
    enabled: true
    scripts:
      - path: ".claude/hooks/scripts/test_output.py"
        agents: ["all"]
      - path: ".claude/hooks/scripts/log_metrics.py"
        agents: ["all"]

  on-human-review:
    enabled: true
    scripts:
      - path: ".claude/hooks/scripts/notify_user.py"
```

## Notes

- Hooks should be fast (< 5 seconds)
- Failed hooks stop workflow by default
- Use hooks for validation, not business logic
- Log all hook executions

---

## Directory Structure

```
.claude/hooks/
├── README.md                          # This file
├── QUICK_START.md                     # Context preservation quick start
├── CONTEXT_PRESERVATION_SETUP.md      # Complete setup documentation
│
├── scripts/                           # Hook scripts
│   ├── save_context.py                # Save context before compression
│   ├── restore_context.py             # Restore context on session start
│   ├── update_work_log.py             # Log activities incrementally
│   ├── generate_context_summary.py    # Generate comprehensive summaries
│   ├── setup_hooks.py                 # Automated hook installation
│   └── test_hooks.py                  # Test suite
│
└── (Environmental scanning hooks)     # Workflow validation hooks
```

## Getting Started

### For Context Preservation

```bash
# Quick installation
python3 .claude/hooks/scripts/test_hooks.py      # Test
python3 .claude/hooks/scripts/setup_hooks.py     # Install
# Restart Claude Code
```

See [QUICK_START.md](./QUICK_START.md) for details.

### For Environmental Scanning Workflow

Follow the workflow validation examples above for agent-specific hooks.

## Version

**Context Preservation System**: v1.0.0 (2026-01-30)
**Workflow Hooks System**: v1.0.0 (2026-01-29)
