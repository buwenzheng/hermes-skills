---
name: skill-audit
description: >-
  Use when the user asks to audit, scan, or review a local Hermes skill for security and format compliance.
  Two-layer audit: automated regex scan (audit_scan.py) plus LLM deep review (agent reads code and judges).
  Outputs a detailed audit report and suggests cleanup actions.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skill, audit, security, scanning, review]
    related_skills: [skill-publisher]
---

# Skill 安全审核工具

对本地 skill 进行安全扫描 + 格式审核，输出详细报告。**不修改本地文件**，只做检测和给出清理建议。隔离操作由 skill-publisher 在临时目录中自动处理。

## When to Use

用户要求审核/扫描/检查某个 skill 时。不是定时任务，不自动化。

## INT 初始化步骤

skill-audit 无需初始化，下载后直接使用。

若需单独运行扫描脚本：

```bash
python3 ~/.hermes/skills/productivity/skill-audit/scripts/audit_scan.py <skill-name>
# 例如
python3 ~/.hermes/skills/productivity/skill-audit/scripts/audit_scan.py siyuan
```

---

## 完整流程

```
用户指定 skill
    ↓
Step 1: 自动化扫描（audit_scan.py — 正则 + 格式）
    ↓ FAIL → 列出问题 → REJECTED
Step 2: LLM 深度审核（agent 读代码 + 人工判断）
    ↓ 严重问题 → 列出问题 → REJECTED
Step 3: 敏感文件报告（只检测，不修改本地文件）
Step 4: 复查（重新扫描）
    ↓ 干净 → APPROVED
```

---

## Step 1: 安全扫描

### 推荐方式：使用 Python 脚本

```bash
python3 ~/.hermes/skills/productivity/skill-audit/scripts/audit_scan.py ${SKILL_NAME}
# 示例
python3 ~/.hermes/skills/productivity/skill-audit/scripts/audit_scan.py siyuan
```

脚本同时检测：敏感信息、禁止文件、格式规范（Frontmatter / README / 正文结构）。

### 手动方式：分步检查

若不方便使用脚本，可分步执行：

#### 1.1 敏感信息扫描

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
  'token\s*[:=]\s*[\'"][a-zA-Z0-9_-]{16,}[\'"]'
  'token\s*[:=]\s*"[a-zA-Z0-9_-]{16,}"'
  'api[_-]?key\s*[:=]\s*[\'"][a-zA-Z0-9_-]{16,}[\'"]'
  'api[_-]?key\s*[:=]\s*"[a-zA-Z0-9_-]{16,}"'
  'password\s*[:=]\s*[\'"][^\'"]{8,}[\'"]'
  'password\s*[:=]\s*"[^"]{8,}"'
)
```

**⚠️ 重要：SKILL.md 也要参与扫描！** 历史教训：music-tag-web-mcp 的 SKILL.md 里有硬编码 token `yadixc2yyemqkv7jjk4gj`，如果 SKILL.md 被排除在扫描外就会漏报。audit_scan.py 当前版本已包含 SKILL.md，但手动扫描时注意不要排除。
for p in "${patterns[@]}"; do
  hits=$(grep -rnE "$p" . --exclude-dir=.git --exclude="SKILL.md" --include="*.py" --include="*.json" --include="*.sh" --include="*.yaml" --include="*.yml" --include="*.env" --include="*.toml" --include="*.txt" --include="*.conf" 2>/dev/null || true)
  [ -n "$hits" ] && { echo "MATCH: $p"; echo "$hits"; FOUND=1; }
done
[ "$FOUND" = "1" ] && echo "FAIL: sensitive data found, abort" && exit 1
```

#### 1.2 禁止文件检查

存在以下任意文件 → REJECTED：

