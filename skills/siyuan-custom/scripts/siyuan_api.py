#!/usr/bin/env python3
"""
思源笔记 API 调用脚本
用法:
    python3 siyuan_api.py <command> [args...]

配置:
    读取 ~/.config/siyuan/config
    或环境变量 SIYUAN_API_URL, SIYUAN_API_TOKEN

缓存:
    默认启用本地缓存（~/.config/siyuan/cache.json）
    缓存两周，写操作后自动失效
    可用 --no-cache 或 --refresh 强制走 API 并刷新缓存
"""

import json
import os
import sys
import requests
import time
import shutil
from pathlib import Path

CONFIG_DIR  = Path.home() / ".config" / "siyuan"
CONFIG_PATH = CONFIG_DIR / "config"
CACHE_PATH  = CONFIG_DIR / "cache.json"
DEFAULT_TTL = 14 * 24 * 3600  # notebook list 缓存两周


# ─────────────────────────────────────────
# 缓存层
# ─────────────────────────────────────────

def load_cache():
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def cache_get(key, ttl=DEFAULT_TTL):
    """缓存未过期返回 (data, True)，过期返回 (None, False)"""
    c = load_cache()
    if key in c:
        entry = c[key]
        if time.time() - entry["ts"] < ttl:
            return entry["data"], True
    return None, False


def cache_set(key, data):
    c = load_cache()
    c[key] = {"ts": time.time(), "data": data}
    save_cache(c)


def cache_invalidate(key=None):
    """key 为 None 清除所有；key 末尾带 * 时按前缀匹配清除；否则只清除指定 key"""
    c = load_cache()
    if key is None:
        c.clear()
    elif key.endswith('*'):
        prefix = key[:-1]
        to_del = [k for k in c if k.startswith(prefix)]
        for k in to_del:
            del c[k]
    elif key in c:
        del c[key]
    save_cache(c)


# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "api_url": os.environ.get("SIYUAN_API_URL", "http://127.0.0.1:6806"),
        "api_token": os.environ.get("SIYUAN_API_TOKEN", ""),
        "local_path": os.environ.get("SIYUAN_LOCAL_PATH", ""),
    }


def get_headers(config):
    headers = {"Content-Type": "application/json"}
    if config.get("api_token"):
        headers["Authorization"] = f"Token {config['api_token']}"
    return headers


def api_request(config, endpoint, data=None, method="POST"):
    url = f"{config['api_url']}{endpoint}"
    headers = get_headers(config)
    try:
        if method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            resp = requests.get(url, headers=headers, params=data, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}", file=sys.stderr)
        if "Response" in dir(e) and e.response is not None:
            print(f"响应内容: {e.response.text}", file=sys.stderr)
        sys.exit(1)


def api_request_no_cache(config, endpoint, data=None, method="POST"):
    """不走缓存的请求"""
    return api_request(config, endpoint, data, method)


# ─────────────────────────────────────────
# 笔记本操作
# ─────────────────────────────────────────

def cmd_list_notebooks(config, use_cache=True):
    """列出所有笔记本（默认走缓存）"""
    if use_cache:
        data, hit = cache_get("notebooks")
        if hit:
            notebooks = data
        else:
            result = api_request(config, "/api/notebook/lsNotebooks")
            notebooks = result.get("data", {}).get("notebooks", [])
            cache_set("notebooks", notebooks)
    else:
        result = api_request(config, "/api/notebook/lsNotebooks")
        notebooks = result.get("data", {}).get("notebooks", [])
        cache_set("notebooks", notebooks)

    if not notebooks:
        print("没有找到笔记本")
        return
    print(f"{'ID':<22} {'名称':<25} {'关闭':<6} {'排序模式':<8} 闪卡/待复习")
    print("-" * 80)
    for nb in notebooks:
        print(f"{nb.get('id', ''):<22} {nb.get('name', ''):<25} {'是' if nb.get('closed') else '否':<6} {nb.get('sortMode', ''):<8} {nb.get('flashcardCount', 0)}/{nb.get('dueFlashcardCount', 0)}")


def cmd_get_notebook(config, notebook_id):
    """获取笔记本配置"""
    result = api_request(config, "/api/notebook/getNotebookConf", {"notebook": notebook_id})
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_create_notebook(config, name):
    """创建笔记本"""
    result = api_request(config, "/api/notebook/createNotebook", {"name": name})
    if result.get("code") == 0:
        print(f"笔记本创建成功: {name}")
        cache_invalidate("notebooks")
    else:
        print(f"创建失败: {result.get('msg')}", file=sys.stderr)


def cmd_open_notebook(config, notebook_id):
    """打开笔记本"""
    result = api_request(config, "/api/notebook/openNotebook", {"notebook": notebook_id})
    if result.get("code") == 0:
        print(f"笔记本已打开: {notebook_id}")
        cache_invalidate("notebooks")
    else:
        print(f"打开失败: {result.get('msg')}", file=sys.stderr)


def cmd_close_notebook(config, notebook_id):
    """关闭笔记本"""
    result = api_request(config, "/api/notebook/closeNotebook", {"notebook": notebook_id})
    if result.get("code") == 0:
        print(f"笔记本已关闭: {notebook_id}")
        cache_invalidate("notebooks")
    else:
        print(f"关闭失败: {result.get('msg')}", file=sys.stderr)


def cmd_rename_notebook(config, notebook_id, new_name):
    """重命名笔记本"""
    result = api_request(config, "/api/notebook/renameNotebook", {"notebook": notebook_id, "name": new_name})
    if result.get("code") == 0:
        print(f"笔记本已重命名为: {new_name}")
        cache_invalidate("notebooks")
    else:
        print(f"重命名失败: {result.get('msg')}", file=sys.stderr)


