---
name: qoder-cli
description: |
  Use when the user mentions qodercli, qoder cli, AI coding assistant, code review/generation/refactoring,
  slash commands like /review /init /agents, or needs to manage Subagent, custom commands, Skills, Hooks,
  or MCP services for an AI programming workflow.
version: 1.0.1
category: coding-agent
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [qodercli, qoder, ai-coding, code-review, subagent, mcp, skills, hooks]
    related_skills: [claude-code, codex, opencode]
---

# Qoder CLI

## Overview

Qoder CLI is an AI-powered programming assistant CLI for code generation, review, refactoring, and Q&A. It runs in TUI (interactive) or Print (non-interactive) mode, supports Subagent management, custom Commands, Skills, Hooks, and MCP service integration.

## When to Use

- User mentions `qodercli`, `qoder cli`, or AI coding assistant
- Code review, generation, or refactoring requests
- Slash commands: `/review`, `/init`, `/agents`, `/commands`, `/skills`, `/mcp`, `/model`, `/quest`, etc.
- Managing Subagent, custom Commands, Skills, Hooks, or MCP services
- Project initialization with `AGENTS.md` memory file

## Installation

**cURL** (macOS / Linux):
```shell
curl -fsSL https://qoder.com/install | bash
```

**Homebrew** (macOS / Linux):
```shell
brew install qoderai/qoder/qodercli --cask
```

**NPM** (macOS / Linux / Windows):
```shell
npm install -g @qoder-ai/qodercli
```

Verify: `qodercli --version`

## Authentication

**TUI interactive login**:
```shell
qodercli         # launch CLI
/login           # select browser or token method
```
Get token: https://qoder.com/account/integrations

**Environment variable** (CI / automation):
```shell
export QODER_PERSONAL_ACCESS_TOKEN="your_token_here"
```

> `/login` command takes precedence over environment variable.

**Logout**: `/logout` (clear env var first if used)

## Usage Modes

### TUI Mode (Interactive)

Run `qodercli` in a project directory:

| Prefix | Mode | Description |
|--------|------|-------------|
| `>` | Dialogue (default) | Natural language conversation |
| `!` | Bash mode | Run shell commands directly |
| `/` | Slash command | Execute built-in commands |
| `\` + Enter | Multiline input | Multi-line text entry |

### Print Mode (Non-Interactive)

```shell
qodercli --print
qodercli -p "your prompt"
qodercli --output-format=json
```

### Launch Options

| Option | Description |
|--------|-------------|
| `-w <dir>` | Set working directory |
| `-c` | Continue last session |
| `-r <session-id>` | Resume specific session |
| `--allowed-tools` | Whitelist tools |
| `--disallowed-tools` | Blacklist tools |
| `--max-turns N` | Max conversation turns |
| `--yolo` | Skip permission checks |
| `--model <tier>` | Specify tier: lite/efficient/auto/performance/ultimate |

## Common Slash Commands

| Command | Purpose |
|---------|---------|
| `/help` | Show help |
| `/init` | Generate `AGENTS.md` memory file in project |
| `/memory` | Manage memory files |
| `/agents` | View and manage Subagents |
| `/commands` | View and manage custom Commands |
| `/skills` | Manage Skills |
| `/mcp` | MCP service management |
| `/model` | Switch model |
| `/review` | Code review |
| `/quest` | Multi-agent workflow orchestration |
| `/resume` | Resume session |
| `/clear` | Clear current session history |
| `/compact` | Compress context |
| `/status` | View CLI status |
| `/config` | View system config |
| `/usage` | View Credits usage |
| `/logout` | Log out |
| `/quit` | Exit TUI |

## Models

### Three Model Types

| Type | Description |
|------|-------------|
| **Tiered (Default)** | Lite (free) / Efficient / Auto (default) / Performance / Ultimate |
| **Frontier (New Models)** | Latest SOTA models, limited-time availability |
| **Custom** | Bring your own API key from model provider (not available on Teams plan) |

### Switching Models

- **TUI**: `/model` → arrow keys, Tab for tabs, Enter to confirm
- **Command line**: `qodercli --model lite` (session-only)

## Subagent

### Quick Start

```shell
# AI-assisted creation: describe in TUI, CLI generates config
帮我使用 general-purpose subagent 分析项目功能
```

### Explicit Invocation

```shell
# TUI
帮我使用 api-reviewer subagent 审查这个 API 设计

