# Hermes Skills

[Hermes Agent](https://github.com/nousresearch/hermes-agent) 自定义技能仓库。

## 现有技能

### skill-publisher
安全发布本地 skill 到 GitHub，包含安全扫描 + 格式审核。

**分类：** productivity

**安装：**
```bash
hermes skills install buwenzheng/hermes-skills/skill-publisher
```

---

## 安装技能

```bash
hermes skills install <owner>/<repo>/<skill-name>
```

## 提交新技能

1. 在 `~/.hermes/skills/<分类>/<技能名>/` 下创建 skill
2. 确保包含有效的 `SKILL.md`（含 frontmatter）
3. 告诉 Hermes 运行 `skill-publisher`，并指定技能名称

## 仓库结构

```
hermes-skills/
├── README.md
└── <skill-name>/
    ├── SKILL.md
    └── README.md
```

所有 skill 均采用平铺结构（直接在根目录），不嵌套在 `skills/` 子目录下。

## 安全说明

发布前所有技能都会经过敏感信息扫描，详见 [skill-publisher](https://github.com/buwenzheng/hermes-skills/tree/main/skill-publisher)。
