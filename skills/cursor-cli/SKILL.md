---
version: 1.0.1
name: cursor-cli
description: Cursor CLI - AI coding agent in terminal. Supports interactive and non-interactive modes, multiple AI modes (Agent/Plan/Ask), sessions, sandbox controls, MCP integration, GitHub Actions, and shell mode. Keywords: cursor, ai agent, coding CLI, terminal, agent mode, plan mode, ask mode, non-interactive, headless, CI/CD, MCP, github actions, shell mode.
trigger: "cursor cli, cursor-agent, agent mode, plan mode, ask mode, cursor shell-mode, cursor headless, cursor github actions, cursor mcp, cursor-cli reference, cursor parameters, cursor authentication, cursor output format, cursor permissions, cursor slash commands, cursor terminal setup"
required_environment_variables: []
int:
  install:
    - macOS/Linux/WSL: `curl https://cursor.com/install -fsS | bash`
    - Windows PowerShell: `irm 'https://cursor.com/install?win32=true' | iex`
  verify: `agent --version`
  update: `agent update`
---

# Cursor CLI

## Overview

Cursor CLI lets you interact with AI agents directly from your terminal to write, review, and modify code. Whether you prefer an interactive terminal interface or print automation for scripts and CI pipelines, the CLI provides powerful coding assistance right where you work.

## When to Use / 何时使用

- **Interactive coding sessions**: Work with an AI agent in real-time, reviewing and approving changes
- **Non-interactive automation**: Integrate into scripts, CI pipelines, or automated workflows
- **Code exploration**: Use Ask mode to understand codebase without making changes
- **Planning before coding**: Use Plan mode to design implementation approach
- **Headless/server environments**: Run agent without TTY or browser
- **MCP integrations**: Extend capabilities via Model Context Protocol servers
- **GitHub Actions**: Automate code review and modifications in CI/CD

## Installation / 安装

### macOS, Linux and Windows (WSL)

```bash
curl https://cursor.com/install -fsS | bash
```

### Windows Native

```powershell
irm 'https://cursor.com/install?win32=true' | iex
```

### Post-installation setup

Add `~/.local/bin` to your PATH.

### Verification

```bash
agent --version
```

### Updates

Cursor CLI will try to auto-update by default to ensure you always have the latest version. To manually update:

```bash
agent update
```

## Interactive Mode

Start a conversational session with the agent to describe your goals, review proposed changes, and approve commands:

```bash
agent
agent "refactor the auth module to use JWT tokens"
```

## Modes

### Agent Mode (Default)

Full access to all tools for complex coding tasks.

### Plan Mode

Design your approach before coding. The agent asks clarifying questions to refine your plan.

### Ask Mode

Read-only exploration without making changes. The agent searches your codebase and provides answers without editing files.

## Non-Interactive Mode

Use print mode for non-interactive scenarios like scripts, CI pipelines, or automation:

```bash
agent -p "find and fix performance issues" --model "gpt-5.2"
agent -p "review these changes for security issues" --output-format text
```

## Sessions

Resume previous conversations to maintain context across multiple interactions:

```bash
agent ls              # List all previous chats
agent resume          # Resume latest conversation
agent --continue      # Continue the last session
agent --resume="chat-id-here"  # Resume specific conversation
```

## Sandbox Controls

Configure command execution settings with `--sandbox <mode>` (`enabled` or `disabled`):

```bash
agent --sandbox enabled    # Enable sandbox mode
agent --sandbox disabled   # Disable sandbox mode
```

Settings persist across sessions. Sandbox controls network access and command execution.

## Max Mode

Enable or disable Max mode on supported models using `/max-mode [on|off]`.

## Sudo Password Prompting

Run commands requiring elevated permissions without leaving the CLI. Password is securely passed to sudo via IPC, never exposed to the AI model.

## Cloud Agent Handoff

Hand off conversations to Cloud Agent to continue working while away. Prefix messages with `&`:

```bash
& refactor the auth module and add comprehensive tests
```

