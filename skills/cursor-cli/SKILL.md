---
name: cursor-cli
description: "Use when the user asks to delegate coding tasks to Cursor CLI, run Cursor agent in terminal, automate code generation with Cursor, use Cursor in CI/CD, manage Cursor sessions, or integrate Cursor MCP servers. Keywords: cursor, ai agent, coding CLI, terminal, agent mode, plan mode, ask mode, non-interactive, headless, CI/CD, MCP, github actions, shell mode."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Cursor, AI, Code-Review, Refactoring, Automation]
    related_skills: [claude-code, codex, opencode]
---

# Cursor CLI — Hermes Orchestration Guide

Delegate coding tasks to Cursor CLI via the Hermes terminal. Cursor CLI supports two modes: **Print Mode** (non-interactive, preferred for automation) and **Interactive PTY** (tmux-based sessions for multi-turn work).

## INT / 初始化

```bash
# 安装
curl https://cursor.com/install -fsS | bash

# 认证（每次命令需要 --api-key 参数）
export CURSOR_API_KEY=crsr_your_key_here

# 验证登录
agent --api-key $CURSOR_API_KEY whoami

# 更新
agent update
```

## When to Use / 何时使用

- **单次编码任务**：用 print 模式（`agent -p`）执行一次性任务
- **多轮迭代开发**：用 tmux 交互模式，需要 slash 命令（`/plan`、`/ask`）
- **CI/CD 自动化**：用 print 模式，无 TTY 环境
- **会话管理**：用 `--continue` 续期之前的会话
- **MCP 集成**：扩展 Cursor 能力的官方协议

## Key Differences from Claude Code

| Feature | Cursor CLI | Claude Code |
|---------|-----------|-------------|
| **tmux 实时输出** | ✗ 无，任务结束一次性返回 | ✓ 流式输出 |
| **模型指定** | `--model auto`（必须，否则报 usage 限制） | `--model sonnet/opus` 可选 |
| **认证方式** | `--api-key <key>` 参数（不接受环境变量） | `ANTHROPIC_API_KEY` 环境变量 |
| **交互模式** | `agent` 启动，但 tmux 无法捕获中间过程 | `claude` 启动，tmux 可用 `capture-pane` 实时监控 |

## Prerequisites

- **Install:** `curl https://cursor.com/install -fsS | bash`
- **Auth:** `agent --api-key <key> whoami` 或在 `~/.hermes/.env` 中设置 `CURSOR_API_KEY`
- **Check version:** `agent --version`
- **Update:** `agent update`

## Two Orchestration Modes

### Mode 1: Print Mode (`-p`) — Non-Interactive (PREFERRED)

Print mode runs a one-shot task, returns the result, and exits. **No PTY needed. No streaming output.** Cursor CLI 只在任务完成后一次性返回所有结果。

```bash
# 必须 --model auto，否则报 "You're out of usage"
terminal(command="export CURSOR_API_KEY=crsr_your_key && agent -p 'Add error handling to src/auth.py' --print --trust --yolo --model auto", workdir="/path/to/project", timeout=120)
```

**When to use print mode:**
- 单次编码任务（创建文件、修复 bug、添加功能）
- CI/CD 自动化和脚本
- 不需要实时监控的离线任务

**关键参数：**
- `--print` — 非交互打印模式
- `--trust --yolo` — 信任工作区，自动允许操作（无 TTY 时的必需参数）
- `--model auto` — **必须**，否则报 usage 限制
- `--output-format text/json` — 输出格式

### Mode 2: Interactive PTY via tmux — Multi-Turn Sessions

交互模式提供完整的会话体验，但 **tmux 无法实时获取输出**。Cursor CLI 不像 Claude Code 那样支持流式输出，所以 `tmux capture-pane` 在任务进行中只能看到空白，任务结束后才能看到完整结果。

