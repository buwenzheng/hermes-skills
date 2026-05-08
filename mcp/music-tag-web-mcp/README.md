# Music Tag Web MCP

通过 Music Tag Web 内置的 MCP 服务管理音乐文件元数据标签。

## 快速开始

1. 启动 Music Tag Web（确保 6002 端口可访问）
2. 获取 MCP Token
3. 设置环境变量：`export MUSIC_TAG_WEB_TOKEN="你的token"`
4. 验证：`curl -s http://127.0.0.1:6002/mcp/ -H "Authorization: Bearer $MUSIC_TAG_WEB_TOKEN"`

## 支持功能

- 查询曲目信息（标题、艺术家、流派、专辑）
- 批量编辑/添加标签
- 按条件筛选音乐

## 配置

详见 [SKILL.md](SKILL.md)
