---
name: skill-publisher
description: Use when the user asks to publish a local Hermes skill to GitHub. Reads the audit report from skill-audit, and only proceeds if the result is APPROVED. Performs git add, staged grep check, commit, and token-authenticated push. Triggered manually — never automated.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skill, publishing, github, git]
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

## 何时触发

用户说"发布"、"push"或"提交"某个 skill 时，且该 skill 已通过 `skill-audit` 审核。

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
确认 skill-audit APPROVED
    ↓
Step 1: 写入 .gitignore（在 git add 前）
    ↓
Step 2: git add + staged grep 二次确认
    ↓ 仍有敏感 → 中断
Step 3: git commit + push 到 GitHub
    ↓
Step 4: 验证（curl GitHub API 确认文件存在）
```

---

## Step 1: 写入 .gitignore

**必须在 git add 前写入**，否则敏感文件进暂存区后即使加 .gitignore 也无法从历史清除。

**用 `>>` 追加，不覆盖**：

```bash
WORK_DIR="/tmp/${SKILL_NAME}-push"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# 追加 .gitignore（先加空行避免粘连）
echo "" >> "$WORK_DIR/.gitignore"
cat >> "$WORK_DIR/.gitignore" << 'EOF'
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

## Step 2: git add + 二次确认

```bash
cd "$WORK_DIR"
git add .
git diff --cached --name-only | head -50

# 只检查 staged 的代码文件，排除 markdown
STAGED_CODE=$(git diff --cached --name-only | grep -iE '\.(py|json|sh|yaml|yml|env|toml|txt|conf)$' || true)
[ -z "$STAGED_CODE" ] && echo "无代码文件需要扫描" && exit 0

while read f; do
  grep -nE "ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}|sk-[a-zA-Z0-9]{48}|sk-proj-[a-zA-Z0-9]{48,}|sk-ant-[a-zA-Z0-9]{32,}|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|AccountKey=[a-zA-Z0-9+/=]{88}|eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*|token\s*[:=]\s*[\"'][a-zA-Z0-9_-]{16,}[\"']|api[_-]?key\s*[:=]\s*[\"'][a-zA-Z0-9_-]{16,}[\"']|password\s*[:=]\s*[\"'][^\"']{8,}[\"']" "$f" && {
    echo "FAIL: sensitive data in $f"
    exit 1
  }
done <<< "$STAGED_CODE"
```

> **pattern 必须和 skill-audit Step 1 完全一致，漏任何一个都是漏洞。**

---

## Step 3: GitHub 发布

### 3.1 确认仓库存在

```bash
REPO_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/${USER}/${REPO}")
if [ "$REPO_EXISTS" != "200" ]; then
  echo "仓库不存在，请先在 GitHub 上创建 ${USER}/${REPO}"
  exit 1
fi
```

### 3.2 clone + 复制 skill

```bash
git clone --depth 1 "https://github.com/${USER}/${REPO}.git" "$WORK_DIR"
mkdir -p "$WORK_DIR/${SKILL_NAME}"
cp -r ~/.hermes/skills/${SKILL_NAME}/. "$WORK_DIR/${SKILL_NAME}/"
```

### 3.3 commit + push

```bash
cd "$WORK_DIR"
git add .
git diff --cached --name-only

# 二次确认（代码文件完整 pattern）
STAGED_CODE=$(git diff --cached --name-only | grep -iE '\.(py|json|sh|yaml|yml|env|toml|txt|conf)$' || true)
[ -z "$STAGED_CODE" ] && echo "无代码文件需要扫描" && exit 0
while read f; do
  grep -nE "ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}|sk-[a-zA-Z0-9]{48}|sk-proj-[a-zA-Z0-9]{48,}|sk-ant-[a-zA-Z0-9]{32,}|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|AccountKey=[a-zA-Z0-9+/=]{88}|eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*|token\s*[:=]\s*[\"'][a-zA-Z0-9_-]{16,}[\"']|api[_-]?key\s*[:=]\s*[\"'][a-zA-Z0-9_-]{16,}[\"']|password\s*[:=]\s*[\"'][^\"']{8,}[\"']" "$f" && {
    echo "FAIL: sensitive data in $f"
    exit 1
  }
done <<< "$STAGED_CODE"

git commit -m "feat: add ${SKILL_NAME}"

# GIT_ASKPASS 方式推送，token 不落盘
export GIT_ASKPASS=/tmp/git-askpass.sh
cat > /tmp/git-askpass.sh << 'EOF'
#!/bin/bash
echo "${GITHUB_TOKEN}"
EOF
chmod 700 /tmp/git-askpass.sh

# 本地检测分支名，不走网络
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||' || echo "main")
git push origin "$DEFAULT_BRANCH" --force-with-lease
```

---

## Step 4: 验证

```bash
curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/${USER}/${REPO}/contents/${SKILL_NAME}/SKILL.md" \
  | jq -r '.sha // .message'
```

- 返回 sha → **发布成功**
- 返回 404 → **发布失败**

---

## 输出模板

```
=== Skill 发布报告 ===
Skill: ${SKILL_NAME}
审核状态: APPROVED（已通过 skill-audit）

■ 发布: SUCCESS / FAIL
  - 分支: <branch>
  - Commit: <sha>

■ 验证: PASS / FAIL
  - GitHub 文件: 存在 / 不存在

■ 最终结果: SUCCESS / FAIL
  - SUCCESS → 已推送至 GitHub
  - FAIL → <错误原因>
```

---

## 常见陷阱（Common Pitfalls）

1. **跳过 audit 直接发布** — 强制要求先有 APPROVED 结果。没有就是拒绝发布。

2. **audit 后改了代码** — 任何代码改动都必须重新跑 skill-audit。

3. **staged grep pattern 不完整** — 必须和 skill-audit Step 1 完全一致。

4. **`echo | while read` subshell exit** — `exit 1` 只杀 subshell，必须用 `while read ... done <<< "$VAR"`。

5. **GIT_ASKPASS 脚本权限不足** — 必须 `chmod 700`，`600` 缺执行位。

6. **token 嵌入 remote URL** — 禁止 `https://token@github.com`，用 GIT_ASKPASS。

7. **用 `--force` 而非 `--force-with-lease`** — 直接 force 会抹掉远程其他内容。

---

## 禁止项

- 未经 skill-audit APPROVED 禁止发布
- 审核后改代码未重新审核禁止发布
- 禁止跳过 staged grep 二次确认
- 禁止 token 写入 .git/config
