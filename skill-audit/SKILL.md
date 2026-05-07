---
name: skill-audit
description: Use when the user asks to audit, scan, or review a local Hermes skill for security and format compliance. Performs security scan, format review, outputs a detailed audit report, and suggests cleanup actions for sensitive files. Triggered manually — never automated.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skill, audit, security, scanning, review]
    related_skills: [skill-publisher]
---

# Skill 安全审核工具

对本地 skill 进行安全扫描 + 格式审核，输出详细报告。**不修改本地文件**，只做检测和给出清理建议。隔离操作由 skill-publisher 在临时目录中自动处理。

## 何时触发

用户要求审核/扫描/检查某个 skill 时。不是定时任务，不自动化。

---

## 完整流程

```
用户指定 skill
    ↓
Step 1: 安全扫描（grep 扫敏感信息）
    ↓ 发现敏感 → 列出位置 → REJECTED
Step 2: 格式审核（frontmatter + 结构 + README + 正文结构）
    ↓ 缺失项 → 列出缺失 → REJECTED
Step 3: 敏感剥离（隔离文件 + 模板化 + 凭证替换）
Step 4: 复查（重新扫描）
    ↓ 干净 → APPROVED
```

---

## Step 1: 安全扫描

### 扫描命令

```bash
cd ~/.hermes/skills/${SKILL_NAME}

# 扫描敏感信息（只扫当前 skill 目录，不影响其他 skill）
patterns=(
  'ghp_[a-zA-Z0-9]{36}'
  'github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}'
  'sk-[a-zA-Z0-9]{48}'
  'sk-proj-[a-zA-Z0-9]{48,}'
  'sk-ant-[a-zA-Z0-9]{32,}'
  'AKIA[0-9A-Z]{16}'
  'ASIA[0-9A-Z]{16}'
  'AIza[0-9A-Za-z_-]{35}'
  'AccountKey=[a-zA-Z0-9+/=]{88}'
  'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'
  'token\s*[:=]\s*["\x27][a-zA-Z0-9_-]{16,}["\x27]'
  'api[_-]?key\s*[:=]\s*["\x27][a-zA-Z0-9_-]{16,}["\x27]'
  'password\s*[:=]\s*["\x27][^"'\'']{8,}["\x27]'
)
FOUND=0
for p in "${patterns[@]}"; do
  hits=$(grep -rnE "$p" . --exclude-dir=.git --exclude="SKILL.md" --include="*.py" --include="*.json" --include="*.sh" --include="*.yaml" --include="*.yml" --include="*.env" --include="*.toml" --include="*.txt" --include="*.conf" 2>/dev/null || true)
  [ -n "$hits" ] && { echo "MATCH: $p"; echo "$hits"; FOUND=1; }
done
[ "$FOUND" = "1" ] && echo "FAIL: sensitive data found, abort" && exit 1
```

### 禁止文件检查

存在以下任意文件 → REJECTED：

```bash
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
| `ghp_` | 36字符 | GitHub PAT |
| `github_pat_` | 81字符 | GitHub Fine-grained PAT |
| `sk-` | 48字符 | OpenAI API Key |
| `sk-proj-` / `sk-ant-` | 32+字符 | 其他 LLM API Key |
| `AKIA` / `ASIA` | 16字符 | AWS Access Key |
| `AIza` | 35字符 | Google API Key |
| `eyJ...` | - | JSON Web Token |
| `token` / `api_key` | ≥16字符 | 自定义 Token |
| `password` | ≥8字符 | 密码字段 |

**任意命中 → REJECTED，列出文件+行号，不发布。**

### Grep 误报处理

如果扫描结果疑似误报（如文档里的示例命令），用白名单验证：

```bash
grep -rnE "token|api_key|ghp_|sk_|password" . \
  | grep -vE '^(\$\{|description|prompt|help|prefix|Authorization|git remote|GITHUB_TOKEN|grep.*token|echo.*\$\{|cat.*EOF|示例|旧方式|references/)'

