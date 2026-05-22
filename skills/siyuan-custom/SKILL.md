---
name: siyuan-custom
description: >-
  Use when the user asks about, queries, searches, creates, edits, or manages
  content in SiYuan Note (思源笔记). Also triggers on: siyuan, 思源, 笔记查询,
  搜索笔记, 查文档, 建块, 块引用, 嵌入块, 模板, 闪卡, 思源 API,
  思源笔记操作, siyuan api. Covers both conceptual questions and practical operations
  (query, search, create, update, delete blocks via API).
version: 1.3.1
tags: [siyuan, 思源, 笔记查询, 搜索笔记, 查文档, 建块, 块引用, 嵌入块, 模板, 闪卡, 思源 API, 思源笔记操作, siyuan api]
related_skills: []
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

## 核心概念

- **内容块（Block）**：思源笔记基本单位，每个块通过全局唯一 ID 标识，格式 `202008250000-a1b2c3d`
- **默认 API 端口**：`http://127.0.0.1:6806`
- **数据存储**：SQLite 数据库，主表为 `blocks`
- **配置**：通过 `~/.config/siyuan/config` 或环境变量配置

## 功能模块参考

| 模块 | 参考文档 |
|------|----------|
| 内容块操作 | [references/block.md](references/block.md) |
| 模板开发 | [references/template.md](references/template.md) |
| API 交互 | [references/api.md](references/api.md) |
| 闪卡系统 | [references/flashcard.md](references/flashcard.md) |
| 缓存机制 | [references/cache-invalidation.md](references/cache-invalidation.md) |

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

### 连接问题排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `401 Auth failed` | Token 正确但 session 无效 | 确认 Token 与 API URL 匹配 |
| 所有 `/api/*` 返回 404 | 端口不是 Siyuan | 确认 Siyuan 实际端口 |
| `Connection refused` | Siyuan 未启动或端口错误 | 检查 Siyuan 运行状态和端口 |

**验证连接**：
```bash
curl -X POST "${SIYUAN_API_URL}/api/system/version" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token ${SIYUAN_API_TOKEN}" -d '{}'
```
成功返回 `{"code":0,"data":"3.6.5"}` 表示连接正常。

---

## 标准操作指南

## 网络注意事项

思源笔记是**内网服务**（默认 `127.0.0.1:6806` 或局域网 IP），调用 API 时**不需要设置/清除代理**。仅外网访问（GitHub、pip install 等）才需要代理。不要在命令前加 `unset http_proxy https_proxy`——环境变量默认未设置，加了是噪音。

所有 API 通过 `scripts/siyuan_api.py` 脚本调用（禁止用 curl 直接推送中文内容）：

### 笔记本操作

```bash
# 列出所有笔记本
python3 scripts/siyuan_api.py list_notebooks

# 创建 / 重命名 / 删除
python3 scripts/siyuan_api.py create_notebook <名称>
python3 scripts/siyuan_api.py rename_notebook <笔记本ID> <新名称>
python3 scripts/siyuan_api.py remove_notebook <笔记本ID>

# 打开 / 关闭（关闭后该笔记本下无法创建文档）
python3 scripts/siyuan_api.py open_notebook <笔记本ID>
python3 scripts/siyuan_api.py close_notebook <笔记本ID>

# 查看 / 修改配置
python3 scripts/siyuan_api.py get_notebook_conf <笔记本ID>
python3 scripts/siyuan_api.py set_notebook_conf <笔记本ID> '<JSON>'
```

### 文档操作

```bash
# 创建文档（路径是 hpath，如 /投资/股票）
python3 scripts/siyuan_api.py create_doc <笔记本ID> /路径 "标题" "内容"
# 多行内容分两步：先创建空文档，再 update_block 写入

# 删除（两种方式）
python3 scripts/siyuan_api.py remove_doc <笔记本ID> /路径.sy        # 按路径
python3 scripts/siyuan_api.py remove_doc_by_id <文档ID>              # 按ID

# 重命名（两种方式）
python3 scripts/siyuan_api.py rename_doc <笔记本ID> /路径 "新标题"   # 按路径
python3 scripts/siyuan_api.py rename_doc_by_id <文档ID> "新标题"     # 按ID

# 移动
python3 scripts/siyuan_api.py move_docs <笔记本ID> /从路径 <目标笔记本ID> /到路径
python3 scripts/siyuan_api.py move_docs_by_id <文档ID> <目标块ID> <索引>

# 查看文档树
python3 scripts/siyuan_api.py doc_tree <笔记本ID>              # 默认走缓存
python3 scripts/siyuan_api.py doc_tree <笔记本ID> --no-cache   # 强制直连API

# 搜索
python3 scripts/siyuan_api.py search_doc <关键词> [笔记本ID]
```

