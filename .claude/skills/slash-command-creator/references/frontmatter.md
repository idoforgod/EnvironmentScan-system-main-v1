# Slash Command Frontmatter Reference

## Required Fields

### `description`
Brief description of what the command does. Shown in `/help` output.

```yaml
description: Create a git commit with staged changes
```

## Optional Fields

### `allowed-tools`
Specifies which tools the command can use. Format: `ToolName(pattern:*)` or just `ToolName`.

```yaml
# Single tool
allowed-tools: Bash(git status:*)

# Multiple tools
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)

# Tool without pattern
allowed-tools: Read, Write, Edit
```

Common tool patterns:
- `Bash(command:*)` - Allow specific bash commands
- `Read` - File reading
- `Write` - File writing
- `Edit` - File editing
- `Grep` - Content search
- `Glob` - File pattern matching

### `argument-hint`
Shows expected arguments when auto-completing the command.

```yaml
# Single argument
argument-hint: [message]

# Multiple arguments
argument-hint: [pr-number] [priority] [assignee]

# Alternative syntax
argument-hint: add [tagId] | remove [tagId] | list
```

### `model`
Specific model to use for this command. See [Models overview](https://docs.claude.com/en/docs/about-claude/models/overview).

```yaml
model: claude-3-5-haiku-20241022
model: claude-sonnet-4-5-20250929
```

### `disable-model-invocation`
Prevents the `SlashCommand` tool from calling this command programmatically.

```yaml
disable-model-invocation: true
```

### `context`
Controls the execution context for the command. Use `fork` to run the command in an isolated sub-agent context. The command executes with a copy of the current conversation context, and only the final result returns to the main conversation. This prevents long-running or data-heavy commands from consuming the main context window.

```yaml
# Run in forked context (isolated execution)
context: fork
```

**When to use `context: fork`:**
- Long-running workflows with many intermediate steps
- Commands that generate large amounts of intermediate data
- Batch processing or data collection tasks

**When NOT to use `context: fork`:**
- Interactive commands that require back-and-forth with the user
- Status-checking commands that need quick responses
- Review/approval commands where conversation context matters

## Complete Frontmatter Example

```yaml
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
argument-hint: [message]
description: Create a git commit with staged changes
model: claude-3-5-haiku-20241022
---
```

### Example with fork context (for heavy workflows)

```yaml
---
description: Execute complete data processing pipeline
context: fork
---
```
