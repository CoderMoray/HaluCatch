"""
HaluCatch Core — AI Skill 执行可靠性审查骨架脚本

用法：
  python3 halucatch_core.py --skill-dir <目标Skill路径> [--validate]
  python3 halucatch_core.py --skill-dir <目标Skill路径> --output-dir <报告输出路径>
"""

import os
import sys
import re
import argparse
import json
from datetime import date

# =============================================================================
# 1. 文件扫描
# =============================================================================

def scan_folder(path):
    """递归扫描文件夹，返回文件清单和 SKILL.md / .py 内容。"""
    if not os.path.isdir(path):
        print(f"❌ 路径不存在: {path}")
        return None

    files = []
    skill_md_content = None
    py_contents = []
    skill_md_path = None
    py_paths = []

    skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'node_modules', '.venv', 'venv', 'avatars'}

    for root, dirs, filenames in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for fname in filenames:
            fpath = os.path.join(root, fname)
            size = os.path.getsize(fpath)
            ext = os.path.splitext(fname)[1].lower()
            fpath_rel = os.path.relpath(fpath, path)
            files.append({'name': fname, 'ext': ext, 'size': size, 'path': fpath, 'rel_path': fpath_rel})

            if fname.lower() in ['skill.md', 'toolcard.md']:
                skill_md_path = fpath
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    skill_md_content = f.read()

            if ext == '.py':
                py_paths.append(fpath)
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    py_contents.append(f.read())

    has_data = any(f['ext'] in ['.xlsx', '.xls', '.csv'] for f in files)

    py_content = '\n'.join(py_contents) if py_contents else None
    py_path = py_paths[0] if py_paths else None
    max_py_lines = max(len(c.splitlines()) for c in py_contents) if py_contents else 0

    print(f"  📁 扫描: {path}")
    print(f"  📄 文件数: {len(files)}")
    if skill_md_content:
        print(f"  📝 SKILL.md: {len(skill_md_content.splitlines())} 行")
    if py_paths:
        print(f"  🐍 .py 文件: {len(py_paths)} 个 ({sum(len(c.splitlines()) for c in py_contents)} 行)")
    if has_data:
        print(f"  📊 数据文件: {sum(1 for f in files if f['ext'] in ['.xlsx', '.xls', '.csv'])} 个")

    return {
        'files': files,
        'skill_md': skill_md_content,
        'skill_md_path': skill_md_path,
        'py': py_content,
        'py_path': py_path,
        'py_count': len(py_paths),
        'max_py_lines': max_py_lines,
        'has_data': has_data,
    }


# =============================================================================
# 2. 技能分类
# =============================================================================

def classify_skill(info):
    """判断 Skill 类型：代码工程型 / 纯方法论型。"""
    has_py = info['py'] is not None
    has_data = info['has_data']
    has_pd = info['skill_md'] and ('pd.read_' in info['skill_md'] or 'pandas' in info['skill_md'].lower())
    has_md_py = info['skill_md'] and ('```python' in info['skill_md'])

    if has_py or has_data or has_pd or has_md_py:
        return 'code-engineered'
    return 'methodology'


# =============================================================================
# 3. 评估函数
# =============================================================================

