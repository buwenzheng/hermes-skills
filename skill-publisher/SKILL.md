---
name: skill-publisher
description: >-
  Use when the user asks to publish, push, push skill, 提交, 发布, 推送, 上传,
  or send a local Hermes skill to GitHub. Also triggers on "push 到 GitHub",
  "提交到 GitHub", "发布 skill", "推送 skill". Reads the audit report from
  skill-audit, and only proceeds if the result is APPROVED. Direct push to main,
  bumps version, isolates sensitive files, updates README. Requires skill-audit
  APPROVED. Triggered manually — never automated.
version: 2.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skill, publishing, github, git, push, 提交, 推送, 上传, 发布]
    related_skills: [skill-audit]
required_environment_variables:
  - name: GITHUB_TOKEN
    prompt: GitHub Personal Access Token（需要有 repo 权限）
    help: 在 https://github.com/settings/tokens/new 生成，勾选 repo 权限
---

# Skill 发布工具

将本地 skill 发布到 GitHub。**前置条件：必须先通过 `skill-audit` 审核并得到 APPROVED 结果。**

## 核心原则

**未经 skill-audit 审核通过，一律不发布。**

---

## When to Use

用户说"发布"、"push"、"push skill"、"提交"、"推送"、"上传"某个 skill 到 GitHub 时。**"push"就是触发词，不是普通 git push。**

## INT 初始化步骤

1. 配置 GitHub Token（持久化到 .env，不依赖 export）：
   ```bash
   echo 'GITHUB_TOKEN=ghp_你的token' >> ~/.hermes/.env
   chmod 600 ~/.hermes/.env
   ```
   脚本会自动从 `~/.hermes/.env` 读取 `GITHUB_TOKEN`，无需手动 export。
2. 配置代理（写入 .env，脚本自动读取 HTTP_PROXY / HTTPS_PROXY）：
   ```bash
   echo 'HTTP_PROXY=http://127.0.0.1:7890' >> ~/.hermes/.env
   echo 'HTTPS_PROXY=http://127.0.0.1:7890' >> ~/.hermes/.env
   ```
   脚本在 clone 和 push 前自动从环境变量读取代理地址，写入 git config。
   **禁止在脚本中硬编码代理地址**，必须从 .env 读取。
3. 确认目标 skill 已通过 `skill-audit` 审核（结果为 APPROVED）
**飞书/聊天平台发布时**：token 会被日志截断（如 `ghp_IG...nJfb`），session 结束后无法恢复。必须先持久化到 .env，再发布。

### ⚠️ Token 安全配置（重要）

**1. `.env` 文件权限必须设为 600**（仅 owner 可读写）：
```bash
chmod 600 ~/.hermes/.env
ls -la ~/.hermes/.env  # 确认 -rw------- (600)
```

**2. 禁止将 token 嵌入 git remote URL**：
```bash
# ❌ 错误：https://ghp_xxx@github.com/...
# ✅ 正确：https://github.com/...  （token 通过 GIT_ASKPASS 注入）
git remote set-url origin https://github.com/user/repo.git
```

**3. 发布前验证 token 可用：**
```bash
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/buwenzheng/hermes-skills
# 返回 200 → token 有效
# 无输出或 401 → token 缺失或失效，需重新配置
```

如果 token 失效：用户重新生成 → 手动写入 `~/.hermes/.env`（不通过飞书传输），再 `export GITHUB_TOKEN`。

### 推荐方式：使用 Python 脚本（直接 push main）

```bash
python3 ~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py ${SKILL_NAME} --user ${USER} --repo ${REPO}
# 示例
python3 ~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py siyuan --user buwenzheng --repo hermes-skills
# 含分类前缀也可（自动平铺）
python3 ~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py mcp/music-tag-web-mcp --user buwenzheng --repo hermes-skills
# 指定版本号（如大版本升级，跳过自动 bump）
python3 ~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py siyuan-custom --user buwenzheng --repo hermes-skills --version 2.0.0
```

脚本自动完成全部流程：
1. clone → 隔离敏感文件 → 版本号 bump（patch +1 或 `--version` 指定）
2. 更新 README.md（扫描仓库内所有 skill 目录，生成技能表格）
3. git add → staged grep 二次确认 → commit → push 到 main
4. GitHub API 验证 + PUBLISHED.md 自动更新

---

## 前置检查

发布前必须确认：

1. **skill-audit 已跑过且 APPROVED** — 询问用户审核报告的 APPROVED 结果
2. **审核后代码没有再改动** — 如果改过，必须重新跑 skill-audit
3. **GITHUB_TOKEN 可用** — `curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/buwenzheng/hermes-skills` 返回 200

