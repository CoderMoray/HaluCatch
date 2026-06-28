"""HaluCatch 文件扫描器：扫描 Skill 目录、提取文件内容和版本号。"""

import os
import sys
import re
import json
from .config import MESSAGES


def _extract_version(files, path):
    """从 _meta.json / meta.json / 任意 .md frontmatter 提取版本号。"""
    # 1) _meta.json / meta.json（优先）
    for meta_name in ['_meta.json', 'meta.json']:
        meta_path = os.path.join(path, meta_name)
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                version = data.get('version')
                if version:
                    return str(version)
            except Exception:
                pass
    # 2) 任意 .md 文件的 frontmatter
    for f in files:
        if f['ext'] != '.md':
            continue
        try:
            with open(f['path'], 'r', encoding='utf-8') as fh:
                content = fh.read()
            if content.startswith('---'):
                fm = content.split('---', 2)
                if len(fm) >= 2:
                    match = re.search(r'^version:\s*["\']?([^\s\n"\']+)["\']?', fm[1], re.M)
                    if match:
                        return match.group(1)
        except Exception:
            pass
    return None


def scan_folder(path, msg):
    """扫描文件夹（仅顶层），返回文件清单和 SKILL.md / .py 内容。"""
    if not os.path.isdir(path):
        print(msg['path_not_exist'].format(path=path))
        return None

    files = []
    skill_md_content = None
    py_contents = []
    skill_md_path = None
    py_paths = []

    skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv', 'avatars'}

    for root, dirs, filenames in os.walk(path):
        # 只扫描顶层目录，不递归子目录（避免误读其他 Skill 的 SKILL.md）
        dirs[:] = []
        for fname in filenames:
            fpath = os.path.join(root, fname)
            size = os.path.getsize(fpath)
            ext = os.path.splitext(fname)[1].lower()
            fpath_rel = os.path.relpath(fpath, path)
            files.append({'name': fname, 'ext': ext, 'size': size, 'path': fpath, 'rel_path': fpath_rel})

    # 尺寸保护：跳过超大文件避免 OOM
    SZ_LIMIT = 10 * 1024 * 1024  # 10MB
    oversized = []
    for f in files:
        if f['size'] > SZ_LIMIT:
            oversized.append(f['name'])
    if oversized:
        print(msg['file_too_large'].format(files="', '".join(oversized)))
    oversized_set = set(oversized)

    # 检查是否有任何 .md 文件
    md_files = [f for f in files if f['ext'] == '.md']
    if not md_files:
        print(msg['no_md_files'].format(path=path))
        return None

    # 查找 SKILL.md（精确大小写不敏感）
    skill_md_found = None
    for f in files:
        if f['name'].lower() == 'skill.md':
            skill_md_found = f
            break

    # 如果没有 SKILL.md，用启发式查找最佳替代 .md 文件
    skill_md_source = None
    if skill_md_found is not None:
        skill_md_path = skill_md_found['path']
        skill_md_source = skill_md_found['name']
        with open(skill_md_path, 'r', encoding='utf-8', errors='backslashreplace') as fh:
            skill_md_content = fh.read()
    else:
        # 启发式：优先 frontmatter，其次文件最大的
        candidates = [f for f in md_files if f['name'] not in oversized_set]
        if candidates:
            best = None
            best_score = -1
            for f in candidates:
                score = 0
                try:
                    with open(f['path'], 'r', encoding='utf-8', errors='backslashreplace') as fh:
                        content = fh.read()
                    if content.startswith('---'):
                        score += 10  # 有 frontmatter 优先
                    score += f['size'] / 1024  # 文件大小作为次要因素
                    if score > best_score:
                        best_score = score
                        best = f
                        skill_md_content = content
                except Exception:
                    continue
            if best:
                skill_md_path = best['path']
                skill_md_source = best['name']
                print(msg['skill_md_substitute'].format(
                    found=skill_md_source,
                    expected='SKILL.md'
                ))
        else:
            # 所有 .md 都超大
            print(msg['no_md_files'].format(path=path))
            return None

    for f in files:
        if f['name'] in oversized_set:
            continue
        if f['ext'] == '.py':
            py_paths.append(f['path'])
            with open(f['path'], 'r', encoding='utf-8', errors='backslashreplace') as fh:
                py_contents.append(fh.read())

    has_data = any(f['ext'] in ['.xlsx', '.xls', '.csv'] for f in files)

    py_content = '\n'.join(py_contents) if py_contents else None
    py_path = py_paths[0] if py_paths else None
    max_py_lines = max(len(c.splitlines()) for c in py_contents) if py_contents else 0

    # 提取版本号
    version = _extract_version(files, path)

    print(msg['scanning'].format(path=path))
    print(msg['file_count'].format(count=len(files)))
    if skill_md_content:
        print(msg['skill_md'].format(lines=len(skill_md_content.splitlines())))
    if py_paths:
        total_py_lines = sum(len(c.splitlines()) for c in py_contents)
        print(msg['py_files'].format(count=len(py_paths), lines=total_py_lines))
    if has_data:
        data_count = sum(1 for f in files if f['ext'] in ['.xlsx', '.xls', '.csv'])
        print(msg['data_files'].format(count=data_count))
    if version:
        print(msg['version_detected'].format(version=version))

    return {
        'files': files,
        'skill_md': skill_md_content,
        'skill_md_path': skill_md_path,
        'skill_md_source': skill_md_source,
        'py': py_content,
        'py_path': py_path,
        'py_count': len(py_paths),
        'max_py_lines': max_py_lines,
        'has_data': has_data,
        'version': version,
    }


# =============================================================================
# 2. 技能分类
# =============================================================================
