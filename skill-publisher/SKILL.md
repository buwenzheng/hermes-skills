---
name: skill-publisher
description: Use when the user asks to package and publish a local Hermes skill to GitHub. Handles security audit, sensitive data removal, format review, .gitignore setup, and token-authenticated push. Triggered manually by the user specifying which skill to publish — never automated.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skill, packaging, publishing, security, github, audit]
    related_skills: [hermes-agent-skill-authoring]
required_environment_variables:
  - name: GITHUB_TOKEN
    prompt: GitHub Personal Access Token（需要有 repo 权限）
    help: 在 https://github.com/settings/tokens/new 生成，勾选 repo 权限
---

# Skill 发布工具（安全审核版）

将本地 skill 封装成符合 Hermes 标准格式，通过安全+格式双重审核后，才能发布到 GitHub。

## INT 初始化步骤（新用户首次使用）

1. 确保 `GITHUB_TOKEN` 已配置（在 `.env` 或通过 `hermes setup`）
2. 确认目标 GitHub 仓库存在，或准备好创建新仓库
3. 用户指定要发布的 skill 名称
4. 按流程执行审核

## 核心原则

**审核不通过，一律不发布。**

流程：安全扫描 → 格式审核 → 修复复查 → 发布

---

## 何时触发

用户明确指定要发布的 skill 名称时。不是定时任务，不自动化。

---

## 完整流程

```
用户指定 skill
    ↓
Step 1: 安全扫描（grep 扫敏感信息）
    ↓ 存在敏感信息 → 列出文件+位置 → 中断
Step 2: 格式审核（frontmatter + 结构 + README + ENV声明）
    ↓ 缺失项 → 列出缺失内容 → 中断
Step 3: 敏感剥离（删缓存、删config、转template）
    ↓
Step 4: 复查（重新扫描一遍）
    ↓ 仍有问题 → 中断
Step 5: 写入 .gitignore（在 git add 前）
    ↓
Step 6: git add + grep 二次确认
    ↓ 仍有敏感 → 中断
Step 7: git commit + push 到 GitHub
    ↓
Step 8: 验证（curl GitHub API 确认文件存在）
```

---

## Step 1: 安全扫描

### 扫描命令

```bash
cd ~/.hermes/skills/<skill-name>
grep -rnE "token\s*[:=]\s*[\"'][a-zA-Z0-9_-]{16,}[\"']" .
grep -rnE "api[_-]?key\s*[:=]\s*[\"'][a-zA-Z0-9_-]{16,}[\"']" .
grep -rnE "password\s*[:=]\s*[\"'][^\"']{8,}[\"']" .
grep -rnE "ghp_[a-zA-Z0-9]{36}" .
grep -rnE "sk-[a-zA-Z0-9]{48}" .
```

### 额外检查文件级泄露

```bash
# 扫描禁止文件（存在即拒发）
find . -name "*_config.json" -type f
find . -name "*_cache.json" -type f
find . -name "__pycache__" -type d
find . -name "*.pyc" -type f
find . -name ".env" -type f
find . -name "*.log" -type f
find . -name "credentials.json" -type f
```

### 敏感信息判断标准

| 模式 | 阈值 | 说明 |
|------|------|------|
| `ghp_` 前缀 | 36字符 | GitHub PAT |
| `sk-` 前缀 | 48字符 | OpenAI API Key |
| `sk-` 前缀 | 50+字符 | 其他 LLM API Key |
| `token` / `api_key` | ≥16字符 | 自定义 Token |
| `password` | ≥8字符 | 密码字段 |

**任意一项命中 → 审核不通过，列出具体文件+行号，中断发布流程。**

### ⚠️ Grep 误报处理

grep pattern 会匹配到 SKILL.md 文档里的变量引用（如 `${GITHUB_TOKEN}`）和说明文字（如 `ghp_ 前缀`），**不是真实泄露**。

**区分方法**：排除以下情况的命中
```
${...}       # 变量占位符
# ...        # 注释行
description  # frontmatter 字段
prompt/help   # 提示文本
Authorization # HTTP 头
git remote   # git 命令
```

**二次确认正确姿势**：
```bash
# 宽泛扫描（记录所有命中）
grep -rnE "token|api_key|ghp_|sk-|password\s*[:=]" .

# 过滤文档（排除上面的白名单词后看是否还有真实泄露）
grep -rnE "token|api_key|ghp_|sk-|password\s*[:=]" . \
  | grep -vE '\$\{|#|description|prompt|help|prefix|Authorization|git remote|GITHUB_TOKEN'

# 如果过滤后无输出 = 干净；有输出 → 逐条核查
```

---

## Step 2: 格式审核

### 2.1 Frontmatter 检查

