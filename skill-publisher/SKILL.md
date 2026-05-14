---
name: skill-publisher
description: >-
  Use when the user asks to publish, push, push skill, 提交, 发布, 推送, 上传,
  or send a local Hermes skill to GitHub. Also triggers on "push 到 GitHub",
  "提交到 GitHub", "发布 skill", "推送 skill". Two-layer pre-check:
  automated regex scan (audit_scan.py) plus LLM deep review (agent reads code).
  Only proceeds if both layers APPROVED. Direct push to main, bumps version,
  isolates sensitive files, updates README.
version: 2.4.2
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

**未经 skill-audit 审核通过，一律不发布。** 脚本内置了 Step 0 自动跑 audit，审核不过直接终止，不依赖人记得手动跑。

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
3. 配置工作目录（写入 .env，脚本自动读取 HERMES_WORK_DIR）：
   ```bash
   echo 'HERMES_WORK_DIR=/home/hermes/hermes-work/default/hermes-skills' >> ~/.hermes/.env
   ```
   脚本优先使用 `--work-dir` 参数，其次读取 `HERMES_WORK_DIR` 环境变量，
   都没有则 clone 到 `/tmp/<skill>-push`。配好后无需每次传 `--work-dir`。

4. 确认目标 skill 已通过 `skill-audit` 审核（结果为 APPROVED）
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
# 使用现有工作目录（跳过 clone，避免网络超时）
python3 ~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py siyuan-custom --user buwenzheng --repo hermes-skills --work-dir ~/hermes-work/default/hermes-skills
```

脚本自动完成全部流程：
1. clone → 隔离敏感文件 → 版本号 bump（patch +1 或 `--version` 指定）
2. 更新 README.md（扫描仓库内所有 skill 目录，生成技能表格）
3. git add → staged grep 二次确认 → commit → push 到 main
4. GitHub API 验证 + PUBLISHED.md 自动更新

---

## 前置检查

发布前必须完成两层审核：

1. **自动化扫描（audit_scan.py）** — 脚本内置 Step 0a，自动执行，无需手动操作
2. **LLM 深度审核（agent 执行）** — Step 0b，agent 加载 `skill-audit`，按其 SKILL.md 中 "Step 2: LLM 深度审核" 的指引，读取目标 skill 的 SKILL.md 和所有脚本代码，自行判断安全/质量问题

两层都通过后才进入发布流程。

如果用户说"直接发布"而不先跑 audit，**拒绝并引导先跑审核**：

```
错误：未通过安全审核。
请先运行 skill-audit 对 <skill-name> 进行审核。
审核 APPROVED 后，再运行 skill-publisher。
```

---

## 完整流程

```
Step 0a: skill-audit 自动化扫描（脚本内置，audit_scan.py，APPROVED 才继续）
Step 0b: skill-audit LLM 深度审核（agent 读 SKILL.md + 脚本代码，自行判断）
    ↓ FAIL → 终止发布
Step 1: 确认仓库存在
    ↓
Step 1.5: 从 .env 读取 HTTP_PROXY / HTTPS_PROXY，写入 git config
    ↓
Step 2: 使用 HERMES_WORK_DIR 工作目录（或 clone）+ 复制 skill + 隔离敏感文件
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
| 0a | 安全审核（自动化）：脚本内置运行 `audit_scan.py`，不通过则终止发布 |
| 0b | 安全审核（LLM）：agent 加载 skill-audit，读取目标 skill 的 SKILL.md + 所有脚本代码，自行判断安全/质量问题。严重问题 → 终止发布 |
| 1 | 确认仓库存在 |
| 1.5 | 从 .env 读取 `HTTP_PROXY` / `HTTPS_PROXY`，写入 git config（clone 和 push 前自动设置） |
| 2 | 使用 `HERMES_WORK_DIR` 工作目录（或 clone）→ 复制 skill → 隔离敏感文件 |
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

**v2.3.0 变更记录**：见 `references/publish-skill-v2.3.0-changes.md`（--work-dir、--version、README 自动更新、代理从 .env 读取等）。
**v2.3.2 变更记录**：见 `references/publish-skill-v2.3.2-changes.md`（递归目录查找、修复 finally 误删工作目录、HERMES_WORK_DIR 环境变量）。
**v2.4.x 变更记录**：见 `references/proxy-pitfall.md`（subprocess 代理传递、LLM 审核步骤）。

---

## 常见陷阱（Common Pitfalls）

