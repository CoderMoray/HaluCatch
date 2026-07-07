"""代码风险扫描：按文件语言分别检测常见 AI 篡改点。"""

import re

# ── 支持的语言后缀 ────────────────────────────────────────────────

LANG_EXTENSIONS = {
    '.py':  'python',
    '.sh':  'shell',
    '.bash': 'shell',
    '.zsh': 'shell',
    '.go':  'go',
    '.js':  'javascript',
    '.ts':  'typescript',
    '.mjs': 'javascript',
    '.rb':  'ruby',
    '.rs':  'rust',
    '.pl':  'perl',
}

# ── 各语言风险规则 ─────────────────────────────────────────────────

# Python（保持原有 7 条）
PYTHON_PATTERNS = [
    ('异常处理', r'except\s*:\s*pass', '裸 except: pass — 可能吞掉内存错误等关键异常'),
    ('浮点比较', r'\w+\s*==\s*0\.0', '浮点数精确相等比较 — 可能漏判接近 0 的值'),
    ('除零风险', r'return\s+[^/\n]*/\s*\w+', 'return 中直接返回除法结果 — 分母为 0 时无保护'),
    ('硬编码阈值', r'skiprows\s*=\s*\d', '固定的 skiprows — 格式漂移时数据错位'),
    ('路径拼接', r'[\'\"][/\w]+\s*\+\s*[\'\"\/]|[\'\"\/]\s*\+\s*[\'\"][\w/]+', '字符串拼接路径 — 建议用 os.path.join'),
    ('静默覆盖', r'open\([^)]*,\s*[\'\"]w[\'\"]', '写模式打开文件 — 未警告覆盖已有内容'),
    ('超时缺失', r'requests\.(get|post|put|delete)\([^)]*\)', 'HTTP 请求未设置 timeout — 可能无限挂起'),
]

# Shell（sh / bash / zsh）
SHELL_PATTERNS = [
    ('无引号变量', r'(?:rm|mv|cp)\s+(?:\$\w+[^"\'\s]|[^"\'\s]*\$[^"\'\s]*)', '危险操作中使用未加引号的变量 — 空格/特殊字符导致意外行为'),
    ('静默吞错', r'\|\|\s*true\b', '|| true 静默丢弃所有错误 — 出问题时无信号'),
    ('参数缺失', r'\$\{[1-9]\d*\}|\$\d+(?!\s*[:-])', '引用位置参数但无默认值 — 参数缺失时静默失败'),
    ('提权操作', r'\bsudo\b', 'sudo 提权 — 可能执行意料之外的高权限操作'),
    ('临时文件风险', r'mktemp\b(?!.*-d)', '创建临时文件未用安全方式 — 竞态条件风险'),
]

# Go
GO_PATTERNS = [
    ('忽略错误', r',\s*_\s*:?=\s*\S+\(\)|_\s*,\s*_', '用 _ 忽略返回值 — 错误被静默丢弃'),
    ('裸 panic', r'\bpanic\(', '裸 panic 无 recover — 缺乏优雅降级'),
    ('硬编码超时', r'time\.(?:Second|Minute|Millisecond)\s*\*\s*\d+', '硬编码超时魔法数字 — 不可配置'),
    ('空上下文', r'context\.Background\(\)(?!.*WithTimeout)', '直接使用 Background context — 缺超时控制和取消'),
]

# JavaScript / TypeScript
JS_PATTERNS = [
    ('空 catch', r'catch\s*\([^)]*\)\s*\{\s*\}', '空 catch 块 — 错误被完全吞掉'),
    ('代码注入', r'\beval\(', 'eval() 调用 — 代码注入风险'),
    ('无校验环境变量', r'process\.env\.\w+\s*\|\|\s*[\'"]', '环境变量直接用 || 回退 — 类型/格式无校验'),
    ('未捕获 Promise', r'\.then\([^)]*\)(?!\s*\.(?:catch|finally))', '.then() 无 .catch() — 未捕获的 Promise rejection'),
]

# Ruby
RUBY_PATTERNS = [
    ('静默 rescue', r'rescue\s*$', '空 rescue 块 — 错误被吞掉'),
    ('危险 eval', r'\beval\b|\bclass_eval\b|\binstance_eval\b', 'eval/class_eval — 代码注入风险'),
    ('硬编码路径', r'([\'"]/(?:usr|etc|var|tmp|home)/[^\'"]+[\'"])', '绝对路径硬编码 — 不可移植'),
]

