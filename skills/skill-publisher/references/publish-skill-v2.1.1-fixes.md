# publish_skill.py v2.1.1 修复记录

## 修复日期：2026-05-08

## 修复列表

### 1. `capture=False` 参数错误（🔴 硬 Bug）
**现象**：`TypeError: run() got an unexpected keyword argument 'capture'`
**原因**：`run()` 自定义 wrapper 只接受 `cmd` 和 `cwd`，但脚本多处调用 `run(..., capture=False)`
**修复**：给 `run()` 添加 `capture_output: bool = True` 参数

### 2. git clone 后目录创建路径错误（🔴 硬 Bug）
**现象**：`FileNotFoundError: [Errno 2] No such file or directory: '/tmp/mcp/music-tag-web-mcp-push/mcp/music-tag-web-mcp'`
**原因**：skill_name 含 `/`（如 `mcp/music-tag-web-mcp`），`target = work_dir / skill_name` 创建嵌套路径，父目录不存在
**修复**：`target.parent.mkdir(parents=True, exist_ok=True)` + 最终方案改用 `flat_name = skill_name.split('/')[-1]` 平铺

### 3. 代理硬编码（🟡 改进）
**现象**：`_git_config(work_dir, key, 'http://127.0.0.1:7890')` 硬编码代理地址
**修复**：新增 `get_proxy_config()` 函数，从 `http_proxy` 环境变量或 `git config --global http.proxy` 自动读取

### 4. `--force-with-lease` 不必要（🟡 改进）
**现象**：单人维护仓库用 force push 没必要，且可能覆盖远程其他提交
**修复**：改为普通 `git push origin main`

### 5. PUBLISHED.md 表格格式被 `/` 破坏（🟡 改进）
**现象**：`| mcp/music-tag-web-mcp | 1.0.2 |` 导致 Markdown 表格列错位
**修复**：PUBLISHED.md 中使用 `flat_name`（平铺后的名称）

### 6. commit message 自动判断 add vs update（🟢 优化）
**实现**：push 前通过 GitHub API 检查 `SKILL.md` 是否已存在，动态选择 `feat: add` 或 `feat: update`

## 测试验证

- `music-tag-web-mcp`（含分类前缀）：平铺发布成功 ✅
- `skill-publisher`（无前缀）：正常发布成功 ✅
- `hermes-config`（新 skill）：首次发布成功 ✅

## 踩坑过程

1. 第一次运行 `publish_skill.py` 时 `capture=False` 报错 → 修复参数
2. 第二次运行时目录创建 `FileNotFoundError` → 添加 `parent.mkdir`
3. `parent.mkdir` 位置错误导致 `SyntaxError` → 重新调整缩进
4. git push 需要 token → 从 remote URL 提取，发现 REST API 401
5. 最终手动用 `git remote set-url` + `git push` 完成发布
6. 重写整个脚本彻底修复所有问题