```bash
FOUND_FORBIDDEN=0
for pattern in "*_config.json" "*_cache.json" "__pycache__" "*.pyc" ".env" "*.log" "credentials.json"; do
  hits=$(find . -name "$pattern" \( -type f -o -type d \) 2>/dev/null || true)
  [ -n "$hits" ] && { echo "FORBIDDEN: $hits"; FOUND_FORBIDDEN=1; }
done
[ "$FOUND_FORBIDDEN" = "1" ] && echo "FAIL: forbidden files found" && exit 1
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

### 2.4 配置文件路径规约

**配置文件和缓存文件必须存放在 skill 目录外**，禁止放在 `~/.hermes/skills/<name>/` 下（会被发布流程删除）。

| 类型 | 正确路径 | 说明 |
|------|----------|------|
| 配置文件 | `~/.config/<skill-name>/config` | init 时自动创建 |
| 缓存文件 | `~/.config/<skill-name>/cache.json` | 本地缓存 |

错误示例：`~/.hermes/skills/<name>/scripts/*_config.json`（会随 skill 发布导致 token 丢失）

正确示例：`~/.config/siyuan/config`（MoviePilot 等 skill 均采用此约定）

**init 命令要求**：
- 写入配置前检查是否已存在，存在则提示用户先删除：`rm -rf ~/.config/<skill-name>`
- 创建配置目录：`CONFIG_DIR.mkdir(parents=True, exist_ok=True)`

---

## Step 2: LLM 深度审核

自动化扫描只能检测正则匹配的模式和格式规范。**LLM 深度审核**由 agent 自身完成，不依赖外部 API 调用。

### 2.1 读取 skill 文件

```
用 read_file 读取目标 skill 目录下的：
1. SKILL.md — 完整内容
2. scripts/ 下所有 .py / .sh 文件 — 代码逻辑
3. references/ 下所有 .md 文件 — 参考文档
```

### 2.2 审核维度

逐项检查以下问题，发现则记录：

| 维度 | 检查内容 |
|------|----------|
| **硬编码凭证** | 正则扫不到的拼接方式：`"sk-" + "xxx"`、base64 编码的 key、从文件读取后未清理 |
| **危险操作** | `rm -rf`、`chmod 777`、`eval()`、`exec()`、`subprocess(shell=True)` + 用户输入 |
| **注入风险** | 用户输入直接拼接进 SQL/shell/HTTP 请求（f-string 构造命令等） |
| **过度权限** | 不必要的网络请求、读写 skill 目录外的敏感路径 |
| **数据泄露** | 可能将用户数据发送到第三方服务 |
| **错误处理** | 关键操作无 try/except、异常时静默失败 |
| **逻辑漏洞** | 竞态条件、缓存不一致、资源泄漏 |

### 2.3 判定标准

- **严重问题**（硬编码凭证、注入、危险操作）→ REJECTED
- **中等问题**（错误处理缺失、过度权限）→ WARNING，建议修复后发布
- **低风险**（代码风格、注释缺失）→ INFO，不阻塞发布

### 2.4 输出格式

```
■ LLM 深度审核
  - [严重] scripts/foo.py:42 — f-string 拼接 shell 命令，存在注入风险
  - [中等] scripts/bar.py:18 — HTTP 请求无超时设置
  - [低] scripts/baz.py:7 — 缺少 docstring
  → PASS / WARNING / FAIL
```

**FAIL → 终止发布。WARNING → 继续但输出建议。INFO → 记录但不阻塞。**

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

■ 自动化扫描: PASS / FAIL
  - 敏感信息: 未发现 / 发现 N 处
  - 禁止文件: 无 / 存在 <文件列表>
  - Frontmatter: 完整 / 缺失 <字段>
  - README.md: 存在 / 缺失
  - 正文结构: 完整 / 缺失 <章节>

■ LLM 深度审核: PASS / WARNING / FAIL
  - [严重] <问题描述>
  - [中等] <问题描述>
  - [低] <问题描述>

■ 敏感文件清理建议:
  - 建议隔离: <文件列表>
  - 建议模板化: <文件列表>
  - 建议替换凭证: <位置>

■ 最终判定: APPROVED / REJECTED
  - APPROVED → 可继续发布流程（运行 skill-publisher）
  - REJECTED → <失败原因>，请修复后重新审核
```

## 常见陷阱（Common Pitfalls）

1. **跳过硬扫直接发布** — 安全扫描是强制性前置步骤，任何时候都不可跳过。

2. **白名单含敏感词** — 白名单只能排除文档类文字（`${`、`#`、`prompt`、`help`、`description` 等）。`ghp_`/`sk-`/`AKIA` 等真实泄露模式严禁加入白名单。

3. **audit 修改本地文件** — audit 只检测不修改。隔离/剥离由 skill-publisher 在临时目录中处理，否则会破坏用户原始文件。

4. **审核通过后手动修改了文件** — 审核通过后若又改了代码，必须重新跑审核。

5. **禁止文件检查未中断** — `find` 命令列出文件后必须 `exit 1`，否则脚本继续执行并可能错误给出 APPROVED。

6. **token/api_key pattern 漏掉双引号格式** — `token\s*[:=]\s*['\'']...` 只匹配单引号包裹，漏掉 `siyuan_config.json` 类场景。必须同时覆盖单引号和双引号两种格式：`token\s*[:=]\s*"..."`。

6. **token/api_key pattern 漏掉双引号格式** — `token\\s*[:=]\\s*['\\'']...` 只匹配单引号包裹，漏掉 `siyuan_config.json` 类场景。必须同时覆盖单引号和双引号两种格式：`token\\s*[:=]\\s*\"...\"`。

7. **禁止文件检查未中断** — `find` 命令列出文件后必须 `exit 1`，否则脚本继续执行并可能错误给出 APPROVED。

8. **config/cache 文件在 skill 目录内** — `*_config.json` 和 `*_cache.json` 在 skill 内会被 skill-audit REJECTED，但即便 audit 通过，发布后 token 也会丢失。正确的做法是配置文件放在 `~/.config/<skill-name>/`，init 时自动创建（参见 Step 2.4 配置文件路径规约）。

9. **audit_scan.py 传目录而非文件** — 脚本依赖目录结构（需要读到 `SKILL.md`、`README.md`），传单个 `.py` 文件路径会错误地扫描其父目录。审计时必须传**目录路径**。脚本路径用 `~/.hermes/skills/productivity/skill-audit/scripts/audit_scan.py`。

    **skill 名称参数格式**：`audit_scan.py` 会在 `~/.hermes/skills/<传入名称>` 下查找 skill。传 `skill-publisher` → 找 `~/.hermes/skills/skill-publisher`；传 `productivity/skill-audit` → 找 `~/.hermes/skills/productivity/skill-audit`（嵌套在子目录里的 skill 才需要带路径前缀）。常用调用方式：

    ```bash
    # 直接用 skill 名（相对于 ~/.hermes/skills/）
    python3 ~/.hermes/skills/productivity/skill-audit/scripts/audit_scan.py chsrc

    # 带子目录前缀（嵌套分类下才需要）
    python3 ~/.hermes/skills/productivity/skill-audit/scripts/audit_scan.py productivity/skill-publisher
    ```

---

## 参考文件

- `references/hermes-skill-standard.md` — Hermès skill 结构规范（必填字段/正文章节/禁止内容）
- `references/github-proxy.md` — GitHub 操作代理配置
- `references/git-token-security.md` — Token 安全推送方式对比 + 泄露应急
- `scripts/audit_scan.py` — Python 自动化扫描脚本（推荐优先使用）