### 读取文档内容

```bash
# ✅ 正确方式：export_md 返回完整 Markdown（含 frontmatter）
python3 scripts/siyuan_api.py export_md <文档ID>

# ❌ get_file 是另一套路径系统（工作区物理路径），不要混用
# get_file 路径格式：/data/<笔记本ID>/<文档路径>.sy
# 用 get_path_by_id <文档ID> 可获取实际路径
```

### 块操作

```bash
# 获取子块列表（文档ID就是根块ID）
python3 scripts/siyuan_api.py get_child_blocks <块ID>

# 创建块（三种方式，区别在于插入位置）
python3 scripts/siyuan_api.py insert_block <父块ID> markdown "内容"    # 插入（指定位置）
python3 scripts/siyuan_api.py append_block <父块ID> markdown "内容"    # 追加到末尾
python3 scripts/siyuan_api.py prepend_block <父块ID> markdown "内容"   # 插入到开头

# 更新块内容（注意：脚本已处理正确的 API 参数格式）
python3 scripts/siyuan_api.py update_block <块ID> "新的 markdown 内容"

# 删除块
python3 scripts/siyuan_api.py delete_block <块ID>

# 获取块源码 / 移动 / 折叠
python3 scripts/siyuan_api.py get_block_kramdown <块ID>
python3 scripts/siyuan_api.py move_block <块ID> <目标块ID> <索引>
python3 scripts/siyuan_api.py fold_block <块ID>
python3 scripts/siyuan_api.py unfold_block <块ID>
```

### 属性操作

```bash
# 读取属性
python3 scripts/siyuan_api.py get_block_attrs <块ID>

# 设置属性（JSON 格式，自定义属性自动加 custom- 前缀）
python3 scripts/siyuan_api.py set_block_attrs <块ID> '{"custom-status": "doing"}'
```

### 路径与 ID 互查

```bash
# ID → 人类可读路径（如 /个人操作部分/z哥/B1）
python3 scripts/siyuan_api.py get_hpath_by_id <块ID>

# ID → 物理路径（如 /20250616102654-1jja3ja/测试.sy）
python3 scripts/siyuan_api.py get_path_by_id <块ID>

# hpath → ID 列表（路径不存在返回空）
python3 scripts/siyuan_api.py get_ids_by_hpath <笔记本ID> "/a/b/c"
```

### SQL 查询

```bash
# 直接执行 SQL（注意：默认限制 64 条，必须显式加 LIMIT）
python3 scripts/siyuan_api.py query_sql "SELECT id, hpath, content FROM blocks WHERE box='笔记本ID' AND type='d' LIMIT 100"
```

### 文件 / 资产 / 导出

```bash
# 工作区文件操作（路径以 /data/ 开头）
python3 scripts/siyuan_api.py get_file /data/xxx.txt
python3 scripts/siyuan_api.py put_file /data/xxx.txt "内容"
python3 scripts/siyuan_api.py read_dir /data/
python3 scripts/siyuan_api.py remove_file /data/xxx.txt
python3 scripts/siyuan_api.py rename_file /旧路径 /新路径

# 上传资产（返回 URL）
python3 scripts/siyuan_api.py upload_asset <本地文件路径>

# 导出
python3 scripts/siyuan_api.py export_md <文档ID>                     # 导出为 Markdown
python3 scripts/siyuan_api.py export_resources <笔记本ID> /路径      # 导出资源（ZIP）
```

### 通知 / 系统

```bash
python3 scripts/siyuan_api.py push_msg "消息内容" [timeout]
python3 scripts/siyuan_api.py push_err_msg "错误信息" [timeout]
python3 scripts/siyuan_api.py ping
python3 scripts/siyuan_api.py version
```

### 缓存管理

