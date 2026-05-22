# skill-publisher v2.3.0 变更记录

## 2026-05-14 会话变更

### 新增功能

1. **`--work-dir` 参数**：跳过 clone，直接使用现有仓库工作目录
   - 传了 → `git pull` 拉最新，不 clone
   - 没传 → 保持原行为（clone 到 /tmp）
   - 解决了代理慢导致 clone 超时的问题

2. **`--version` 参数**：指定版本号，不自动 bump
   - 大版本升级时用 `--version 2.0.0`
   - 不传则自动 bump patch（1.0.0 → 1.0.1）

3. **Step 2.7：自动更新 README.md**
   - 扫描仓库内所有 skill 目录
   - 从 SKILL.md frontmatter 提取 name/version/description/category
   - 重新生成"现有技能"表格
   - 支持 YAML 多行 description（`>-`、`|` 等语法）

4. **Step 1.5：代理配置从 .env 读取**
   - 读取 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量
   - 写入 git config（clone 和 push 前自动设置）
   - 禁止在脚本中硬编码代理地址

### Bug 修复

1. **YAML 多行 description 解析**：`_extract_desc()` 函数能识别 `>-`、`>`、`|`、`|-` 等 YAML 多行语法
2. **`run()` 函数 stdout 为 None**：subprocess 超时时 stdout 可能为 None，已修复切片逻辑
3. **重复 `quarantine.mkdir` 调用**：已清理

### 用户纠正

1. **"push skill" ≠ git push**：用户说 "push" 是指发布 skill 到 GitHub，不是 git push。必须走 audit → publish 流程。
2. **版本号控制**：不要手动改 SKILL.md 版本号再让脚本 bump，会导致 +2。大版本用 `--version` 指定。
3. **手动发布也要更新 README**：即使脚本挂了用手动流程，也要包含 README 更新步骤。

### 手动发布流程（脚本失效时）

```bash
cd ~/hermes-work/default/hermes-skills
cp -r <skill-dir> ./
rm -rf <skill>/__pycache__ <skill>/*_config.json <skill>/*_cache.json
# 版本号
sed -i 's/^version: X.Y.Z$/version: X.Y.(Z+1)/' <skill>/SKILL.md
# 更新 README（用 Python 脚本扫描所有 skill）
python3 -c "..."
git add <skill>/ README.md
git commit -m "..."
GIT_ASKPASS=... git push origin main
```

### 代理配置

`.env` 文件需包含：
```
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

脚本通过 `_load_dotenv()` 自动读取，无需手动 export。
