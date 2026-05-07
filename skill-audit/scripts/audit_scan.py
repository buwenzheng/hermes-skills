#!/usr/bin/env python3
"""
Hermes Skill 安全扫描脚本
检测敏感信息、禁止文件、格式规范
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Optional

# ── 敏感信息 patterns ──────────────────────────────────────────────────────
SENSITIVE_PATTERNS = [
    # GitHub / 云服务商 Key
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub PAT'),
    (r'github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}', 'GitHub Fine-grained PAT'),
    (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
    (r'sk-proj-[a-zA-Z0-9]{48,}', 'Other sk- Key'),
    (r'sk-ant-[a-zA-Z0-9]{32,}', 'Anthropic/sk-ant Key'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
    (r'ASIA[0-9A-Z]{16}', 'AWS Session Token'),
    (r'AIza[0-9A-Za-z_-]{35}', 'Google API Key'),
    (r'AccountKey=[a-zA-Z0-9+/=]{88}', 'Azure Account Key'),
    # JWT
    (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', 'JSON Web Token'),
    # token / api_key / password (单引号包裹)
    (r'token\s*[:=]\s*\'[a-zA-Z0-9_/-]{16,}\'', 'Token (单引号)'),
    (r'api[_-]?key\s*[:=]\s*\'[a-zA-Z0-9_/-]{16,}\'', 'API Key (单引号)'),
    (r'password\s*[:=]\s*\'[^\']{8,}\'', 'Password (单引号)'),
    # token / api_key / password (双引号包裹)
    (r'token\s*[:=]\s*"[a-zA-Z0-9_/-]{16,}"', 'Token (双引号)'),
    (r'api[_-]?key\s*[:=]\s*"[a-zA-Z0-9_/-]{16,}"', 'API Key (双引号)'),
    (r'password\s*[:=]\s*"[^"]{8,}"', 'Password (双引号)'),
]

# ── 禁止文件 ──────────────────────────────────────────────────────────────
FORBIDDEN_PATTERNS = [
    '*_config.json',
    '*_cache.json',
    '__pycache__',
    '*.pyc',
    '.env',
    '*.log',
    'credentials.json',
]

# ── Frontmatter 必填字段 ───────────────────────────────────────────────────
REQUIRED_FRONTMATTER = ['name', 'description', 'version']
REQUIRED_CONTENT_SECTIONS = ['INT', '初始化', 'When to Use', '何时使用', '触发']
REQUIRED_PITFALL_SECTIONS = ['Common Pitfalls', '避坑', '陷阱', 'Common Errors']


def scan_sensitive(skill_dir: Path) -> list[dict]:
    """扫描敏感信息"""
    findings = []
    extensions = ['.py', '.json', '.sh', '.yaml', '.yml', '.env', '.toml', '.txt', '.conf']

    for file_path in skill_dir.rglob('*'):
        if file_path.is_dir():
            continue
        # 跳过 SKILL.md 和 .git
        if file_path.name == 'SKILL.md' or '.git' in file_path.parts:
            continue
        if file_path.suffix not in extensions and not any(
            file_path.name.endswith(ext) for ext in ['.env']
        ):
            continue

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for pattern, label in SENSITIVE_PATTERNS:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                findings.append({
                    'file': str(file_path.relative_to(skill_dir)),
                    'line': line_num,
                    'type': label,
                    'matched': match.group()[:60],
                    'pattern': pattern,
                })
    return findings


def scan_forbidden(skill_dir: Path) -> list[str]:
    """扫描禁止文件"""
    forbidden = []
    for pattern in FORBIDDEN_PATTERNS:
        # 处理通配符
        if '*' in pattern:
            for file_path in skill_dir.rglob(pattern):
                forbidden.append(str(file_path.relative_to(skill_dir)))
        else:
            for file_path in skill_dir.rglob(pattern):
                if file_path.is_file() or file_path.is_dir():
                    forbidden.append(str(file_path.relative_to(skill_dir)))
    return sorted(set(forbidden))


def parse_frontmatter(skill_md_path: Path) -> tuple[Optional[dict], int]:
    """解析 YAML frontmatter，返回 (frontmatter_dict, 正文起始行)"""
    try:
        content = skill_md_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return None, 0

    lines = content.split('\n')
    if not lines or lines[0].strip() != '---':
        return {}, 0

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            end_idx = i
            break

    if end_idx is None:
        return {}, 0

    fm_text = '\n'.join(lines[1:end_idx])
    fm = {}
    current_key = None
    current_indent = 0

    for line in lines[1:end_idx]:
        # 检测嵌套字段（metadata.hermes.tags 等）
        if ':' in line:
            key = line.split(':', 1)[0].strip()
            val = line.split(':', 1)[1].strip()
            if key in ('name', 'description', 'version'):
                fm[key] = val
            elif key in ('tags', 'required_environment_variables'):
                fm[key] = val if val else []
            elif '.' in key:
                fm[key] = val
            current_key = key
            current_indent = len(line) - len(line.lstrip())
        elif current_key in fm and isinstance(fm[current_key], list) and line.strip().startswith('-'):
            fm[current_key].append(line.strip()[1:].strip())

    return fm, end_idx + 1


def check_format(skill_dir: Path) -> dict:
    """格式审核"""
    skill_md = skill_dir / 'SKILL.md'
    result = {
        'frontmatter': {'ok': False, 'missing': [], 'warnings': []},
        'readme': {'ok': False},
        'structure': {'ok': False, 'missing': []},
    }

    if not skill_md.exists():
        return result

    # Frontmatter 检查
    fm, _ = parse_frontmatter(skill_md)
    if fm:
        for field in REQUIRED_FRONTMATTER:
            if field not in fm or not fm[field]:
                result['frontmatter']['missing'].append(field)
        if not result['frontmatter']['missing']:
            result['frontmatter']['ok'] = True
    else:
        result['frontmatter']['missing'] = REQUIRED_FRONTMATTER

    # README 检查
    readme = skill_dir / 'README.md'
    result['readme']['ok'] = readme.exists()

    # 正文结构检查
    body = skill_md.read_text(encoding='utf-8', errors='ignore')
    has_int = any(s in body for s in REQUIRED_CONTENT_SECTIONS)
    has_pitfalls = any(s in body for s in REQUIRED_PITFALL_SECTIONS)
    has_trigger = any(s in body for s in ['## When to Use', '## 何时使用', '## 触发条件', '## 触发'])

    result['structure']['missing'] = []
    if not has_int:
        result['structure']['missing'].append('INT / 初始化')
    if not has_trigger:
        result['structure']['missing'].append('When to Use / 何时使用')
    if not has_pitfalls:
        result['structure']['missing'].append('Common Pitfalls / 避坑')
    result['structure']['ok'] = len(result['structure']['missing']) == 0

    return result


def main(skill_name: Optional[str] = None):
    if skill_name:
        skill_dir = Path.home() / '.hermes' / 'skills' / skill_name
    else:
        # 默认扫描当前目录
        skill_dir = Path.cwd()

    if not skill_dir.exists():
        print(f"❌ Skill 目录不存在: {skill_dir}")
        sys.exit(1)

    print(f"=== Skill 安全审核扫描 ===")
    print(f"Skill: {skill_dir.name}")
    print()

    # 1. 敏感信息扫描
    print("■ 敏感信息扫描")
    findings = scan_sensitive(skill_dir)
    if findings:
        for f in findings:
            print(f"  [{f['type']}] {f['file']}:{f['line']}")
            print(f"    匹配: {f['matched']}")
        print(f"  → FAIL: 发现 {len(findings)} 处敏感信息")
    else:
        print("  → PASS: 未发现敏感信息")

    print()

    # 2. 禁止文件扫描
    print("■ 禁止文件扫描")
    forbidden = scan_forbidden(skill_dir)
    if forbidden:
        for f in forbidden:
            print(f"  FORBIDDEN: {f}")
        print(f"  → FAIL: 发现 {len(forbidden)} 个禁止文件")
    else:
        print("  → PASS: 无禁止文件")

    print()

    # 3. 格式审核
    print("■ 格式审核")
    fmt = check_format(skill_dir)
    if fmt['frontmatter']['ok']:
        print("  Frontmatter: ✓")
    else:
        print(f"  Frontmatter: ✗ 缺失 {fmt['frontmatter']['missing']}")

    if fmt['readme']['ok']:
        print("  README.md: ✓")
    else:
        print("  README.md: ✗ 缺失")

    if fmt['structure']['ok']:
        print("  正文结构: ✓")
    else:
        print(f"  正文结构: ✗ 缺失 {fmt['structure']['missing']}")

    print()

    # 最终判定
    rejected = bool(findings) or bool(forbidden) or not fmt['frontmatter']['ok'] or not fmt['readme']['ok'] or not fmt['structure']['ok']

    if rejected:
        print("■ 最终判定: REJECTED")
        if findings:
            print("  → 敏感信息未清理，请修复后重新审核")
        if forbidden:
            print("  → 禁止文件存在，请清理或模板化")
        if not fmt['readme']['ok']:
            print("  → README.md 缺失，请添加")
        if not fmt['structure']['ok']:
            print("  → 正文结构不完整，请补充 INT/何时使用/避坑 章节")
        sys.exit(1)
    else:
        print("■ 最终判定: APPROVED")
        print("  → 可继续发布流程（运行 skill-publisher）")
        sys.exit(0)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Hermes Skill 安全扫描')
    parser.add_argument('skill_name', nargs='?', help='Skill 名称（不填则扫描当前目录）')
    args = parser.parse_args()
    main(args.skill_name)