def check_foundation(info):
    """地基检查：有 .py？路径写死？有 validate？"""
    issues = []
    score = 0
    total = 6

    # 1) 有固化脚本
    if info['py']:
        issues.append(('✅ 有固化 .py 脚本', 'pass'))
        score += 1
    else:
        issues.append(('🔴 无固化 .py 脚本——AI 须自行编写全部代码', 'fail'))

    # 2) 路径参数化
    if info['py']:
        matches = re.findall(r"['\"](/[^'\"]+?)['\"]", info['py'])
        hardcoded = [m for m in matches if 'Users/' in m or 'home/' in m or 'C:' in m]
        if hardcoded:
            issues.append((f'🔴 发现 {len(hardcoded)} 处硬编码路径: {hardcoded[:3]}', 'fail'))
        else:
            issues.append(('✅ 路径已参数化或无本地绝对路径', 'pass'))
            score += 1
    else:
        issues.append(('🟡 无 .py 文件，无法检查路径', 'skip'))

    # 3) validate 模式
    if info['py'] and '--validate' in info['py']:
        issues.append(('✅ 有 --validate 验证模式', 'pass'))
        score += 1
    elif info['py']:
        issues.append(('🟠 有 .py 但缺少 --validate 验证模式', 'warn'))
    else:
        issues.append(('🟡 无 .py 文件，无法检查验证模式', 'skip'))

    # 4) 列名预检/输入验证
    if info['py'] and ('check_columns' in info['py'] or 'required_' in info['py'] or '列名预检' in info['py'] or '列名' in info['py']):
        issues.append(('✅ 有输入验证/列名校验', 'pass'))
        score += 1
    elif info['py']:
        issues.append(('🟠 有 .py 但缺少输入验证', 'warn'))
    else:
        issues.append(('🟡 无 .py 文件，无法检查输入验证', 'skip'))

    # 5) 文件发现机制
    if info['py']:
        if 'glob' in info['py'] or 'os.listdir' in info['py']:
            issues.append(('✅ 使用通配符/自动发现文件', 'pass'))
            score += 1
        else:
            issues.append(('🟠 有 .py 但缺少文件自动发现机制（建议用 glob）', 'warn'))
    else:
        issues.append(('🟡 无 .py 文件，跳过文件发现检查', 'skip'))

    # 6) 依赖声明
    if info['skill_md'] and ('依赖' in info['skill_md'] or 'requirements' in info['skill_md'].lower()):
        issues.append(('✅ SKILL.md 声明了依赖', 'pass'))
        score += 1
    else:
        issues.append(('🟡 SKILL.md 未声明依赖', 'warn'))

    # 评级
    pct = score / max(total, 1)
    if pct >= 0.8:
        rating = '🟢 稳固'
    elif pct >= 0.4:
        rating = '🟡 有隐患'
    else:
        rating = '🔴 无地基'

    return {'rating': rating, 'issues': issues, 'score': f'{score}/{total}'}


def check_code_risks(info):
    """代码风险扫描：常见 AI 复现篡改点。"""
    issues = []
    total_checks = 0
    found_risks = 0

    if not info['py']:
        return {'rating': '🟡 无嵌入式代码', 'issues': [('🟡 无 .py 文件，无法扫描代码风险', 'skip')], 'score': '-'}

    patterns = [
        ('异常处理', r'except\s*:\s*pass', '裸 except: pass — 可能吞掉内存错误等关键异常'),
        ('浮点比较', r'\w+\s*==\s*0\.0', '浮点数精确相等比较 — 可能漏判接近 0 的值'),
        ('除零风险', r'return\s+[^/]*/\s*\w+', 'return 中直接返回除法结果 — 分母为 0 时无保护'),
        ('硬编码阈值', r'skiprows\s*=\s*\d', '固定的 skiprows — 格式漂移时数据错位'),
        ('路径拼接', r'[\'\"][/\w]+\s*\+\s*[\'\"\/]|[\'\"\/]\s*\+\s*[\'\"][\w/]+', '字符串拼接路径 — 建议用 os.path.join'),
        ('静默覆盖', r'open\([^)]*,\s*[\'\"]w[\'\"]', '写模式打开文件 — 未警告覆盖已有内容'),
        ('超时缺失', r'requests\.(get|post|put|delete)\([^)]*\)', 'HTTP 请求未设置 timeout — 可能无限挂起'),
    ]

    for name, pattern, desc in patterns:
        total_checks += 1
        if re.search(pattern, info['py']):
            issues.append((f'🟠 [{name}] {desc}', 'warn'))
            found_risks += 1

    if found_risks == 0:
        issues.append(('✅ 未检测到常见篡改点', 'pass'))

    # 评级基于嵌入代码行数（取最大单文件）
    lines = info.get('max_py_lines', len(info['py'].splitlines()) if info['py'] else 0)
    py_count = info.get('py_count', 1 if info['py'] else 0)
    if lines > 200:
        if py_count > 1:
            issues.append((f'🟡 嵌入代码 {py_count} 个 .py 文件，最大单文件 {lines} 行 — 文件较多，AI 复现时可能遗漏', 'warn'))
        else:
            issues.append((f'🟡 嵌入代码 {lines} 行 — 较长，AI 复现时可能遗漏或篡改', 'warn'))

    if found_risks == 0 and lines <= 200:
        rating = '🟢 低风险'
    elif found_risks <= 2:
        rating = '🟠 有风险'
    else:
        rating = '🔴 高风险'

    return {'rating': rating, 'issues': issues, 'score': f'{found_risks}/{total_checks}'}