1. **~~跳过 audit 直接发布~~** — v2.3.3 起脚本内置 Step 0 自动跑 audit，审核不过直接终止。不再依赖人记得手动跑。如果 audit 脚本不存在（`~/.hermes/skills/productivity/skill-audit/scripts/audit_scan.py`），会警告但继续发布。

2. **用普通 git push 代替 skill-publisher** — 这是最高频的错误。用户说「push」「提交」时，不能直接 `git push`，必须走 audit → skill-publisher 流程。直接 push 会跳过：敏感文件隔离、版本号 bump、staged grep、README 更新、PUBLISHED.md 更新、curator pin。**skill-publisher 的 description 里明确写了触发词（push/提交/推送/上传），加载 skill 后按流程走。**

3. **audit 后改了代码** — 任何代码改动都必须重新跑 skill-audit。

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

17. **publish_skill.py 失效时的手动发布流程** — 脚本报错（网络/token）时，用现有仓库目录手动操作更可靠：
    ```
    cd ~/hermes-work/default/hermes-skills
    cp -r <skill-dir> ./
    rm -rf <skill>/__pycache__ <skill>/*_config.json <skill>/*_cache.json
    # 版本号：大版本用 sed 改 SKILL.md，小版本让脚本 bump
    sed -i 's/^version: X.Y.Z$/version: X.Y.(Z+1)/' <skill>/SKILL.md
    # 更新 README.md（扫描所有 skill 目录，重新生成表格）
    python3 -c "
    import re, os
    from pathlib import Path
    work = Path('.')
    skills = []
    for item in sorted(work.iterdir()):
        if not item.is_dir(): continue
        md = item / 'SKILL.md'
        if not md.exists(): continue
        c = md.read_text()
        fm = re.search(r'^---\s*\n(.*?)\n---', c, re.DOTALL)
        if not fm: continue
        f = fm.group(1)
        n = re.search(r'^name:\s*(\S+)', f, re.MULTILINE)
        v = re.search(r'^version:\s*(\S+)', f, re.MULTILINE)
        d = re.search(r'^description:\s*(.+)', f, re.MULTILINE)
        skills.append((n.group(1) if n else item.name, v.group(1) if v else '?', d.group(1).strip()[:60] if d else ''))
    tbl = '| Skill | 版本 | 说明 | 分类 |\n|-------|------|------|------|\n'
    tbl += '\n'.join(f'| [{s[0]}](./{s[0]}) | {s[1]} | {s[2]} | - |' for s in skills)
    readme = Path('README.md').read_text()
    readme = re.sub(r'(## 现有技能\n\n).*?(\n## )', f'\\1{tbl}\n\\2', readme, count=1, flags=re.DOTALL)
    Path('README.md').write_text(readme)
    print(f'✓ README.md updated ({len(skills)} skills)')
    "
    git add <skill>/ README.md
    git commit -m "..."
    GIT_ASKPASS=... git push origin main
    ```

18. **Skill 触发机制** — Hermes 的 skill 触发完全靠 LLM 匹配 SKILL.md frontmatter 中的 `description` 字段。LLM 看到的是 description 文本，不是 tags，不是关键词匹配。所以 description 必须包含用户可能使用的所有自然语言变体（中英文、push/publish/提交/推送/上传等）。如果用户说了某个词但 skill 没触发，第一件事就是检查 description 是否覆盖了那个词。

19. **版本号控制** — 不要手动改 SKILL.md 的版本号再让脚本 bump，脚本会多加一次。正确做法：大版本升级时用 `--version X.Y.Z` 指定，不传则自动 bump patch。

20. **run() 函数 stdout 为 None** — `subprocess.run` 在网络超时等场景下 stdout/stderr 可能为 None，直接切片 `[:300]` 会 TypeError。已修复为 `(result.stdout or '')[:300]`。

21. **用户说 "push" 不等于 git push** — "push skill"、"push 到 GitHub"、"提交"、"推送"、"上传" 都是 skill-publisher 的触发词。收到这些指令时 **脚本会自动先跑 skill-audit（Step 0），APPROVED 后继续发布**。不能当成普通 git push 直接操作。**这是最高频错误，多次被用户纠正。** 历史教训：2026-05-13 和 2026-05-14 用户说 push skill，agent 跳过了 audit 直接 publish 或 git push，用户明确指出这是错误的。v2.3.3 起 audit 已内置到脚本中。