# Headless
qodercli -p "帮我使用 api-reviewer subagent 审查这个 API 设计"
```

### Chain Invocation

```shell
qodercli -p "先使用 general-purpose subagent 检查实现方案，再使用 api-reviewer subagent 审查 API 设计" --max-turns 10
```

### Create Subagent (AI-Assisted)

1. `/agents` → select tab (User/Project) → "Create new agent..."
2. Enter description, CLI auto-generates config
3. Config locations:
   - Project: `.qoder/agents/<name>.md`
   - User: `~/.qoder/agents/<name>.md`

### Manual Config Fields

```yaml
---
name: agent-name           # required, unique identifier
description: Purpose text  # required, model uses this to select
tools: Read,Grep,Glob      # optional, defaults to * (all tools)
---
# System prompt
```

> Project-level takes precedence over user-level.

## Custom Commands

### AI-Assisted Creation

1. `/commands` → select tab (User/Project) → "Create new command..."
2. Enter description, e.g.: `View all git changes and make a good commit`
3. CLI auto-generates to:
   - Project: `.qoder/commands/`
   - User: `~/.qoder/commands/`

### Manual Config

```markdown
---
name: git-commit
description: |
  Use this command when you need to review all git changes in the current
  repository and generate a well-structured commit message.
---
You are an expert Git commit message generator...
```

### Rules

- `name`: lowercase letters and hyphens
- `description`: functional description, multi-line YAML supported
- Priority: Project-level > User-level

## Skills

### Skill vs Command

| Feature | Skill | Command |
|---------|-------|---------|
| Trigger | Model auto判断 or `/skill-name` | Must type `/command-name` |
| Primary use | Professional domain knowledge, complex workflows | Quick preset tasks |

### Directory Structure

```
{skill-name}/
├── SKILL.md           # required
├── REFERENCE.md       # optional
├── EXAMPLES.md        # optional
└── scripts/           # optional
    └── helper.py
```

### SKILL.md Format

```markdown
---
name: skill-name
description: Functional description with usage context
---
# Skill Name

## Instructions
Step-by-step guidance

## Examples
Usage examples
```

**Fields**:
- `name`: lowercase letters/numbers/hyphens, max 64 chars
- `description`: max 1024 chars, determines when skill is triggered

### Storage

- User: `~/.qoder/skills/{skill-name}/SKILL.md`
- Project: `.qoder/skills/{skill-name}/SKILL.md`

> Project-level takes precedence. Run `/skills reload` after updates.

## MCP Services

### Add Services

```shell
# stdio type (default)
qodercli mcp add playwright -- npx -y @playwright/mcp@latest
qodercli mcp add context7 -- npx -y @upstash/context7-mcp@latest
qodercli mcp add deepwiki -- npx -y mcp-deepwiki@latest

# Specify type
qodercli mcp add myservice -t http -- <command>
```

### Manage Services

```shell
qodercli mcp list              # list configured services
qodercli mcp remove playwright # remove service
/mcp reload                    # reload in CLI
```

### Scopes

| Scope | Description |
|-------|-------------|
| `user` | Available to all projects |
| `local` | Current machine, current project only (default) |
| `project` | Shared with project |

Config files:
- User: `~/.qoder/settings.json`
- Project local: `${project}/.qoder/settings.local.json`
- Project: `${project}/.mcp.json`

## Permissions

### Permission Modes

```shell
qodercli --permission-mode default           # regular interactive (default)
qodercli --permission-mode accept_edits       # daily coding
qodercli --permission-mode plan               # review/planning
qodercli --permission-mode auto               # automation
qodercli --permission-mode bypass_permissions # trusted experiments
qodercli --permission-mode dont_ask          # headless
```

Also supports camelCase: `acceptEdits`, `bypassPermissions`, `dontAsk`.

### Config File

```json
{
  "permissions": {
    "allow": ["Read(/src/**)", "Edit(/src/**)", "Bash(npm run test:*)"],
    "ask": ["Bash(npm publish:*)", "WebFetch"],
    "deny": ["Read(*.pem)", "Bash(rm -rf:*)"]
  }
}
```

Paths: `~/.qoder/settings.json` (user), `${project}/.qoder/settings.json` (project), `${project}/.qoder/settings.local.json` (local)

### Rule Syntax

| Pattern | Meaning |
|---------|---------|
| `ToolName` | Entire tool |
| `ToolName(content)` | Path, command, etc. |
| `*` | Match all |

MCP tool name format: `mcp__<server>__<tool>`

## Hooks

### Quick Example: Block Dangerous Commands

```bash
mkdir -p ~/.qoder/hooks
cat > ~/.qoder/hooks/block-rm.sh << 'EOF'
#!/bin/bash
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command')
if echo "$command" | grep -q 'rm -rf'; then
  echo "危险命令已被阻止: $command" >&2
  exit 2