def check_rules(info):
    """规则评估：检查 SKILL.md 中的业务规则是否明确、无歧义。"""
    md = info['skill_md']
    issues = []

    if not md:
        return {'rating': '🟡 无 SKILL.md', 'issues': [('🟡 未找到 SKILL.md，无法评估规则', 'skip')], 'score': '-'}

    total = 6
    score = 0

    # 1) 分类歧义 — 查找模糊词汇
    fuzzy_words = ['一般', '大概', '酌情', '适当', '差不多', '基本上', '通常', '大致', '左右']
    found_fuzzy = [w for w in fuzzy_words if w in md]
    if found_fuzzy:
        issues.append((f'🟠 存在模糊表述: {found_fuzzy[:3]}', 'warn'))
    else:
        issues.append(('✅ 未检测到模糊词汇', 'pass'))
        score += 1

    # 2) 边界/数值约束
    if re.search(r'(最小|最大|范围|不低于|不超过|>=|<=)', md):
        issues.append(('✅ 定义了数值边界/范围', 'pass'))
        score += 1
    else:
        issues.append(('🟡 未检测到明确的数值边界约束', 'warn'))

    # 3) 公式/计算明确性
    if re.search(r'([+\-*/^]|公式|计算|sum|avg|mean)', md):
        issues.append(('✅ 包含计算/公式说明', 'pass'))
        score += 1
    else:
        issues.append(('🟡 未检测到计算公式', 'info'))

    # 4) 单位一致性
    mult_units = re.findall(r'(元|万元|亿|%|百分比|千分比|bps)', md)
    if len(set(mult_units)) > 2:
        issues.append((f'🟠 多单位混用: {list(set(mult_units))}', 'warn'))
    else:
        issues.append(('✅ 单位使用一致', 'pass'))
        score += 1

    # 5) 异常分支覆盖
    if re.search(r'(如果.*不|若.*不|错误|异常|失败|缺失|为空)', md):
        issues.append(('✅ 有异常分支处理', 'pass'))
        score += 1
    else:
        issues.append(('🟠 缺少异常值/失败场景处理说明', 'warn'))

    # 6) 默认值声明
    if re.search(r'(默认|缺省|default|fallback)', md):
        issues.append(('✅ 声明了默认值/回退策略', 'pass'))
        score += 1
    else:
        issues.append(('🟡 未声明默认值策略', 'warn'))

    pct = score / total
    if pct >= 0.8:
        rating = '🟢 明确'
    elif pct >= 0.4:
        rating = '🟡 有歧义'
    else:
        rating = '🔴 歧义较多'

    return {'rating': rating, 'issues': issues, 'score': f'{score}/{total}'}


def _is_tool_skill(info):
    """工具库型 Skill：专注文件操作/格式转换，不做数据分析。"""
    md = info.get('skill_md', '')
    tool_signals = [
        'create', 'edit', 'convert', 'merge', 'split',
        'spreadsheet', 'workbook', 'presentation',
        'format', 'template', 'validate',
    ]
    analysis_signals = [
        'analyze', 'analysis', '计算', '统计', '分析',
        'visualize', 'report', 'insight',
        'chart', 'graph', 'forecast', 'trend',
    ]
    tool_count = sum(1 for s in tool_signals if s in md.lower())
    analysis_count = sum(1 for s in analysis_signals if s in md.lower())
    return tool_count > analysis_count


