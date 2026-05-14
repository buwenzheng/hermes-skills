# Hermes Skills

[Hermes Agent](https://github.com/nousresearch/hermes-agent) 自定义技能仓库。

## 现有技能

| Skill | 版本 | 说明 | 分类 |
|-------|------|------|------|
| [chsrc](./chsrc) | 1.0.1 | chsrc 换源工具，通过自动测速为各种编程语言/OS/软件切换到国内最快镜像源 | productivity |
| [hermes-config](./hermes-config) | 1.1.0 | Use when modifying Hermes Agent configuration, including adding providers, chang | uncategorized |
| [music-tag-web-mcp](./music-tag-web-mcp) | 1.0.2 | "Use when querying or editing music file metadata (tags, genres, titles, artists | uncategorized |
| [siyuan-custom](./siyuan-custom) | 1.3.1 | Use when the user asks about, queries, searches, creates, edits, or manages cont | uncategorized |
| [skill-audit](./skill-audit) | 1.1.0 | Use when the user asks to audit, scan, or review a local Hermes skill for securi | uncategorized |
| [skill-publisher](./skill-publisher) | 2.4.5 | Use when the user asks to publish, push, push skill, 提交, 发布, 推送, 上传, or send a l | uncategorized |

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