```bash
# 启动 tmux session
terminal(command="tmux new-session -d -s cursor-work -x 140 -y 40")

# 在 tmux 中运行 Cursor（无 -p 参数，进入交互模式）
terminal(command="tmux send-keys -t cursor-work 'cd /path/to/project && CURSOR_API_KEY=xxx agent' Enter")

# 等待启动后发送任务
terminal(command="sleep 5 && tmux send-keys -t cursor-work 'Refactor the auth module' Enter")

# 任务完成后才能 capture 到结果（进行中只能看到空白的 shell 提示符）
terminal(command="sleep 60 && tmux capture-pane -t cursor-work -p -S -50")

# 清理
terminal(command="tmux kill-session -t cursor-work")
```

**When to use interactive mode:**
- 需要多轮对话、迭代式开发
- 需要使用 slash 命令（`/plan`、`/ask`、`/max-mode`）
- **注意：** 如果只需要单次任务，直接用 print 模式更高效

## CLI Subcommands

| Subcommand | Purpose |
|------------|---------|
| `agent` | Start interactive REPL |
| `agent "query"` | Start REPL with initial prompt |
| `agent -p "query"` | Print mode (non-interactive) |
| `agent --continue` | Continue the most recent session |
| `agent --resume <id>` | Resume specific chat |
| `agent ls` | List all previous chats |
| `agent models` | List available models |
| `agent mcp list` | List configured MCP servers |
| `agent mcp tools <name>` | List tools for specific MCP |
| `agent update` | Update Cursor Agent |
| `agent --signout` | Clear authentication |

## Modes

| Mode | Command | Description |
|------|---------|-------------|
| **Agent** (默认) | `agent` | 完整工具访问权限 |
| **Plan** | `agent --plan` 或 `/plan` | 设计实现方案，agent 提问澄清 |
| **Ask** | `agent --ask` 或 `/ask` | 只读模式，不修改文件 |

## Session Management

```bash
# 列出所有会话
agent ls

# 续期最近会话
agent --continue

# 续期特定会话
agent --resume <chat-id>

# 打印模式下续期会话
agent --continue -p "continue the task" --print --trust --yolo --model auto
```

## Complete CLI Flags Reference

### Session & Environment
| Flag | Effect |
|------|--------|
| `-p, --print` | 非交互打印模式（必须用于自动化） |
| `--continue` | 续期最近会话 |
| `--resume <id>` | 续期指定会话 |
| `--model auto` | **必须**，否则报 usage 限制 |
| `--sandbox <mode>` | 沙箱控制：`enabled` 或 `disabled` |
| `--trust --yolo` | 信任工作区 + 自动允许（无 TTY 时必需） |

### Permission & Safety
| Flag | Effect |
|------|--------|
| `--force-allow` | 强制允许命令（除非明确拒绝） |
| `--allow-mcp` | 自动批准所有 MCP 服务器 |
| `--headless` | 无提示信任工作区 |

### Output & Input Format
| Flag | Effect |
|------|--------|
| `--output-format <fmt>` | `text`（默认）、`json`、`markdown` |
| `--print` | 打印模式，输出到 stdout |

## Authentication

Cursor CLI **不读取 `CURSOR_API_KEY` 环境变量**，必须通过以下方式认证：

```bash
# 方式 1：CLI 参数（每次调用都要传）
agent --api-key crsr_xxx whoami

# 方式 2：~/.hermes/.env 中配置
CURSOR_API_KEY=crsr_xxx

# 方式 3：shell 内联
CURSOR_API_KEY=crsr_xxx agent -p "..." --print --model auto
```

**验证登录：**
```bash
agent --api-key $CURSOR_API_KEY whoami
# ✓ Logged in as xxx@163.com
```

## Environment Variables

| Variable | Effect |
|----------|--------|
| `CURSOR_API_KEY` | API Key（**必须通过 `--api-key` 参数传递**，不接受 env） |

## Print Mode Deep Dive

### Structured Output
```bash
agent -p "Analyze auth.py for security issues" --output-format json --print --trust --yolo --model auto
```

