# HaluCatch V6→V7 修复计划

**日期**: 2026-06-17 | **来源**: V6 去语言化回归测试 | **执行顺序**: 步骤1 → 实测 → 步骤2

---

## 步骤 1：护栏剩余 3 项去语言化

### 问题

`check_guardrails()` 的 8 项检查中，第 4/5/7 项仍用中文关键词正则，与之前第 2 项是同根问题。当前未暴露只因为测的 Skill 都是中英混合的。

| # | 检查项 | 当前正则 | 纯英文 Skill 预期 |
|---|--------|---------|------------------|
| 4 | 置信度 | `置信\|可信度\|confidence\|不确定\|风险` | `uncertainty`/`reliability`/`error margin` 命中不了 |
| 5 | 数据来源 | `数据.*来源\|数据.*范围\|数据.*限制\|仅.*数据\|不包括` | `data scope`/`data source`/`limited to` 不命中 |
| 7 | 时效性 | `截至\|更新时间\|有效期\|时效\|T\+\|交易日\|截止` | `as of`/`last updated`/`valid until`/`expires` 不命中 |

### 修复方案

每项都已有一个英文兜底词（confidence/—/—），补齐即可。改动最小——每处多补 2~3 个英文词，不加函数。

**位置**: `halucatch_core.py` → `check_guardrails()`

```diff
  # 4) 置信度
- if re.search(r'(置信|可信度|confidence|不确定|风险)', md):
+ if re.search(r'(置信|可信度|confidence|uncertainty|reliability|error\s+margin|不确定|风险)', md):
```

```diff
  # 5) 数据来源限制
- if re.search(r'(数据.*来源|数据.*范围|数据.*限制|仅.*数据|不包括)', md):
+ if re.search(r'(数据.*来源|数据.*范围|数据.*限制|仅.*数据|不包括|data\s+(source|scope)|limited\s+to|coverage)', md):
```

```diff
  # 7) 时效性
- if re.search(r'(截至|更新时间|有效期|时效|T\+|交易日|截止)', md):
+ if re.search(r'(截至|更新时间|有效期|时效|T\+|交易日|截止|as\s+of|last\s+updated|valid\s+until|expir)', md):
```

**影响面**: 零——纯正则扩展，不改变控制流。现有测试预期不变（测试用例 md 是中文）。

---

## 实测：纯英文 Skill + 嵌入式 Python Skill

步骤 1 修完后，需要用实际 Skill 验证去语言化是否生效。

### 标的 1：纯英文 Skill

找一个只有英文 SKILL.md、无中文的 Skill。推荐 clawhub 上的英文 Skill，例如：

```bash
clawhub install self-improving-agent   # 或 proactive-agent / agent-browser-clawdbot
```

验证点：
- 护栏 4/5/7 三项能否命中英文关键词（confidence/data source/as of 等）
- 方法论 `_branch_density` 对英文清单/表格信号仍正常
- `_prohibition_signal` 对英文否定词仍正常

### 标的 2：嵌入式 Python（`has_md_py` 路径）

找一个 SKILL.md 里有 `\`\`\`python` 代码块但无独立 .py 的 Skill。例如：

```bash
clawhub install ontology   # 或 weather
```

验证点：
- `classify_skill` 的 `has_md_py` 分支触发 → 分类为数据驱动型
- 地基检查报告「无固化 .py 脚本」（预期：确有嵌入代码但无独立脚本）
- `py_content` 为 `None`，代码风险扫描跳过

---

## 步骤 2：数据驱动型护栏分层

### 问题

当前 10 个 Skill 中，所有数据驱动型（xlsx/pptx/skill-sharpener）的护栏维度**全是 🔴 薄弱**。根因：8 项检查里有 3 项（数据来源、时效性、置信度）对纯工具库型 Skill 天生不适用，但全部参与计分。

### 修复方案

在 `check_guardrails(info, skill_type)` 中增加子类型判断，数据驱动型拆两档：

```python
def _is_tool_skill(info):
    """工具库型 Skill：专注文件操作/格式转换，不做数据分析。"""
    md = info.get('skill_md', '')
    tool_signals = [
        'create', 'edit', 'convert', 'merge', 'split',   # 文件操作
        'spreadsheet', 'workbook', 'presentation',        # 文档类型
        'format', 'template', 'validate',                 # 格式/验证
    ]
    analysis_signals = [
        'analyze', '计算', '统计', '分析',
        'visualize', 'report', 'insight',
        'chart', 'graph', 'forecast',
    ]
    tool_count = sum(1 for s in tool_signals if s in md.lower())
    analysis_count = sum(1 for s in analysis_signals if s in md.lower())
    return tool_count > analysis_count
```

然后在 `check_guardrails` 中：

```python
if skill_type == 'data-driven':
    if _is_tool_skill(info):
        # 工具库型：跳过 4/5/7（置信度/数据来源/时效性），只查 5 项
        total = 5
    else:
        # 分析型：全 8 项
        total = 8
```

**影响**:
| Skill | 当前分类 | 护栏 V6 | 护栏 V7 | 
|-------|---------|--------|--------|
| xlsx | 工具库 | 🔴 2/8 | 2/5 → 🟡 缺项 |
| pptx | 工具库 | 🔴 2/8 | 2/5 → 🟡 缺项 |
| skill-sharpener | 工具库 | 🔴 ?/8 | ?/5 |

### 注意

这个分层比方法论型的分层更复杂（需要判断「分析型 vs 工具型」）。可以作为 `_is_tool_skill()` 的初版，后续根据实测数据调整 `tool_signals` 和 `analysis_signals` 的权重。

---

## 执行顺序与依赖

```
步骤 1（护栏去语言化）
  │  改动: 3 处正则补英文词
  │  测试: 20 用例全过 + skill-vetter/myknowledge 重测
  │
  ├─→ 实测：纯英文 Skill
  │      改动: 无（仅运行验证）
  │      目的: 确认步骤 1 的去语言化生效
  │
  ├─→ 实测：嵌入式 Python Skill  
  │      改动: 无（仅运行验证）
  │      目的: 覆盖 has_md_py 盲区
  │
  └─→ 步骤 2（数据驱动护栏分层）
         改动: _is_tool_skill() + check_guardrails 分支
         测试: 20 用例 + 数据驱动型 3 个全测
```

步骤 1 和实测**独立**、可并行。步骤 2 **依赖**步骤 1 的测试通过后才能上。