def check_guardrails(info, skill_type='code-engineered'):
    """护栏评估：检查解读规则是否到位，防止 AI 自信地输出错误结论。
    code-engineered 分析型: 全 8 项（置信度/数据来源/时效性 全查）;
    code-engineered 工具库型: 精简 5 项（跳过置信度/数据来源/时效性）;
    methodology 型: 精简 5 项（同上）。"""
    md = info['skill_md']
    issues = []

    if not md:
        return {'rating': '🟡 无 SKILL.md', 'issues': [('🟡 未找到 SKILL.md，无法评估护栏', 'skip')], 'score': '-'}

    # 代码工程型拆两档：工具库 vs 分析型
    is_tool = skill_type == 'code-engineered' and _is_tool_skill(info)

    total = 8
    score = 0

    # 1) 输出格式明确
    if re.search(r'(```|json|markdown|table|表格|图表|输出格式|export)', md):
        issues.append(('✅ 明确了输出格式', 'pass'))
        score += 1
    else:
        issues.append(('🟠 未定义输出格式', 'warn'))

    # 2) 禁令/护栏 — 跨语言信号（否定词/大写警告/中文禁止）
    status, text = _prohibition_signal(md)
    issues.append((text, status))
    if status == 'pass':
        score += 1

    # 3) 验证/自检
    if re.search(r'(验证|检查|确认|validate|verify|check|自检)', md):
        issues.append(('✅ 包含验证/自检步骤', 'pass'))
        score += 1
    else:
        issues.append(('🟠 缺少输出验证/自检要求', 'warn'))

    # 4) 置信度（分析型代码工程专属，工具库/方法论跳过）
    if skill_type == 'code-engineered' and not is_tool:
        if re.search(r'(置信|可信度|confidence|uncertainty|reliability|error\s+margin|不确定|风险)', md):
            issues.append(('✅ 涉及置信度/风险评估', 'pass'))
            score += 1
        else:
            issues.append(('🟡 未要求置信度声明', 'info'))
    elif is_tool:
        issues.append(('🟡 工具库型 Skill，置信度检查跳过', 'skip'))
        total -= 1
    else:
        issues.append(('🟡 纯方法论型，置信度检查跳过', 'skip'))
        total -= 1

    # 5) 数据来源限制（分析型代码工程专属，工具库/方法论跳过）
    if skill_type == 'code-engineered' and not is_tool:
        if re.search(r'(数据.*来源|数据.*范围|数据.*限制|仅.*数据|不包括|data\s+(source|scope)|limited\s+to|coverage)', md):
            issues.append(('✅ 声明了数据来源/范围限制', 'pass'))
            score += 1
        else:
            issues.append(('🟡 未声明数据来源限制', 'info'))
    elif is_tool:
        issues.append(('🟡 工具库型 Skill，数据来源检查跳过', 'skip'))
        total -= 1
    else:
        issues.append(('🟡 纯方法论型，数据来源检查跳过', 'skip'))
        total -= 1

    # 6) 错误回退
    if re.search(r'(错误|失败|异常|无法|不可用|回退|fallback)', md):
        issues.append(('✅ 定义了错误处理/回退策略', 'pass'))
        score += 1
    else:
        issues.append(('🟠 未定义错误回退策略', 'warn'))

    # 7) 时效性（分析型代码工程专属，工具库/方法论跳过）
    if skill_type == 'code-engineered' and not is_tool:
        if re.search(r'(截至|更新时间|有效期|时效|T\+|交易日|截止|as\s+of|last\s+updated|valid\s+until|expir)', md):
            issues.append(('✅ 声明了数据时效性', 'pass'))
            score += 1
        else:
            issues.append(('🟡 未声明数据时效性约束', 'info'))
    elif is_tool:
        issues.append(('🟡 工具库型 Skill，时效性检查跳过', 'skip'))
        total -= 1
    else:
        issues.append(('🟡 纯方法论型，时效性检查跳过', 'skip'))
        total -= 1

    # 8) 前提假设
    if re.search(r'(假设|前提|前置|前提条件)', md):
        issues.append(('✅ 声明了前提假设', 'pass'))
        score += 1
    else:
        issues.append(('🟡 未声明前提假设', 'info'))

    pct = score / total
    if pct >= 0.8:
        rating = '🟢 到位'
    elif pct >= 0.5:
        rating = '🟡 缺项'
    else:
        rating = '🔴 薄弱'

    return {'rating': rating, 'issues': issues, 'score': f'{score}/{total}'}


