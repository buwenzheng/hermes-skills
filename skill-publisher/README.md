# Skill Publisher

将本地 Hermes skill 安全发布到 GitHub。

## 前置条件

**必须先通过 `skill-audit` 审核并得到 APPROVED 结果。**

## 功能

- 读取 audit 结果，强制二次确认
- .gitignore 追加
- staged grep 二次确认（完整 12 个 pattern）
- GIT_ASKPASS 安全推送
- GitHub API 验证

## 使用

```
当用户要求发布/推送/提交某个已通过审核的 skill 时
```

## 审核后流程

```
skill-audit APPROVED
    ↓
skill-publisher
    ↓
Step 1: .gitignore
Step 2: staged grep 二次确认
Step 3: commit + push
Step 4: API 验证
```

## 目录结构

```
skill-publisher/
├── SKILL.md      # 主文件
└── README.md     # 本文件
```

## 安全原则

未经 skill-audit APPROVED，一律不发布。
