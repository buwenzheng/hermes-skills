---
name: siyuan-custom
description: >-
  Use when the user asks about, queries, searches, creates, edits, or manages
  content in SiYuan Note (思源笔记). Also triggers on: siyuan, 思源, 笔记查询,
  搜索笔记, 查文档, 建块, 块引用, 嵌入块, 模板, 闪卡, 思源 API,
  思源笔记操作, siyuan api. Covers both conceptual questions and practical
  operations (query, search, create, update, delete blocks via API).
version: 1.2.5
tags: [siyuan, 思源, 笔记, knowledge-management, 搜索, 查询, 块操作]
required_environment_variables:
  - name: SIYUAN_API_URL
    prompt: 思源笔记 API 地址（如 http://127.0.0.1:6806）
    help: 在思源笔记「设置 → 关于 → API Token」中查看
  - name: SIYUAN_API_TOKEN
    prompt: 思源笔记 API Token
    help: 在思源笔记「设置 → 关于 → API Token」中创建并复制 Token
---

# 思源笔记技能指南

## INT 初始化步骤（新用户首次使用）

1. 运行初始化命令：
   ```bash
   python3 scripts/siyuan_api.py init <API URL> <Token>
   ```
   例如：
   ```bash
   python3 scripts/siyuan_api.py init http://127.0.0.1:6806 your_token_here
   ```
   初始化会自动：
   - 写入 `~/.config/siyuan/config`（配置文件，不随 skill 发布）
   - 写入 `~/.config/siyuan/cache.json`（缓存文件）
   - 验证连接并预热缓存

> **注意**：如果远程访问思源，API URL 应填写实际可访问的地址（如 `http://192.168.1.100:6806`），确保Hermes所在机器能连通该端口。

思源笔记是一款基于内容块的隐私优先知识管理工具。本技能提供核心操作指南，涵盖内容块管理、模板开发、API 交互和闪卡系统。

## When to Use / 何时使用

当用户询问以下内容时使用本 skill：
- 思源笔记的基本概念（内容块、块引用、嵌入块）
- API 原理或特定端调用
- 块操作语法（插入、更新、删除、移动）
- 模板开发或 Sprig 模板语法
- 闪卡系统的使用和导出
- 文档/笔记本的创建、搜索、导出操作
- 获取文档内容（`export_md` vs `get_file` 的选择）

**不要在以下情况使用**：用户只是普通聊天、询问其他笔记工具、或与思源无关的知识问答。

## Common Pitfalls / 避坑

1. **`ping` 命令内部走 `/api/system/version`**：脚本 `ping` 命令调用 `/api/system/version`，返回 `{"code":0,"data":"3.6.5"}` 表示正常。如需直接验证连通性，可用 curl 调 `/api/system/version`。
2. **`get_ids_by_hpath` 需要 notebook 参数**：`/api/filetree/getIDsByHPath` 需要同时传 `notebook` 和 `path`。CLI 签名：`get_ids_by_hpath <笔记本ID> <hpath>`。返回值 `data` 可能是列表 `["id1","id2"]` 或 null。
3. **`get_file` ≠ 读文档内容**：两者是两套路径系统。读文档正文用 `export_md <文档ID>`；`get_file` 用的是工作区物理路径 `/data/<笔记本ID>/<文档路径>.sy`。
4. **`put_file` 使用 multipart/form-data**：`/api/file/putFile` 不能用 JSON body，必须用 multipart 上传。
5. **`create_doc` 多行内容**：命令行传入多行内容时换行符会被转义。若需多行内容，先 `create_doc` 创建空文档，再用 `update_block` 写入。
6. **缓存不随 skill 发布**：`~/.config/siyuan/cache.json` 是本地缓存文件，不随 skill 发布。脚本默认使用本地缓存，用 `--no-cache` 可强制直连 API。
7. **Terminal 与 execute_code 沙箱视图不一致**：始终用 terminal 工具操作脚本文件，不要依赖 execute_code 沙箱读写同一路径。
8. **`export_resources` 需要工作区完整路径**：`/api/export/exportResources` 的 `paths` 参数必须是 `/data/<笔记本ID>/<目录名>` 格式，不是 hpath。脚本已自动转换。
9. **`notebook` vs `notebookId` 参数命名不统一**：思源不同端点参数名不同。笔记本操作（open/close/rename/remove）用 `notebook`；`exportResources` 也用 `notebook`。脚本已统一处理，但直接调 API 时要注意。
10. **`doc_tree` 缓存导致数据不全**：`doc_tree` 默认走本地缓存（TTL 14 天）。如果在缓存期间新增/移动了文档，旧缓存不会自动更新。解决：`cache_clear` 清除缓存，或 `doc_tree <笔记本ID> --no-cache` 强制直连 API。现象：同一个笔记本，一个 agent 看到 5 个子目录，另一个只看到 3 个。

