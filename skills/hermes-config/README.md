# hermes-config

Hermes Agent 配置管理经验库。记录修改配置时遇到的坑和最佳实践。

## 何时使用

- 添加/修改 LLM provider
- 切换默认模型
- 编辑 API key
- 配置相关报错排查

## 核心原则

1. **验证 key 用 curl，不用 Hermes 输出** — Hermes 可能静默 fallback
2. **key 写 .env，config.yaml 用 `${VAR}` 引用** — 不要混在一起
3. **改完配置要重启** — CLI `/reset`，Gateway `hermes gateway restart`
4. **token 不进日志** — 飞书等平台会截断，必须持久化到 .env

详见 [SKILL.md](SKILL.md)
