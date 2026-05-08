---
name: music-tag-web-mcp
description: "Use when querying or editing music file metadata (tags, genres, titles, artists) via Music Tag Web's MCP service."
version: 1.0.2
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Music, Metadata, MCP, Media]
    related_skills: [music-tag-web-mcp]
required_environment_variables:
  - MUSIC_TAG_WEB_TOKEN
---

# Music Tag Web MCP

通过 Music Tag Web 内置的 MCP（Model Context Protocol）服务管理音乐文件元数据标签。

## INT 初始化步骤

首次使用前，需要配置 MCP Token：

```bash
# 1. 确认 Music Tag Web 已启动并运行在 6002 端口
curl -s http://127.0.0.1:6002/mcp/ > /dev/null 2>&1 && echo "服务正常" || echo "服务未启动"

# 2. 获取你的 Token（从 Music Tag Web 管理界面或启动日志获取）
# 3. 设置环境变量
export MUSIC_TAG_WEB_TOKEN="你的实际token"

# 4. 验证连接
curl -s http://127.0.0.1:6002/mcp/ \
  -H "Authorization: Bearer $MUSIC_TAG_WEB_TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  | python3 -m json.tool
```

## When to Use

- 查询音乐库中的曲目信息（标题、艺术家、流派、专辑等）
- 批量编辑或添加音乐标签
- 按流派/艺术家等条件筛选音乐
- 读取或修改音乐文件元数据

**前置条件：** Music Tag Web 已启动并正常运行。

## MCP 服务信息

```
地址:   http://127.0.0.1:6002/mcp/
Token:  $MUSIC_TAG_WEB_TOKEN（环境变量）
```

所有 MCP 请求需在 HTTP 头携带 Token：

```
Authorization: Bearer $MUSIC_TAG_WEB_TOKEN
```

## 常用 MCP 工具调用

### initialize（初始化连接）

```bash
curl -s -X POST http://127.0.0.1:6002/mcp/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $MUSIC_TAG_WEB_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
  }'
```

### 列出所有可用工具

```bash
curl -s -X POST http://127.0.0.1:6002/mcp/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $MUSIC_TAG_WEB_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

### 调用具体工具

先通过 `tools/list` 获取实际工具名称（格式如下），再调用具体工具：

```bash
curl -s -X POST http://127.0.0.1:6002/mcp/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $MUSIC_TAG_WEB_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "<工具名>",
      "arguments": {}
    }
  }'
```

（不要硬编码工具名，先用 `tools/list` 确认当前可用工具）

## 配置文件示例

在 Claude Code 的 `.mcp.json` 中配置：

```json
{
  "mcpServers": {
    "music-tag-web": {
      "type": "http",
      "url": "http://127.0.0.1:6002/mcp/",
      "headers": {
        "Authorization": "Bearer ${MUSIC_TAG_WEB_TOKEN}"
      }
    }
  }
}
```

在 Codex 的 `config.toml` 中配置：

```toml
[mcp_servers.music-tag]
url = "http://127.0.0.1:6002/mcp/"
http_headers = { "Authorization" = "Bearer ${MUSIC_TAG_WEB_TOKEN}" }
```

## 流派标签说明

Music Tag Web 的流派标签采用自由字符串格式，中英文混用均可，示例：

- `嘻哈` / `hip-hop`
- `电子` / `electronic`
- `流行` / `pop`

建议按原样存储和搜索，不做多标签解析。

## Common Pitfalls

1. **Token 错误**：MCP 服务返回 401 时，首先检查 Token 是否正确、是否遗漏 `Bearer ` 前缀。
2. **端口不对**：确认 Music Tag Web 监听端口（默认 8002，当前实例为 6002）。
3. **curl 结果为空**：加上 `-s` 静默模式，如果服务未启动或端口不对，curl 会卡住或超时。

## Verification Checklist

- [ ] 环境变量 `MUSIC_TAG_WEB_TOKEN` 已设置
- [ ] MCP 服务已验证可用（`initialize` 返回 `serverInfo`，证明连接正常）
- [ ] `tools/list` 返回了工具清单
- [ ] 至少成功调用了一个 MCP 工具