def _branch_density(md):
    """跨语言异常分支覆盖信号：不看具体用词，看结构化密度。"""
    checklist = len(re.findall(r'^\s*[-*]\s', md, re.MULTILINE))
    warn_icons = len(re.findall(r'[⚠️🚨❌✅🔴⛔🟡🟠🟢]', md))
    tables = md.count('|---')
    checkbox = len(re.findall(r'\[ \]|\[x\]', md, re.IGNORECASE))
    signal = checklist + warn_icons * 2 + tables * 3 + checkbox * 2
    if signal >= 5:
        return ('pass', f'✅ 检测到条件分支信号（清单 {checklist} 项 / 图标 {warn_icons} / 表格 {tables}）')
    else:
        return ('warn', '🟡 未检测到足够的条件分支信号，建议 AI 人工审查')


def _prohibition_signal(md):
    """跨语言禁止/护栏声明信号：否定词 + 大写警告词 + 中文禁止词。"""
    negations = len(re.findall(
        r'\b(?:never|not|no|don\'?t|REJECT|DENY|BLOCK|SHALL\s+NOT)\b',
        md, re.IGNORECASE
    ))
    caps_warnings = len(re.findall(r'[A-Z]{5,}', md))
    zh_prohibition = len(re.findall(r'(不要|不能|禁止|切勿|严禁)', md))
    red_flags = len(re.findall(r'RED\s+FLAG|🚨|⛔', md, re.IGNORECASE))
    signal = negations * 2 + caps_warnings + zh_prohibition * 2 + red_flags * 3
    if signal >= 3:
        return ('pass', f'✅ 检测到禁止/护栏声明（否定词 {negations} / 中文禁止 {zh_prohibition}）')
    else:
        return ('warn', '🟡 未检测到明确的禁止操作声明')


def check_methodology(info):
    """纯方法论型 Skill 评估。"""
    md = info['skill_md']
    issues = []

    if not md:
        return {'rating': '🟡 无 SKILL.md', 'issues': [('🟡 未找到 SKILL.md', 'skip')], 'score': '-'}

    total = 5
    score = 0

    # 1) 步骤清晰
    if re.search(r'(步骤|Step|##\s+\d|第[一二三四五六七八九十\d]+步)', md):
        issues.append(('✅ 有结构化步骤', 'pass'))
        score += 1
    else:
        issues.append(('🟠 缺少结构化步骤描述', 'warn'))

    # 2) 边界处理 — 跨语言结构信号（清单/图标/表格密度）
    status, text = _branch_density(md)
    issues.append((text, status))
    if status == 'pass':
        score += 1

    # 3) 输出格式定义 — 关键词 + 代码块检测
    has_output_kw = re.search(r'(输出|产出|结果|report|生成|respond\s+with|returns?\s+the)', md) is not None
    code_blocks = len(re.findall(r'```', md)) // 2
    if has_output_kw or code_blocks >= 2:
        issues.append(('✅ 定义了输出格式', 'pass'))
        score += 1
    else:
        issues.append(('🟡 未明确定义输出格式', 'warn'))

    # 4) 有示例
    if '例如' in md or '示例' in md or 'e.g.' in md.lower() or 'eg' in md.lower() or '```' in md:
        issues.append(('✅ 包含示例', 'pass'))
        score += 1
    else:
        issues.append(('🟡 缺少示例说明', 'warn'))

    # 5) 自洽 — 检查 SKILL.md 引用的文件是否在文件夹中存在
    mentioned_files = re.findall(r'[`"]([a-zA-Z0-9_./-]*[a-zA-Z0-9_]+\.(?:py|md|xlsx|xls|csv|json|yaml|yml|toml))[`"]', md)
    existing_names = {f['name'] for f in info.get('files', [])}
    existing_paths = {f.get('rel_path', f['name']) for f in info.get('files', [])}
    # 优先用完整相对路径匹配，退化为 basename
    missing = [m for m in mentioned_files if m not in existing_paths and os.path.basename(m) not in existing_names]
    if missing:
        issues.append((f'🟠 引用了不存在的文件: {missing[:3]}', 'warn'))
    elif mentioned_files:
        issues.append((f'✅ 引用文件均在文件夹中（{len(mentioned_files)} 个）', 'pass'))
        score += 1
    else:
        issues.append(('🟡 未在 SKILL.md 中检测到文件引用，跳过自洽检查', 'skip'))

    issues.append(('📝 以上为结构信号基线，语义判断（分支是否完备、逻辑是否正确）请由 AI 补充', 'info'))

    pct = score / total
    if pct >= 0.8:
        rating = '🟢 可靠'
    elif pct >= 0.4:
        rating = '🟡 有改进空间'
    else:
        rating = '🔴 不可靠'

    return {'rating': rating, 'issues': issues, 'score': f'{score}/{total}'}


