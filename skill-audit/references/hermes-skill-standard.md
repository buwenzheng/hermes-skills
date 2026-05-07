# Hermès Skill 规范标准

本文档记录 Hermès skill 的结构规范和审核标准，用于 skill-audit 和 skill-publisher 的格式核查。

## 必须元素（Mandatory Elements）

### Frontmatter 必填字段

| 字段 | 要求 | 说明 |
|------|------|------|
| `name` | 必须 | 小写 + 连字符（`skill-name`），≤64字符，与目录名一致 |
| `description` | 必须 | ≤1024字符，以 `Use when` 或中文 `当` 开头 |
| `version` | 必须 | 格式 `X.Y.Z` |
| `tags` | 必须 | 非空数组，`metadata.hermes.tags` |
| `required_environment_variables` | 如涉及 API key 必须声明 | 每个变量含 `name` + `prompt` + `help` |

### 正文结构（SKILL.md）

| 章节 | 触发关键词 | 说明 |
|------|-----------|------|
| INT / 初始化 | `## INT` 或 `## 初始化` | 新用户首次使用引导步骤（必须可运行） |
| When to Use / 何时使用 | `## When to Use` 或 `## 何时使用` | 触发条件，非自动化 |
| Common Pitfalls / 避坑 | `## Common Pitfalls` 或 `## 避坑` | 常见错误和禁忌 |
| 正文内容 | - | 与 skill 定位匹配，不是空壳 |

### 目录结构

```
<skill-name>/
├── SKILL.md      ← 必须
├── README.md     ← 必须
├── references/   ← 可选，支撑文档
└── scripts/      ← 可选，自动化脚本
```

### 禁止内容（Hard Reject）

- 含真实 API key / token / password 硬编码
- `*_config.json` 含真实凭据
- `__pycache__/`、`.env`、`.log`、`credentials.json`
- Frontmatter 缺失 `name` / `description` / `version` 任一

## 敏感信息判断标准

| 模式 | 阈值 | 说明 |
|------|------|------|
| `ghp_` | 36字符 | GitHub PAT |
| `github_pat_` | 81字符 | GitHub Fine-grained PAT |
| `sk-` | 48字符 | OpenAI API Key |
| `sk-proj-` / `sk-ant-` | 32+字符 | 其他 LLM API Key |
| `AKIA` / `ASIA` | 16字符 | AWS Access Key |
| `AIza` | 35字符 | Google API Key |
| `eyJ...eyJ...eyJ...` | - | JSON Web Token |
| `token= '...'` 或 `token="..."` | ≥16字符 | 自定义 Token |
| `api_key= '...'` 或 `api_key="..."` | ≥16字符 | API Key |
| `password= '...'` 或 `password="..."` | ≥8字符 | 密码字段 |

> **注意**：ERE 中 `\'` = 字面量单引号（ERE 不支持字符类内转义），`\'` in `['\'']` = 单引号或反斜杠。
> token/api_key/password 检测需同时覆盖单引号和双引号两种格式，防止 `siyuan_config.json` 类场景漏报。

## 模板化建议

```
❌ config.json（含 "api_token": "real_value"）
✅ config.template.json（含 "api_token": "${API_TOKEN}"）
```

## 参考

- `scripts/audit_scan.py` — Python 自动化扫描脚本（推荐优先使用）