如果用户说"直接发布"而不先跑 audit，**拒绝并引导先跑审核**：

```
错误：未通过安全审核。
请先运行 skill-audit 对 <skill-name> 进行审核。
审核 APPROVED 后，再运行 skill-publisher。
```

---

## 完整流程

```
skill-audit APPROVED
    ↓
skill-publisher（直接 push main）
    ↓
Step 1: 确认仓库存在
    ↓
Step 1.5: 从 .env 读取 HTTP_PROXY / HTTPS_PROXY，写入 git config
    ↓
Step 2: clone + 复制 skill + 隔离敏感文件
    ↓
Step 2.5: 版本号 bump（patch +1 或指定版本）
    ↓
Step 2.7: 更新 hermes-skills/README.md（技能列表 + 版本号）
    ↓
Step 3: git add + staged grep 二次确认 + commit + push
    ↓
Step 4: GitHub API 验证
    ↓
Step 5: PUBLISHED.md 自动更新 + 第二次 push
    ↓
Step 6: 自动 pin 本机 skill（防止 curator 归档）
```

**注意：单人维护仓库直接 push main，不走 PR 流程。**

---

## 各 Step 说明

所有步骤由脚本自动执行，无需手动操作：

| Step | 说明 |
|------|------|
| 1 | 确认仓库存在 |
| 1.5 | 从 .env 读取 `HTTP_PROXY` / `HTTPS_PROXY`，写入 git config（clone 和 push 前自动设置） |
| 2 | clone → 复制 skill → 隔离敏感文件（`_config.json`/`*.log`/`.env` 等） |
| 2.5 | 版本号 bump（patch +1）或使用 `--version` 指定版本 |
| 2.7 | 更新 `README.md`：扫描仓库内所有 skill 目录，重新生成"现有技能"表格（名称、版本、说明、分类） |
| 3 | git add → staged grep 扫描 → commit → push 到 main |
| 4 | GitHub API 验证（确认文件已存在于远程） |
| 5 | PUBLISHED.md 自动更新 → 第二次 commit + push |
| 6 | `hermes curator pin <skill-name>` — 防止 curator 归档 |

**发布后自动 pin**：发布成功后自动执行 `hermes curator pin <skill-name>`，防止 curator 因不活跃而归档。如果 pin 失败（skill 不存在于本地），仅警告不中断。

脚本路径：`~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py`

**v2.2.0 修复记录**：见 `references/publish-skill-v2.2.0-changes.md`（触发词扩展、README 自动更新、.env 加载修复）。
**v2.1.1 修复记录**：见 `references/publish-skill-v2.1.1-fixes.md`（目录嵌套、代理硬编码、force-push 等 6 项修复）。

---

## 常见陷阱（Common Pitfalls）

1. **跳过 audit 直接发布** — 强制要求先有 APPROVED 结果。没有就是拒绝发布。

2. **audit 后改了代码** — 任何代码改动都必须重新跑 skill-audit。

3. **staged grep 只扫代码文件** — README.md 也可能含 token，必须扫描所有 staged 文件（除 SKILL.md 外）。

4. **GIT_ASKPASS 脚本权限不足** — 必须 `chmod 700`，`600` 缺执行位。

5. **token 嵌入 remote URL** — 禁止 `https://token@github.com`，用 GIT_ASKPASS 注入。历史教训：token 嵌入 URL 后 `git remote -v` 会暴露，且 REST API 调用会 401。

6. **skill 名含 `/`（分类前缀）时目标目录不存在** — `work_dir / "mcp/music-tag-web-mcp"` 会因父目录不存在而 `FileNotFoundError`。v2.1.1 已修复：脚本自动用 `skill_name.split('/')[-1]` 平铺目录，不保留分类前缀。

7. **PUBLISHED.md 表格格式被 `/` 破坏** — skill 名含 `/` 时 Markdown 表格列会错位。v2.1.1 已修复：PUBLISHED.md 中使用平铺后的名称。

8. **代理硬编码** — 旧版脚本中 `http.proxy` / `https.proxy` 硬编码为 `127.0.0.1:7890`。v2.1.1 已修复：新增 `get_proxy_config()` 自动从环境变量或 git config 读取。

9. **`--force-with-lease` 不必要** — 单人维护仓库正常 push 即可，无需 force。v2.1.1 已修复。

