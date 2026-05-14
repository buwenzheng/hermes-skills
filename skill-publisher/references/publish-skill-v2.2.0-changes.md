# publish_skill.py v2.2.0 变更记录

日期：2026-05-14

## 变更内容

### 1. 触发词扩展（frontmatter）
- description 从 "publish" 扩展为包含 push、push skill、提交、发布、推送、上传、发到 GitHub 等中英文关键词
- tags 新增：push、提交、推送、上传、发布
- **原因**：用户实际说的是 "push"，但触发描述只有 "publish"，导致 agent 跳过了 skill 加载

### 2. 新增 Step 2.7：更新 README.md
- 发布前自动扫描仓库内所有 skill 目录
- 从每个 SKILL.md 的 frontmatter 提取 name、version、description、category
- 用正则替换 README.md 中 `## 现有技能` 到下一个 `##` 之间的表格内容
- 如果 README 中没有 `## 现有技能` 段落，警告但不中断

### 3. 新增 .env 加载逻辑
- 脚本开头添加 `_load_dotenv()` 函数
- 从 `~/.hermes/.env` 读取环境变量并注入 `os.environ`
- 之前 SKILL.md 声称有此功能但脚本实际缺失

## 新增 Pitfalls
- #18: "push" 是 skill-publisher 触发词，不等于 git push
- #19: README.md 在每次发布时自动更新