def cmd_remove_notebook(config, notebook_id):
    """删除笔记本"""
    result = api_request(config, "/api/notebook/removeNotebook", {"notebook": notebook_id})
    if result.get("code") == 0:
        print(f"笔记本已删除: {notebook_id}")
        cache_invalidate("notebooks")
        cache_invalidate(f"doc_tree:{notebook_id}")
    else:
        print(f"删除失败: {result.get('msg')}", file=sys.stderr)


def cmd_set_notebook_conf(config, notebook_id, conf_json):
    """保存笔记本配置（JSON 字符串）"""
    try:
        conf = json.loads(conf_json)
    except json.JSONDecodeError:
        print("错误: conf_json 应为合法 JSON 字符串", file=sys.stderr)
        sys.exit(1)
    conf["notebook"] = notebook_id
    result = api_request(config, "/api/notebook/setNotebookConf", conf)
    if result.get("code") == 0:
        print(f"笔记本配置已保存: {notebook_id}")
    else:
        print(f"保存失败: {result.get('msg')}", file=sys.stderr)


# ─────────────────────────────────────────
# 文档树（支持缓存）
# ─────────────────────────────────────────

def _build_doc_tree(config, notebook_id):
    """从 API 重新构建文档树
    过滤条件：type='d' AND content IS NOT NULL
    原因：思源 deleteBlock/removeDocByID 不真正删除 blocks 表记录，
    只清空内容或删文件，留下 type='d' 但 content=NULL 的孤儿记录
    """
    result = api_request(config, "/api/query/sql", {
        "stmt": f'SELECT id, path, hpath, name, type FROM blocks WHERE box="{notebook_id}" AND type="d" AND content IS NOT NULL ORDER BY hpath ASC LIMIT 10000'
    })
    docs = result.get("data", [])
    return docs


def cmd_doc_tree(config, notebook_id, use_cache=True):
    """查看笔记本的文档树（默认走缓存）"""
    cache_key = f"doc_tree:{notebook_id}"
    if not use_cache:
        # --no-cache / --refresh：先清缓存，再重新构建
        cache_invalidate(cache_key)
        docs = _build_doc_tree(config, notebook_id)
        cache_set(cache_key, docs)
    else:
        docs, hit = cache_get(cache_key, ttl=14 * 24 * 3600)  # doc_tree 缓存两周
        if not hit:
            docs = _build_doc_tree(config, notebook_id)
            cache_set(cache_key, docs)

    if not docs:
        print("(空笔记本)")
        return

    # 按层级缩进打印
    for doc in docs:
        hpath = doc.get("hpath", "")
        # 统计深度（用 / 分段）
        depth = hpath.count("/") - 1
        indent = "  " * depth
        name = doc.get("name") or hpath.split("/")[-1]
        doc_id = doc.get("id", "")
        print(f"{indent}{name}  [{doc_id}]")


def cmd_search_doc(config, query, notebook_id=None):
    """搜索文档（可指定笔记本或不指定）"""
    if notebook_id:
        stmt = f'SELECT id, hpath, name FROM blocks WHERE box="{notebook_id}" AND type="d" AND (hpath LIKE "%{query}%" OR name LIKE "%{query}%" OR content LIKE "%{query}%") LIMIT 20'
    else:
        stmt = f'SELECT id, hpath, name, box FROM blocks WHERE type="d" AND (hpath LIKE "%{query}%" OR name LIKE "%{query}%" OR content LIKE "%{query}%") LIMIT 20'
    result = api_request(config, "/api/query/sql", {"stmt": stmt})
    rows = result.get("data", [])
    if not rows:
        print("(无结果)")
        return
    for r in rows:
        box = r.get("box", "")
        hpath = r.get("hpath", "")
        name = r.get("name", "")
        doc_id = r.get("id", "")
        print(f"[{box}] {hpath or name}  [{doc_id}]")


# ─────────────────────────────────────────
# 文档（文件树）操作
# ─────────────────────────────────────────

def cmd_create_doc(config, notebook_id, path, title, markdown_content=""):
    """创建文档
    注意：命令行传入的 \n 会被 shell 当作字面量，这里自动转换为真实换行
    """
    # 将 shell 传入的字面 \n 转换为真实换行符
    markdown_content = markdown_content.replace("\\n", "\n")
    data = {"notebook": notebook_id, "path": path, "markdown": markdown_content}
    result = api_request(config, "/api/filetree/createDocWithMd", data)
    if result.get("code") == 0:
        doc_id = result.get("data")
        if isinstance(doc_id, dict):
            doc_id = doc_id.get("id")
        print(f"文档创建成功: {path} (id={doc_id})")
        cache_invalidate(f"doc_tree:{notebook_id}")
        return doc_id
    else:
        print(f"创建失败: {result.get('msg')}", file=sys.stderr)
        return None


def cmd_remove_doc(config, notebook_id, path):
    """删除文档（按路径）"""
    result = api_request(config, "/api/filetree/removeDoc", {"notebook": notebook_id, "path": path})
    if result.get("code") == 0:
        print(f"文档删除成功: {path}")
        cache_invalidate(f"doc_tree:{notebook_id}")
    else:
        print(f"删除失败: {result.get('msg')}", file=sys.stderr)


def cmd_remove_doc_by_id(config, doc_id):
    """删除文档（按 ID）"""
    result = api_request(config, "/api/filetree/removeDocByID", {"id": doc_id})
    if result.get("code") == 0:
        print(f"文档删除成功: {doc_id}")
        cache_invalidate(f"doc_tree:*")  # 不知道属于哪个 notebook，全清
    else:
        print(f"删除失败: {result.get('msg')}", file=sys.stderr)


