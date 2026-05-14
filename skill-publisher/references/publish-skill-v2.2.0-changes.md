# v2.2.0 变更记录

**日期**: 2026-05-14

## 变更内容

### 1. 触发描述扩展（frontmatter）
- description 从 "Use when the user asks to publish a local Hermes skill to GitHub"
  扩展为包含：push, push skill, 提交, 发布, 推送, 上传, push 到 GitHub, 提交到 GitHub, 发布 skill, 推送 skill
- tags 新增：push, 提交, 推送, 上传, 发布

### 2. 新增 `--version` 参数
- 用法：`publish_skill.py <skill> --version 2.0.0`
- 传了 `--version` → 直接使用指定版本，不自动 bump
- 不传 `--version` → 自动 bump patch（1.0.0 → 1.0.1）
- 大版本/中版本升级必须手动指定，否则会被脚本覆盖

### 3. 新增 Step 2.7：README.md 自动更新
- 每次发布前扫描仓库内所有 skill 目录
- 从 SKILL.md frontmatter 提取 name/version/description/category
- 重新生成"现有技能"表格替换 README.md 对应段落
- 支持 YAML 多行 description（`>-`、`|` 等语法）

### 4. 修复 .env 加载逻辑
- 脚本之前缺少 .env 加载代码（SKILL.md 声称有但实际没有）
- 新增 `_load_dotenv()` 函数，启动时自动读取 `~/.hermes/.env`
- 不覆盖已存在的环境变量

### 5. 修复 YAML 多行 description 解析
- `update_readme` 原先用正则 `^description:\s*(.+)` 只能匹配单行
- 遇到 `>-` 会截断为两个字符
- 新增 `_extract_desc()` 函数，识别 `>-`/`>`/`|`/`|-` 并收集后续缩进行

## 根因

用户问"为什么上次 push 没有触发 audit 跟 push skill"——
agent 在 2026-05-13 直接 git push 了 siyuan-custom，
跳过了 skill-audit + skill-publisher 完整流程。
根本原因是 skill-publisher 的 description 没有覆盖 "push" 这个触发词。
