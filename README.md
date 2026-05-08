# Hermes Skills

[Hermes Agent](https://github.com/nousresearch/hermes-agent) 自定义技能仓库。

## 现有技能

| Skill | 版本 | 说明 | 分类 |
|-------|------|------|------|
| [siyuan](./siyuan) | 1.0.0 | 思源笔记基础知识库 | note-taking |
| [skill-audit](./skill-audit) | 1.0.0 | Skill 安全/格式审查 | productivity |
| [skill-publisher](./skill-publisher) | 2.1.1 | Skill 发布到 GitHub | productivity |
| [chsrc](./chsrc) | 1.0.1 | 换源工具（自动测速切换镜像源） | chsrc |
| [music-tag-web-mcp](./music-tag-web-mcp) | 1.0.2 | Music Tag Web MCP 音乐元数据管理 | mcp |
| [hermes-config](./hermes-config) | 1.0.1 | Hermes 配置管理经验库 | autonomous-ai-agents |

## 安装技能

```bash
hermes skills install buwenzheng/hermes-skills/<skill-name>
```

## 提交新技能

1. 在 `~/.hermes/skills/<分类>/<技能名>/` 下创建 skill
2. 确保包含有效的 `SKILL.md`（含 frontmatter）和 `README.md`
3. 运行 `skill-audit` 审核通过后，用 `skill-publisher` 发布

## 仓库结构

```
hermes-skills/
├── README.md
├── PUBLISHED.md          # 发布记录
├── .gitignore
├── <skill-name>/         # 平铺结构，不嵌套
│   ├── SKILL.md
│   └── README.md
└── ...
```

## 安全说明

发布前所有技能都会经过 `skill-audit` 敏感信息扫描，详见 [skill-publisher](./skill-publisher)。
