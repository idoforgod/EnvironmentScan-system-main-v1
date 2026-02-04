# Hook Events Reference

## Event Overview

| Event | Trigger | Can Block | Typical Use |
|-------|---------|-----------|-------------|
| PreToolUse | Before tool execution | Yes (exit 2) | Validation, blocking |
| PostToolUse | After tool completion | No | Formatting, logging |
| PermissionRequest | Permission dialog shown | Yes | Auto-allow/deny |
| UserPromptSubmit | User submits prompt | No | Pre-processing |
| Notification | Claude sends notification | No | Custom alerts |
| Stop | Claude finishes responding | No | Post-processing |
| SubagentStop | Subagent task completes | No | Subagent cleanup |
| PreCompact | Before compact operation | No | Pre-compact actions |
| SessionStart | Session starts/resumes | No | Initialization |
| SessionEnd | Session ends | No | Cleanup |

## PreToolUse

Runs before tool calls. Can block execution.

**Input Schema:**
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "ls -la",
    "description": "List files"
  }
}
```

**Exit Codes:**
- `0` - Allow tool to proceed
- `2` - Block tool, stdout sent as feedback to Claude

**Common tool_input fields by tool:**
- `Bash`: `command`, `description`
- `Edit`: `file_path`, `old_string`, `new_string`
- `Write`: `file_path`, `content`
- `Read`: `file_path`
- `Glob`: `pattern`, `path`
- `Grep`: `pattern`, `path`

## PostToolUse

Runs after tool calls complete.

**Input Schema:**
```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.ts"
  },
  "tool_response": "File edited successfully"
}
```

**Use Cases:**
- Auto-formatting edited files
- Logging tool results
- Triggering dependent actions

## PermissionRequest

Runs when permission dialog is shown.

**Input Schema:**
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm install"
  },
  "permission_type": "execute"
}
```

**Exit Codes:**
- `0` - Let user decide
- `1` - Auto-deny
- `2` - Auto-approve

## Notification

Runs when Claude sends notifications.

**Input Schema:**
```json
{
  "message": "Waiting for your input",
  "type": "input_required"
}
```

**Use Cases:**
- Custom desktop notifications
- Slack/Discord alerts
- Sound notifications

## UserPromptSubmit

Runs when user submits a prompt, before Claude processes it.

**Input Schema:**
```json
{
  "prompt": "Help me fix this bug",
  "session_id": "abc123"
}
```

**Use Cases:**
- Prompt logging
- Pre-processing
- Context injection

## Stop

Runs when Claude finishes responding.

**Input Schema:**
```json
{
  "stop_reason": "end_turn",
  "session_id": "abc123"
}
```

**Use Cases:**
- Session logging
- Cleanup tasks
- Metrics collection

## SubagentStop

Runs when subagent (Task tool) tasks complete.

**Input Schema:**
```json
{
  "subagent_type": "Explore",
  "result": "Found 5 matching files"
}
```

## PreCompact

Runs before Claude compacts conversation context.

**Input Schema:**
```json
{
  "reason": "context_limit",
  "current_tokens": 50000
}
```

## SessionStart

Runs when Claude Code starts or resumes a session.

**Input Schema:**
```json
{
  "session_id": "abc123",
  "is_resume": false,
  "project_dir": "/path/to/project"
}
```

**Use Cases:**
- Environment setup
- Loading project config
- Starting background services

## SessionEnd

Runs when Claude Code session ends.

**Input Schema:**
```json
{
  "session_id": "abc123",
  "end_reason": "user_exit"
}
```

**Use Cases:**
- Cleanup resources
- Save session state
- Stop background services