22. **README.md 在每次发布时自动更新** — Step 2.7 会扫描仓库内所有 skill 目录，从 SKILL.md frontmatter 提取 name/version/description/category，重新生成"现有技能"表格。如果 README 中没有 `## 现有技能` 段落，脚本会警告但不中断。

23. **`--version` 指定版本 vs 自动 bump** — 不传 `--version` 时脚本自动 bump patch（1.0.0 → 1.0.1）。大版本/中版本升级时必须手动传 `--version 2.0.0`，否则会被脚本覆盖。不要在 SKILL.md 里手动改版本号再让脚本 bump，那样会多跳一个版本。

24. **YAML 多行 description（`>-` / `|`）在 README 更新时被截断** — `update_readme` 函数用正则提取 frontmatter 时，`description: >-` 只匹配到 `>-` 两个字符。v2.2.0 已修复：`_extract_desc()` 函数能识别 `>-`、`>`、`|`、`|-` 等 YAML 多行语法，收集后续缩进行拼接为完整描述（截断到 80 字符）。如果 description 仍然异常，检查 SKILL.md frontmatter 中 `description:` 后是否跟了正确的 YAML 多行标记。

25. **代理必须在 clone 前设置** — 代理配置（Step 1.5）必须在 Step 2 clone 之前执行，否则 clone 阶段不走代理会超时。代理地址从 .env 的 `HTTP_PROXY` / `HTTPS_PROXY` 读取，禁止硬编码。

26. **Skill 目录查找不支持分类子目录** — 脚本查找 skill 目录时，不能假设所有 skill 都在 `~/.hermes/skills/<name>/`。实际 skill 可能在 `~/.hermes/skills/<category>/<name>/`（如 `productivity/skill-publisher`）。v2.3.2 已修复：使用 `Path.rglob(name)` 递归搜索。如果仍找不到，检查 `~/.hermes/skills/` 下的目录结构。

27. **finally 块误删用户工作目录** — 旧版脚本的 `finally` 块会 `shutil.rmtree(work_dir)`，包括用户通过 `--work-dir` 或 `HERMES_WORK_DIR` 指定的现有仓库目录。v2.3.2 已修复：只删除脚本自己创建的临时目录（`/tmp/<skill>-push`），不删除用户指定的工作目录。如果发现工作目录被意外删除，检查脚本的 finally 逻辑是否正确区分了临时目录和用户目录。

28. **Skill 目录查找需递归搜索** — 脚本不能假设 skill 在 `~/.hermes/skills/<name>/`。实际可能在子目录如 `~/.hermes/skills/productivity/skill-publisher`。v2.3.3 已修复：用 `Path.rglob(name)` 递归搜索 `~/.hermes/skills/`。如果仍找不到，检查目录结构。

29. **HERMES_WORK_DIR 环境变量** — INT 步骤中配置 `HERMES_WORK_DIR` 到 `~/.hermes/.env`，脚本自动读取，无需每次传 `--work-dir`。配置方式：`echo 'HERMES_WORK_DIR=/home/hermes/hermes-work/default/hermes-skills' >> ~/.hermes/.env`。

30. **发布必须走两层审核** — Step 0a 自动化扫描（audit_scan.py）+ Step 0b LLM 深度审核（agent 读代码自行判断）。两层都通过才发布。不能只跑脚本不读代码，也不能只读代码不跑脚本。这是用户多次纠正的核心工作流。

31. **GIT_ASKPASS 认证方式** — push 使用 GIT_ASKPASS 注入 token，禁止嵌入 remote URL。脚本自动创建 `/tmp/git-askpass.sh`（chmod 700）。如果手动 push 需同样设置：`GIT_ASKPASS=/tmp/git-askpass.sh git push origin main`。

32. **代理必须在 push 前设置** — `export https_proxy=http://127.0.0.1:7890`，push 完后 `unset https_proxy`。代理地址从 .env 读取，禁止硬编码。

---

## 版本号策略

- **自动 bump patch**（默认）：适用于小修小改，1.0.0 → 1.0.1
- **`--version` 指定**：适用于大版本升级、功能重构，如 1.1 → 2.0.0
- **不要在 SKILL.md 里手动改版本号再让脚本 bump**：会导致版本号 +2（手动改的 + 脚本 bump 的）

## 禁止项

- 未经 skill-audit APPROVED 禁止发布
- 审核后改代码未重新审核禁止发布
- 禁止跳过 staged grep 二次确认
- 禁止 token 写入 .git/config
- 禁止 token 嵌入 git remote URL