# =============================================================================
# 4. 报告生成
# =============================================================================


def generate_report(info, results, output_dir=None):
    """生成审查报告三版本。"""
    skill_name = 'Unknown'
    if info['skill_md']:
        m = re.search(r'name:\s*(.+)', info['skill_md'])
        if m:
            skill_name = m.group(1).strip()

    today = date.today().isoformat()
    skill_type = classify_skill(info)

    # 评级
    f = results['foundation']
    c = results['code']
    r = results['rules']
    g = results['guardrails']

    # 摘要
    all_items = f['issues'] + c['issues'] + r['issues'] + g['issues']
    issues = [i for i in all_items if i[1] in ['fail', 'warn']]
    infos = [i for i in all_items if i[1] == 'info']
    if not issues and not infos:
        summary = '✅ 未发现风险。'
    elif not issues:
        summary = f'📌 无阻塞项，{len(infos)} 项需 AI 补充判断。'
    else:
        critical = sum(1 for i in issues if i[1] == 'fail')
        warnings = sum(1 for i in issues if i[1] == 'warn')
        summary = f'⚠️ 发现 {critical} 项阻塞、{warnings} 项高危风险。'
        if infos:
            summary += f' 另有 {len(infos)} 项需 AI 补充判断。'

    # 议题文本
    def fmt_issues(iss):
        lines = []
        for text, status in iss:
            lines.append(f'- {text}')
        return '\n'.join(lines) if lines else '- 无'

    f_rating = f['rating']
    f_score = f['score']
    c_rating = c['rating']
    c_score = c['score']
    r_rating = r['rating']
    r_score = r['score']
    g_rating = g['rating']
    g_score = g['score']
    fi = fmt_issues(f['issues'])
    ci = fmt_issues(c['issues'])
    ri = fmt_issues(r['issues'])
    gi = fmt_issues(g['issues'])
    sp = info.get('skill_md_path', '')

    # 专业版
    self_check_passed = all(k in results for k in ['foundation', 'code', 'rules', 'guardrails'])
    self_check_msg = '✅ 全部通过（文件完整、四维评估完整）' if self_check_passed else '⚠️ 部分评估维度缺失'

    report = f"""# HaluCatch Report — {skill_name}

**日期**: {today}
**Skill 类型**: {skill_type}
**文件**: {sp}

---

## 📌 TL;DR

{summary}

---

## 🎯 核心结论卡片

| 维度 | 评级 | 分数 |
|------|------|------|
| 🏗️ 地基 | {f_rating} | {f_score} |
| 🤖 代码 | {c_rating} | {c_score} |
| 📝 规则/方法论 | {r_rating} | {r_score} |
| 🛡️ 护栏 | {g_rating} | {g_score} |

---

## 🔍 审查发现

### 🏗️ 地基
{fi}

### 🤖 代码
{ci}

### 📝 规则/方法论
{ri}

### 🛡️ 护栏
{gi}

---

> 本报告由 HaluCatch 生成。自检: {self_check_msg}
"""

    # 通俗版 — 附带语境解释
    context_map = {
        '硬编码路径': '脚本里写死了某个人的电脑路径，换台机器就跑不了',
        '裸 except': '异常被静默吞掉，出错时没有任何提示，很难排查',
        'skiprows': '数据格式跟预期不一样时，强行跳过行会导致数据错位',
        '自动发现': '没有自动发现文件的机制，每次都得手动指定文件',
        '未检测到异常分支': '遇到意外情况时，AI 不知道该怎么做，可能给出错误结果',
        '缺少输出': '没说输出长什么样，不同 AI 可能给出格式完全不同的结果',
        '缺少结构化步骤': '指令像流水账，AI 可能跳过关键步骤或顺序混乱',
        '缺少示例': '没有例子，AI 只能靠猜，容易理解偏差',
        '缺少验证': '没有检查步骤，AI 可能自信地输出错误内容不做验证',
        '未声明前提假设': '没说明在什么条件下这个 Skill 才能正常工作',
        '未定义错误回退': '执行失败时没有备用方案，AI 会卡住',
    }
    simple_issues = []
    for iss in issues:
        text = iss[0].replace('🔴', '❌').replace('🟠', '⚠️').replace('🟡', '📌')
        hint = ''
        for key, val in context_map.items():
            if key in text:
                hint = f'（{val}）'
                break
        simple_issues.append(f'- {text}{hint}')

    simple_body = '\n'.join(simple_issues) if simple_issues else '✅ 无发现问题。'

    simple_report = f"""# HaluCatch 通俗报告 — {skill_name}

**日期**: {today}

## 一句话
{summary}

## 发现的问题
{simple_body}

---

> 本报告是专业版的白话版本。如需技术细节，见同目录下的专业版报告。
"""

    # AI 行动版
    fix_items = []
    for iss in issues:
        if '硬编码路径' in iss[0]:
            fix_items.append('- 硬编码路径 → 改为 `--data-dir` 参数传入')
        elif 'except' in iss[0]:
            fix_items.append('- 裸 except → 改为 `except Exception as e:` 并打印日志')
        elif 'validate' in iss[0]:
            fix_items.append('- 缺 validate 模式 → 添加 `--validate` 参数和数据验证函数')
        elif '输入验证' in iss[0]:
            fix_items.append('- 缺输入验证 → 添加 check_columns() 函数')
        elif '嵌入式代码' in iss[0]:
            fix_items.append('- 无固化 .py → 生成骨架脚本')
        else:
            fix_items.append(f'- {iss[0]}')

    action_report = f"""# HaluCatch AI 行动版 — {skill_name}

**日期**: {today}

## 修复清单
{chr(10).join(fix_items) if fix_items else '无修复项'}

## 修复后验证检查点
- [ ] 运行 `--validate` 通过
- [ ] 所有列名校验通过
- [ ] 无硬编码路径
- [ ] 用真实数据跑通一次
- [ ] 生成 feedback.md

## feedback.md 模板

```markdown
# HaluCatch 修复反馈

**时间**: [当前时间]

## 修改清单
- [ ] 修复项 1
- [ ] 修复项 2

## 验证输出
[粘贴 --validate 输出]

## 完整运行
[粘贴运行输出的最后 10 行]

## 问题
[无 / 描述]
```

---

## 下一步（请选择）

1. **执行修复** — 将本报告发给你的 AI，让它按方案修改目标 Skill。修复后重新运行 `halucatch_core.py --skill-dir <路径>` 验证。
2. **不执行** — 不做任何修改，审查结束。
3. **我有更好的意见** — 描述你的修复想法，我据此重新生成修复方案。
"""

    # 落盘
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base = os.path.join(output_dir, f'HaluCatch-report-{today}')
        for suffix, content in [('', report), ('-通俗版', simple_report), ('-行动版', action_report)]:
            path = f'{base}{suffix}.md'
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  📄 报告已生成: {path}")
    else:
        print(report)

    return {'professional': report, 'simple': simple_report, 'action': action_report}


