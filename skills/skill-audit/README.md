# Skill Audit

对本地 Hermes skill 进行安全扫描和格式审核，输出详细报告。

## 功能

- 安全扫描：12 种敏感信息 pattern 检测
- 格式审核：frontmatter + README + 正文结构
- 敏感剥离：隔离文件 + 模板化 + 凭证替换
- 复查：清理后重新扫描确认

## 使用

```
当用户要求审核/扫描/检查某个 skill 时
```

## 审核流程

```
Step 1: 安全扫描（grep 敏感信息 + 禁止文件）
Step 2: 格式审核（frontmatter + 目录结构 + 正文结构）
Step 3: 敏感剥离（隔离/模板化/替换）
Step 4: 复查（重新扫描）
```

## 输出

输出 APPROVED / REJECTED 详细报告。APPROVED 才能继续发布。

## 目录结构

```
skill-audit/
├── SKILL.md      # 主文件
└── README.md     # 本文件
```