# 无输出 = 干净；有输出 → 逐条核查
```

> **警告：敏感词 ghp_/sk_/AKIA 等绝对不能加入白名单，否则静默漏报。**

---

## Step 2: 格式审核

### 2.1 Frontmatter 检查

读取 SKILL.md 前 50 行，解析 YAML frontmatter。缺失任意一项 → REJECTED：

| 字段 | 要求 |
|------|------|
| `name` | 必须，小写+连字符，≤64字符 |
| `description` | 必须，≤1024字符，以 "Use when" 或中文 "当" 开头 |
| `version` | 必须，格式 `X.Y.Z` |
| `metadata.hermes.tags` | 必须，非空数组 |
| `required_environment_variables` | 如 skill 涉及 API key 必须声明 |

### 2.2 目录结构

检查本地 skill 目录结构必须包含：

```
<skill-name>/
├── SKILL.md      ← 必须
└── README.md     ← 必须
```

> 注意：本地 `skills/category/skill-name/` 分类结构**不**影响审核，GitHub 发布时会自动平铺。

### 2.3 正文内容检查

SKILL.md 正文（不含 frontmatter）必须包含：

| 内容 | 说明 |
|------|------|
| `## INT` 或 `## 初始化` | 新用户首次使用引导步骤 |
| `## When to Use` 或 `## 何时使用` | 触发条件 |
| `## Common Pitfalls` 或 `## 避坑` | 常见错误 |

---

## Step 3: 敏感文件报告

**不修改本地文件**，只列出建议清理的文件，由用户确认或交给 skill-publisher 处理：

```bash
echo "⚠️ 以下文件建议清理（发布前由 skill-publisher 自动处理）："
find . -name "*_config.json" -type f
find . -name "*_cache.json" -type f
find . -name "__pycache__" -type d
find . -name "*.pyc" -type f
find . -name ".env" -type f
find . -name "*.log" -type f
find . -name "credentials.json" -type f
echo "skill-publisher 会在临时目录中自动隔离并排除这些文件"
```

### 3.2 模板化建议

如果 `*_config.json` 内容合理（含占位符），可以转为 `<name>.template.json` 保留结构。

### 3.3 凭证替换建议

scripts/*.py 中若有硬编码凭证，建议替换为 `${VAR_NAME}`。

---

## Step 4: 复查

重新跑 Step 1 的所有扫描命令，确认干净。发现问题 → REJECTED。

---

## 输出模板

审核完成后，向用户报告：

```bash
VERSION=$(grep -m1 '^version:' ~/.hermes/skills/${SKILL_NAME}/SKILL.md | awk '{print $2}')
```

```
=== Skill 安全审核报告 ===
Skill: ${SKILL_NAME}
版本: ${VERSION}

■ 安全扫描: PASS / FAIL
  - 敏感信息: 未发现 / 发现 N 处
  - 禁止文件: 无 / 存在 <文件列表>

■ 格式审核: PASS / FAIL
  - Frontmatter: 完整 / 缺失 <字段>
  - README.md: 存在 / 缺失
  - 正文结构: 完整 / 缺失 <章节>

■ 敏感文件清理建议:
  - 建议隔离: <文件列表>
  - 建议模板化: <文件列表>
  - 建议替换凭证: <位置>

■ 最终判定: APPROVED / REJECTED
  - APPROVED → 可继续发布流程（运行 skill-publisher）
  - REJECTED → <失败原因>，请修复后重新审核
```

---

## 常见陷阱（Common Pitfalls）

1. **跳过硬扫直接发布** — 安全扫描是强制性前置步骤，任何时候都不可跳过。

2. **白名单含敏感词** — 白名单只能排除文档类文字（`${`、`#`、`prompt`、`help`、`description` 等）。`ghp_`/`sk-`/`AKIA` 等真实泄露模式严禁加入白名单。**注意：ERE 中 `|` 是或逻辑，不是字面量 `|`。**

3. **audit 修改本地文件** — audit 只检测不修改。隔离/剥离由 skill-publisher 在临时目录中处理，否则会破坏用户原始文件。

4. **审核通过后手动修改了文件** — 审核通过后若又改了代码，必须重新跑审核。

5. **macOS grep 不支持 `\x27`** — 单引号转义在 macOS BSD grep 里不工作，改用 `[^"']`。

6. **password pattern 里的 `[^"'\']`** — 在 shell 单引号中 `\'` 表示转义的单引号字符，实际解析为排除了 `\` 和单引号，可能截断含反斜杠的密码匹配。建议统一用 `[^"']`。

---

## 参考文件

- `references/github-proxy.md` — GitHub 操作代理配置
- `references/git-token-security.md` — Token 安全推送方式对比 + 泄露应急
