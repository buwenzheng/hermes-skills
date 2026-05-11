# 思源笔记 API 交互指南

## API 概述

- **实际服务地址**：`http://192.168.9.100:6806`（配置在 `scripts/siyuan_config.json`）
- **请求方法**：所有 API 使用 POST
- **数据格式**：JSON
- **认证**：在请求头中添加 `Authorization: Token YOUR_API_TOKEN`

## 认证

```python
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Token {api_token}"
}
```

API Token 在思源笔记设置 → 关于 → API Token 中获取。

## 常用 API 端点

### 内容块操作 `/api/block/*`

| 端点 | 描述 |
|------|------|
| /api/block/getBlockKramdown | 获取块 Kramdown 源码 |
| /api/block/insertBlock | 插入块 |
| /api/block/updateBlock | 更新块 |
| /api/block/deleteBlock | 删除块 |
| /api/block/moveBlock | 移动块 |
| /api/block/appendBlock | 追加块 |
| /api/block/prependBlock | 前置块 |
| /api/block/getChildBlocks | 获取子块列表 |
| /api/block/foldBlock | 折叠块 |
| /api/block/unfoldBlock | 展开块 |
| /api/block/transferBlockRef | 转移块引用 |

### 文档树操作 `/api/filetree/*`

| 端点 | 描述 |
|------|------|
| /api/filetree/createDocWithMd | 使用 Markdown 创建文档 |
| /api/filetree/renameDoc | 重命名文档（按路径） |
| /api/filetree/renameDocByID | 重命名文档（按ID） |
| /api/filetree/removeDoc | 删除文档（按路径） |
| /api/filetree/removeDocByID | 删除文档（按ID） |
| /api/filetree/moveDocs | 移动文档（按路径） |
| /api/filetree/moveDocsByID | 移动文档（按ID） |
| /api/filetree/getHPathByID | 根据 ID 获取人类可读路径 |
| /api/filetree/getHPathByPath | 根据路径获取人类可读路径 |
| /api/filetree/getIDsByHPath | 人类可读路径 → ID |
| /api/filetree/getPathByID | ID → 物理路径 |

### 文件操作 `/api/file/*`

| 端点 | 描述 |
|------|------|
| /api/file/getFile | 获取文件内容 |
| /api/file/putFile | 上传/写入文件 |
| /api/file/removeFile | 删除文件 |
| /api/file/readDir | 读取目录 |

### SQL 查询 `/api/query/*`

| 端点 | 描述 |
|------|------|
| /api/query/sql | 执行 SQL 查询 |

### 笔记本操作 `/api/notebook/*`

| 端点 | 描述 |
|------|------|
| /api/notebook/lsNotebooks | 列出所有笔记本 |
| /api/notebook/getNotebookConf | 获取笔记本详情/配置 |
| /api/notebook/createNotebook | 创建笔记本 |
| /api/notebook/openNotebook | 打开笔记本 |
| /api/notebook/closeNotebook | 关闭笔记本 |
| /api/notebook/renameNotebook | 重命名笔记本 |
| /api/notebook/removeNotebook | 删除笔记本 |
| /api/notebook/setNotebookConf | 保存笔记本配置 |

> 注意：旧版文档曾用 `listNotebooks` 和 `getNotebook`，实际端点为 `lsNotebooks` 和 `getNotebookConf`。

## 响应格式

```json
{
  "code": 0,
  "msg": "",
  "data": { ... }
}
```

- `code: 0` 表示成功
- `msg` 包含错误信息
- `data` 为返回数据

## 🚨 重要警告：中文编码

**禁止使用 curl 直接推送包含中文的内容**，会导致乱码。必须使用 Python 脚本调用 API。

```python
# ✅ 正确
import requests
response = requests.post(
    f'{api_url}/api/filetree/createDocWithMd',
    headers={'Authorization': f'Token {token}', 'Content-Type': 'application/json'},
    json={'notebook': nb_id, 'path': '/文档名', 'markdown': '中文内容'}
)

# ❌ 错误（会产生乱码）
curl -X POST "http://127.0.0.1:6806/api/filetree/createDocWithMd" \
  -H "Authorization: Token xxx" \
  -d '{"markdown": "中文内容"}'
```

## 脚本调用

通过 `scripts/siyuan_api.py` 调用：

```bash
# 列出笔记本（API 路径: /api/notebook/lsNotebooks）
python3 scripts/siyuan_api.py list_notebooks

# SQL 查询
python3 scripts/siyuan_api.py query_sql "SELECT * FROM blocks WHERE type='d' LIMIT 5"

# 创建文档
python3 scripts/siyuan_api.py create_doc <笔记本ID> /路径 "标题" "# 内容"

# 搜索文档
python3 scripts/siyuan_api.py search_docs "关键词"
```

## 文件操作警告

**请通过内核 API 操作文件**，不要自行使用 `fs` 等 Node.js API，否则可能导致数据同步时分块丢失，造成云端数据损坏。

使用 `/api/file/*` 系列 API。

## 相关资源

- [思源笔记 GitHub](https://github.com/siyuan-note/siyuan)
- [完整 API 文档](https://github.com/siyuan-note/siyuan/blob/master/API_zh_CN.md)
- [SQL 查询文档](https://github.com/siyuan-note/siyuan/blob/master/SQL_zh_CN.md)