读取 SKILL.md 前 50 行，解析 YAML frontmatter。缺失任意一项 → 审核不通过：

| 字段 | 要求 |
|------|------|
| `name` | 必须，小写+连字符，≤64字符 |
| `description` | 必须，≤1024字符，以 "Use when" 或中文 "当" 开头 |
| `version` | 必须，格式 `X.Y.Z` |
| `metadata.hermes.tags` | 必须，非空数组 |
| `required_environment_variables` | 如 skill 涉及 API key 必须声明 |

### 1.2 GitHub 目录结构（重要）

**必须使用平铺结构，不沿用本地分类**：

```
hermes-skills-repo/
├── .gitignore
├── skill-publisher/
│   ├── SKILL.md
│   └── README.md
├── siyuan/
│   ├── SKILL.md
│   └── README.md
└── another-skill/
    ├── SKILL.md
    └── README.md
```

每个 skill 一个根目录，`skills/category/skill-name/` 这种本地结构**不要照搬到 GitHub**。

### 2.3 正文内容检查

SKILL.md 正文（不含 frontmatter）必须包含：

| 内容 | 说明 |
|------|------|
| `## INT` 或 `## 初始化` | 新用户首次使用引导步骤 |
| `## When to Use` 或 `## 何时使用` | 触发条件 |
| `## Common Pitfalls` 或 `## 避坑` | 常见错误 |

---

## Step 3: 敏感剥离

按以下优先级处理：

### 3.1 禁止文件（一律删除）

```bash
find . -name "*_config.json" -type f -delete      # 用户真实配置
find . -name "*_cache.json" -type f -delete      # 缓存数据
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -type f -delete
find . -name "*.pyo" -type f -delete
find . -name ".env" -type f -delete
find . -name "*.log" -type f -delete
find . -name "credentials.json" -type f -delete
```

### 3.2 模板化（转为 .template.json）

如果有 `*_config.json` 存在，但内容合理（如含占位符），可转为 `<name>.template.json` 保留结构。

### 3.3 脚本内凭证替换

scripts/*.py 中的硬编码凭证替换为 `${VAR_NAME}`：

```python
# 替换前
api_key = "sk-real-key-here"

# 替换后
api_key = "${API_KEY}"
```

---

## Step 4: 复查

重新跑 Step 1 的所有扫描命令，确认干净。

**发现问题 → 中断，不发布。**

---

## Step 5: 写入 .gitignore

**必须在 git add 前写入**，否则敏感文件进暂存区后即使加 .gitignore 也无法从历史清除。

**用 `>>` 追加，不要覆盖**，避免丢失仓库已有的 .gitignore 内容：

```bash
# 追加到 .gitignore（已有内容不会被覆盖）
cat >> /tmp/${SKILL_NAME}-push/.gitignore << 'EOF'
# 敏感文件
**/*_config.json
**/*_cache.json
**/credentials.json
# Python
**/__pycache__/
**/*.pyc
**/*.pyo
# OS
.DS_Store
EOF
```

---

## Step 6: git add + 二次确认

```bash
git add .
git diff --cached --name-only | head -50

# 只检查新增行（^+ ），排除删除行（^- ）和文档注释
git diff --cached --no-color | grep '^+' | grep -v '^+++' | \
  grep -iE "token|api_key|ghp_|sk-|password\s*[:=]" | \
  grep -vE '(\$\{|#|description|prompt|help|prefix|Authorization|git remote|GITHUB_TOKEN|grep.*token|echo.*\$\{|cat.*EOF|旧方式|示例)' \
  && echo "FAIL: sensitive data found in staged files" && exit 1
```

**grep 有输出 → 中断，不发布。**

---

## Step 7: GitHub 发布

### 7.1 确认目标仓库

```bash
curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/repos/${USER}/${REPO} | jq -r '.full_name // .message'
```

- **404** → 需要先创建仓库（见 7.2）
- **返回 repo 名** → 仓库存在，直接推送（见 7.3）

### 7.2 创建仓库（如不存在）

```bash
curl -s -X POST -H "Authorization: token ${GITHUB_TOKEN}" \
  -d '{"name":"hermes-skills","private":true,"description":"Hermes Agent custom skills"}' \
  https://api.github.com/user/repos | jq -r '.full_name // .message'
```

### 7.3 推送到 GitHub

**目录结构必须是 flat（平铺），每个 skill 一个根目录**：

```
hermes-skills-repo/
├── .gitignore
├── skill-name-1/
│   ├── SKILL.md
│   └── README.md
└── skill-name-2/
    ├── SKILL.md
    └── README.md
```

推送步骤：

```bash
# 1. clone 到临时目录（--depth 1 减少数据）
git clone --depth 1 https://github.com/${USER}/hermes-skills.git /tmp/${SKILL_NAME}-push