# Rust
RUST_PATTERNS = [
    ('unwrap 滥用', r'\.unwrap\(\)', '.unwrap() — panic 替代了错误处理'),
    ('expect 混淆', r'\.expect\([\'"]', '.expect() 隐藏了真实错误信息'),
]

# Perl
PERL_PATTERNS = [
    ('system 注入', r'\bsystem\s*\(?\s*[\'"]?\$', 'system 调用中包含变量 — 命令注入风险'),
    ('open 风险', r'open\s*\(?\s*\w+\s*,\s*[\'"]\|', 'open 管道模式 — 可能意外执行命令'),
]

# 通用（跨语言）
UNIVERSAL_PATTERNS = [
    ('硬编码密钥', r'(?:api_key|apikey|secret_key|password|token)\s*=\s*[\'"][^\'"]+[\'"]', '硬编码的凭据/密钥在代码中'),
    ('超长行', None, '单行过长（>200 字符）— 可读性和 diff 困难'),  # 特殊处理
]

# ── 辅助函数 ───────────────────────────────────────────────────────

def _preprocess(source):
    """移除字符串字面量和注释，避免误扫。"""
    code = source
    code = re.sub(r"r'[^']*'", ' ', code)
    code = re.sub(r'r"[^"]*"', ' ', code)
    code = re.sub(r"'''[\s\S]*?'''", ' ', code)
    code = re.sub(r'"""[\s\S]*?"""', ' ', code)
    code = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", ' ', code)
    code = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', ' ', code)
    code = re.sub(r'#.*', ' ', code)
    return code


def _check_legacy_python(py_content, info):
    """旧版兼容：直接用 py_content 字符串扫描 Python。"""
    issues = []
    total_checks = 0
    found_risks = 0

    # 合并核心代码和测试代码
    all_py = py_content
    if info.get('test_py'):
        all_py += '\n' + info['test_py']

    py_code = _preprocess(all_py)

    for name, pattern, desc in PYTHON_PATTERNS:
        total_checks += 1
        if re.search(pattern, py_code):
            issues.append((f'🟠 [{name}] {desc}', 'warn'))
            found_risks += 1

    if found_risks == 0:
        issues.append(('✅ 未检测到常见篡改点', 'pass'))

    lines = info.get('max_py_lines', len(py_content.splitlines()) if py_content else 0)
    py_count = info.get('py_count', 1 if py_content else 0)
    if lines > 200:
        if py_count > 1:
            issues.append((f'🟡 嵌入代码 {py_count} 个 .py 文件，最大单文件 {lines} 行 — 文件较多，AI 复现时可能遗漏', 'warn'))
        else:
            issues.append((f'🟡 嵌入代码 {lines} 行 — 较长，AI 复现时可能遗漏或篡改', 'warn'))

    test_py_count = info.get('test_py_count', 0)
    if test_py_count > 0:
        issues.append((f'✅ 检测到 {test_py_count} 个测试文件（有测试代码，质量意识不错）', 'pass'))

    if found_risks == 0 and lines <= 200:
        rating = '🟢 低风险'
    elif found_risks <= 2:
        rating = '🟠 有风险'
    else:
        rating = '🔴 高风险'

    score_display = f'{total_checks - found_risks}/{total_checks}' if total_checks > 0 else '-'
    return {'rating': rating, 'issues': issues, 'score': score_display}


def _is_safe_division(code):
    """检查代码中的除法是否安全（分母是常量或函数调用）。"""
    for m in re.finditer(r'return\s+[^/\n]*/\s*(\w+)(\s*\()?', code):
        denom = m.group(1)
        has_paren = m.group(2) is not None
        if denom.isdigit():
            continue  # 纯数字常量，安全
        if has_paren:
            continue  # 分母后跟 (，是 max/min/len 等函数调用，安全
        return False  # 找到真正危险的（变量除法无保护）
    return True  # 所有除法都安全

def _read_file(path):
    """读取文件内容，失败返回空。"""
    try:
        with open(path, 'r', encoding='utf-8', errors='backslashreplace') as fh:
            return fh.read()
    except Exception:
        return ''




# ── 主函数 ─────────────────────────────────────────────────────────

