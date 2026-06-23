# JD 签到脚本独立运行说明

## 背景

faker2 仓库 (shufflewzc/faker2) 的 JD 签到脚本设计用于青龙面板，但实际可以独立运行。

## 依赖分析

| 组件 | 依赖青龙？ | 说明 |
|------|-----------|------|
| `JD_COOKIE` 环境变量 | ❌ | `jdCookie.js` 从 `process.env.JD_COOKIE` 读取 |
| `Env` 类 | ❌ | 自包含工具类，提供 HTTP、通知、存储 |
| `ql.js` | ✅ | 调青龙 API (`localhost:5600`) 管理 Cookie，签到脚本不用 |
| npm 依赖 | ❌ | `got`、`tough-cookie`、`crypto-js`、`dotenv` |

## 运行步骤

```bash
cd faker2目录
npm init -y
npm install got tough-cookie crypto-js dotenv
export JD_COOKIE="pt_key=xxx;pt_pin=xxx;"
node jd_xxx.js
```

## Cookie 获取（⚠️ 2026.05 更新）

**京东已更改认证策略，浏览器 Cookie 中不再包含 `pt_key`。**

验证过程：分别从 jd.com 和 m.jd.com 获取完整 Cookie，均无 `pt_key` 和 `pt_pin` 字段。现有 Cookie 只有 `pin`、`__jda`、`__jdv` 等追踪类字段。

### 可行的替代方案

| 方案 | 可行性 | 说明 |
|------|--------|------|
| 抓包京东 APP | ⭐⭐⭐ | 用 Charles/mitmproxy 抓 APP 请求，Cookie 中有 pt_key |
| Playwright 模拟签到 | ⭐⭐⭐ | 浏览器自动化，模拟点击签到按钮，不依赖 pt_key |
| 等社区修复 | ? | 看有没有新的获取方式 |

### 抓包获取 pt_key 步骤

1. 电脑安装 Charles/mitmproxy
2. 手机配置代理指向电脑
3. 安装并信任 CA 证书
4. 打开京东 APP 随便点一下
5. 在抓包工具中找到请求头里的 Cookie
6. 提取 `pt_key=xxx;pt_pin=xxx;`

## 注意事项

- 部分脚本有 GITHUB 环境检测会自动退出
- Cookie 有效期有限，需定期更新
- 代码高度混淆，维护成本高
- 即使拿到 pt_key，签名算法也在不断更新，脚本可能随时失效
