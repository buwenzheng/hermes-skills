# siyuan-custom 缓存机制变更记录

## 2026-05-14 会话变更

### 新增 `--refresh` 参数

- 语义更清晰：强制刷新缓存（等同 `--no-cache`，但更直观）
- 实现：先 `cache_invalidate(cache_key)` 清缓存，再重新构建
- 用法：`python3 scripts/siyuan_api.py doc_tree <笔记本ID> --refresh`

### 缓存失效机制

写操作后自动 invalidate 相关缓存：

| 操作 | 缓存失效 |
|------|----------|
| create_notebook | notebooks |
| remove_notebook | notebooks + doc_tree:{id} |
| create_doc | doc_tree:{notebook_id} |
| remove_doc | doc_tree:{notebook_id} |
| remove_doc_by_id | doc_tree:* |
| move_docs | doc_tree:{from} + doc_tree:{to} |

### 用户纠正

另一个 agent 查询 `doc_tree` 时只返回了 3 个子目录（到「常士杉」结束），实际应该有 5 个。原因是缓存 stale。解决方案：加 `--refresh` 参数强制刷新。

### 使用建议

- 外部操作（思源客户端里改了数据）后，用 `--refresh` 刷新
- 写操作后缓存自动失效，无需手动刷新
- `cache_clear` 清全部缓存
- `cache_status` 查看缓存状态