Access Cloud Agent tasks at cursor.com/agents on web or mobile.

## CLI Worktrees

Cursor CLI supports worktree operations for parallel development.

## Command Approval

Review and approve/reject proposed commands in interactive mode.

## Global Options

```bash
agent --print           # Print responses to console (scripts/non-interactive)
agent --force-allow     # Force allow commands unless explicitly denied
agent --allow-mcp       # Automatically approve all MCP servers
agent --headless        # Trust workspace without prompting
agent --plugin <path>   # Load local plugin directory
agent --signout         # Sign out and clear stored authentication
agent --version         # Display version, system, and account info
```

## MCP Servers

Manage MCP servers configured for Cursor Agent:

```bash
agent mcp list          # List configured MCP servers and their status
agent mcp tools <name>  # List available tools for a specific MCP
```

## Commands

```bash
agent <prompt>          # Start in chat mode with initial prompt
agent update            # Update Cursor Agent to the latest version
agent mcp list          # List configured MCP servers
agent mcp tools <name>  # List tools for specific MCP
```

## Arguments

When starting in chat mode, provide an initial prompt:

```bash
agent "your prompt here"
```

## Getting Help

Use `--help` or consult the documentation at cursor.com/docs/cli.

## Authentication

Cursor CLI uses Cursor account authentication. Sign in via:

```bash
agent --signin
```

## Configuration

Configure via `~/.cursor/cli.json` or environment variables.

## Output Format

Supports multiple output formats: text (default), JSON, markdown.

## Permissions

Cursor CLI requires appropriate file system and network permissions. Sandbox mode controls command execution access.

## Slash Commands

Common slash commands in interactive mode:

- `/plan` - Switch to Plan mode
- `/ask` - Switch to Ask mode
- `/max-mode on/off` - Toggle Max mode
- `/sandbox` - Toggle sandbox controls
- `/exit` - End session

## Terminal Setup

Ensure your terminal supports UTF-8 encoding for best results. Some features require proper locale settings.

## Non-Interactive Mode Details

Cursor has full write access in non-interactive mode. Use `--print` for scripted workflows:

```bash
agent -p "your task" --print --output-format text
```

## Complete CLI Flags Reference

| Flag | Description |
|------|-------------|
| `--print` | Print mode for scripts/CI |
| `--model <model>` | Specify AI model |
| `--output-format <format>` | Output format (text/json/markdown) |
| `--sandbox <mode>` | Sandbox controls (enabled/disabled) |
| `--headless` | Headless mode without prompts |
| `--plugin <path>` | Load plugin directory |
| `--continue` | Continue last session |
| `--resume <id>` | Resume specific chat |
| `--force-allow` | Force allow commands |
| `--allow-mcp` | Auto-approve MCP servers |
| `--signout` | Clear authentication |
| `--version` | Show version info |
| `update` | Update to latest version |

## Common Pitfalls

1. **PATH not configured**: After install, ensure `~/.local/bin` is in your PATH
2. **Authentication expired**: Use `agent --signout` then re-authenticate
3. **Sandbox blocking needed commands**: Use `--sandbox disabled` or `--force-allow` with caution
4. **Non-interactive mode still waiting**: Use `--print` flag explicitly for scripted runs
5. **Large codebase slow to index**: Initial indexing may take time on large repos
6. **Model not available**: Check Cursor subscription supports requested model
7. **MCP server connection failed**: Verify MCP server is running and accessible
8. **Headless mode security**: `--headless` trusts workspace fully; use only in safe environments
9. **Concurrent session conflicts**: Each session maintains state; avoid running multiple conflicting sessions

## Verification Checklist

- [ ] `agent --version` returns version info
- [ ] `agent` starts interactive session
- [ ] `agent "test"` works with initial prompt
- [ ] `--print` mode produces output without TTY
- [ ] `agent mcp list` shows MCP status (if configured)
- [ ] `--help` displays available options
- [ ] Shell autocomplete works (if configured)
- [ ] Non-interactive mode works in CI environment