### Single-Task Pattern (Recommended)
```bash
export CURSOR_API_KEY=crsr_xxx
agent -p "create app.py with Flask server" --print --trust --yolo --model auto
```

### Session Continuation Pattern
```bash
# Start task
export CURSOR_API_KEY=crsr_xxx
agent -p "Start refactoring the database layer" --print --trust --yolo --model auto > /tmp/session.json

# Continue with same session
export CURSOR_API_KEY=crsr_xxx
agent --continue -p "Add connection pooling" --print --trust --yolo --model auto
```

### Multi-File Creation
```bash
agent -p "Create a Python project with: main.py (Flask app), requirements.txt, README.md" --print --trust --yolo --model auto
```

## Non-Interactive Mode Details

Cursor 在非交互模式下有完整写入权限。使用 `--print` 用于脚本工作流：

```bash
agent -p "your task" --print --output-format text --trust --yolo --model auto
```

**必须参数（无 TTY 模式）：**
- `--print` — 打印模式
- `--trust --yolo` — 信任工作区，自动允许操作
- `--model auto` — 避免 usage 限制

## Common Pitfalls

1. **缺少 `--model auto`** — Cursor 报 "You're out of usage" 时，加 `--model auto` 解决
2. **tmux 无实时输出** — Cursor CLI 不支持流式输出，任务结束前 `capture-pane` 只能看到空白
3. **`CURSOR_API_KEY` 环境变量无效** — 必须用 `--api-key <key>` 参数
4. **PATH 未配置** — 安装后确保 `~/.local/bin` 在 PATH 中
5. **交互模式等待** — 无 `-p` 参数时，agent 会启动交互 REPL，需要手动 `/exit` 退出
6. **沙箱阻止命令** — 用 `--sandbox disabled` 或 `--force-allow`（谨慎使用）
7. **大代码库索引慢** — 首次运行需要时间建立索引

## tmux Orchestration Pattern

**注意：** Cursor CLI 不像 Claude Code 那样支持实时输出。以下模式可用，但监控效果有限：

```bash
# 启动 session
tmux new-session -d -s cursor-work -x 140 -y 40

# 发送任务（无 -p，进入交互模式）
tmux send-keys -t cursor-work 'cd /path && CURSOR_API_KEY=xxx agent' Enter

# 等待并发送任务
sleep 5
tmux send-keys -t cursor-work 'Refactor the auth module' Enter

# 等待足够长时间后 capture（任务进行中只能看到空 prompt）
sleep 90
tmux capture-pane -t cursor-work -p -S -80

# 清理
tmux kill-session -t cursor-work
```

**对于自动化任务，始终使用 Print Mode（`agent -p`），不使用 tmux 交互模式。**

## Verification Checklist

- [ ] `agent --version` 返回版本信息
- [ ] `agent --api-key $CURSOR_API_KEY whoami` 显示登录状态
- [ ] `agent models` 列出可用模型
- [ ] `agent -p "echo hello" --print --trust --yolo --model auto` 单次任务成功
- [ ] `agent --continue -p "echo continue" --print --trust --yolo --model auto` 会话续期成功
- [ ] `agent mcp list` 显示 MCP 状态（如果配置了）
- [ ] `--help` 显示可用选项

## Rules for Hermes Agents

1. **自动化任务始终用 print 模式** — `agent -p "..." --print --trust --yolo --model auto`
2. **不要尝试在 tmux 中监控 Cursor 实时输出** — Cursor CLI 不支持流式，`capture-pane` 在任务结束前只能看到空白
3. **必须 `--model auto`** — 否则报 usage 限制
4. **认证必须用 `--api-key`** — 不接受 `CURSOR_API_KEY` 环境变量
5. **交互模式仅用于 slash 命令场景** — 需要 `/plan`、`/ask` 等交互时使用 tmux
6. **设置 `workdir`** — 保持 Cursor 聚焦在正确的项目目录
7. **tmux session 记得清理** — `tmux kill-session -t <name>`
