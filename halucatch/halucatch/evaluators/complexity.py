"""复杂度与可维护性评估：结构指标检测，无需语义理解。"""

import re

# ── 脚本支持相关 ────────────────────────────────────────────────

# SKILL.md 内嵌代码块的语言白名单
CODE_BLOCK_LANGS = frozenset({
    'python', 'py', 'bash', 'sh', 'shell', 'zsh',
    'ruby', 'rb', 'js', 'javascript', 'ts', 'typescript',
    'go', 'golang', 'c', 'cpp', 'c++', 'perl', 'pl',
    'makefile', 'make', 'dockerfile',
})

# 命令行调用模式
CLI_CALL_PAT = re.compile(
    r'(^|\s)('
    r'(python3?|python\s+-m)\s+'
    r'|\./([a-zA-Z0-9_-]+\.(?:py|sh|rb|js|pl|go|ts))'
    r'|bash\s+|sh\s+|node\s+|ruby\s+|go\s+run\s+'
    r'|\bpip\s+(?:install|run)\b'
    r'|\bnpx\s+'
    r'|\bmake\b'
    r')', re.MULTILINE
)

# 步骤模式
STEP_PAT = re.compile(
    r'(?:'
    r'^\s*(?:\d+\.|[-*])\s+'      # 编号列表 1. / - *
    r'|\[[ x]\]\s+'                 # checkbox [ ] / [x]
    r'|(?:步骤|第[一二三四五六七八九十\d]+步|Step\s*\d+|step\s*\d+)'
    r')', re.MULTILINE | re.IGNORECASE
)

# ── 各指标计算 ──────────────────────────────────────────────────

def _count_steps(md):
    """统计 SKILL.md 中的步骤数（仅 ## 指令类标题下）。"""
    if not md:
        return 0
    lines = md.split('\n')
    in_instructions = False
    count = 0
    for line in lines:
        if re.match(r'^## ', line):
            heading = line.lower()
            # 只统计指令/流程/使用/Quick Start 类章节
            in_instructions = any(kw in heading for kw in (
                'instruction', 'usage', 'quick', 'steps', 'flow',
                'workflow', 'procedure', '指南', '指令', '步骤', '流程',
                '使用', '快速开始', 'how to', 'getting started', 'setup',
            ))
            continue
        if in_instructions and STEP_PAT.search(line):
            count += 1
    # 如果没找到任何指令章节，全文统计（回退）
    if count == 0:
        count = len(STEP_PAT.findall(md))
    return count


def _count_script_refs(info):
    """统计脚本引用数：scripts/ 文件 + 内嵌代码块 + CLI 调用。"""
    if not info:
        return 0
    count = 0

    # 1) scripts/ 目录下的脚本文件
    if info.get('files'):
        for f in info['files']:
            fp = f.get('path', '') or f.get('name', '')
            # 在 scripts/ 或 src/ 目录下，排除 pycache 和 .pyc
            if ('scripts/' in fp or 'src/' in fp or '/bin/' in fp) and \
               '__pycache__' not in fp and not fp.endswith('.pyc'):
                count += 1

    # 2) SKILL.md 内嵌代码块
    md = info.get('skill_md', '') or ''
    if md:
        # 找所有 fenced code blocks
        blocks = re.findall(r'```(\w*)', md)
        for lang in blocks:
            if lang.lower() in CODE_BLOCK_LANGS:
                count += 1

    # 3) SKILL.md 中命令行调用
    if md:
        # 去重：同一个脚本被多次引用只算一次
        calls = set()
        for m in CLI_CALL_PAT.finditer(md):
            calls.add(m.group(2).strip())
        count += len(calls)

    return count


def _heading_depth(md):
    """章节深度：最深标题层级 × 2，仅反映最深处。"""
    if not md:
        return 0
    headings = re.findall(r'^(#{2,}) ', md, re.MULTILINE)
    if not headings:
        return 0
    max_depth = max(len(h) for h in headings)
    # h2→0, h3→2, h4→5, h5→8, h6→10
    depth_map = {2: 0, 3: 2, 4: 5, 5: 8, 6: 10}
    return depth_map.get(max_depth, 10)


