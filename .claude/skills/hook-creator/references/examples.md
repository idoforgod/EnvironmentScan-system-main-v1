# Hook Examples

Complete, tested hook configurations for common use cases.

## Logging Hooks

### Log All Bash Commands

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"\\(.tool_input.command) - \\(.tool_input.description // \"No description\")\"' >> ~/.claude/bash-command-log.txt"
          }
        ]
      }
    ]
  }
}
```

### Log All File Edits

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"[\\(now | strftime(\"%Y-%m-%d %H:%M:%S\"))] \\(.tool_name): \\(.tool_input.file_path)\"' >> ~/.claude/edit-log.txt"
          }
        ]
      }
    ]
  }
}
```

## Auto-Formatting Hooks

### Format TypeScript Files

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -q '\\.tsx\\?$'; then npx prettier --write \"$file_path\" 2>/dev/null; fi; }"
          }
        ]
      }
    ]
  }
}
```

### Format Python Files with Black

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read f; [[ \"$f\" == *.py ]] && black \"$f\" 2>/dev/null; }"
          }
        ]
      }
    ]
  }
}
```

### Format Go Files

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read f; [[ \"$f\" == *.go ]] && gofmt -w \"$f\"; }"
          }
        ]
      }
    ]
  }
}
```

## File Protection Hooks

### Block Edits to Sensitive Files

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json, sys; data=json.load(sys.stdin); path=data.get('tool_input',{}).get('file_path',''); blocked=['.env', 'package-lock.json', '.git/', 'secrets']; sys.exit(2 if any(p in path for p in blocked) else 0)\""
          }
        ]
      }
    ]
  }
}
```

### Block Modifications to Production Directory

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input | .file_path // .command // \"\"' | grep -q '/prod/' && echo 'BLOCKED: Cannot modify production files' && exit 2 || exit 0"
          }
        ]
      }
    ]
  }
}
```

## Notification Hooks

### macOS Desktop Notification

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.message' | xargs -I{} osascript -e 'display notification \"{}\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

### Linux Desktop Notification

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.message' | xargs -I{} notify-send 'Claude Code' '{}'"
          }
        ]
      }
    ]
  }
}
```

### Sound Notification (macOS)

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "afplay /System/Library/Sounds/Glass.aiff"
          }
        ]
      }
    ]
  }
}
```

## Validation Hooks

### Validate JSON Before Write

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -e '.tool_input | select(.file_path | endswith(\".json\")) | .content' | jq . > /dev/null 2>&1 || { echo 'Invalid JSON content'; exit 2; }"
          }
        ]
      }
    ]
  }
}
```

### Lint TypeScript Before Commit

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.command' | grep -q 'git commit' && npx eslint . --max-warnings 0 || exit 0"
          }
        ]
      }
    ]
  }
}
```

## Session Hooks

### Initialize Environment on Session Start

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "[ -f .claude-env ] && source .claude-env"
          }
        ]
      }
    ]
  }
}
```

### Cleanup on Session End

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "rm -f /tmp/claude-session-* 2>/dev/null; exit 0"
          }
        ]
      }
    ]
  }
}
```

## Multiple Hooks Example

Combine multiple hooks in one configuration:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json,sys; p=json.load(sys.stdin).get('tool_input',{}).get('file_path',''); sys.exit(2 if '.env' in p else 0)\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read f; [[ \"$f\" == *.ts ]] && npx prettier --write \"$f\" 2>/dev/null; exit 0; }"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "afplay /System/Library/Sounds/Glass.aiff"
          }
        ]
      }
    ]
  }
}
```
