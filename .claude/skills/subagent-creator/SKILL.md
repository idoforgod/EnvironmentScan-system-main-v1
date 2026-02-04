---
name: subagent-creator
description: Create specialized Claude Code sub-agents with custom system prompts and tool configurations. Use when users ask to create a new sub-agent, custom agent, specialized assistant, or want to configure task-specific AI workflows for Claude Code.
---

# Sub-agent Creator

Create specialized AI sub-agents for Claude Code that handle specific tasks with customized prompts and tool access.

## Sub-agent File Format

Sub-agents are Markdown files with YAML frontmatter stored in:
- **Project**: `.claude/agents/` (higher priority)
- **User**: `~/.claude/agents/` (lower priority)

### Structure

```markdown
---
name: subagent-name
description: When to use this subagent (include "use proactively" for auto-delegation)
tools: Tool1, Tool2, Tool3  # Optional - inherits all if omitted
model: sonnet               # Optional - sonnet/opus/haiku/inherit
permissionMode: default     # Optional - default/acceptEdits/bypassPermissions/plan
skills: skill1, skill2      # Optional - auto-load skills
---

System prompt goes here. Define role, responsibilities, and behavior.
```

### Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Lowercase with hyphens |
| `description` | Yes | Purpose and when to use (key for auto-delegation) |
| `tools` | No | Comma-separated tool list (omit to inherit all) |
| `model` | No | `sonnet`, `opus`, `haiku`, or `inherit` |
| `permissionMode` | No | `default`, `acceptEdits`, `bypassPermissions`, `plan` |
| `skills` | No | Skills to auto-load |

## Creation Workflow

1. **Gather requirements**: Ask about the sub-agent's purpose, when to use it, and required capabilities
2. **Choose scope**: Project (`.claude/agents/`) or user (`~/.claude/agents/`)
3. **Define configuration**: Name, description, tools, model
4. **Write system prompt**: Clear role, responsibilities, and output format
5. **Create file**: Write the `.md` file to the appropriate location

## Skill-Agent Binding

Skills can reference a dedicated agent via the `agent` field in SKILL.md frontmatter:

```yaml
# In SKILL.md
---
name: my-skill
description: ...
agent: my-orchestrator    # References .claude/agents/my-orchestrator.md
---
```

The referenced agent **must** have proper YAML frontmatter (`name`, `description`) to be recognized by the system. Without frontmatter, the agent file exists but is not registered and the `agent` reference will not resolve.

## Writing Effective Sub-agents

### Description Best Practices

The `description` field is critical for automatic delegation:

```yaml
# Good - specific triggers (auto-delegated)
description: Expert code reviewer. Use PROACTIVELY after writing or modifying code.

# Good - clear use cases (auto-delegated)
description: Debugging specialist for errors, test failures, and unexpected behavior.

# Good - skill-invoked only (NOT auto-delegated)
description: Master orchestrator for the scanning workflow. Invoked by the scanner skill — do not use directly.

# Bad - too vague
description: Helps with code
```

**Skill-bound agents**: When an agent is referenced by a skill's `agent` field, include "do not use directly" in the description to prevent auto-delegation. These agents should only be invoked through their parent skill.

### System Prompt Guidelines

1. **Define role clearly**: "You are a [specific expert role]"
2. **List actions on invocation**: What to do first
3. **Specify responsibilities**: What the sub-agent handles
4. **Include guidelines**: Constraints and best practices
5. **Define output format**: How to structure responses

### Tool Selection

- **Read-only tasks**: `Read, Grep, Glob, Bash`
- **Code modification**: `Read, Write, Edit, Grep, Glob, Bash`
- **Full access**: Omit `tools` field

See [references/available-tools.md](references/available-tools.md) for complete tool list.

## Example Sub-agents

See [references/examples.md](references/examples.md) for complete examples:
- Code Reviewer
- Debugger
- Data Scientist
- Test Runner
- Documentation Writer
- Security Auditor

## Template

Copy from [assets/subagent-template.md](assets/subagent-template.md) to start a new sub-agent.

## Quick Start Example

Create a code reviewer sub-agent:

```bash
mkdir -p .claude/agents
```

Write to `.claude/agents/code-reviewer.md`:

```markdown
---
name: code-reviewer
description: Reviews code for quality and security. Use proactively after code changes.
tools: Read, Grep, Glob, Bash
model: inherit
---

You are a senior code reviewer.

When invoked:
1. Run git diff to see changes
2. Review modified files
3. Report issues by priority

Focus on:
- Code readability
- Security vulnerabilities
- Error handling
- Best practices
```
