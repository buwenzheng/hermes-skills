# Skill Publisher

将本地 Hermes skill 安全发布到 GitHub。

## 依赖的 Skill

| 依赖 | 作用 |
|------|------|
| **skill-audit** | 发布前置审核，只有 APPROVED 才能继续 |

## 前置条件

**必须先通过 `skill-audit` 审核并得到 APPROVED 结果。**

## 功能

- 强制二次确认 audit 结果
- 隔离敏感文件（`*_config.json` / `*.log` / `.env` 等）
- staged grep 二次扫描（12 个敏感 pattern）
- 版本号自动 bump（patch +1）
- PUBLISHED.md 自动更新
- GIT_ASKPASS 安全推送

## 使用

```
用户要求发布/推送某个已通过审核的 skill
    ↓
skill-publisher 执行
    ↓
直接 push main
    ↓
报告完成（commit hash、版本、文件链接）
```

## 发布流程

```
skill-audit APPROVED
    ↓
skill-publisher
    ↓
Step 1: 确认仓库存在
Step 2: clone + 复制 skill + 隔离敏感文件
Step 3: 版本号 bump（patch +1）
Step 4: git add + staged grep + commit + push
Step 5: GitHub API 验证
Step 6: PUBLISHED.md 更新 + 第二次 push
```

## 目录结构

```
skill-publisher/
├── SKILL.md               # 主文件
├── README.md              # 本文件
└── scripts/
    └── publish_skill.py   # 发布脚本
```

## 安全原则

- 未经 skill-audit APPROVED，一律不发布
- 禁止跳过 staged grep 二次确认
- 禁止 token 写入 .git/config
- 禁止在 .gitignore 就绪前执行 git add
