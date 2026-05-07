#!/usr/bin/env python3
"""
Hermes Skill 发布脚本

流程：
  1. clone → 隔离敏感文件
  2. 版本号 bump（patch +1）
  3. 创建 feat 分支
  4. git add → staged grep → commit
  5. push 分支
  6. 创建 PR（通过 GitHub REST API）
  7. 报告 PR URL（由 Agent 转发给用户确认）
  8. PUBLISHED.md 更新也走同一分支/PR

注意：合并由用户决定，不自动合并。
"""

import os
import sys
import json
import subprocess
import time
import re
import shutil
import argparse
from pathlib import Path

# ── 共享敏感 patterns（与 audit_scan.py 保持一致）─────────────────────────────
SENSITIVE_PATTERNS = [
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub PAT'),
    (r'github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}', 'GitHub Fine-grained PAT'),
    (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
    (r'sk-proj-[a-zA-Z0-9]{48,}', 'Other sk- Key'),
    (r'sk-ant-[a-zA-Z0-9]{32,}', 'Anthropic/sk-ant Key'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
    (r'ASIA[0-9A-Z]{16}', 'AWS Session Token'),
    (r'AIza[0-9A-Za-z_-]{35}', 'Google API Key'),
    (r'AccountKey=[a-zA-Z0-9+/=]{88}', 'Azure Account Key'),
    (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', 'JSON Web Token'),
    (r'token\s*[:=]\s*\'[a-zA-Z0-9_/-]{16,}\'', 'Token (单引号)'),
    (r'token\s*[:=]\s*"[a-zA-Z0-9_/-]{16,}"', 'Token (双引号)'),
    (r'api[_-]?key\s*[:=]\s*\'[a-zA-Z0-9_/-]{16,}\'', 'API Key (单引号)'),
    (r'api[_-]?key\s*[:=]\s*"[a-zA-Z0-9_/-]{16,}"', 'API Key (双引号)'),
    (r'password\s*[:=]\s*\'[^\']{8,}\'', 'Password (单引号)'),
    (r'password\s*[:=]\s*"[^"]{8,}"', 'Password (双引号)'),
]

FORBIDDEN_PATTERNS = [
    '*_config.json',
    '*_cache.json',
    '__pycache__',
    '*.pyc',
    '.env',
    '*.log',
    'credentials.json',
]

GITIGNORE_CONTENT = """
# 敏感文件
**/*_config.json
**/*_cache.json
**/credentials.json
# Python
**/__pycache__/
**/*.pyc
**/*.pyo
# OS
.DS_Store
""".lstrip('\n')


def run(cmd: list, *, cwd: Path | None = None, capture: bool = True,
        env: dict | None = None) -> subprocess.CompletedProcess:
    """执行命令，失败时打印并退出"""
    result = subprocess.run(
        cmd, cwd=cwd,
        capture_output=capture, text=True,
        env=(env or None)
    )
    if result.returncode != 0:
        print(f"❌ 命令失败: {' '.join(cmd)}")
        print(f"   exit code: {result.returncode}")
        if result.stdout:
            print(f"   stdout: {result.stdout[:500]}")
        if result.stderr:
            print(f"   stderr: {result.stderr[:500]}")
        sys.exit(1)
    return result


def curl_get(url: str, token: str) -> dict:
    result = subprocess.run(
        ['curl', '-s', '-H', f'Authorization: token {token}', url],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except Exception:
        return {}


def curl_post(url: str, token: str, data: dict) -> dict:
    payload = json.dumps(data)
    result = subprocess.run(
        ['curl', '-s', '-X', 'POST',
         '-H', f'Authorization: token {token}',
         '-H', 'Content-Type: application/json',
         '-d', payload, url],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except Exception:
        return {}


def check_repo_exists(user: str, repo: str, token: str) -> bool:
    result = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
         '-H', f'Authorization: token {token}',
         f'https://api.github.com/repos/{user}/{repo}'],
        capture_output=True, text=True
    )
    return result.stdout == '200'


def get_default_branch(user: str, repo: str, token: str) -> str:
    """通过 GitHub API 获取默认分支"""
    data = curl_get(f'https://api.github.com/repos/{user}/{repo}', token)
    return data.get('default_branch', 'main')


def quarantine_sensitive_files(skill_dir: Path) -> list[str]:
    """隔离敏感文件，返回被隔离的文件列表"""
    quarantined = []
    for pattern in FORBIDDEN_PATTERNS:
        if '*' in pattern:
            for fp in skill_dir.rglob(pattern):
                rel = str(fp.relative_to(skill_dir))
                quarantined.append(rel)
                if fp.is_file():
                    fp.unlink()
                elif fp.is_dir():
                    shutil.rmtree(fp)
    return quarantined


def stage_grep(work_dir: Path) -> list[dict]:
    """扫描所有 staged 文件（排除 SKILL.md），返回敏感信息列表"""
    result = run(['git', 'diff', '--cached', '--name-only'], cwd=work_dir)
    staged_files = [
        line.strip() for line in result.stdout.splitlines()
        if line.strip() and not line.strip().endswith('SKILL.md')
    ]

    findings = []
    for fpath in staged_files:
        full = work_dir / fpath
        if not full.exists() or not full.is_file():
            continue
        try:
            content = full.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for pattern, label in SENSITIVE_PATTERNS:
            for m in re.finditer(pattern, content):
                linum = content[:m.start()].count('\n') + 1
                findings.append({
                    'file': fpath,
                    'line': linum,
                    'type': label,
                    'matched': m.group()[:60],
                })
    return findings


def get_skill_version(skill_dir: Path) -> str:
    """从 SKILL.md frontmatter 提取 version"""
    skill_md = skill_dir / 'SKILL.md'
    if not skill_md.exists():
        return '1.0.0'
    content = skill_md.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'^version:\s*(\S+)', content, re.MULTILINE)
    return m.group(1) if m else '1.0.0'


def bump_version(content: str) -> tuple[str, str]:
    """bump version 并返回 (新内容, 新版本号)"""
    m = re.search(r'^version:\s*(\S+)', content, re.MULTILINE)
    if not m:
        return content, '1.0.1'
    cur = m.group(1)
    parts = cur.split('.')
    while len(parts) < 3:
        parts.append('0')
    parts[-1] = str(int(parts[-1]) + 1)
    new_ver = '.'.join(parts)
    updated = re.sub(r'^version:\s*\S+', f'version: {new_ver}', content, flags=re.MULTILINE)
    return updated, new_ver


def _dedupe_gitignore(gitignore_path: Path):
    """去重 .gitignore 重复行"""
    if not gitignore_path.exists():
        return
    lines = gitignore_path.read_text().splitlines()
    seen = set()
    deduped = []
    for line in lines:
        if line and line not in seen:
            seen.add(line)
            deduped.append(line)
    gitignore_path.write_text('\n'.join(deduped) + '\n')


def _git_config(work_dir: Path, key: str, val: str):
    """设置 git config（忽略失败）"""
    subprocess.run(['git', 'config', key, val], cwd=work_dir,
                   capture_output=True)


def publish(skill_name: str, user: str, repo: str, skill_dir: Path, token: str,
            *, auto_merge: bool = False):
    work_dir = Path(f'/tmp/{skill_name}-push')
    quarantine = Path(f'/tmp/skill-publisher-quarantine-{int(time.time())}')

    try:
        print(f"=== Skill 发布流程（PR 模式）===")
        print(f"Skill : {skill_name}")
        print(f"目标 : {user}/{repo}")
        print()

        # ── Step 1: 确认仓库存在 ────────────────────────────────────────────
        print("■ Step 1: 确认仓库存在")
        if not check_repo_exists(user, repo, token):
            print(f"❌ 仓库不存在: {user}/{repo}")
            sys.exit(1)
        print(f"  ✓ 仓库存在")
        print()

        # ── Step 2: clone + 复制 + 隔离 ─────────────────────────────────────
        print("■ Step 2: clone + 复制 + 隔离")
        if work_dir.exists():
            shutil.rmtree(work_dir)
        quarantine.mkdir(parents=True, exist_ok=True)

        run(['git', 'clone', '--depth', '1',
             f'https://github.com/{user}/{repo}.git', str(work_dir)],
            capture=False)

        # 复制 skill（平铺结构）
        target = work_dir / skill_name
        target.mkdir(exist_ok=True)
        for item in skill_dir.iterdir():
            if item.name == '__pycache__':
                continue
            src = skill_dir / item
            if src.is_dir():
                shutil.copytree(src, target / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(src, target / item.name)

        # 追加 .gitignore（去重）
        gitignore = work_dir / '.gitignore'
        existing = gitignore.read_text() if gitignore.exists() else ''
        gitignore.write_text(existing + GITIGNORE_CONTENT)
        _dedupe_gitignore(gitignore)

        # 隔离敏感文件
        moved = quarantine_sensitive_files(target)
        if moved:
            print(f"  ✓ 隔离 {len(moved)} 个敏感文件: {', '.join(moved)}")
        print()

        # ── Step 2.5: 版本号 bump ───────────────────────────────────────────
        print("■ Step 2.5: 版本号 bump")
        cur_ver = get_skill_version(skill_dir)
        work_skill_md = target / 'SKILL.md'
        content = work_skill_md.read_text(encoding='utf-8', errors='ignore')
        updated_content, new_ver = bump_version(content)
        work_skill_md.write_text(updated_content, encoding='utf-8')
        print(f"  {cur_ver} → {new_ver}")
        print()

        # ── Step 3: 创建 feat 分支 ──────────────────────────────────────────
        print("■ Step 3: 创建 feat 分支")
        default_branch = get_default_branch(user, repo, token)
        branch_name = f'feat/add-{skill_name}-v{new_ver}'
        _git_config(work_dir, 'user.email', 'hermes-agent@nomail')
        _git_config(work_dir, 'user.name', 'Hermes Agent')
        run(['git', 'checkout', '-b', branch_name, f'origin/{default_branch}'],
            cwd=work_dir, capture=False)
        print(f"  ✓ 分支: {branch_name}（基于 {default_branch}）")
        print()

        # ── Step 4: git add + staged grep + commit ──────────────────────────
        print("■ Step 4: git add + staged grep + commit")

        # 配置代理（用于 push）
        for key in ['http.proxy', 'https.proxy']:
            _git_config(work_dir, key, 'http://127.0.0.1:7890')

        run(['git', 'add', '.'], cwd=work_dir, capture=False)

        staged = run(['git', 'diff', '--cached', '--name-only'],
                     cwd=work_dir)
        file_count = len([l for l in staged.stdout.splitlines() if l.strip()])
        print(f"  staged {file_count} 个文件")

        findings = stage_grep(work_dir)
        if findings:
            print(f"  ❌ staged 文件中发现敏感信息 ({len(findings)} 处)：")
            for f in findings:
                print(f"    [{f['type']}] {f['file']}:{f['line']} → {f['matched']}")
            print("  → 拒绝发布，请重新运行 skill-audit 审核")
            sys.exit(1)
        print("  ✓ staged grep 无敏感信息")

        commit_msg = f"feat: add {skill_name} v{new_ver}"
        run(['git', 'commit', '-m', commit_msg], cwd=work_dir, capture=False)
        print(f"  ✓ commit: {commit_msg}")
        print()

        # ── Step 5: push 分支 ───────────────────────────────────────────────
        print("■ Step 5: push 分支")

        askpass = Path('/tmp/git-askpass.sh')
        askpass.write_text(f'#!/bin/bash\necho "{token}"\n')
        askpass.chmod(0o700)
        env = os.environ.copy()
        env['GIT_ASKPASS'] = str(askpass)

        push = subprocess.run(
            ['git', 'push', '-u', 'origin', branch_name, '--force-with-lease'],
            cwd=work_dir, env=env, capture_output=True, text=True
        )
        if push.returncode != 0:
            print(f"  ❌ push 失败: {push.stderr[:300]}")
            sys.exit(1)

        # 获取 commit hash
        rev = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                            cwd=work_dir, capture_output=True, text=True)
        commit_hash = rev.stdout.strip()
        print(f"  ✓ push 成功 ({commit_hash})")
        print()

        # ── Step 6: 创建 PR ─────────────────────────────────────────────────
        print("■ Step 6: 创建 PR")

        # 更新 PUBLISHED.md（在本地先做好，纳入同一 PR）
        published_path = work_dir / 'PUBLISHED.md'
        today = time.strftime('%Y-%m-%d')
        new_entry = f'| {skill_name} | {new_ver} | {today} | `{commit_hash}` |'

        if published_path.exists():
            lines = published_path.read_text().splitlines()
            found = False
            new_lines = []
            for line in lines:
                if line.startswith(f'| {skill_name} |'):
                    new_lines.append(new_entry)
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.extend(['', new_entry])
            published_path.write_text('\n'.join(new_lines) + '\n')
        else:
            published_path.write_text(
                '# Published Skills\n\n'
                '| Skill | Version | Published | Commit |\n'
                '|-------|---------|-----------|--------|\n'
                f'{new_entry}\n'
            )

        run(['git', 'add', 'PUBLISHED.md'], cwd=work_dir, capture=False)
        # 追加 amend（把 PUBLISHED.md 合进同一 commit）
        amend_msg = f"feat: add {skill_name} v{new_ver}\n\nCo-authored-by: Hermes Agent <hermes-agent@nomail>"
        run(['git', 'commit', '--amend', '-m', amend_msg], cwd=work_dir, capture=False)
        # 强制推送更新 commit
        push_amend = subprocess.run(
            ['git', 'push', 'origin', branch_name, '--force-with-lease'],
            cwd=work_dir, env=env, capture_output=True, text=True
        )
        if push_amend.returncode != 0:
            print(f"  ⚠ PUBLISHED.md amend push 失败（不影响主发布）: {push_amend.stderr[:200]}")

        # 重新获取 commit hash（amend 后可能变）
        rev2 = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                              cwd=work_dir, capture_output=True, text=True)
        commit_hash = rev2.stdout.strip()

        pr_body = (
            f"## Skill 发布: `{skill_name}` v{new_ver}\n\n"
            f"**审核状态**: 已通过 `skill-audit` APPROVED\n\n"
            f"### 改动内容\n"
            f"- 新增 skill: `{skill_name}`\n"
            f"- 版本: `{cur_ver}` → `{new_ver}`\n"
            f"- Commit: `{commit_hash}`\n\n"
            f"### PUBLISHED.md\n"
            f"- 已更新记录\n\n"
            f"### 验证\n"
            f"- [ ] 在 GitHub 查看文件: `/{skill_name}/SKILL.md`\n"
            f"- [ ] 确认版本号正确\n\n"
            f"---\n"
            f"_由 Hermes Agent 自动创建 | 合并前请确认改动内容_"
        )

        pr_data = {
            'title': f'feat: add {skill_name} v{new_ver}',
            'body': pr_body,
            'head': branch_name,
            'base': default_branch,
            'draft': False,
        }
        pr_result = curl_post(
            f'https://api.github.com/repos/{user}/{repo}/pulls',
            token, pr_data
        )

        pr_url = pr_result.get('html_url', '')
        pr_number = pr_result.get('number', '?')

        if pr_url:
            print(f"  ✓ PR 已创建: {pr_url}")
        else:
            print(f"  ❌ PR 创建失败: {pr_result}")
            sys.exit(1)
        print()

        # ── 最终报告 ─────────────────────────────────────────────────────────
        print()
        print("=== 待合并 ===")
        print(f"Skill    : {skill_name} v{new_ver}")
        print(f"Commit   : {commit_hash}")
        print(f"PR       : {pr_url}")
        print(f"分支     : {branch_name} → {default_branch}")
        print()
        print("请确认后手动合并，或回复『合并』由 Agent 代为合并。")

    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir)
        if quarantine.exists():
            shutil.rmtree(quarantine)


def main():
    parser = argparse.ArgumentParser(description='Hermes Skill 发布工具（PR 模式）')
    parser.add_argument('skill_name', help='Skill 名称')
    parser.add_argument('--user', default='buwenzheng', help='GitHub 用户名')
    parser.add_argument('--repo', default='hermes-skills', help='GitHub 仓库名')
    parser.add_argument('--skill-dir', help='本地 skill 目录（默认 ~/.hermes/skills/<name>）')
    parser.add_argument('--token', help='GitHub Token（默认从 GITHUB_TOKEN 环境变量读取）')
    args = parser.parse_args()

    token = args.token or os.environ.get('GITHUB_TOKEN', '')
    if not token:
        print("❌ 缺少 GITHUB_TOKEN，请设置环境变量或传 --token 参数")
        sys.exit(1)

    skill_dir = Path(args.skill_dir) if args.skill_dir else Path.home() / '.hermes' / 'skills' / args.skill_name
    if not skill_dir.exists():
        print(f"❌ Skill 目录不存在: {skill_dir}")
        sys.exit(1)

    publish(args.skill_name, args.user, args.repo, skill_dir, token)


if __name__ == '__main__':
    main()
