# Proxy Pitfall — publish_skill.py

## Problem

`subprocess.run()` without explicit `env` parameter does NOT inherit shell proxy
variables reliably. The script's `_load_dotenv()` loads from `~/.hermes/.env`, but
when the shell already has `HTTP_PROXY` set (via `source ~/.hermes/.env`), the
load_dotenv skips it (line 37: `if key not in os.environ`). The subprocess may
then lose the proxy.

## Symptoms

```
fatal: unable to access '...': GnuTLS recv error (-110)
```

This is a TLS/proxy error, NOT an auth error. Push/pull/clone all fail.

## Fix

Every `subprocess.run()` call must use `env=_proxy_env()`:

```python
def _proxy_env() -> dict:
    """返回包含代理环境变量的 env dict，供 subprocess 使用。"""
    env = os.environ.copy()
    proxy = env.get('HTTP_PROXY') or env.get('http_proxy')
    if proxy:
        env['http_proxy'] = proxy
        env['https.proxy'] = proxy
    return env
```

Apply to: `run()`, `curl_get()`, `check_repo_exists()`, `git pull`, `git push`.

## Where NOT to apply

- `git config` (local, no network)
- `git rev-parse` (local, no network)
- `audit_scan.py` subprocess (local script)

## Reference

- Script: `~/.hermes/skills/productivity/skill-publisher/scripts/publish_skill.py`
- See `_proxy_env()` function definition
- Added in v2.4.1 (2026-05-14)
