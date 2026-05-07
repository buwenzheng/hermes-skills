# GitHub 操作代理配置

## 何时需要

GitHub 在国内访问经常超时，需要为单个项目配置 HTTP/HTTPS 代理。

## 项目级配置（推荐）

```bash
cd /path/to/repo
git config http.proxy http://127.0.0.1:7890
git config https.proxy http://127.0.0.1:7890
```

这会在 `.git/config` 里写入，**不影响全局**，只影响当前仓库。

## 验证

```bash
git remote -v
git config --get http.proxy
```

## 临时用代理 clone

```bash
git clone --depth 1 https://github.com/owner/repo.git /tmp/repo \
  -c http.proxy=http://127.0.0.1:7890 \
  -c https.proxy=http://127.0.0.1:7890
```

## 常用代理端口参考

| 代理工具 | HTTP 端口 | SOCKS5 端口 |
|----------|-----------|-------------|
| Clash | 7890 | 7891 |
| V2Ray | 10809 | 10808 |
| Surge | 6153 | 6152 |

实际端口以本地配置为准。