## 核心概念

- **内容块（Block）**：思源笔记基本单位，每个块通过全局唯一 ID 标识，格式 `202008250000-a1b2c3d`
- **默认 API 端口**：`http://127.0.0.1:6806`
- **数据存储**：SQLite 数据库，主表为 `blocks`
- **配置**：通过 `~/.config/siyuan/config` 或环境变量配置

## 功能模块

| 模块 | 参考文档 |
|------|----------|
| 内容块操作 | [references/block.md](references/block.md) |
| 模板开发 | [references/template.md](references/template.md) |
| API 交互 | [references/api.md](references/api.md) |
| 闪卡系统 | [references/flashcard.md](references/flashcard.md) |

## 快速参考

### 块类型代码

| 代码 | 类型 |
|------|------|
| `d` | 文档块 |
| `h` | 标题块 |
| `p` | 段落块 |
| `l` | 列表块 |
| `i` | 列表项块 |
| `b` | 引述块 |
| `callout` | 提示块 |
| `s` | 超级块 |
| `c` | 代码块 |
| `m` | 公式块 |
| `t` | 表格块 |
| `av` | 数据库块 |
| `query_embed` | 嵌入块 |

### 块引用语法

```markdown
((块ID "锚文本"))   -- 静态锚文本
((块ID '锚文本'))   -- 动态锚文本
((块ID))            -- 使用块内容作为锚文本
```

### 嵌入块语法

```sql
{{ SELECT * FROM blocks WHERE content LIKE '%关键词%' }}
```

## 配置

推荐使用环境变量，脚本读取优先级：**命令行参数 > 环境变量 > 配置文件**。

| 变量 | 说明 |
|------|------|
| `SIYUAN_API_URL` | 思源服务地址（默认 `127.0.0.1:6806`） |
| `SIYUAN_API_TOKEN` | 在思源设置 → 关于 → API Token 中获取 |

> ⚠️ `siyuan_config.json` 不随 skill 发布（禁止文件），不要把 token 写进配置文件。

配置文件位置：`~/.config/siyuan/config`（init 时自动创建，不随 skill 发布）。

如需使用配置文件（仅本地临时用途），参考 `scripts/siyuan_config.json.template`：

```json
{
    "api_url": "http://127.0.0.1:6806",
    "api_token": "${SIYUAN_API_TOKEN}",
    "local_path": ""
}
```

### 连接问题排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `401 Auth failed` | Token 正确但 session 无效 | 确认 Token 与 API URL 匹配 |
| 所有 `/api/*` 返回 404 | 端口不是 Siyuan | 确认 Siyuan 实际端口 |
| `Connection refused` | Siyuan 未启动或端口错误 | 检查 Siyuan 运行状态和端口 |

**验证连接**：
```bash
unset http_proxy https_proxy ALL_PROXY
curl -X POST "${SIYUAN_API_URL}/api/system/version" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token ${SIYUAN_API_TOKEN}" -d '{}'
```
成功返回 `{"code":0,"data":"3.6.5"}` 表示连接正常。

## API 调用

所有 API 通过 `scripts/siyuan_api.py` 脚本调用（禁止用 curl 直接推送中文内容）：

