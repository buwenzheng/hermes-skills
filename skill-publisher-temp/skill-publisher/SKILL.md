---
name: skill-publisher
description: Use when the user asks to publish a local Hermes skill to GitHub. Reads the audit report from skill-audit, and only proceeds if the result is APPROVED. Creates a PR for review (not direct push to main), bumps version, isolates sensitive files, and reports the PR URL to the user. Requires skill-audit APPROVED and github-pr-workflow for git operations. Triggered manually — never automated.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skill, publishing, github, git]
    related_skills: [skill-audit, github-pr-workflow]
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

用户说"发布"、"push"或"提交"某个 skill 时，且该 skill 已通过 `skill-audit` 审核。

## INT 初始化步骤

1. 配置 GitHub Token（环境变量或 `~/.netrc`）：
   ```bash
   export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
   ```
2. 确保代理可用（如需访问 GitHub）：
   ```bash
   git config --global http.proxy http://127.0.0.1:7890
   git config --global https.proxy http://127.0.0.1:7890
   ```
3. 确认目标 skill 已通过 `skill-audit` 审核（结果为 APPROVED）

### ⚠️ Token 必须持久化存储

飞书等聊天平台会截断日志中的 token（如 `ghp_IG...nJfb`），session 结束后无法恢复。

**发布 skill 前必须确认 token 可用：**
```bash
# 检查 token 是否已持久化
grep -r 'ghp_' ~/.hermes/ 2>/dev/null | grep -v '.log:' | grep -v '__pycache__'
# 或直接测试
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/buwenzheng/hermes-skills
# 返回 200 → token 有效
# 无输出或 401 → token 缺失或失效，需重新配置
```

如果 token 失效：用户重新生成 → 通过加密渠道发来 → **手动写入 `~/.hermes/.env`**（不通过飞书传输），再 `export GITHUB_TOKEN`。

### 推荐方式：使用 Python 脚本（PR 模式）

```bash
python3 ~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py ${SKILL_NAME} --user ${USER} --repo ${REPO}
# 示例
python3 ~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py siyuan --user buwenzheng --repo hermes-skills
```

脚本自动完成全部流程：
1. clone → 隔离敏感文件 → 版本号 bump
2. 创建 feat 分支 → commit → push
3. **创建 PR**（PR URL 报告给用户）
4. PUBLISHED.md 更新纳入同一 PR

合并由用户决定，不自动合并。

---

## 前置检查

发布前必须确认：

1. **skill-audit 已跑过且 APPROVED** — 询问用户审核报告的 APPROVED 结果
2. **审核后代码没有再改动** — 如果改过，必须重新跑 skill-audit

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
skill-publisher（走 PR 模式）
    ↓
Step 1: 确认仓库存在
    ↓
Step 2: clone + 复制 skill + 隔离敏感文件
    ↓
Step 3: 版本号 bump（patch +1）
    ↓
Step 4: 创建 feat 分支
    ↓
Step 5: git add + staged grep 二次确认 + commit
    ↓
Step 6: push 分支
    ↓
Step 7: 创建 PR（报告 URL 给用户）
    ↓
用户确认后合并，或回复「合并」由 Agent 代为合并
```

**注意：发布后不直接合并 main，通过 PR 让所有改动可见。**

---

## 各 Step 说明

所有步骤由脚本自动执行，无需手动操作：

| Step | 说明 |
|------|------|
| 1 | 确认仓库存在 |
| 2 | clone → 复制 skill → 隔离敏感文件（`_config.json`/`*.log`/`.env` 等） |
| 3 | 版本号 bump（patch +1），写入克隆目录，不动本地文件 |
| 4 | 创建 `feat/add-{skill}-v{version}` 分支 |
| 5 | git add → staged grep 扫描 → commit |
| 6 | push 分支到 origin |
| 7 | 通过 GitHub REST API 创建 PR，报告 URL |

脚本路径：`~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py`

---

## 合并流程（用户确认后）

用户回复「合并」后，调用 `github-pr-workflow` 合并步骤：

```bash
# squash merge + delete branch
gh pr merge {PR_NUMBER} --squash --delete-branch

# 或 curl 方式
curl -X PUT \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/repos/${USER}/${REPO}/pulls/{PR_NUMBER}/merge \
  -d '{"merge_method": "squash"}'
```

---

## 常见陷阱（Common Pitfalls）

1. **跳过 audit 直接发布** — 强制要求先有 APPROVED 结果。没有就是拒绝发布。

2. **audit 后改了代码** — 任何代码改动都必须重新跑 skill-audit。

3. **staged grep 只扫代码文件** — README.md 也可能含 token，必须扫描所有 staged 文件（除 SKILL.md 外）。

4. **GIT_ASKPASS 脚本权限不足** — 必须 `chmod 700`，`600` 缺执行位。

5. **token 嵌入 remote URL** — 禁止 `https://token@github.com`，用 GIT_ASKPASS。

6. **用 `--force` 而非 `--force-with-lease`** — 直接 force 会抹掉远程其他内容。

7. **subprocess 读不到 Hermes 的 .env 变量** — `os.environ.get('GITHUB_TOKEN')` 可能返回空。脚本优先用 `--token` 参数显式传递。

8. **clone 阶段网络超时（代理慢）** — `git clone --depth 1` 在代理条件下可能超过 120s 超时。可用已有工作目录绕过：`cd ~/hermes-work/default/hermes-skills && cp -r <skill-dir> ./ && git add . && git commit && git push`。

9. **audit_scan.py 传目录而非文件** — 审计时必须传**目录路径**：`<skill-dir>/`，不是 `.py` 文件路径。

10. **GitHub Token 在飞书日志中被截断** — session 结束后无法从日志恢复。必须将 token 持久化写入 `~/.hermes/.env`（`hermes config set GITHUB_TOKEN <token>`），不通过飞书传输。

11. **publish_skill.py 大函数重写宜整体** — 逐块 patch 容易在 try/finally 缩进处产生悬挂。正确做法：通读全函数后一次性重写整函数体，写完用 `python3 -c "import ast; ast.parse(open(f).read())"` 验证。

12. **PUBLISHED.md 更新失败不影响主发布** — PUBLISHED.md push 失败时警告但不中断主发布流程。

13. **禁止直接 push 到 main** — 必须走 PR 流程。

---

## 禁止项

- 未经 skill-audit APPROVED 禁止发布
- 审核后改代码未重新审核禁止发布
- 禁止跳过 staged grep 二次确认
- 禁止 token 写入 .git/config
- **禁止直接 push 到 main**，必须走 PR 流程