def cmd_rename_doc(config, notebook_id, path, new_name):
    """重命名文档（按路径）"""
    result = api_request(config, "/api/filetree/renameDoc", {"notebook": notebook_id, "path": path, "title": new_name})
    if result.get("code") == 0:
        print(f"文档已重命名: {new_name}")
        cache_invalidate(f"doc_tree:{notebook_id}")
    else:
        print(f"重命名失败: {result.get('msg')}", file=sys.stderr)


def cmd_rename_doc_by_id(config, doc_id, new_name):
    """重命名文档（按 ID）
    注意：思源 renameDocByID 只改文件名，不更新 blocks 表的 hpath。
    思源 SQL API 只读，无法手动同步。search_doc 搜不到改名后的文档，
    需要用 doc_tree 或 getHPathByID 查找。
    """
    result = api_request(config, "/api/filetree/renameDocByID", {"id": doc_id, "title": new_name})
    if result.get("code") == 0:
        print(f"文档已重命名: {new_name}")
        cache_invalidate(f"doc_tree:*")
    else:
        print(f"重命名失败: {result.get('msg')}", file=sys.stderr)


def cmd_move_docs(config, notebook_id, from_path, to_notebook_id, to_path):
    """移动文档（按路径）"""
    data = {
        "fromNotebook": notebook_id,
        "fromPath": from_path,
        "toNotebook": to_notebook_id,
        "toPath": to_path,
    }
    result = api_request(config, "/api/filetree/moveDocs", data)
    if result.get("code") == 0:
        print(f"文档已移动: {from_path} -> {to_notebook_id}{to_path}")
        cache_invalidate(f"doc_tree:{notebook_id}")
        if to_notebook_id != notebook_id:
            cache_invalidate(f"doc_tree:{to_notebook_id}")
    else:
        print(f"移动失败: {result.get('msg')}", file=sys.stderr)


def cmd_move_docs_by_id(config, doc_id, target_block_id, target_index):
    """移动文档（按 ID）"""
    data = {
        "docId": doc_id,
        "targetBlockId": target_block_id,
        "targetIndex": int(target_index),
    }
    result = api_request(config, "/api/filetree/moveDocsByID", data)
    if result.get("code") == 0:
        print(f"文档已移动到 {target_block_id} 的索引 {target_index}")
        cache_invalidate(f"doc_tree:*")
    else:
        print(f"移动失败: {result.get('msg')}", file=sys.stderr)


def cmd_get_hpath_by_id(config, block_id):
    """根据 ID 获取人类可读路径"""
    result = api_request(config, "/api/filetree/getHPathByID", {"id": block_id})
    if result.get("code") == 0:
        data = result.get("data")
        if isinstance(data, str):
            print(data)
        elif isinstance(data, dict):
            print(data.get("hPath", ""))
        else:
            print(data or "")
    else:
        print(f"获取失败: {result.get('msg')}", file=sys.stderr)


def cmd_get_hpath_by_path(config, notebook_id, path):
    """根据路径获取人类可读路径"""
    result = api_request(config, "/api/filetree/getHPathByPath", {"notebook": notebook_id, "path": path})
    if result.get("code") == 0:
        print(result.get("data", {}).get("hPath", ""))
    else:
        print(f"获取失败: {result.get('msg')}", file=sys.stderr)


def cmd_get_ids_by_hpath(config, notebook_id, hpath):
    """根据人类可读路径获取 ID 列表"""
    result = api_request(config, "/api/filetree/getIDsByHPath", {"notebook": notebook_id, "path": hpath})
    if result.get("code") == 0:
        data = result.get("data")
        if isinstance(data, list):
            ids = data
        elif isinstance(data, dict):
            ids = data.get("id") or data.get("ids") or []
        else:
            ids = []
        if ids:
            print("\n".join(str(i) for i in ids))
        else:
            print("(无结果)")
    else:
        print(f"获取失败: {result.get('msg')}", file=sys.stderr)


def cmd_get_path_by_id(config, block_id):
    """根据 ID 获取物理路径"""
    result = api_request(config, "/api/filetree/getPathByID", {"id": block_id})
    if result.get("code") == 0:
        print(result.get("data", {}).get("path", ""))
    else:
        print(f"获取失败: {result.get('msg')}", file=sys.stderr)


# ─────────────────────────────────────────
# 块操作
# ─────────────────────────────────────────

def _extract_block_id(result):
    """从 insertBlock/appendBlock/prependBlock 返回中提取块ID
    API 实际返回格式: [{doOperations: [{id: "...", ...}]}]
    """
    data = result.get("data", [])
    if isinstance(data, list) and data:
        # 格式1: [{doOperations: [{id: "..."}]}] — 思源实际格式
        ops = data[0].get("doOperations", [])
        if isinstance(ops, list) and ops:
            bid = ops[0].get("id", "")
            if bid:
                return bid
        # 格式2: [{id: "..."}] — 兼容旧版假设
        bid = data[0].get("id", "")
        if bid:
            return bid
    elif isinstance(data, dict):
        return data.get("id", "") or data.get("block", {}).get("id", "")
    return ""


def cmd_insert_block(config, parent_id, data_type, markdown):
    """插入块"""
    data = {"parentID": parent_id, "dataType": data_type, "data": markdown}
    result = api_request(config, "/api/block/insertBlock", data)
    if result.get("code") == 0:
        block_id = _extract_block_id(result)
        print(f"块插入成功: {block_id}")
        return block_id
    else:
        print(f"插入失败: {result.get('msg')}", file=sys.stderr)
        return None


def cmd_append_block(config, parent_id, block_type, markdown):
    """追加块"""
    data = {"parentID": parent_id, "dataType": block_type, "data": markdown}
    result = api_request(config, "/api/block/appendBlock", data)
    if result.get("code") == 0:
        block_id = _extract_block_id(result)
        print(f"块追加成功: {block_id}")
        return block_id
    else:
        print(f"追加失败: {result.get('msg')}", file=sys.stderr)
        return None