```bash
# ── 初始化 ──
python3 scripts/siyuan_api.py init <API URL> <Token>     # 三合一：写入配置 + 验证连接 + 预热缓存

# ── 笔记本 ──
python3 scripts/siyuan_api.py list_notebooks                          # 列出所有笔记本
python3 scripts/siyuan_api.py get_notebook_conf <笔记本ID>              # 获取笔记本配置
python3 scripts/siyuan_api.py create_notebook <名称>                   # 创建笔记本
python3 scripts/siyuan_api.py open_notebook <笔记本ID>                 # 打开笔记本
python3 scripts/siyuan_api.py close_notebook <笔记本ID>                # 关闭笔记本
python3 scripts/siyuan_api.py rename_notebook <笔记本ID> <新名称>       # 重命名笔记本
python3 scripts/siyuan_api.py remove_notebook <笔记本ID>               # 删除笔记本
python3 scripts/siyuan_api.py set_notebook_conf <笔记本ID> '<JSON>'    # 保存笔记本配置

# ── 文档 ──
python3 scripts/siyuan_api.py create_doc <笔记本ID> /路径 "标题" ["内容"]  # 创建文档
python3 scripts/siyuan_api.py remove_doc <笔记本ID> /系统路径.sy           # 删除文档（按路径）
python3 scripts/siyuan_api.py remove_doc_by_id <文档ID>                    # 删除文档（按ID）
python3 scripts/siyuan_api.py rename_doc <笔记本ID> /路径 "新标题"         # 重命名（按路径）
python3 scripts/siyuan_api.py rename_doc_by_id <文档ID> "新标题"           # 重命名（按ID）
python3 scripts/siyuan_api.py move_docs <笔记本ID> /从路径 <目标笔记本ID> /到路径  # 移动文档
python3 scripts/siyuan_api.py move_docs_by_id <文档ID> <目标块ID> <索引>     # 移动文档（按ID）
python3 scripts/siyuan_api.py get_hpath_by_id <块ID>                        # 获取人类可读路径
python3 scripts/siyuan_api.py get_hpath_by_path <笔记本ID> /路径            # 获取人类可读路径（按路径）
python3 scripts/siyuan_api.py get_path_by_id <块ID>                          # 获取物理路径
python3 scripts/siyuan_api.py get_ids_by_hpath <笔记本ID> "/a/b/c"          # 获取人类可读路径对应的ID列表（路径不存在返回 (无结果)）

# ── 搜索 ──
python3 scripts/siyuan_api.py search_doc <关键词> [笔记本ID]              # 搜索文档

# ── 块 ──
python3 scripts/siyuan_api.py insert_block <父块ID> markdown "内容"           # 插入块
python3 scripts/siyuan_api.py append_block <父块ID> <类型> "内容"           # 追加块
python3 scripts/siyuan_api.py prepend_block <父块ID> <类型> "内容"          # 前置块
python3 scripts/siyuan_api.py update_block <块ID> "markdown内容"            # 更新块内容
python3 scripts/siyuan_api.py delete_block <块ID>                            # 删除块
python3 scripts/siyuan_api.py get_block_kramdown <块ID>                      # 获取块 Kramdown 源码
python3 scripts/siyuan_api.py get_child_blocks <块ID>                        # 获取子块列表
python3 scripts/siyuan_api.py move_block <块ID> <目标块ID> <索引>           # 移动块
python3 scripts/siyuan_api.py fold_block <块ID>                              # 折叠块
python3 scripts/siyuan_api.py unfold_block <块ID>                            # 展开块
python3 scripts/siyuan_api.py transfer_block_ref <块ID> <目标块ID>            # 转移块引用

# ── 属性 ──
python3 scripts/siyuan_api.py get_block_attrs <块ID>                         # 获取块属性
python3 scripts/siyuan_api.py set_block_attrs <块ID> '<JSON>'                # 设置块属性

# ── SQL / 事务 ──
python3 scripts/siyuan_api.py query_sql "SELECT * FROM blocks LIMIT 5"       # SQL 查询
python3 scripts/siyuan_api.py flush_transaction                              # 刷新事务（落盘）

# ── 模板 ──
python3 scripts/siyuan_api.py template_render <块ID> "<模板内容>"             # 渲染模板
python3 scripts/siyuan_api.py template_render_sprig <块ID> "<Sprig模板>"    # 渲染 Sprig 模板

# ── 文件 ──
python3 scripts/siyuan_api.py get_file /data/xxx.txt                          # 读取工作区文件
python3 scripts/siyuan_api.py put_file /data/xxx.txt "内容"                    # 写入工作区文件
python3 scripts/siyuan_api.py read_dir /data/                                  # 列出工作区目录
python3 scripts/siyuan_api.py remove_file /data/xxx.txt                       # 删除工作区文件
python3 scripts/siyuan_api.py rename_file /旧路径 /新路径                     # 重命名工作区文件

# ── 资产 ──
python3 scripts/siyuan_api.py upload_asset <本地文件路径>                    # 上传资产（返回 URL）

# ── 导出 ──
python3 scripts/siyuan_api.py export_md <文档ID>                              # 导出文档为 Markdown
python3 scripts/siyuan_api.py export_resources <笔记本ID> /路径              # 导出资源（ZIP，paths参数）

# ── 通知 ──
python3 scripts/siyuan_api.py push_msg "消息内容" [timeout]                   # 推送消息
python3 scripts/siyuan_api.py push_err_msg "错误信息" [timeout]             # 推送错误消息

# ── 系统 ──
python3 scripts/siyuan_api.py ping                                         # 测试连接
python3 scripts/siyuan_api.py version                                      # 获取系统版本
python3 scripts/siyuan_api.py boot_progress                                # 获取启动进度
python3 scripts/siyuan_api.py current_time                                 # 获取系统当前时间

# ── 缓存 ──
python3 scripts/siyuan_api.py cache_status                                   # 查看缓存状态
python3 scripts/siyuan_api.py cache_clear [key]                              # 清除缓存（省略 key 清所有）
```

