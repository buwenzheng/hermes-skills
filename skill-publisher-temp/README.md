# Skill Publisher

将本地 Hermes skill 安全发布到 GitHub，通过 PR 流程让所有改动透明可见。

## 依赖的 Skill

| 依赖 | 作用 |
|------|------|
| **skill-audit** | 发布前置审核，只有 APPROVED 才能继续 |
| **github-pr-workflow** | 本脚本底层 git 操作（clone / push / PR）参考其认证和 API 调用模式 |

## 前置条件

**必须先通过 `skill-audit` 审核并得到 APPROVED 结果。**

## 功能

- 强制二次确认 audit 结果
- 隔离敏感文件（`*_config.json` / `*.log` / `.env` 等）
- staged grep 二次扫描（12 个敏感 pattern）
- 版本号自动 bump（patch +1）
- **走 PR 流程**，所有改动通过 PR 可见
- PUBLISHED.md 更新纳入同一 PR
- GIT_ASKPASS 安全推送

## 使用

```
用户要求发布/推送某个已通过审核的 skill
    ↓
skill-publisher 执行（创建 PR）
    ↓
报告 PR URL
    ↓
用户确认后手动合并，或回复「合并」由 Agent 代为合并
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
Step 4: 创建 feat 分支
Step 5: git add + staged grep + commit
Step 6: push 分支到 origin
Step 7: 创建 PR（附带改动说明）
    ↓
报告 PR URL 给用户
    ↓
用户确认 → 合并 PR
```

## 合并后更新 PUBLISHED.md

PUBLISHED.md 的更新也在同一个 feat 分支里，合并时一起生效。

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