def _heading_complexity(md):
    """章节复杂度：加权统计所有子标题的分散程度。"""
    if not md:
        return 0
    headings = re.findall(r'^(#{2,}) ', md, re.MULTILINE)
    if not headings:
        return 0
    # h3×1 + h4×2 + h5×3 + h6×4
    total = 0
    for h in headings:
        level = len(h)
        if level >= 3:
            total += (level - 2)  # h3→1, h4→2, h5→3, h6→4
    return min(total / 3, 10)


def _doc_ref_depth(info):
    """文档引用深度：SKILL.md → 文档 → 再引用文档，最高 2 层。"""
    md = info.get('skill_md', '')
    if not md:
        return 0
    doc_exts = r'(?:md|pdf|png|jpg|jpeg|gif|svg|doc|xlsx|csv|txt|yaml|yml|json|toml)'
    refs = re.findall(rf'\[.*?\]\(([^):]+\.{doc_exts})\)', md)
    depth = 1 if refs else 0
    if not depth or not info.get('files'):
        return depth
    for ref in refs:
        ref_content = None
        for f in info['files']:
            fn = f.get('name', '') or f.get('path', '')
            if ref in fn or fn.endswith(ref):
                ref_content = f.get('_content', '')
                break
        if ref_content:
            sub_refs = re.findall(rf'\[.*?\]\(([^):]+\.{doc_exts})\)', ref_content)
            if sub_refs:
                depth = 2
                break
    return depth




def _cross_file_deps(info):
    """跨文件依赖度 = 被引用的外部文件数 + 脚本数。"""
    md = info.get('skill_md', '')
    if not md:
        return 0
    refs = len(re.findall(r'\[.*?\]\(([^):]+\.(?:md|py|sh|rb|js|go|yaml|yml|json|toml|txt))\)', md))
    scripts = _count_script_refs(info)
    # 去重：如果已经在 refs 里的不额外算
    return refs + scripts


def _code_doc_ratio(info):
    """代码/文档比：codelines / (codelines + SKILL.md 行数)。"""
    md = info.get('skill_md', '') or ''
    md_lines = len(md.splitlines()) if md else 0
    if md_lines == 0:
        return 0

    # 统计所有 Python 文件的代码行数
    code_lines = 0
    py_content = info.get('py', '') or ''
    if py_content:
        # py_content 是拼接的内容，去掉注释和空行
        for line in py_content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                code_lines += 1

    total = code_lines + md_lines
    return code_lines / max(total, 1)


def _redundancy_score(md):
    """重复冗余度：相近短语反复出现次数 / 行数。"""
    if not md:
        return 0
    lines = [ln.strip() for ln in md.splitlines() if ln.strip() and not ln.startswith('#')]
    if len(lines) < 10:
        return 0

    # 提取 5-10 个词的中等长度段落（有意义的指令片段）
    phrases = {}
    for line in lines:
        words = line.split()
        if 3 <= len(words) <= 15:
            key = ' '.join(words[:5]).lower()
            phrases[key] = phrases.get(key, 0) + 1

    # 出现 >= 3 次的短语数 / 总行数 → 归一化到 0-10
    duplicates = sum(1 for c in phrases.values() if c >= 3)
    ratio = duplicates / max(len(lines), 1)
    return min(ratio * 100, 10)


def _table_complexity(md):
    """表格复杂度 = 表格数 × 平均列数 / 参考值。"""
    if not md:
        return 0
    tables = re.findall(r'^\|[-| ]+\|\s*$', md, re.MULTILINE)
    if not tables:
        return 0
    table_count = 0
    total_cols = 0
    for match in re.finditer(r'^\|[-| ]+\|\s*$', md, re.MULTILINE):
        table_count += 1
        cols = len(match.group().split('|')) - 2  # 去掉首尾空
        total_cols += max(cols, 0)
    if table_count == 0:
        return 0
    avg_cols = total_cols / table_count
    # 阈值：3 列 × 3 张表 = 9，超过线性增长
    return min(table_count * avg_cols / 3, 10)