缓存：
    默认启用本地缓存（~/.config/siyuan/cache.json）
    notebook 列表和 doc_tree 缓存，写操作后自动失效
    可用 `--no-cache` 强制直连 API

## 缓存机制

脚本默认启用本地缓存，缓存文件：`~/.config/siyuan/cache.json`

| 数据 | TTL | 说明 |
|------|-----|------|
| `notebooks` | 14 天 | 笔记本列表 |
| `doc_tree:<id>` | 14 天 | 各笔记本文档树 |

- 所有写操作（创建/删除/重命名/移动笔记本或文档）后自动使相关缓存失效
- 可用 `--no-cache` 参数强制直连 API
- 可用 `--refresh` 参数强制刷新缓存（等同 `--no-cache`，但语义更清晰）
- `cache_status` 查看当前缓存状态和年龄
- `cache_clear` 清除指定 key 或全部

## 经验教训

### `createDocWithMd` 返回格式
`/api/filetree/createDocWithMd` 成功时 `data` 字段直接是文档 ID 字符串，**不是** `{"id": "..."}` 对象。脚本已做兼容处理，但不要假设必须是 dict。

### `create_doc` 的 markdown 参数局限
命令行传入多行内容时，换行符 `\n` 会被转义成字面量 `\n`（shell 解析问题）。若需创建带多行内容的文档，分两步：先用 `create_doc` 创建空文档，再用 `update_block <文档ID> "内容"` 写入 markdown。

### `get_file` 路径格式
不是文档名，而是完整的 data 路径，格式为：
```
/data/<笔记本ID>/<文档路径>.sy
```
例如文档路径为 `/test-doc`，完整路径为 `/data/20250616102654-1jja3ja/test-doc.sy`。用 `get_path_by_id <文档ID>` 可获取实际路径。

### 读取文档内容 → 用 `export_md`，不要用 `get_file`
`export_md <文档ID>` 是读取文档正文的正确方式，返回完整的 Markdown 内容（带 frontmatter）。

`get_file` 用的是**工作区物理路径**（`/data/<笔记本ID>/<文档路径>.sy`），与笔记本文档路径完全不同，不要混用：
```bash
# ✅ 正确：读文档内容
python3 scripts/siyuan_api.py export_md 20260506002110-gyhz5j1

# ❌ 错误：get_file 的路径格式与笔记本文档路径是两套系统
python3 scripts/siyuan_api.py get_file "20250616102654-1jja3ja/测试"   # 失败
```

### API 返回 data 格式不一致
思源不同端点的 data 字段格式差异很大，脚本中已做兼容处理：
- `getHPathByID` → data 是**字符串**（hpath），不是 dict
- `insertBlock`/`appendBlock`/`prependBlock` → data 是**列表**（blocks 数组）
- `getChildBlocks` → data 是**列表**
- `getIDsByHPath` → data 是**列表**（ID 数组），不是 {"id":[...]}
- `currentTime` → data 是**整数**（毫秒时间戳）
- `readDir` → data 是**列表**（文件数组）
- `getFile` → 返回纯文本，不是 JSON
- `putFile` → 必须用 multipart/form-data，不能用 JSON body

### 思源 SQL API 默认限制 64 条结果
`/api/query/sql` 不加 LIMIT 时默认只返回 64 条。`_build_doc_tree` 已加 `LIMIT 10000`。其他需要全量数据的 SQL 查询也必须显式加 LIMIT。

### search_docs → search_doc
CLI 命令名是 `search_doc`，不是 `search_docs`（Skill 旧版本中的拼写错误已更正）。

### 文件系统隔离问题
Hermes Agent 的 terminal 工具和 Python execute_code 沙箱对 siyuan scripts 目录的文件视图可能不一致。始终用 terminal 工具操作脚本文件，不要依赖 execute_code 沙箱读写同一路径。