def check_code_risks(info):
    """代码风险扫描：按文件语言分别检测。"""
    issues = []
    total_checks = 0
    found_risks = 0

    files = info.get('files', [])
    if not files:
        # 回退：旧版只用 py_content 字符串
        py_content = info.get('py')
        if not py_content:
            return {'rating': '🟡 无嵌入式代码', 'issues': [('🟡 无 .py 文件，无法扫描代码风险', 'skip')], 'score': '-'}
        return _check_legacy_python(py_content, info)

    # 收集各语言的脚本文件
    lang_files = {}
    has_any_code = False

    for f in files:
        ext = f.get('ext', '')
        if ext in LANG_EXTENSIONS:
            lang = LANG_EXTENSIONS[ext]
            has_any_code = True
            lang_files.setdefault(lang, []).append(f)

    if not has_any_code:
        return {'rating': '🟡 无嵌入式代码', 'issues': [('🟡 无 .py 文件，无法扫描代码风险', 'skip')], 'score': '-'}

    # 按语言扫描
    lang_patterns = {
        'python': PYTHON_PATTERNS,
        'shell': SHELL_PATTERNS,
        'go': GO_PATTERNS,
        'javascript': JS_PATTERNS,
        'typescript': JS_PATTERNS,
        'ruby': RUBY_PATTERNS,
        'rust': RUST_PATTERNS,
        'perl': PERL_PATTERNS,
    }

    files_with_issues = 0
    total_files = 0

    for lang, file_list in lang_files.items():
        patterns = lang_patterns.get(lang, [])
        if not patterns:
            continue

        for f in file_list:
            path = f.get('rel_path') or f.get('path') or f.get('name', '')
            source = _read_file(f.get('path', ''))
            file_has_issue = False
            total_files += 1

            # 语言专属规则
            preprocessed = _preprocess(source) if lang == 'python' else source
            for name, pattern, desc in patterns:
                total_checks += 1
                if re.search(pattern, preprocessed, re.MULTILINE | re.DOTALL):
                    # 除零风险：排除分母为常量或 max()/min() 保护的情况
                    if name == '除零风险' and _is_safe_division(preprocessed):
                        continue
                    issues.append((f'🟠 [{lang}/{name}] {desc}（{path}）', 'warn'))
                    found_risks += 1
                    file_has_issue = True

            # 通用规则
            for uv_name, uv_pattern, uv_desc in UNIVERSAL_PATTERNS:
                total_checks += 1
                if uv_name == '超长行':
                    long_lines = [ln for ln in source.splitlines() if len(ln) > 200]
                    if long_lines:
                        issues.append((
                            f'🟡 [超长行] {uv_desc}（{len(long_lines)} 行超过 200 字符，出现在 {path}）',
                            'warn'
                        ))
                        found_risks += 1
                        file_has_issue = True
                elif uv_pattern and re.search(uv_pattern, preprocessed, re.IGNORECASE):
                    issues.append((f'🔴 [{uv_name}] {uv_desc}（{path}）', 'fail'))
                    found_risks += 1
                    file_has_issue = True

            if file_has_issue:
                files_with_issues += 1

    # 全局：Python 代码量统计（兼容旧逻辑）
    py_lines = 0
    py_count = 0
    if 'python' in lang_files:
        for f in lang_files['python']:
            try:
                with open(f['path'], 'r') as fh:
                    py_lines += len(fh.readlines())
            except Exception:
                pass
            py_count += 1

    if py_lines > 200:
        if py_count > 1:
            issues.append((f'🟡 嵌入代码 {py_count} 个 .py 文件，最大单文件约 {py_lines} 行 — 文件较多，AI 复现时可能遗漏', 'warn'))
        else:
            issues.append((f'🟡 嵌入代码 {py_lines} 行 — 较长，AI 复现时可能遗漏或篡改', 'warn'))

    # 测试文件正向信号
    test_py_count = info.get('test_py_count', 0)
    if test_py_count > 0:
        issues.append((f'✅ 检测到 {test_py_count} 个测试文件（有测试代码，质量意识不错）', 'pass'))

    # 评级（按有问题的文件数）
    if files_with_issues == 0:
        rating = '🟢 低风险'
    elif files_with_issues <= 2:
        rating = '🟠 有风险'
    else:
        rating = '🔴 高风险'

    score_display = f'{total_checks - found_risks}/{total_checks}' if total_checks > 0 else '-'
    if total_files > 0 and files_with_issues > 0:
        score_display += f'（{total_files - files_with_issues}/{total_files} 文件无问题）'
    elif total_files > 0:
        score_display += f'（{total_files} 文件全过）'
    return {'rating': rating, 'issues': issues, 'score': score_display}