fi
exit 0
EOF
chmod +x ~/.qoder/hooks/block-rm.sh
```

Add to `~/.qoder/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.qoder/hooks/block-rm.sh"
          }
        ]
      }
    ]
  }
}
```

### Common Events

| Event | Trigger |
|-------|---------|
| `SessionStart` | Session begins |
| `SessionEnd` | Session ends |
| `UserPromptSubmit` | After user submits prompt |
| `PreToolUse` | Before tool execution (can block) |
| `PostToolUse` | After tool succeeds |
| `PostToolUseFailure` | After tool fails |
| `Stop` | After Agent completes response (can prevent stop) |
| `PreCompact` | Before context compression |

### Script Output

| Exit Code | Behavior |
|-----------|----------|
| 0 | Success |
| 2 | Block (stderr injected into conversation) |
| other | Non-blocking error |

## Worktree

Run in isolated Git worktree:
```shell
qodercli --worktree feature-a
qodercli --worktree feature-a "Implement the login fix"
```

Session end prints resume command:
```shell
cd <worktree-path> && qodercli --resume <session-id>
```

Manual removal: `git worktree remove <worktree-path>`

## AGENTS.md Memory

Paths:
- User: `~/.qoder/AGENTS.md`
- Project: `${project}/AGENTS.md`
- Local project: `${project}/AGENTS.local.md`

Operations:
- `/init` generate in project
- `/memory` manage memory files
- Or create/edit manually

## Upgrade

```shell
# cURL
curl -fsSL https://qoder.com/install | bash -s -- --force

# Homebrew
brew update && brew upgrade

# NPM
npm install -g @qoder-ai/qodercli

# Built-in command
qodercli update
```

Disable auto-upgrade: set `"general.enableAutoUpdate": false` in `~/.qoder/settings.json`

## Common Pitfalls

1. **Login not persisting**: Ensure `QODER_PERSONAL_ACCESS_TOKEN` env var is set before running CLI, or use `/login` in TUI first.

2. **Subagent not triggering**: Check that description is specific enough (what the agent does, not just what the task is). Use keywords like "审查 API 设计" in description.

3. **MCP service not working**: Run `/mcp reload` after adding or modifying services. Verify the command after `--` works in terminal.

4. **Permissions blocking actions**: In headless mode (`-p`), any action that would return `ask` is denied. Use `--permission-mode accept_edits` or configure precise `allow` rules.

5. **AGENTS.md not loaded**: Must be in project root. User-level `~/.qoder/AGENTS.md` applies to all projects. Project-level overrides user-level.

6. **Hooks not firing**: Check `~/.qoder/settings.json` has valid JSON. Exit code 2 blocks execution, other exit codes are non-blocking errors.

## Verification Checklist

- [ ] `qodercli --version` returns version number
- [ ] `/login` or env var authentication successful
- [ ] TUI mode launches with `qodercli` command
- [ ] `/help` shows available commands
- [ ] `/init` generates `AGENTS.md` in project
- [ ] Subagent can be created and invoked
- [ ] Custom command can be created and executed
- [ ] MCP service added with `qodercli mcp add`
- [ ] Permission rules applied correctly
- [ ] Hook script blocks dangerous commands as expected
- [ ] Upgrade command works