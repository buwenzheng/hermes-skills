#!/usr/bin/env python3
"""
Hermes Skill 发布脚本
封装 clone → 隔离敏感文件 → git add → staged grep → commit → push → 验证
"""

import os
import sys
import json
import subprocess
import time
import re
import shutil
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


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """执行命令，失败时打印并退出"""
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"❌ 命令失败: {' '.join(cmd)}")
        print(f"   exit code: {result.returncode}")
        if result.stdout:
            print(f"   stdout: {result.stdout.decode(errors='replace')}")
        if result.stderr:
            print(f"   stderr: {result.stderr.decode(errors='replace')}")
        sys.exit(1)
    return result


def check_repo_exists(user: str, repo: str, token: str) -> bool:
    """检查 GitHub 仓库是否存在"""
    result = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
         '-H', f'Authorization: token {token}',
         f'https://api.github.com/repos/{user}/{repo}'],
        capture_output=True, text=True
    )
    return result.stdout == '200'


def get_default_branch(work_dir: Path, token: str, user: str, repo: str) -> str:
    """获取默认分支名（多层 fallback）"""
    # 1. symbolic-ref（正常 clone）
    result = subprocess.run(
        ['git', 'symbolic-ref', 'refs/remotes/origin/HEAD'],
        cwd=work_dir, capture_output=True, text=True
    )
    if result.returncode == 0:
        branch = result.stdout.strip().replace('refs/remotes/origin/', '')
        if branch:
            return branch

    # 2. git remote show（--depth 1 时可能可用）
    result = subprocess.run(
        ['git', 'remote', 'show', 'origin'],
        cwd=work_dir, capture_output=True, text=True
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if 'HEAD branch' in line:
                branch = line.split(':')[-1].strip()
                if branch:
                    return branch

    # 3. GitHub API
    result = subprocess.run(
        ['curl', '-s',
         '-H', f'Authorization: token {token}',
         f'https://api.github.com/repos/{user}/{repo}'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            return data.get('default_branch', 'main')
        except Exception:
            pass

    return 'main'


def quarantine_sensitive_files(skill_dir: Path) -> list[str]:
    """隔离敏感文件（直接删除），返回被删除的文件列表"""
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
    """扫描所有 staged 文件，排除 SKILL.md"""
    findings = []
    result = run(['git', 'diff', '--cached', '--name-only'],
                 cwd=work_dir, capture_output=True, text=True)
    staged_files = [
        line.strip() for line in result.stdout.splitlines()
        if line.strip() and not line.strip().endswith('SKILL.md')
    ]

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


def verify_published(user: str, repo: str, skill_name: str, token: str) -> tuple[bool, str]:
    """验证文件已推送到 GitHub"""
    result = subprocess.run(
        ['curl', '-s',
         '-H', f'Authorization: token {token}',
         f'https://api.github.com/repos/{user}/{repo}/contents/{skill_name}/SKILL.md'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False, 'curl failed'
    try:
        data = json.loads(result.stdout)
        sha = data.get('sha', '')
        if sha:
            return True, sha
        return False, data.get('message', 'no sha')
    except Exception:
        return False, result.stdout[:100]


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


def publish(skill_name: str, user: str, repo: str, skill_dir: Path, token: str):
    work_dir = Path(f'/tmp/{skill_name}-push')
    quarantine = Path(f'/tmp/skill-publisher-quarantine-{int(time.time())}')

    try:
        print(f"=== Skill 发布流程 ===")
        print(f"Skill: {skill_name}")
        print(f"目标: {user}/{repo}")
        print()

        # Step 1: 确认仓库存在
        print("■ Step 1: 确认仓库存在")
        if not check_repo_exists(user, repo, token):
            print(f"❌ 仓库不存在: {user}/{repo}，请先在 GitHub 创建")
            sys.exit(1)
        print(f"  ✓ 仓库存在")
        print()

        # Step 2: clone + 复制 + 隔离
        print("■ Step 2: clone + 复制 + 隔离")
        if work_dir.exists():
            shutil.rmtree(work_dir)
        quarantine.mkdir(parents=True, exist_ok=True)

        run(['git', 'clone', '--depth', '1',
             f'https://github.com/{user}/{repo}.git', str(work_dir)])

        # 复制 skill（平铺结构）
        target = work_dir / skill_name
        target.mkdir(exist_ok=True)
        for item in skill_dir.iterdir():
            if item.name == '__pycache__':
                continue
            src = skill_dir / item
            if src.is_dir():
                shutil.copytree(src, target / item.name)
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

        # Step 3: git add + staged grep + commit + push
        print("■ Step 3: git add + staged grep + commit + push")

        # 配置代理
        for key in ['http.proxy', 'https.proxy']:
            run(['git', 'config', key, 'http://127.0.0.1:7890'], cwd=work_dir)

        run(['git', 'add', '.'], cwd=work_dir)

        staged = run(['git', 'diff', '--cached', '--name-only'],
                      cwd=work_dir, capture_output=True, text=True)
        print(f"  staged 文件 ({len(staged.stdout.strip().splitlines())}): {staged.stdout.strip()[:200]}")

        findings = stage_grep(work_dir)
        if findings:
            print(f"  ❌ staged 文件中发现敏感信息 ({len(findings)} 处)：")
            for f in findings:
                print(f"    [{f['type']}] {f['file']}:{f['line']} → {f['matched']}")
            print("  → 拒绝发布，请重新运行 skill-audit 审核")
            sys.exit(1)
        print("  ✓ staged grep 无敏感信息")

        commit_msg = f"feat: add {skill_name}"
        run(['git', 'commit', '-m', commit_msg], cwd=work_dir)
        print(f"  ✓ commit: {commit_msg}")

        # GIT_ASKPASS 推送
        askpass = Path('/tmp/git-askpass.sh')
        askpass.write_text(f'#!/bin/bash\necho "{token}"\n')
        askpass.chmod(0o700)
        env = os.environ.copy()
        env['GIT_ASKPASS'] = str(askpass)

        default_branch = get_default_branch(work_dir, token, user, repo)
        print(f"  ✓ 分支: {default_branch}")

        push = subprocess.run(
            ['git', 'push', 'origin', default_branch, '--force-with-lease'],
            cwd=work_dir, env=env, capture_output=True, text=True
        )
        if push.returncode != 0:
            print(f"  ❌ push 失败: {push.stderr}")
            sys.exit(1)
        print(f"  ✓ push 成功")
        print()

        # Step 4: 验证
        print("■ Step 4: 验证")
        ok, msg = verify_published(user, repo, skill_name, token)
        if ok:
            print(f"  ✓ 发布成功: SHA {msg}")
        else:
            print(f"  ❌ 验证失败: {msg}")
            sys.exit(1)

        print()
        print("=== 发布完成 ===")
        rev = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                              cwd=work_dir, capture_output=True, text=True)
        commit_hash = rev.stdout.strip()
        print(f"Skill: {skill_name}")
        print(f"Commit: {commit_hash} — {commit_msg}")
        print(f"地址: https://github.com/{user}/{repo}/tree/{default_branch}/{skill_name}")
        print(f"验证: ✓ PASS")

    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir)
        if quarantine.exists():
            shutil.rmtree(quarantine)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Hermes Skill 发布工具')
    parser.add_argument('skill_name', help='Skill 名称')
    parser.add_argument('--user', default='buwenzheng', help='GitHub 用户名')
    parser.add_argument('--repo', default='hermes-skills', help='GitHub 仓库名')
    parser.add_argument('--skill-dir', help='本地 skill 目录路径（默认 ~/.hermes/skills/<name>）')
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
