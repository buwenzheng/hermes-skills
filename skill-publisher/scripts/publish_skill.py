#!/usr/bin/env python3
"""
Hermes Skill 发布脚本

流程：
  1. clone → 隔离敏感文件
  2. 版本号 bump（patch +1）
  3. git add → staged grep → commit → push
  4. GitHub API 验证
  5. PUBLISHED.md 更新 → 第二次 commit + push
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

# 内建 .env 加载：从 ~/.hermes/.env 读取环境变量
def _load_dotenv():
    env_path = Path.home() / '.hermes' / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

_load_dotenv()

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
    (r'token\s*[:=]\s*[\'"][a-zA-Z0-9_/-]{16,}[\'"]', 'Token'),
    (r'api[_-]?key\s*[:=]\s*[\'"][a-zA-Z0-9_/-]{16,}[\'"]', 'API Key'),
    (r'password\s*[:=]\s*[\'"][^\']{8,}[\'"]', 'Password'),
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


def get_flat_name(skill_name: str) -> str:
    """去掉分类前缀，返回平铺的 skill 名称。
    例：mcp/music-tag-web-mcp → music-tag-web-mcp
    """
    return skill_name.split('/')[-1]


def get_proxy_config() -> dict:
    """从环境变量或 git config 读取代理配置。"""
    proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
    if proxy:
        return {'http.proxy': proxy, 'https.proxy': proxy}
    # 检查 git global config
    try:
        r = subprocess.run(['git', 'config', '--global', 'http.proxy'],
                           capture_output=True, text=True)
        if r.stdout.strip():
            return {'http.proxy': r.stdout.strip(), 'https.proxy': r.stdout.strip()}
    except Exception:
        pass
    return {}


def run(cmd: list, *, cwd: Path | None = None, capture_output: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=capture_output, text=True)
    if result.returncode != 0:
        print(f"❌ 命令失败: {' '.join(cmd)}")
        print(f"   exit code: {result.returncode}")
        print(f"   stdout: {result.stdout[:300]}")
        print(f"   stderr: {result.stderr[:300]}")
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


def check_repo_exists(user: str, repo: str, token: str) -> bool:
    r = subprocess.run(
        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
         '-H', f'Authorization: token {token}',
         f'https://api.github.com/repos/{user}/{repo}'],
        capture_output=True, text=True
    )
    return r.stdout == '200'


def get_default_branch(user: str, repo: str, token: str) -> str:
    data = curl_get(f'https://api.github.com/repos/{user}/{repo}', token)
    return data.get('default_branch', 'main')


def quarantine_sensitive_files(skill_dir: Path) -> list[str]:
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
    skill_md = skill_dir / 'SKILL.md'
    if not skill_md.exists():
        return '1.0.0'
    content = skill_md.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'^version:\s*(\S+)', content, re.MULTILINE)
    return m.group(1) if m else '1.0.0'


def bump_version(content: str) -> tuple[str, str]:
    m = re.search(r'^version:\s*(\S+)', content, re.MULTILINE)
    if not m:
        return content, '1.0.1'
    cur = m.group(1)
    parts = cur.split('.')
    while len(parts) < 3:
        parts.append('0')
    parts[-1] = str(int(parts[-1]) + 1)
    new_ver = '.'.join(parts)
    updated = re.sub(r'^version:\s*\S+', f'version: {new_ver}',
                     content, flags=re.MULTILINE)
    return updated, new_ver


def _dedupe_gitignore(gitignore_path: Path):
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


def update_readme(work_dir: Path, token: str):
    """扫描仓库内所有 skill 目录，重新生成 README.md 中的"现有技能"表格。"""
    def _extract_desc(fm: str) -> str:
        """从 frontmatter 提取 description，支持 >- / | 等 YAML 多行语法。"""
        lines = fm.splitlines()
        for i, line in enumerate(lines):
            if re.match(r'^description:\s*', line):
                val = re.sub(r'^description:\s*', '', line).strip()
                if val in ('>-', '>', '|', '|-'):
                    # 多行：收集后续缩进行
                    collected = []
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j]
                        if next_line.strip() == '' or next_line.startswith(' '):
                            collected.append(next_line.strip())
                        else:
                            break
                    return ' '.join(collected).strip()[:80]
                return val[:80]
        return ''

    readme_path = work_dir / 'README.md'
    if not readme_path.exists():
        print("  ⚠ README.md 不存在，跳过更新")
        return

    # 扫描所有 skill 目录（排除非 skill 目录）
    skills = []
    for item in sorted(work_dir.iterdir()):
        if not item.is_dir():
            continue
        skill_md = item / 'SKILL.md'
        if not skill_md.exists():
            continue
        content = skill_md.read_text(encoding='utf-8', errors='ignore')
        # 提取 frontmatter
        fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not fm_match:
            continue
        fm = fm_match.group(1)
        name_m = re.search(r'^name:\s*(\S+)', fm, re.MULTILINE)
        ver_m = re.search(r'^version:\s*(\S+)', fm, re.MULTILINE)
        desc_m = re.search(r'^description:\s*(.+)', fm, re.MULTILINE)
        cat_m = re.search(r'^category:\s*(\S+)', fm, re.MULTILINE)
        skills.append({
            'name': name_m.group(1) if name_m else item.name,
            'version': ver_m.group(1) if ver_m else '0.0.0',
            'desc': _extract_desc(fm) or (desc_m.group(1).strip()[:60] if desc_m else ''),
            'category': cat_m.group(1) if cat_m else 'uncategorized',
        })

    if not skills:
        print("  ⚠ 未发现任何 skill，跳过 README 更新")
        return

    # 生成表格
    table_lines = [
        '| Skill | 版本 | 说明 | 分类 |',
        '|-------|------|------|------|',
    ]
    for s in skills:
        table_lines.append(
            f'| [{s["name"]}](./{s["name"]}) | {s["version"]} | {s["desc"]} | {s["category"]} |'
        )
    table = '\n'.join(table_lines)

    # 替换 README 中 "## 现有技能" 到下一个 "##" 之间的内容
    readme_content = readme_path.read_text(encoding='utf-8')
    pattern = r'(## 现有技能\n\n).*?(\n## )'
    replacement = f'\\1{table}\n\\2'
    new_readme = re.sub(pattern, replacement, readme_content, count=1, flags=re.DOTALL)
    if new_readme == readme_content:
        print("  ⚠ 未找到 '## 现有技能' 段落，跳过 README 更新")
        return
    readme_path.write_text(new_readme, encoding='utf-8')
    print(f"  ✓ README.md 已更新（{len(skills)} 个 skill）")


def _git_config(work_dir: Path, key: str, val: str):
    subprocess.run(['git', 'config', key, val], cwd=work_dir,
                   capture_output=True)


def publish(skill_name: str, user: str, repo: str, skill_dir: Path, token: str, explicit_version: str = None):
    # 平铺名称：去掉分类前缀
    flat_name = get_flat_name(skill_name)
    work_dir = Path(f'/tmp/{flat_name}-push')
    quarantine = Path(f'/tmp/skill-publisher-quarantine-{int(time.time())}')

    try:
        print(f"=== Skill 发布流程 ===")
        print(f"Skill : {skill_name} → {flat_name}")
        print(f"目标 : {user}/{repo}")
        print()

        # Step 1: 确认仓库存在
        print("■ Step 1: 确认仓库存在")
        if not check_repo_exists(user, repo, token):
            print(f"❌ 仓库不存在: {user}/{repo}")
            sys.exit(1)
        print(f"  ✓ 仓库存在")
        print()

        # Step 2: clone + 复制 + 隔离
        print("■ Step 2: clone + 复制 + 隔离")
        if work_dir.exists():
            shutil.rmtree(work_dir)
        quarantine.mkdir(parents=True, exist_ok=True)

        run(['git', 'clone', '--depth', '1',
             f'https://github.com/{user}/{repo}.git', str(work_dir)],
            capture_output=False)

        # 平铺：直接在仓库根目录创建 skill 目录
        target = work_dir / flat_name
        target.mkdir(exist_ok=True)
        for item in skill_dir.iterdir():
            if item.name == '__pycache__':
                continue
            src = skill_dir / item
            if src.is_dir():
                shutil.copytree(src, target / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(src, target / item.name)

        gitignore = work_dir / '.gitignore'
        existing = gitignore.read_text() if gitignore.exists() else ''
        gitignore.write_text(existing + GITIGNORE_CONTENT)
        _dedupe_gitignore(gitignore)

        moved = quarantine_sensitive_files(target)
        if moved:
            print(f"  ✓ 隔离 {len(moved)} 个敏感文件: {', '.join(moved)}")
        print()

        # Step 2.5: 版本号 bump
        print("■ Step 2.5: 版本号 bump")
        cur_ver = get_skill_version(skill_dir)
        work_skill_md = target / 'SKILL.md'
        content = work_skill_md.read_text(encoding='utf-8', errors='ignore')
        if explicit_version:
            new_ver = explicit_version
            updated_content = re.sub(r'^version:\s*\S+', f'version: {new_ver}',
                                     content, flags=re.MULTILINE)
        else:
            updated_content, new_ver = bump_version(content)
        work_skill_md.write_text(updated_content, encoding='utf-8')
        print(f"  {cur_ver} → {new_ver}")
        print()

        # Step 2.7: 更新 README.md
        print("■ Step 2.7: 更新 README.md")
        update_readme(work_dir, token)
        print()

        # Step 3: git add + staged grep + commit + push
        print("■ Step 3: git add + staged grep + commit + push")

        default_branch = get_default_branch(user, repo, token)
        _git_config(work_dir, 'user.email', 'hermes-agent@nomail')
        _git_config(work_dir, 'user.name', 'Hermes Agent')

        # 代理配置：从环境变量或 git config 读取，不再硬编码
        proxy_config = get_proxy_config()
        for key, val in proxy_config.items():
            _git_config(work_dir, key, val)

        run(['git', 'add', '.'], cwd=work_dir)

        staged = run(['git', 'diff', '--cached', '--name-only'], cwd=work_dir)
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

        # 判断是新增还是更新
        existing_skill = curl_get(
            f'https://api.github.com/repos/{user}/{repo}/contents/{flat_name}/SKILL.md',
            token
        )
        action = "update" if existing_skill.get('sha') else "add"
        commit_msg = f"feat: {action} {flat_name} v{new_ver}"
        run(['git', 'commit', '-m', commit_msg], cwd=work_dir)
        print(f"  ✓ commit: {commit_msg}")

        askpass = Path('/tmp/git-askpass.sh')
        askpass.write_text(f'#!/bin/bash\necho "{token}"\n')
        askpass.chmod(0o700)
        env = os.environ.copy()
        env['GIT_ASKPASS'] = str(askpass)

        # 直接 push，不用 --force-with-lease
        push = subprocess.run(
            ['git', 'push', 'origin', default_branch],
            cwd=work_dir, env=env, capture_output=True, text=True
        )
        if push.returncode != 0:
            print(f"  ❌ push 失败: {push.stderr[:300]}")
            sys.exit(1)
        print(f"  ✓ push 成功")
        print()

        # Step 4: 验证
        print("■ Step 4: 验证")
        rev = subprocess.run(['git', '-C', str(work_dir), 'rev-parse', '--short', 'HEAD'],
                           capture_output=True, text=True)
        commit_hash = rev.stdout.strip()
        data = curl_get(
            f'https://api.github.com/repos/{user}/{repo}/contents/{flat_name}/SKILL.md',
            token
        )
        sha = data.get('sha', '')
        if sha:
            print(f"  ✓ 发布成功: SHA {sha}")
        else:
            print(f"  ❌ 验证失败: {data.get('message', 'no sha')}")
            sys.exit(1)

        # Step 5: 更新 PUBLISHED.md
        print("■ Step 5: 更新 PUBLISHED.md")
        published_path = work_dir / 'PUBLISHED.md'
        today = time.strftime('%Y-%m-%d')
        # PUBLISHED.md 用 flat_name 避免表格错位
        new_entry = f'| {flat_name} | {new_ver} | {today} | `{commit_hash}` |'

        if published_path.exists():
            lines = published_path.read_text().splitlines()
            found = False
            new_lines = []
            for line in lines:
                # 匹配时也用 flat_name
                if line.startswith(f'| {flat_name} |'):
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

        run(['git', 'add', 'PUBLISHED.md'], cwd=work_dir)
        run(['git', 'commit', '-m', f'chore: update PUBLISHED.md for {flat_name}'],
            cwd=work_dir, capture_output=False)
        push2 = subprocess.run(
            ['git', 'push', 'origin', default_branch],
            cwd=work_dir, env=env, capture_output=True, text=True
        )
        if push2.returncode != 0:
            print(f"  ⚠ PUBLISHED.md push 失败（不影响主发布）: {push2.stderr[:200]}")
        else:
            rev2 = subprocess.run(['git', '-C', str(work_dir), 'rev-parse', '--short', 'HEAD'],
                                capture_output=True, text=True)
            commit_hash2 = rev2.stdout.strip()
            print(f"  ✓ PUBLISHED.md push 成功 ({commit_hash2})")
        print()

        print()
        print("=== 发布完成 ===")
        print(f"Skill : {flat_name} v{new_ver}")
        print(f"Commit: {commit_hash}")
        print(f"地址 : https://github.com/{user}/{repo}/tree/{default_branch}/{flat_name}")
        print(f"验证 : ✓ PASS")

    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir)
        if quarantine.exists():
            shutil.rmtree(quarantine)


def main():
    parser = argparse.ArgumentParser(description='Hermes Skill 发布工具')
    parser.add_argument('skill_name', help='Skill 名称（支持分类前缀如 mcp/xxx）')
    parser.add_argument('--user', default='buwenzheng', help='GitHub 用户名')
    parser.add_argument('--repo', default='hermes-skills', help='GitHub 仓库名')
    parser.add_argument('--skill-dir', help='本地 skill 目录（默认 ~/.hermes/skills/<name>）')
    parser.add_argument('--token', help='GitHub Token（默认从 GITHUB_TOKEN 环境变量读取）')
    parser.add_argument('--version', help='指定版本号（如 1.3.0），不传则自动 bump patch')
    args = parser.parse_args()

    token = args.token or os.environ.get('GITHUB_TOKEN', '')
    if not token:
        print("❌ 缺少 GITHUB_TOKEN，请设置环境变量或传 --token 参数")
        sys.exit(1)

    skill_dir = Path(args.skill_dir) if args.skill_dir else \
        Path.home() / '.hermes' / 'skills' / args.skill_name
    if not skill_dir.exists():
        print(f"❌ Skill 目录不存在: {skill_dir}")
        sys.exit(1)

    publish(args.skill_name, args.user, args.repo, skill_dir, token, args.version)


if __name__ == '__main__':
    main()