10. **subprocess 读不到 Hermes 的 .env 变量** — `publish_skill.py` 脚本开头已内建 `.env` 加载逻辑，会自动读取 `~/.hermes/.env` 并注入 `GITHUB_TOKEN`。如果仍报"缺少 GITHUB_TOKEN"，先确认 `.env` 格式正确（`GITHUB_TOKEN=ghp_...`，无引号，无空格）。

11. **clone 阶段网络超时（代理慢）** — `git clone --depth 1` 在代理条件下可能超过 120s 超时。可用已有工作目录绕过：`cd ~/hermes-work/default/hermes-skills && cp -r <skill-dir> ./ && git add . && git commit && git push`。

12. **audit_scan.py 传目录而非文件** — 审计时必须传**目录路径**：`<skill-dir>/`，不是 `.py` 文件路径。

13. **GitHub Token 在飞书日志中被截断** — session 结束后无法从日志恢复。必须将 token 持久化写入 `~/.hermes/.env`（`hermes config set GITHUB_TOKEN <token>`），不通过飞书传输。

14. **publish_skill.py 大函数重写宜整体** — 逐块 patch 容易在 try/finally 缩进处产生悬挂。正确做法：通读全函数后一次性重写整函数体，写完用 `python3 -c "import ast; ast.parse(open(f).read())"` 验证。

15. **PUBLISHED.md 更新失败不影响主发布** — PUBLISHED.md push 失败时警告但不中断主发布流程。

16. **自定义 skill 与官方同名冲突** — 发布官方 skill 的自定义版本时，必须先改名再首次发布（如 `siyuan` → `siyuan-custom`）。流程：`cp -r` 新目录 → 改 SKILL.md `name` 字段 → `rm -rf` 旧目录 → 在仓库中 `git rm -rf <旧名> && git add <新名>` → commit + push。同名发布后用户安装会装成官方版本。

17. **publish_skill.py 失效时的手动发布流程** — 脚本报错（网络/token）时，用现有仓库目录手动操作更可靠：`cd ~/hermes-work/default/hermes-skills && cp -r <skill-dir> ./ && rm -rf <skill>/__pycache__ <skill>/*_config.json <skill>/*_cache.json && sed -i 's/^version: X.Y.Z$/version: X.Y.(Z+1)/' <skill>/SKILL.md && git add <skill>/ && git commit -m "..." && GIT_ASKPASS=... git push origin main`。

18. **版本号控制** — 不要手动改 SKILL.md 的版本号再让脚本 bump，脚本会多加一次。正确做法：大版本升级时用 `--version X.Y.Z` 指定，不传则自动 bump patch。

19. **run() 函数 stdout 为 None** — `subprocess.run` 在网络超时等场景下 stdout/stderr 可能为 None，直接切片 `[:300]` 会 TypeError。已修复为 `(result.stdout or '')[:300]`。

18. **用户说 "push" 不等于 git push** — "push skill"、"push 到 GitHub"、"提交"、"推送" 都是 skill-publisher 的触发词。收到这些指令时必须加载 skill-publisher 并走完整流程（audit → publish），不能当成普通 git push 直接操作。历史教训：2026-05-13 用户说 push siyuan-custom，agent 跳过了 audit 和 publish 直接 git push，用户明确指出这是错误的。

19. **README.md 在每次发布时自动更新** — Step 2.7 会扫描仓库内所有 skill 目录，从 SKILL.md frontmatter 提取 name/version/description/category，重新生成"现有技能"表格。如果 README 中没有 `## 现有技能` 段落，脚本会警告但不中断。

20. **`--version` 指定版本 vs 自动 bump** — 不传 `--version` 时脚本自动 bump patch（1.0.0 → 1.0.1）。大版本/中版本升级时必须手动传 `--version 2.0.0`，否则会被脚本覆盖。不要在 SKILL.md 里手动改版本号再让脚本 bump，那样会多跳一个版本。

21. **YAML 多行 description（`>-` / `|`）在 README 更新时被截断** — `update_readme` 函数用正则提取 frontmatter 时，`description: >-` 只匹配到 `>-` 两个字符。v2.2.0 已修复：`_extract_desc()` 函数能识别 `>-`、`>`、`|`、`|-` 等 YAML 多行语法，收集后续缩进行拼接为完整描述（截断到 80 字符）。如果 description 仍然异常，检查 SKILL.md frontmatter 中 `description:` 后是否跟了正确的 YAML 多行标记。

---

## 禁止项

- 未经 skill-audit APPROVED 禁止发布
- 审核后改代码未重新审核禁止发布
- 禁止跳过 staged grep 二次确认
- 禁止 token 写入 .git/config
- 禁止 token 嵌入 git remote URL