def cmd_prepend_block(config, parent_id, block_type, markdown):
    """前置块"""
    data = {"parentID": parent_id, "dataType": block_type, "data": markdown}
    result = api_request(config, "/api/block/prependBlock", data)
    if result.get("code") == 0:
        block_id = _extract_block_id(result)
        print(f"块前置成功: {block_id}")
        return block_id
    else:
        print(f"前置失败: {result.get('msg')}", file=sys.stderr)
        return None


def cmd_update_block(config, block_id, markdown):
    """更新块内容
    注意：思源 API 需要 dataType + data 格式，用 {"id", "markdown"} 不生效
    """
    data = {"id": block_id, "dataType": "markdown", "data": markdown}
    result = api_request(config, "/api/block/updateBlock", data)
    if result.get("code") == 0:
        print(f"块更新成功: {block_id}")
    else:
        print(f"更新失败: {result.get('msg')}", file=sys.stderr)


def cmd_delete_block(config, block_id):
    """删除块"""
    data = {"id": block_id}
    result = api_request(config, "/api/block/deleteBlock", data)
    if result.get("code") == 0:
        print(f"块删除成功: {block_id}")
    else:
        print(f"删除失败: {result.get('msg')}", file=sys.stderr)


def cmd_get_block_kramdown(config, block_id):
    """获取块 Kramdown 源码"""
    result = api_request(config, "/api/block/getBlockKramdown", {"id": block_id})
    if result.get("code") == 0:
        print(json.dumps(result.get("data", {}), indent=2, ensure_ascii=False))
    else:
        print(f"获取失败: {result.get('msg')}", file=sys.stderr)


def cmd_get_child_blocks(config, block_id):
    """获取子块列表"""
    result = api_request(config, "/api/block/getChildBlocks", {"id": block_id})
    if result.get("code") == 0:
        data = result.get("data", [])
        if isinstance(data, list):
            children = data
        elif isinstance(data, dict):
            children = data.get("blocks", [])
        else:
            children = []
        if not children:
            print("(无子块)")
            return
        for b in children:
            print(f"{b.get('id'):<22} [{b.get('type'):<6}] {str(b.get('content', ''))[:60]}")
    else:
        print(f"获取失败: {result.get('msg')}", file=sys.stderr)


def cmd_move_block(config, block_id, target_block_id, target_index):
    """移动块"""
    data = {"blockId": block_id, "targetBlockId": target_block_id, "targetIndex": int(target_index)}
    result = api_request(config, "/api/block/moveBlock", data)
    if result.get("code") == 0:
        print(f"块 {block_id} 已移动到 {target_block_id} 的索引 {target_index}")
    else:
        print(f"移动失败: {result.get('msg')}", file=sys.stderr)


def cmd_fold_block(config, block_id):
    """折叠块"""
    result = api_request(config, "/api/block/foldBlock", {"id": block_id})
    if result.get("code") == 0:
        print(f"块已折叠: {block_id}")
    else:
        print(f"折叠失败: {result.get('msg')}", file=sys.stderr)


def cmd_unfold_block(config, block_id):
    """展开块"""
    result = api_request(config, "/api/block/unfoldBlock", {"id": block_id})
    if result.get("code") == 0:
        print(f"块已展开: {block_id}")
    else:
        print(f"展开失败: {result.get('msg')}", file=sys.stderr)


def cmd_transfer_block_ref(config, block_id, ref_id):
    """转移块引用"""
    data = {"blockId": block_id, "refId": ref_id}
    result = api_request(config, "/api/block/transferBlockRef", data)
    if result.get("code") == 0:
        print(f"块引用已从 {block_id} 转移到 {ref_id}")
    else:
        print(f"转移失败: {result.get('msg')}", file=sys.stderr)


# ─────────────────────────────────────────
# 属性
# ─────────────────────────────────────────

def cmd_get_block_attrs(config, block_id):
    """获取块属性"""
    result = api_request(config, "/api/attr/getBlockAttrs", {"id": block_id})
    if result.get("code") == 0:
        print(json.dumps(result.get("data", {}), indent=2, ensure_ascii=False))
    else:
        print(f"获取失败: {result.get('msg')}", file=sys.stderr)


def cmd_set_block_attrs(config, block_id, attrs_json):
    """设置块属性（JSON 字符串）
    注意：思源 API 需要 {"id": "...", "attrs": {...}} 格式，平铺传递不生效
    """
    try:
        attrs = json.loads(attrs_json)
    except json.JSONDecodeError:
        print("错误: attrs_json 应为合法 JSON 字符串", file=sys.stderr)
        sys.exit(1)
    payload = {"id": block_id, "attrs": attrs}
    result = api_request(config, "/api/attr/setBlockAttrs", payload)
    if result.get("code") == 0:
        print(f"块属性已保存: {block_id}")
    else:
        print(f"保存失败: {result.get('msg')}", file=sys.stderr)


# ─────────────────────────────────────────
# SQL / 事务
# ─────────────────────────────────────────

def cmd_query_sql(config, stmt):
    """执行 SQL 查询"""
    result = api_request(config, "/api/query/sql", {"stmt": stmt})
    data = result.get("data", [])
    if not data:
        print("(无结果)")
        return
    if isinstance(data, list) and len(data) > 0:
        keys = data[0].keys()
        print(" | ".join(str(k) for k in keys))
        print("-" * 100)
        for row in data[:50]:
            print(" | ".join(str(row.get(k, "")) for k in keys))
        if len(data) > 50:
            print(f"... 共 {len(data)} 条结果")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_flush_transaction(config):
    """刷新事务（落盘）"""
    result = api_request(config, "/api/sqlite/flushTransaction")
    if result.get("code") == 0:
        print("事务已刷新")
    else:
        print(f"刷新失败: {result.get('msg')}", file=sys.stderr)


