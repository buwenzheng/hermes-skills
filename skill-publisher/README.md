# Skill Publisher

将本地 Hermes skill 安全发布到 GitHub 的工具。

## 功能

- 安全扫描：检测 token、API key、密码等敏感信息
- 格式审核：检查 frontmatter、README、正文结构
- 敏感剥离：删除缓存、配置，模板化
- GitHub 发布：创建仓库 + push + 验证

## 目录结构

```
skill-publisher/
├── SKILL.md      # 主文件（含完整审核流程）
└── README.md     # 本文件
```

## 使用方式

当用户指定要发布的 skill 名称时，运行 `skill-publisher` skill。

## 安全原则

审核不通过，一律不发布。禁止项：
- 跳过安全扫描直接发布
- 在 .gitignore 就绪前执行 git add
- 跳过二次 grep 确认直接 push
- 在文档中暴露真实 API Key
