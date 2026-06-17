"""
HaluCatch 单元测试 — 覆盖 6 个检查函数的核心分支
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from halucatch_core import classify_skill, check_foundation, check_code_risks, check_methodology, check_rules, check_guardrails


# ---- helpers ----

def make_info(py_content=None, md_content=None, files=None, has_data=False):
    """构造 scan_folder 返回的 info dict。"""
    return {
        'files': files or [],
        'skill_md': md_content or '',
        'skill_md_path': '/fake/SKILL.md',
        'py': py_content,
        'py_path': '/fake/core.py' if py_content else None,
        'has_data': has_data,
    }


# ---- classify_skill ----

def test_classify_data_driven_by_py():
    info = make_info(py_content='print(1)')
    assert classify_skill(info) == 'data-driven'


def test_classify_data_driven_by_data():
    info = make_info(md_content='pd.read_csv()', has_data=True)
    assert classify_skill(info) == 'data-driven'


def test_classify_methodology():
    info = make_info(md_content='## 步骤\n1. 做A\n2. 做B')
    assert classify_skill(info) == 'methodology'


# ---- check_foundation ----

def test_foundation_no_py():
    info = make_info(md_content='name: TestSkill')
    result = check_foundation(info)
    # item 1 fail, items 2-5 skip, item 6 checks md
    assert result['rating'] in ('🔴 无地基', '🟡 有隐患')
    # 验证无 .py → skip 而非 warn
    issues = dict(result['issues'])
    assert 'skip' in str(result['issues'])


def test_foundation_full():
    py = '\n'.join([
        'import glob',
        'def check_columns(): pass',
        "# --validate mode disabled by default",
        "files = glob.glob('*.csv')",
    ])
    md = 'name: TestSkill\n依赖: numpy, pandas'
    info = make_info(py_content=py, md_content=md)
    result = check_foundation(info)
    assert result['rating'] == '🟢 稳固'
    assert result['score'] >= '5/6'


def test_foundation_hardcoded_path():
    py = "data = '/Users/bob/data.csv'\nglob.glob('*')"
    info = make_info(py_content=py)
    result = check_foundation(info)
    issues_text = ' '.join(i[0] for i in result['issues'])
    assert '硬编码' in issues_text


# ---- check_code_risks ----

def test_code_risks_no_py():
    info = make_info()
    result = check_code_risks(info)
    assert result['rating'] == '🟡 无嵌入式代码'


def test_code_risks_bare_except():
    py = 'try:\n    x=1\nexcept:\n    pass\n'
    info = make_info(py_content=py)
    result = check_code_risks(info)
    issues_text = ' '.join(i[0] for i in result['issues'])
    assert 'except' in issues_text


def test_code_risks_clean():
    py = 'x = 1\nprint(x)\n'
    info = make_info(py_content=py)
    result = check_code_risks(info)
    assert result['rating'] == '🟢 低风险'


# ---- check_methodology ----

def test_methodology_complete():
    md = '\n'.join([
        '## 步骤 1',
        '如果数据缺失则报错',
        '输出 report.md',
        '例如：```python```',
        '参见 scripts/run.py',
    ])
    info = make_info(md_content=md)
    result = check_methodology(info)
    assert result['rating'] == '🟢 可靠'


def test_methodology_minimal():
    md = 'some instructions here'
    info = make_info(md_content=md)
    result = check_methodology(info)
    assert result['rating'] in ('🟡 有改进空间', '🔴 不可靠')


def test_methodology_missing_file_ref():
    md = '运行 `nonexistent.py` 开始'
    info = make_info(md_content=md, files=[{'name': 'SKILL.md'}])
    result = check_methodology(info)
    issues_text = ' '.join(i[0] for i in result['issues'])
    assert '不存在' in issues_text


# ---- check_rules ----

def test_rules_fuzzy_words():
    md = '一般情况下酌情处理，大概 100 左右'
    info = make_info(md_content=md)
    result = check_rules(info)
    issues_text = ' '.join(i[0] for i in result['issues'])
    assert '模糊' in issues_text


def test_rules_clean():
    md = '\n'.join([
        'name: TestSkill',
        '最小值为 0，最大值为 100',
        '计算公式: x + y * z',
        '如果输入为空则使用默认值 50',
        'default: 50',
    ])
    info = make_info(md_content=md)
    result = check_rules(info)
    assert result['rating'] == '🟢 明确'


# ---- check_guardrails ----

def test_guardrails_strong():
    md = '\n'.join([
        '输出 json 格式',
        '不要 输出不确认的数据',
        '执行后验证结果',
        '置信度 < 0.8 时标记',
        '数据来源: 仅限 2024 年报',
        '若失败则回退到默认值',
        '截至 2026-06-01',
        '假设: 用户已登录',
    ])
    info = make_info(md_content=md)
    result = check_guardrails(info)
    assert result['rating'] == '🟢 到位'


def test_guardrails_weak():
    md = 'do something and output it'
    info = make_info(md_content=md)
    result = check_guardrails(info)
    assert result['rating'] in ('🔴 薄弱', '🟡 缺项')


# ---- 边界用例 — 输入不完整时行为正确 ----

import tempfile

def test_scan_empty_folder():
    with tempfile.TemporaryDirectory() as td:
        result = __import__('halucatch_core').scan_folder(td)
        assert result is not None
        assert result['skill_md'] is None
        assert result['py'] is None
        assert len(result['files']) == 0


def test_scan_only_skillmd():
    with tempfile.TemporaryDirectory() as td:
        md_path = os.path.join(td, 'SKILL.md')
        with open(md_path, 'w') as f:
            f.write('name: Test\n\n## 步骤 1\n做 A\n如果失败则报错')
        result = __import__('halucatch_core').scan_folder(td)
        assert result is not None
        assert result['skill_md'] is not None
        assert result['py'] is None
        assert len(result['files']) == 1


def test_scan_only_py_no_skillmd():
    with tempfile.TemporaryDirectory() as td:
        py_path = os.path.join(td, 'core.py')
        with open(py_path, 'w') as f:
            f.write("print('hello')\nglob.glob('*')")
        result = __import__('halucatch_core').scan_folder(td)
        assert result is not None
        assert result['skill_md'] is None
        assert result['py'] is not None
        assert len(result['files']) == 1


def test_scan_deep_nested_py():
    with tempfile.TemporaryDirectory() as td:
        nested = os.path.join(td, 'a', 'b', 'c')
        os.makedirs(nested)
        py_path = os.path.join(nested, 'deep.py')
        with open(py_path, 'w') as f:
            f.write('x = 1')
        result = __import__('halucatch_core').scan_folder(td)
        assert result is not None
        assert result['py'] is not None
        assert len(result['files']) == 1
        # 验证 rel_path 正确
        f = result['files'][0]
        assert f['rel_path'] == 'a/b/c/deep.py'
