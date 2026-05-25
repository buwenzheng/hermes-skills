# Cursor CLI Skill

Terminal-based AI coding agent from Cursor.

## Quick Start

```bash
# Install (macOS/Linux/WSL)
curl https://cursor.com/install -fsS | bash

# Verify
agent --version

# Interactive session
agent

# Non-interactive
agent -p "your task" --print
```

## Key Features

- **Agent Mode**: Full tool access for complex coding
- **Plan Mode**: Design approach before coding
- **Ask Mode**: Read-only code exploration
- **Sessions**: Resume conversations across interactions
- **Sandbox Controls**: Control command execution
- **MCP Integration**: Extend via Model Context Protocol
- **GitHub Actions**: CI/CD automation
- **Headless Mode**: Server environments

## Commands

```bash
agent              # Interactive mode
agent "prompt"     # With initial prompt
agent -p "task"    # Non-interactive
agent --continue   # Resume last session
agent mcp list     # List MCP servers
agent update       # Update CLI
```

## Documentation

See `SKILL.md` for full reference including all modes, flags, and configuration options.