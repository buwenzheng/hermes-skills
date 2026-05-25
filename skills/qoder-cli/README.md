# Qoder CLI Skill

Qoder CLI 是一款 AI 编程助手 CLI 工具，支持代码生成、审查、重构、Subagent 管理、MCP 服务集成等。

## 文件结构

```
qoder-cli/
├── SKILL.md    # 主技能文件
└── README.md   # 本文档
```

## 基本使用

- 安装：`curl -fsSL https://qoder.com/install | bash`
- 启动：`qodercli`
- 登录：`/login` 或设置 `QODER_PERSONAL_ACCESS_TOKEN` 环境变量

## 触发场景

- 用户提及 `qodercli`、`qoder cli`、AI 编程助手
- 代码审查、生成、重构请求
- 斜杠命令：`/review`、`/init`、`/agents`、`/commands`、`/skills`、`/mcp` 等
- 管理 Subagent、自定义命令、Skill、Hook、MCP 服务

## 更多信息

详见 `SKILL.md`。