def _instruction_density(md):
    """指令密度 = (祈使句 + 步骤项 + 代码块) / 总行数，0-10 归一化。"""
    if not md:
        return 0
    lines = md.splitlines()
    total = max(len(lines), 1)

    # 祈使句：以动词开头的行或包含 "必须/应该/不要" 等
    imperatives = len(re.findall(
        r'(?i)(?:you\s+(?:should|must|cannot|need|have)|'
        r'[Mm]ake\s+sure|[Ee]nsure\s+|[Dd]o\s+not|[Nn]ever\s+|'
        r'[Aa]lways\s+|必须|应该|不要|请|务必|切勿)',
        md
    ))
    steps = _count_steps(md)
    code_blocks = len(re.findall(r'```', md)) // 2  # 每对 ``` 算一个块

    density = (imperatives + steps + code_blocks) / total
    return min(density * 100, 10)  # 归一化到 0-10


# ── 主评估函数 ──────────────────────────────────────────────────

def _score_to_level(score):
    """分数 → 等级映射。"""
    if score <= 3:
        return '🟢 低'
    elif score <= 6:
        return '🟡 中'
    return '🔴 高'


def _script_coverage_ratio(info):
    """计算脚本覆盖比 (0-1) 并返回乘数。"""
    md = info.get('skill_md', '') or ''
    steps = _count_steps(md)
    if steps == 0:
        return 1.0, 0.0, 0, 0  # 无法判断时不惩罚

    script_refs = _count_script_refs(info)
    ratio = min(script_refs / steps, 1.0)

    if ratio >= 0.9:
        multiplier = 0.3
    elif ratio >= 0.7:
        multiplier = 0.6
    elif ratio >= 0.5:
        multiplier = 0.8
    else:
        multiplier = 1.0

    return multiplier, ratio, steps, script_refs