# ─────────────────────────────────────────
# 模板
# ─────────────────────────────────────────

def cmd_template_render(config, id_, template):
    """渲染模板"""
    data = {"id": id_, "template": template}
    result = api_request(config, "/api/template/render", data)
    if result.get("code") == 0:
        data = result.get("data")
        if isinstance(data, dict):
            print(data.get("html", ""))
        elif data is None:
            print("(模板无输出)")
        else:
            print(data)
    else:
        print(f"渲染失败: {result.get('msg')}", file=sys.stderr)


def cmd_template_render_sprig(config, id_, text):
    """渲染 Sprig 模板"""
    data = {"id": id_, "text": text}
    result = api_request(config, "/api/template/renderSprig", data)
    if result.get("code") == 0:
        data = result.get("data")
        if isinstance(data, dict):
            print(data.get("html", ""))
        elif data is None:
            print("(模板无输出)")
        else:
            print(data)
    else:
        print(f"渲染失败: {result.get('msg')}", file=sys.stderr)


# ─────────────────────────────────────────
# 文件操作
# ─────────────────────────────────────────

def cmd_get_file(config, path):
    """读取工作区文件"""
    url = f"{config['api_url']}/api/file/getFile"
    headers = {}
    if config.get("api_token"):
        headers["Authorization"] = f"Token {config['api_token']}"
    try:
        resp = requests.post(url, headers={**headers, "Content-Type": "application/json"},
                             json={"path": path}, timeout=30)
        resp.raise_for_status()
        # getFile 成功时返回纯文本内容（非 JSON），失败时返回 JSON
        text = resp.text
        if text.startswith("{"):
            try:
                result = json.loads(text)
                if result.get("code") != 0:
                    print(f"读取失败: {result.get('msg')}", file=sys.stderr)
                    return
            except json.JSONDecodeError:
                pass
        print(text, end="")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_put_file(config, path, content):
    """写入工作区文件"""
    url = f"{config['api_url']}/api/file/putFile"
    headers = {}
    if config.get("api_token"):
        headers["Authorization"] = f"Token {config['api_token']}"
    # putFile 需要 multipart/form-data，不能用 JSON
    try:
        resp = requests.post(url, headers=headers,
                             files={"file": (path, content.encode("utf-8"), "application/octet-stream")},
                             data={"path": path},
                             timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") == 0:
            print(f"文件写入成功: {path}")
        else:
            print(f"写入失败: {result.get('msg')}", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_read_dir(config, path):
    """列出工作区目录"""
    result = api_request(config, "/api/file/readDir", {"path": path})
    if result.get("code") == 0:
        data = result.get("data")
        # API 返回 data: [list] 或 data: {"files": [list]}
        if isinstance(data, list):
            files = data
        elif isinstance(data, dict):
            files = data.get("files", [])
        else:
            files = []
        for f in files:
            if isinstance(f, dict):
                print(f"{f.get('name', ''):<40} {'dir' if f.get('isDir') else 'file':<6} {f.get('size', 0)}")
    else:
        print(f"读取失败: {result.get('msg')}", file=sys.stderr)


def cmd_remove_file(config, path):
    """删除工作区文件"""
    result = api_request(config, "/api/file/removeFile", {"path": path})
    if result.get("code") == 0:
        print(f"文件删除成功: {path}")
    else:
        print(f"删除失败: {result.get('msg')}", file=sys.stderr)


def cmd_rename_file(config, old_path, new_path):
    """重命名工作区文件"""
    data = {"path": old_path, "newPath": new_path}
    result = api_request(config, "/api/file/renameFile", data)
    if result.get("code") == 0:
        print(f"文件已重命名: {old_path} -> {new_path}")
    else:
        print(f"重命名失败: {result.get('msg')}", file=sys.stderr)


# ─────────────────────────────────────────
# 资产
# ─────────────────────────────────────────

def cmd_upload_asset(config, file_path):
    """上传资产文件"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)
    url = f"{config['api_url']}/api/asset/upload"
    # 上传文件不能带 Content-Type: application/json，否则和 multipart 冲突
    headers = {}
    if config.get("api_token"):
        headers["Authorization"] = f"Token {config['api_token']}"
    with open(file_path, "rb") as f:
        files = {"file": f}
        resp = requests.post(url, headers=headers, files=files, timeout=60)
    resp.raise_for_status()
    result = resp.json()
    if result.get("code") == 0:
        data = result.get("data")
        if isinstance(data, dict):
            print(data.get("url", "") or data.get("path", "") or str(data))
        elif isinstance(data, str):
            print(data)
        else:
            print(f"上传成功: {result}")
    else:
        print(f"上传失败: {result.get('msg')}", file=sys.stderr)


# ─────────────────────────────────────────
# 导出
# ─────────────────────────────────────────

def cmd_export_md(config, doc_id):
    """导出文档为 Markdown"""
    result = api_request(config, "/api/export/exportMdContent", {"id": doc_id})
    if result.get("code") == 0:
        print(result.get("data", {}).get("content", ""))
    else:
        print(f"导出失败: {result.get('msg')}", file=sys.stderr)


def cmd_export_resources(config, notebook_id, path):
    """导出一个目录下的所有资源文件（ZIP）
    path: hpath（如 /CherryStudio），脚本自动转为工作区路径 /data/<nb_id>/<name>
    """
    # API 要求工作区完整路径，不是 hpath
    ws_path = f"/data/{notebook_id}{path}"
    data = {"notebook": notebook_id, "paths": [ws_path]}
    result = api_request(config, "/api/export/exportResources", data)
    if result.get("code") == 0:
        print(json.dumps(result.get("data", {}), indent=2, ensure_ascii=False))
    else:
        print(f"导出失败: {result.get('msg')}", file=sys.stderr)


# ─────────────────────────────────────────
# 通知
# ─────────────────────────────────────────

def cmd_push_msg(config, msg, timeout="7s"):
    """推送消息"""
    data = {"msg": msg, "timeout": timeout}
    result = api_request(config, "/api/notification/pushMsg", data)
    if result.get("code") == 0:
        print("消息已推送")


def cmd_push_err_msg(config, msg, timeout="7s"):
    """推送错误消息"""
    data = {"msg": msg, "timeout": timeout}
    result = api_request(config, "/api/notification/pushErrMsg", data)
    if result.get("code") == 0:
        print("错误消息已推送")


# ─────────────────────────────────────────
# 系统
# ─────────────────────────────────────────

def cmd_init(config, api_url, api_token):
    """初始化：写入配置 + 验证连接 + 预热缓存"""
    # 检查是否已有配置，防止覆盖
    if CONFIG_PATH.exists():
        print(f"⚠️  配置已存在: {CONFIG_PATH}", file=sys.stderr)
        print("如需重新初始化，请先删除配置文件：", file=sys.stderr)
        print(f"  rm -rf {CONFIG_DIR}", file=sys.stderr)
        sys.exit(1)

    # 1. 写入配置
    new_config = {
        "api_url": api_url.rstrip("/"),
        "api_token": api_token,
        "local_path": config.get("local_path", ""),
    }
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(new_config, f, ensure_ascii=False, indent=2)

    # 2. 验证连接
    print(f"正在连接 {api_url} ...")
    try:
        result = api_request(new_config, "/api/system/version")
        version = result.get("data", "")
        print(f"✓ 连接成功，版本: {version}")
    except SystemExit:
        print("✗ 连接失败，请检查 URL / Token", file=sys.stderr)
        sys.exit(1)

    # 3. 预热缓存：获取笔记本列表
    print("正在获取笔记本列表 ...")
    result = api_request(new_config, "/api/notebook/lsNotebooks")
    notebooks = result.get("data", {}).get("notebooks", [])
    cache_set("notebooks", notebooks)
    print(f"✓ 已缓存 {len(notebooks)} 个笔记本")

    # 4. 预热缓存：获取每个笔记本的文档树
    print("正在预热文档树缓存 ...")
    for nb in notebooks:
        nb_id = nb.get("id")
        nb_name = nb.get("name", nb_id)
        docs = _build_doc_tree(new_config, nb_id)
        cache_set(f"doc_tree:{nb_id}", docs)
        print(f"  ✓ {nb_name}: {len(docs)} 篇文档")

    print(f"\n初始化完成！缓存文件: {CACHE_PATH}")
    print("后续直接使用其他命令即可，缓存自动命中")


def cmd_version(config):
    """获取系统版本"""
    result = api_request(config, "/api/system/version")
    print(result.get("data", ""))


def cmd_boot_progress(config):
    """获取启动进度"""
    result = api_request(config, "/api/system/bootProgress")
    if result.get("code") == 0:
        data = result.get("data", {})
        print(f"进度: {data.get('progress')} / 状态: {data.get('msg')}")
    else:
        print(f"获取失败: {result.get('msg')}", file=sys.stderr)


def cmd_current_time(config):
    """获取系统当前时间"""
    result = api_request(config, "/api/system/currentTime")
    if result.get("code") == 0:
        data = result.get("data")
        # API 返回毫秒时间戳（整数），也兼容 dict 格式
        if isinstance(data, dict):
            print(data.get("time", ""))
        else:
            print(data)
    else:
        print(f"获取失败: {result.get('msg')}", file=sys.stderr)


# ─────────────────────────────────────────
# ping
# ─────────────────────────────────────────

def cmd_ping(config):
    """测试连接（用 version 接口）"""
    result = api_request(config, "/api/system/version")
    print(f"版本: {result.get('data')} | 连接正常")


# ─────────────────────────────────────────
# 使用说明
# ─────────────────────────────────────────

def usage():
    print("""思源笔记 API 调用脚本

用法:
    python3 siyuan_api.py <command> [args...] [--no-cache]
缓存说明:
    默认走本地缓存（~/.config/siyuan/cache.json）
    --no-cache / --refresh 强制直连 API 并刷新缓存
    写操作（增/删/改）后自动使缓存失效

【缓存管理】
    cache_clear [key]        清除缓存（省略 key 则清所有）
    cache_status             查看缓存状态

【初始化】
    init <API URL> <Token>                    初始化配置并预热缓存

【笔记本】
    list_notebooks                              列出所有笔记本（缓存 14 天）
    get_notebook_conf <笔记本ID>                 获取笔记本配置
    create_notebook <名称>                       创建笔记本
    open_notebook <笔记本ID>                     打开笔记本
    close_notebook <笔记本ID>                    关闭笔记本
    rename_notebook <笔记本ID> <新名称>          重命名笔记本
    remove_notebook <笔记本ID>                   删除笔记本
    set_notebook_conf <笔记本ID> <JSON配置>       保存笔记本配置

【文档树】
    doc_tree <笔记本ID>                          查看文档树（缓存 14 天）
    search_doc <关键词> [笔记本ID]               搜索文档

【文档（文件树）】
    create_doc <笔记本ID> /路径 "标题" ["内容"]   创建文档
    remove_doc <笔记本ID> /系统路径.sy            删除文档（按路径）
    remove_doc_by_id <文档ID>                     删除文档（按ID）
    rename_doc <笔记本ID> /路径 "新标题"          重命名文档（按路径）
    rename_doc_by_id <文档ID> "新标题"            重命名文档（按ID）
    move_docs <笔记本ID> /从路径 <目标笔记本ID> /到路径  移动文档
    move_docs_by_id <文档ID> <目标块ID> <索引>   移动文档（按ID）
    get_hpath_by_id <块ID>                        获取人类可读路径（按ID）
    get_hpath_by_path <笔记本ID> /路径            获取人类可读路径（按路径）
    get_ids_by_hpath <笔记本ID> "/a/b/c"          获取人类可读路径对应的ID列表
    get_path_by_id <块ID>                        获取物理路径（按ID）

【块操作】
    insert_block <父块ID> markdown "内容"         插入块
    append_block <父块ID> <类型> "内容"           追加块（类型: markdown/query_embed/dom）
    prepend_block <父块ID> <类型> "内容"          前置块
    update_block <块ID> "markdown内容"            更新块内容
    delete_block <块ID>                          删除块
    get_block_kramdown <块ID>                   获取块 Kramdown 源码
    get_child_blocks <块ID>                     获取子块列表
    move_block <块ID> <目标块ID> <索引>          移动块
    fold_block <块ID>                            折叠块
    unfold_block <块ID>                          展开块
    transfer_block_ref <块ID> <目标块ID>          转移块引用

【属性】
    get_block_attrs <块ID>                       获取块属性
    set_block_attrs <块ID> '<JSON>'              设置块属性

【SQL / 事务】
    query_sql <SQL语句>                          执行 SQL 查询
    flush_transaction                            刷新事务（落盘）

【模板】
    template_render <块ID> "<模板内容>"           渲染模板
    template_render_sprig <块ID> "<Sprig模板>"   渲染 Sprig 模板

【文件操作】
    get_file /data/xxx.txt                       读取工作区文件
    put_file /data/xxx.txt "内容"                写入工作区文件
    read_dir /data/                              列出工作区目录
    remove_file /data/xxx.txt                     删除工作区文件
    rename_file /旧路径 /新路径                   重命名工作区文件

【资产】
    upload_asset <本地文件路径>                    上传资产文件（返回 URL）

【导出】
    export_md <文档ID>                           导出文档为 Markdown
    export_resources <笔记本ID> /路径            导出一个目录下的资源（ZIP，paths参数）

【通知】
    push_msg "消息内容" [timeout]                 推送消息（默认 7s）
    push_err_msg "错误信息" [timeout]            推送错误消息

【系统】
    ping                                         测试连接
    version                                      获取系统版本
    boot_progress                               获取启动进度
    current_time                                获取系统当前时间
""", file=sys.stderr)


if __name__ == "__main__":
    config = load_config()

    # 解析 --no-cache / --refresh 参数
    use_cache = True
    real_args = []
    for a in sys.argv[1:]:
        if a in ("--no-cache", "--refresh"):
            use_cache = False
        else:
            real_args.append(a)

    if not real_args:
        usage()
        sys.exit(1)

    cmd = real_args[0]
    args = real_args[1:]

    # ── 缓存管理 ──
    if cmd == "cache_status":
        c = load_cache()
        print("缓存状态:")
        for key, entry in c.items():
            age = int(time.time() - entry["ts"])
            data = entry["data"]
            if isinstance(data, list):
                desc = f"{len(data)} 项"
            elif isinstance(data, dict):
                desc = f"dict ({len(data)} keys)"
            else:
                desc = str(data)[:40]
            print(f"  {key:<30} {age:>4}s 前  {desc}")
        print(f"\n缓存文件: {CACHE_PATH}")
        print(f"总计 {len(c)} 条记录")
        sys.exit(0)

    if cmd == "cache_clear":
        key = args[0] if args else None
        if key and key != "*":
            cache_invalidate(key)
            print(f"已清除缓存: {key}")
        else:
            cache_invalidate()
            print("已清除所有缓存")
        sys.exit(0)

    # ── 初始化 ──
    if cmd == "init":
        if len(args) < 2:
            print("用法: python3 siyuan_api.py init <API URL> <Token>", file=sys.stderr)
            sys.exit(1)
        cmd_init(config, args[0], args[1])

    # ── 笔记本 ──
    if cmd == "list_notebooks":
        cmd_list_notebooks(config, use_cache)

    elif cmd == "get_notebook_conf":
        cmd_get_notebook(config, args[0]) if args else (print("缺少笔记本ID", file=sys.stderr), sys.exit(1))

    elif cmd == "create_notebook":
        cmd_create_notebook(config, args[0]) if args else (print("缺少名称", file=sys.stderr), sys.exit(1))

    elif cmd == "open_notebook":
        cmd_open_notebook(config, args[0]) if args else (print("缺少笔记本ID", file=sys.stderr), sys.exit(1))

    elif cmd == "close_notebook":
        cmd_close_notebook(config, args[0]) if args else (print("缺少笔记本ID", file=sys.stderr), sys.exit(1))

    elif cmd == "rename_notebook":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_rename_notebook(config, args[0], args[1])

    elif cmd == "remove_notebook":
        cmd_remove_notebook(config, args[0]) if args else (print("缺少笔记本ID", file=sys.stderr), sys.exit(1))

    elif cmd == "set_notebook_conf":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_set_notebook_conf(config, args[0], args[1])

    # ── 文档树 ──
    elif cmd == "doc_tree":
        if not args: print("缺少笔记本ID", file=sys.stderr), sys.exit(1)
        cmd_doc_tree(config, args[0], use_cache)

    elif cmd == "search_doc":
        notebook = args[1] if len(args) > 1 else None
        cmd_search_doc(config, args[0], notebook)

    # ── 文档 ──
    elif cmd == "create_doc":
        if len(args) < 3: print("缺少参数", file=sys.stderr), sys.exit(1)
        nb, path, title = args[0], args[1], args[2]
        content = args[3] if len(args) > 3 else f"# {title}"
        cmd_create_doc(config, nb, path, title, content)

    elif cmd == "remove_doc":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_remove_doc(config, args[0], args[1])

    elif cmd == "remove_doc_by_id":
        cmd_remove_doc_by_id(config, args[0]) if args else (print("缺少文档ID", file=sys.stderr), sys.exit(1))

    elif cmd == "rename_doc":
        if len(args) < 3: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_rename_doc(config, args[0], args[1], args[2])

    elif cmd == "rename_doc_by_id":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_rename_doc_by_id(config, args[0], args[1])

    elif cmd == "move_docs":
        if len(args) < 5: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_move_docs(config, args[0], args[1], args[2], args[3])

    elif cmd == "move_docs_by_id":
        if len(args) < 3: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_move_docs_by_id(config, args[0], args[1], args[2])

    elif cmd == "get_hpath_by_id":
        cmd_get_hpath_by_id(config, args[0]) if args else (print("缺少块ID", file=sys.stderr), sys.exit(1))

    elif cmd == "get_hpath_by_path":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_get_hpath_by_path(config, args[0], args[1])

    elif cmd == "get_ids_by_hpath":
        if len(args) < 2: print("用法: get_ids_by_hpath <笔记本ID> /路径", file=sys.stderr), sys.exit(1)
        cmd_get_ids_by_hpath(config, args[0], args[1])

    elif cmd == "get_path_by_id":
        cmd_get_path_by_id(config, args[0]) if args else (print("缺少块ID", file=sys.stderr), sys.exit(1))

    # ── 块 ──
    elif cmd == "insert_block":
        if len(args) < 3: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_insert_block(config, args[0], args[1], args[2])

    elif cmd == "append_block":
        if len(args) < 3: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_append_block(config, args[0], args[1], args[2])

    elif cmd == "prepend_block":
        if len(args) < 3: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_prepend_block(config, args[0], args[1], args[2])

    elif cmd == "update_block":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_update_block(config, args[0], args[1])

    elif cmd == "delete_block":
        cmd_delete_block(config, args[0]) if args else (print("缺少块ID", file=sys.stderr), sys.exit(1))

    elif cmd == "get_block_kramdown":
        cmd_get_block_kramdown(config, args[0]) if args else (print("缺少块ID", file=sys.stderr), sys.exit(1))

    elif cmd == "get_child_blocks":
        cmd_get_child_blocks(config, args[0]) if args else (print("缺少块ID", file=sys.stderr), sys.exit(1))

    elif cmd == "move_block":
        if len(args) < 3: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_move_block(config, args[0], args[1], args[2])

    elif cmd == "fold_block":
        cmd_fold_block(config, args[0]) if args else (print("缺少块ID", file=sys.stderr), sys.exit(1))

    elif cmd == "unfold_block":
        cmd_unfold_block(config, args[0]) if args else (print("缺少块ID", file=sys.stderr), sys.exit(1))

    elif cmd == "transfer_block_ref":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_transfer_block_ref(config, args[0], args[1])

    # ── 属性 ──
    elif cmd == "get_block_attrs":
        cmd_get_block_attrs(config, args[0]) if args else (print("缺少块ID", file=sys.stderr), sys.exit(1))

    elif cmd == "set_block_attrs":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_set_block_attrs(config, args[0], args[1])

    # ── SQL ──
    elif cmd == "query_sql":
        cmd_query_sql(config, args[0]) if args else (print("缺少 SQL", file=sys.stderr), sys.exit(1))

    elif cmd == "flush_transaction":
        cmd_flush_transaction(config)

    # ── 模板 ──
    elif cmd == "template_render":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_template_render(config, args[0], args[1])

    elif cmd == "template_render_sprig":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_template_render_sprig(config, args[0], args[1])

    # ── 文件 ──
    elif cmd == "get_file":
        cmd_get_file(config, args[0]) if args else (print("缺少路径", file=sys.stderr), sys.exit(1))

    elif cmd == "put_file":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_put_file(config, args[0], args[1])

    elif cmd == "read_dir":
        cmd_read_dir(config, args[0]) if args else (print("缺少路径", file=sys.stderr), sys.exit(1))

    elif cmd == "remove_file":
        cmd_remove_file(config, args[0]) if args else (print("缺少路径", file=sys.stderr), sys.exit(1))

    elif cmd == "rename_file":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_rename_file(config, args[0], args[1])

    # ── 资产 ──
    elif cmd == "upload_asset":
        cmd_upload_asset(config, args[0]) if args else (print("缺少文件路径", file=sys.stderr), sys.exit(1))

    # ── 导出 ──
    elif cmd == "export_md":
        cmd_export_md(config, args[0]) if args else (print("缺少文档ID", file=sys.stderr), sys.exit(1))

    elif cmd == "export_resources":
        if len(args) < 2: print("缺少参数", file=sys.stderr), sys.exit(1)
        cmd_export_resources(config, args[0], args[1])

    # ── 通知 ──
    elif cmd == "push_msg":
        msg = args[0] if args else ""
        timeout = args[1] if len(args) > 1 else "7s"
        cmd_push_msg(config, msg, timeout)

    elif cmd == "push_err_msg":
        msg = args[0] if args else ""
        timeout = args[1] if len(args) > 1 else "7s"
        cmd_push_err_msg(config, msg, timeout)

    # ── 系统 ──
    elif cmd == "version":
        cmd_version(config)

    elif cmd == "boot_progress":
        cmd_boot_progress(config)

    elif cmd == "current_time":
        cmd_current_time(config)

    elif cmd == "ping":
        cmd_ping(config)

    else:
        print(f"未知命令: {cmd}", file=sys.stderr)
        usage()
        sys.exit(1)
