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
    """扫描文件夹，返回文件清单和 SKILL.md / .py 内容。"""
    if not os.path.isdir(path):
        print(f"❌ 路径不存在: {path}")
        return None

    files = []
    skill_md_content = None
    py_content = None
    skill_md_path = None
    py_path = None

    for fname in os.listdir(path):
        fpath = os.path.join(path, fname)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath)
            ext = os.path.splitext(fname)[1].lower()
            files.append({'name': fname, 'ext': ext, 'size': size, 'path': fpath})

            if fname.lower() in ['skill.md', 'toolcard.md']:
                skill_md_path = fpath
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    skill_md_content = f.read()

            if ext == '.py':
                py_path = fpath
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    py_content = f.read()

    has_data = any(f['ext'] in ['.xlsx', '.xls', '.csv'] for f in files)

    print(f"  📁 扫描: {path}")
    print(f"  📄 文件数: {len(files)}")
    if skill_md_content:
        print(f"  📝 SKILL.md: {len(skill_md_content.splitlines())} 行")
    if py_content:
        print(f"  🐍 .py 文件: {len(py_content.splitlines())} 行")
    if has_data:
        print(f"  📊 数据文件: {sum(1 for f in files if f['ext'] in ['.xlsx', '.xls', '.csv'])} 个")

    return {
        'files': files,
        'skill_md': skill_md_content,
        'skill_md_path': skill_md_path,
        'py': py_content,
        'py_path': py_path,
        'has_data': has_data,
    }


# =============================================================================
# 2. 技能分类
# =============================================================================

def classify_skill(info):
    """判断 Skill 类型：数据驱动型 / 纯方法论型。"""
    has_py = info['py'] is not None
    has_data = info['has_data']
    has_pd = info['skill_md'] and ('pd.read_' in info['skill_md'] or 'pandas' in info['skill_md'].lower())
    has_md_py = info['skill_md'] and ('```python' in info['skill_md'])

    if has_py or has_data or has_pd or has_md_py:
        return 'data-driven'
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
    if info['py'] and ('glob' in info['py'] or 'os.listdir' in info['py']):
        issues.append(('✅ 使用通配符/自动发现文件', 'pass'))
        score += 1
    else:
        issues.append(('🟡 未检测到自动文件发现机制', 'warn'))

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
        ('浮点比较', r'(p_pool|p_val)\s*==\s*0', '浮点数精确相等比较 — 可能漏判接近 0 的值'),
        ('统计函数', r'(math\.exp|scipy\.stats)', '自定义统计函数 — AI 可能替换为不同实现'),
        ('硬编码阈值', r'skiprows\s*=\s*\d', '固定的 skiprows — 格式漂移时数据错位'),
        ('除零风险', r'/\s*store_weeks', '除法未保护 — store_weeks=0 时产生 inf'),
    ]

    for name, pattern, desc in patterns:
        total_checks += 1
        if re.search(pattern, info['py']):
            issues.append((f'🟠 [{name}] {desc}', 'warn'))
            found_risks += 1

    if found_risks == 0:
        issues.append(('✅ 未检测到常见篡改点', 'pass'))

    # 评级基于嵌入代码行数
    lines = len(info['py'].splitlines())
    if lines > 200:
        issues.append((f'🟡 嵌入代码 {lines} 行 — 较长，AI 复现时可能遗漏或篡改', 'warn'))

    if found_risks == 0 and lines <= 200:
        rating = '🟢 低风险'
    elif found_risks <= 2:
        rating = '🟠 有风险'
    else:
        rating = '🔴 高风险'

    return {'rating': rating, 'issues': issues, 'score': f'{found_risks}/{total_checks}'}


def check_methodology(info):
    """纯方法论型 Skill 评估。"""
    md = info['skill_md']
    issues = []

    if not md:
        return {'rating': '🟡 无 SKILL.md', 'issues': [('🟡 未找到 SKILL.md', 'skip')], 'score': '-'}

    total = 5
    score = 0

    # 1) 步骤清晰
    if re.search(r'(步骤|Step|##\s+\d)', md):
        issues.append(('✅ 有结构化步骤', 'pass'))
        score += 1
    else:
        issues.append(('🟠 缺少结构化步骤描述', 'warn'))

    # 2) 边界处理
    if re.search(r'(如果|若|当|如果.*不|except)', md):
        issues.append(('✅ 有异常/边界情况处理', 'pass'))
        score += 1
    else:
        issues.append(('🟡 未检测到异常分支处理', 'warn'))

    # 3) 输出格式定义
    if re.search(r'(输出|产出|结果|report|生成)', md):
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

    # 5) 自洽
    if score >= 3:
        issues.append(('✅ 指令整体逻辑自洽', 'pass'))
        score += 1
    else:
        issues.append(('🟠 指令逻辑需加强', 'warn'))

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
    issues = [i for i in (f['issues'] + c['issues'] + r['issues'] + g['issues']) if i[1] in ['fail', 'warn']]
    if not issues:
        summary = '✅ 未发现风险。'
    else:
        critical = sum(1 for i in issues if i[1] == 'fail')
        warnings = sum(1 for i in issues if i[1] == 'warn')
        summary = f'⚠️ 发现 {critical} 项阻塞、{warnings} 项高危风险。'

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

> 本报告由 HaluCatch 生成。关键决策请人工复核。
"""

    # 通俗版
    simple_issues = []
    for iss in issues:
        text = iss[0].replace('🔴', '❌').replace('🟠', '⚠️').replace('🟡', '📌')
        simple_issues.append(f'- {text}')

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
    print(f"\n[2/3] 分类: {'数据驱动型' if skill_type == 'data-driven' else '纯方法论型'}")

    # Phase 2: 评估
    print("\n[3/3] 执行评估...")
    results = {}

    if skill_type == 'data-driven':
        print("  🏗️ 地基检查...")
        results['foundation'] = check_foundation(info)
        print(f"     {results['foundation']['rating']}")
        print("  🤖 代码风险扫描...")
        results['code'] = check_code_risks(info)
        print(f"     {results['code']['rating']}")
        print("  📝 规则评估（需 AI 判断）...")
        results['rules'] = {'rating': '🟡 待 AI 判断', 'issues': [('📝 业务规则需 AI 阅读 SKILL.md 后判断', 'info')], 'score': '-'}
        print("  🛡️ 护栏评估（需 AI 判断）...")
        results['guardrails'] = {'rating': '🟡 待 AI 判断', 'issues': [('🛡️ 解读护栏需 AI 阅读 SKILL.md 后判断', 'info')], 'score': '-'}
    else:
        print("  📝 方法论评估...")
        results['rules'] = check_methodology(info)
        results['foundation'] = {'rating': '🟢 纯方法论', 'issues': [('✅ 纯方法论型 Skill，地基检查不适用', 'pass')], 'score': '-'}
        results['code'] = {'rating': '🟢 纯方法论', 'issues': [('✅ 纯方法论型 Skill，代码风险不适用', 'pass')], 'score': '-'}
        results['guardrails'] = {'rating': '🟡 待 AI 判断', 'issues': [('🛡️ 解读护栏需 AI 阅读 SKILL.md 后判断', 'info')], 'score': '-'}

    # Phase 3: 报告
    print("\n📊 生成报告...")
    generate_report(info, results, args.output_dir if args.output_dir else args.skill_dir)

    print("\n✅ HaluCatch 审查完成。")
    print(f"   报告已保存至: {args.output_dir or args.skill_dir}")


if __name__ == '__main__':
    main()