# 2. 创建 skill 目录（flat 结构，直接放根目录）
mkdir -p /tmp/${SKILL_NAME}-push/${SKILL_NAME}
cp -r ~/.hermes/skills/${SKILL_NAME}/* /tmp/${SKILL_NAME}-push/${SKILL_NAME}/

# 3. .gitignore 追加（不要覆盖，用户可能已有自定义规则）
cat >> /tmp/${SKILL_NAME}-push/.gitignore << 'EOF'
# 敏感文件
**/*_config.json
**/*_cache.json
**/credentials.json
# Python
**/__pycache__/
**/*.pyc
**/*.pyo
# OS
.DS_Store
EOF

# 4. git add → 二次确认（只检查新增行，过滤删除行和文档注释）→ commit → push
cd /tmp/${SKILL_NAME}-push
git add .
git diff --cached --name-only

# 只检查新增行（^+ ），排除删除行（^- ）和文档文字
git diff --cached --no-color | grep '^+' | grep -v '^+++' | \
  grep -iE "token|api_key|ghp_|sk-|password\s*[:=]" | \
  grep -vE '(\$\{|#|description|prompt|help|prefix|Authorization|git remote|GITHUB_TOKEN)' \
  && echo "FAIL: sensitive data in staged files" && exit 1

git commit -m "feat: add ${SKILL_NAME}"

# 用 GIT_ASKPASS 方式推送，token 不写入 .git/config
export GIT_ASKPASS=/tmp/git-askpass.sh
cat > /tmp/git-askpass.sh << 'EOF'
#!/bin/bash
echo "${GITHUB_TOKEN}"
EOF
chmod +x /tmp/git-askpass.sh
git push origin main --force-with-lease
```

---

## Step 8: 验证

```bash
curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/${USER}/hermes-skills/contents/<skill-name>/SKILL.md" \
  | jq -r '.sha // .message'
```

- 返回 sha → **发布成功**
- 返回 404 → **发布失败，检查错误**

---

## 审核决策表

```
扫描结果          格式结果           行动
─────────────────────────────────────────
干净              完整               → 发布
干净              缺失 README        → 中断，补完再发布
干净              缺失 frontmatter    → 中断，补完再发布
发现敏感信息       任意               → 中断，列出位置，不发布
敏感已清理        完整               → 发布
```

---

## 常见陷阱（Common Pitfalls）

1. **把本地 `skills/category/skill-name/` 结构照搬到 GitHub** — 本地 skills 目录有分类，GitHub 上必须平铺，每个 skill 直接放在根目录。否则安装命令 `hermes skills install owner/repo/skill-name` 无法识别。

2. **pre-add grep 太宽泛** — `${TOKEN}` 变量引用、`token` 字段说明文字会误报。用排除词（`${`、`#`、`prompt`、`help`）过滤后再判断。

3. **README.md 遗漏** — 审核时漏查 README，导致外部用户看不懂 skill 用途。

4. **推送后不验证** — 认为 push 成功就是成功了。必须 curl GitHub API 确认文件真的存在。

5. **token 嵌在 remote URL 里 push** — 旧方式 `https://token@github.com` 会把 token 永久写入 `.git/config`。改用 `GIT_ASKPASS` 方式推送（见 Step 7.3），token 不落盘。若已误用，立刻检查 `git log` 确认 token 没残留在 commit 历史，然后 `git filter-branch` + force push + 轮换 token。

6. **用 `--force` 覆盖远程** — 直接 `--force` 会抹掉远程其他内容。改用 `--force-with-lease`，只有确认本地领先远程时才强制推送。

## 禁止项

- 禁止跳过安全扫描直接发布
- 禁止在 .gitignore 就绪前执行 git add
- 禁止在二次 grep 确认前执行 git push
- 禁止在 SKILL.md 正文中出现真实 API Key（只允许 `${VAR_NAME}` 占位符）
- 禁止在 scripts/ 中 hardcode 凭证
- 禁止发布任何包含 `ghp_` / `sk-` 前缀的文件

---

## 输出模板

审核完成后，向用户报告：

```
=== Skill 安全审核报告 ===
Skill: <name>
版本: <version>

■ 安全扫描: PASS / FAIL
  - 敏感信息: 未发现 / 发现 N 处
  - 禁止文件: 无 / 存在 <文件列表>

■ 格式审核: PASS / FAIL
  - Frontmatter: 完整 / 缺失 <字段>
  - README.md: 存在 / 缺失
  - 正文结构: 完整 / 缺失 <章节>

■ 最终判定: APPROVED / REJECTED
  - APPROVED → 已推送至 GitHub
  - REJECTED → <失败原因>，请修复后重试
```