# =============================================================================
# 5. 主入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='HaluCatch — AI Skill 执行可靠性审查')
    parser.add_argument('--skill-dir', required=True, help='目标 Skill 文件夹路径')
    parser.add_argument('--output-dir', default=None, help='报告输出目录（缺省则输出到终端）')
    parser.add_argument('--validate', action='store_true', help='仅扫描文件清单，不执行评估')
    args = parser.parse_args()

    print("=" * 60)
    print("  HaluCatch — AI Skill 执行可靠性审查")
    print("=" * 60)

    # Phase 1: 扫描
    print("\n[1/3] 扫描文件...")
    info = scan_folder(args.skill_dir)
    if info is None:
        return

    if args.validate:
        print("\n✅ 文件扫描完成。--validate 模式下不执行评估。")
        return

    # Phase 0: 分类
    skill_type = classify_skill(info)
    print(f"\n[2/3] 分类: {'代码工程型' if skill_type == 'code-engineered' else '纯方法论型'}")

    # Phase 2: 评估
    print("\n[3/3] 执行评估...")
    results = {}

    if skill_type == 'code-engineered':
        print("  🏗️ 地基检查...")
        results['foundation'] = check_foundation(info)
        print(f"     {results['foundation']['rating']}")
        print("  🤖 代码风险扫描...")
        results['code'] = check_code_risks(info)
        print(f"     {results['code']['rating']}")
        print("  📝 规则评估...")
        results['rules'] = check_rules(info)
        print(f"     {results['rules']['rating']}")
        results['rules']['issues'].append(('📝 以上为脚本基线检查，AI 应在此基础上补充语义分析', 'info'))
        print("  🛡️ 护栏评估...")
        results['guardrails'] = check_guardrails(info, skill_type)
        print(f"     {results['guardrails']['rating']}")
        results['guardrails']['issues'].append(('🛡️ 以上为脚本基线检查，AI 应在此基础上补充语义分析', 'info'))
    else:
        print("  📝 方法论评估...")
        results['rules'] = check_methodology(info)
        results['foundation'] = {'rating': '🟢 纯方法论', 'issues': [('✅ 纯方法论型 Skill，地基检查不适用', 'pass')], 'score': '-'}
        results['code'] = {'rating': '🟢 纯方法论', 'issues': [('✅ 纯方法论型 Skill，代码风险不适用', 'pass')], 'score': '-'}
        print("  🛡️ 护栏评估...")
        results['guardrails'] = check_guardrails(info, skill_type)
        print(f"     {results['guardrails']['rating']}")
        results['guardrails']['issues'].append(('🛡️ 以上为脚本基线检查，AI 应在此基础上补充语义分析', 'info'))

    # Phase 3: 报告（缺省输出到自身 reports/ 目录，避免污染目标 Skill 目录）
    print("\n📊 生成报告...")
    default_out = args.output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    reports = generate_report(info, results, default_out)

    # 自检
    dims = ['foundation', 'code', 'rules', 'guardrails']
    all_dims_done = all(d in results and 'rating' in results[d] for d in dims)
    has_info_items = any(
        any(i[1] == 'info' for i in results[d].get('issues', []))
        for d in dims
    )
    if not all_dims_done:
        print("  ⚠️ 自检: 部分评估维度未完成")
    elif has_info_items:
        print("  ✅ 自检: 四维评估完成（部分维度建议 AI 补充语义分析）")
    else:
        print("  ✅ 自检: 全部通过")

    print("\n✅ HaluCatch 审查完成。")
    print(f"   报告已保存至: {default_out}")


if __name__ == '__main__':
    main()