```bash
python3 scripts/siyuan_api.py cache_status                           # 查看缓存状态
python3 scripts/siyuan_api.py cache_clear                            # 清除所有缓存
python3 scripts/siyuan_api.py cache_clear doc_tree:<笔记本ID>        # 清除指定缓存
```

---

## API 响应格式说明

思源不同端点的 `data` 字段格式不一致，脚本已做兼容处理。直接调 API 时注意：

| 端点 | data 类型 | 示例 |
|------|-----------|------|
| `/api/system/version` | `string` | `"3.6.5"` |
| `/api/notebook/lsNotebooks` | `{"notebooks": [...]}` | 唯一用 dict 包装的 |
| `/api/filetree/getHPathByID` | `string` | `"/文档路径"` |
| `/api/filetree/getIDsByHPath` | `["id1", "id2"]` | 直接是列表 |
| `/api/block/insertBlock` 等 | `[{doOperations: [{id: "..."}]}]` | 块ID在 doOperations 内 |
| `/api/block/getChildBlocks` | `[{id: "...", ...}]` | 直接是列表 |
| `/api/block/getBlockKramdown` | `{"id": "...", "kramdown": "..."}` | 正常 dict |
| `/api/attr/getBlockAttrs` | `{"id": "...", "key": "val"}` | 正常 dict |
| `/api/query/sql` | `[{col: "val"}]` | 直接是列表 |
| `/api/file/getFile` | 纯文本（非 JSON） | 失败时才返回 JSON |
| `/api/file/putFile` | `{"code":0}` | 必须 multipart/form-data |

**关键点**：
- `createDocWithMd` 返回的 `data` 是文档 ID **字符串**，不是 dict
- `insertBlock/appendBlock/prependBlock` 的块 ID 在 `data[0].doOperations[0].id`
- `getFile` 返回纯文本，`putFile` 必须用 multipart 上传
- SQL 查询默认限制 64 条，全量查询必须加 `LIMIT`

---

## 缓存机制

脚本默认启用本地缓存，缓存文件：`~/.config/siyuan/cache.json`

| 数据 | TTL | 说明 |
|------|-----|------|
| `notebooks` | 14 天 | 笔记本列表 |
| `doc_tree:<id>` | 14 天 | 各笔记本文档树 |

- 所有写操作后自动使相关缓存失效
- `--no-cache` / `--refresh` 强制直连 API 并刷新缓存
- `_by_id` 操作（remove/rename/move）因不知道所属 notebook，会清所有 doc_tree 缓存

---

## Common Pitfalls / 避坑

1. **读文档内容用 `export_md`，不用 `get_file`** — 两套路径系统完全不同
2. **创建多行文档分两步** — `create_doc` 创建空文档 → `update_block` 写入内容（脚本已自动将 `\n` 转为真实换行）
3. **SQL 必须加 LIMIT** — 不加默认只返回 64 条
4. **`set_block_attrs` 需要 `attrs` 嵌套** — 格式 `{"id": "...", "attrs": {...}}`，平铺传递不生效
5. **`update_block` 需要 `dataType + data`** — 格式 `{"id": "...", "dataType": "markdown", "data": "..."}`，用 `markdown` 字段不生效
6. **`renameDocByID` 不更新 blocks 表** — 改了文件名但 SQL 查到的 hpath 仍是旧名，`search_doc` 搜不到改名后的文档。这是思源设计：官方 API 无专门搜索端点，SQL 是唯一搜索方式，而 rename 不同步 hpath。找改名后的文档用 `doc_tree` 遍历或 `getHPathByID`
7. **`removeDocByID` 不删除 blocks 记录** — 只删文件，block 变孤儿（`type='d'` 但内容为空）。`doc_tree` 查询已加 `content IS NOT NULL` 过滤
8. **思源 SQL API 只读** — `/api/query/sql` 的 INSERT/UPDATE/DELETE 返回 code=0 但不执行
9. **Terminal 与 execute_code 沙箱文件视图不一致** — 始终用 terminal 工具操作脚本文件
10. **`remove_doc_by_id` 后缓存可能残留** — API 返回成功但 doc_tree 缓存未自动失效，需手动 `cache_clear doc_tree:<笔记本ID>` 或 `--no-cache`
