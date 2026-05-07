# Git Token 安全推送

## 三种推送方式对比

| 方式 | Token 落盘位置 | 安全等级 |
|------|---------------|---------|
| `https://token@github.com` | `.git/config` 明文 | ❌ 危险 |
| `GIT_ASKPASS` + `/tmp/` 脚本 | 内存 + `/tmp/` 进程退出即删 | ⚠️ 可接受 |
| `git credential.helper cache` | 内存（超时后清除） | ⚠️ 可接受 |
| SSH 密钥 | 无 token 落盘 | ✅ 最安全 |

## 推荐：GIT_ASKPASS 方式

```bash
export GIT_ASKPASS=/tmp/git-askpass.sh
cat > /tmp/git-askpass.sh << 'EOF'
#!/bin/bash
echo "${GITHUB_TOKEN}"
EOF
chmod +x /tmp/git-askpass.sh
git push origin main
```

**优点**：remote URL 保持干净（不含 token），push 完进程结束脚本就没了。

**注意**：不要把 `GIT_ASKPASS` 脚本放到持久化目录，推荐 `/tmp/`。

## Token 泄露检查

```bash
# 检查 commit 历史是否有 token
git log --all --source --oneline | xargs -I{} sh -c \
  'git show {} 2>/dev/null | grep -E "ghp_[a-zA-Z0-9]{36}"' || echo "clean"

# 检查 .git/config
cat .git/config | grep -E "token|ghp_"
```

## 发现泄露后的应急

```bash
# 1. 立刻轮换 GitHub token
#    Settings → Developer settings → Personal access tokens → Regenerate

# 2. 清除历史（如果已经 push）
git filter-branch --force --index-filter \
  'git rm -rf --cached --ignore-unmatch PATH/TO/SENSITIVE_FILE' \
  --prune-empty --tag-name-filter cat -- --all

# 3. Force push
git push origin main --force-with-lease
```

## SSH 方式（最安全但需额外配置）

```bash
# 生成本地密钥（不设密码，一路回车）
ssh-keygen -t ed25519 -C "your_email" -f ~/.ssh/hermes_github

# 上传公钥到 GitHub
# Settings → SSH and GPG keys → New SSH key

# 配置 remote
git remote set-url origin git@github.com:owner/repo.git

# 验证
ssh -T git@github.com
```