def check_complexity(info, skill_type='code-engineered'):
    """复杂度与可维护性评估。

    代码工程型：7 项指标 + 脚本覆盖比乘数
    纯方法论型：5 项指标（无脚本/代码相关），无乘数
    """
    md = info.get('skill_md', '') or ''
    is_code = skill_type == 'code-engineered'

    scores = {}

    # ── 共通指标 ──
    # 1) 章节深度
    hdepth = _heading_depth(md)
    scores['heading_depth'] = {
        'label': '章节深度',
        'value': f'{hdepth:.0f} 分',
        'score': hdepth,
        'level': _score_to_level(hdepth),
    }

    # 2) 章节复杂度
    hcomp = _heading_complexity(md)
    scores['heading_complexity'] = {
        'label': '章节复杂度',
        'value': f'{hcomp:.1f}',
        'score': hcomp,
        'level': _score_to_level(hcomp),
    }

    # 3) 文档引用链
    doc_ref = _doc_ref_depth(info)
    doc_ref_score = doc_ref * 5
    scores['doc_ref'] = {
        'label': '文档引用链',
        'value': f'{doc_ref} 层',
        'score': doc_ref_score,
        'level': _score_to_level(doc_ref_score),
    }

    # 4) 跨文件依赖度
    deps = _cross_file_deps(info)
    dep_score = min(deps / 3, 10)  # 3+ 个依赖 = 10 分
    scores['deps'] = {
        'label': '跨文件依赖',
        'value': f'{deps} 项',
        'score': dep_score,
        'level': _score_to_level(dep_score),
    }

    # 4) 重复冗余度
    redundancy = _redundancy_score(md)
    scores['redundancy'] = {
        'label': '重复冗余',
        'value': f'{redundancy:.1f}',
        'score': redundancy,
        'level': _score_to_level(redundancy),
    }

    # 5) 表格复杂度
    table_score = _table_complexity(md)
    scores['table'] = {
        'label': '表格复杂度',
        'value': f'{table_score:.1f}',
        'score': table_score,
        'level': _score_to_level(table_score),
    }

    # ── 代码工程型专属 ──
    if is_code:
        # 6) 脚本覆盖比（计算但不计入 weighted，用作乘数）
        multiplier, ratio, steps_count, script_count = _script_coverage_ratio(info)
        coverage_pct = f'{ratio:.0%}' if ratio > 0 else '0%'
        coverage_label = '🟢 全覆盖' if ratio >= 0.9 else (
            '🟡 多数覆盖' if ratio >= 0.7 else (
                '🟠 半数覆盖' if ratio >= 0.5 else '🔴 覆盖不足'
            )
        )
        scores['coverage'] = {
            'label': '脚本覆盖比',
            'value': f'{coverage_pct} ({script_count} 脚本/{steps_count} 步骤) — {coverage_label}',
            'score': (1.0 - ratio) * 10,  # 0→10, 1.0→0
            'level': coverage_label,
            'multiplier': multiplier,
        }

        # 7) 代码/文档比
        cdr = _code_doc_ratio(info)
        cdr_score = max(0, (1.0 - cdr) * 10) if cdr < 0.3 else 0  # 代码<30% 才有风险
        cdr_pct = f'{cdr:.0%}'
        cdr_label = '🟢 描述充分' if cdr >= 0.3 else (
            '🟡 描述偏少' if cdr >= 0.15 else '🔴 描述不足'
        )
        scores['code_doc_ratio'] = {
            'label': '代码/文档比',
            'value': f'{cdr_pct} — {cdr_label}',
            'score': cdr_score,
            'level': cdr_label,
        }

        # 8) 指令密度
        density = _instruction_density(md)
        scores['density'] = {
            'label': '指令密度',
            'value': f'{density:.1f}',
            'score': density,
            'level': _score_to_level(density),
        }

        # ── 加权平均 ──
        weights = {
            'heading_depth': 0.05,
            'heading_complexity': 0.05,
            'doc_ref': 0.08,
            'deps': 0.15,
            'redundancy': 0.05,
            'table': 0.10,
            'coverage': 0.10,
            'code_doc_ratio': 0.15,
            'density': 0.27,
        }
    else:
        density = _instruction_density(md)
        scores['density'] = {
            'label': '指令密度',
            'value': f'{density:.1f}',
            'score': density,
            'level': _score_to_level(density),
        }

        weights = {
            'heading_depth': 0.08,
            'heading_complexity': 0.07,
            'doc_ref': 0.10,
            'deps': 0.30,
            'redundancy': 0.15,
            'table': 0.10,
            'density': 0.20,
        }

    # 计算加权平均分
    weighted = sum(scores[k]['score'] * weights.get(k, 0) for k in scores)
    weighted = min(max(weighted, 0), 10)

    # 应用脚本覆盖比乘数（仅代码工程型）
    if is_code and 'coverage' in scores:
        final = weighted * scores['coverage']['multiplier']
    else:
        final = weighted

    # 最终评级
    if final <= 2:
        rating = '🟢 低风险'
    elif final <= 5:
        rating = '🟡 注意'
    else:
        rating = '🔴 复杂'

    # 构建 issues 列表
    issues = []
    for _key, s in scores.items():
        if s['score'] <= 3:
            issues.append((f"✅ {s['label']}: {s['value']}", 'pass'))
        elif s['score'] <= 6:
            issues.append((f"🟡 {s['label']}: {s['value']}", 'warn'))
        else:
            issues.append((f"🔴 {s['label']}: {s['value']}", 'fail'))

    if is_code and 'coverage' in scores:
        issues.append((
            f"📊 脚本覆盖乘数: ×{scores['coverage']['multiplier']} "
            f"→ 加权 {weighted:.1f} × {scores['coverage']['multiplier']} = 最终 {final:.1f}",
            'info'
        ))

    score_display = f'{final:.1f}/10 (加权 {weighted:.1f})' if is_code else f'{final:.1f}/10'

    return {
        'rating': rating,
        'score': score_display,
        'issues': issues,
        'raw': scores,
        'weighted': weighted,
        'final': final,
    }
