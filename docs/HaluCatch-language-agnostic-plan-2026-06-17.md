# HaluCatch 方法论评估去语言化方案

**日期**: 2026-06-17 | **来源**: skill-vetter 审查暴露的正则局限性

---

## 问题

当前 `check_methodology` 和 `check_guardrails` 的部分检查项用中文关键词正则做结论，英文/多语言 Skill 会产生误报：

| 检查项 | 当前正则 | 误报案例 |
|--------|---------|---------|
| 异常分支处理 | `如果\|若\|当\|except\|if\|when` | skill-vetter 用 `REJECT IMMEDIATELY IF` + 表格 + 图标，未命中 |
| 禁止操作 | `不要\|不能\|禁止\|切勿` | skill-vetter 用 `REJECT`/`DO NOT`/`NEVER`，未命中 |

根本原因：正则猜语义 → 永远只能覆盖已知语言的已知写法。

---

## 方案：结构化信号替代语义关键词

**核心思路**：脚本只做语言无关的结构密度测量（清单数、图标数、否定词频、大写警告密度），不做语义结论。结论交给 AI。

### 改动 1: `_branch_density()` — 替代异常分支检查

**位置**: `halucatch_core.py` → `check_methodology()` 第 396 行

**旧代码**:
```python
if re.search(r'(如果|若|当|如果.*不|except|\bif\s|\bwhen\s|\bin\s+case\s)', md):
```

**新代码**:
```python
def _branch_density(md):
    """跨语言异常分支覆盖信号：不看具体用词，看结构化密度。"""
    checklist = len(re.findall(r'^\s*[-*]\s', md, re.MULTILINE))     # 清单行
    warn_icons = len(re.findall(r'[⚠️🚨❌✅🔴⛔🟡🟠🟢]', md))         # 警示图标
    tables = md.count('|---')                                          # 表格
    checkbox = len(re.findall(r'\[ \]|\[x\]', md, re.IGNORECASE))       # 复选框

    signal = checklist + warn_icons * 2 + tables * 3 + checkbox * 2
    if signal >= 5:
        return ('pass', f'✅ 检测到条件分支信号（清单 {checklist} 项 / 图标 {warn_icons} / 表格 {tables}）')
    else:
        return ('warn', '🟡 未检测到足够的条件分支信号，建议 AI 人工审查')

# 在 check_methodology 中：
status, text = _branch_density(md)
issues.append((text, status))
if status == 'pass':
    score += 1
```

**效果**:
| Skill | 语言 | 清单 | 图标 | 表格 | 信号 | 旧结果 | 新结果 |
|-------|------|------|------|------|------|--------|--------|
| find-skills | EN/ZH | 3 | 5 | 0 | 13 | ❌→✅ * | ✅ pass |
| skill-vetter | EN | 14 | 2 | 1 | 21 | ❌ 未检测到 | ✅ pass |
| ppt-generator | ZH | 2 | 2 | 1 | 11 | ✅ pass | ✅ pass |

*注：经过 P1-2 补英文修复后已是 pass

### 改动 2: `_prohibition_signal()` — 替代禁止操作检查

**位置**: `halucatch_core.py` → `check_guardrails()` 第 295 行

**旧代码**:
```python
if re.search(r'(不要|不能|禁止|切勿) ', md):
```

**新代码**:
```python
def _prohibition_signal(md):
    """跨语言禁止/护栏声明信号：否定词 + 大写警告词 + CRITICAL/REJECT 标志。"""
    negations = len(re.findall(
        r'\b(?:never|not|no|don\'?t|REJECT|DENY|BLOCK|SHALL\s+NOT)\b',
        md, re.IGNORECASE
    ))
    caps_warnings = len(re.findall(
        r'[A-Z]{5,}', md
    ))  # 大写警告词（REJECT、CRITICAL、MANDATORY 等）
    zh_prohibition = len(re.findall(
        r'(不要|不能|禁止|切勿|严禁)',
        md
    ))
    red_flags = len(re.findall(
        r'RED\s+FLAG|🚨|⛔',
        md, re.IGNORECASE
    ))

    signal = negations * 2 + caps_warnings + zh_prohibition * 2 + red_flags * 3
    if signal >= 3:
        return ('pass', f'✅ 检测到禁止/护栏声明（否定词 {negations} / 中文禁止 {zh_prohibition}）')
    else:
        return ('warn', '🟡 未检测到明确的禁止操作声明')

# 在 check_guardrails 中替换原有逻辑:
status, text = _prohibition_signal(md)
if status == 'pass':
    issues.append((text, 'pass'))
    score += 1
else:
    issues.append((text, 'warn'))
```

**效果**:
| Skill | 语言 | 否定词 | 大写词 | 中文禁词 | 信号 | 旧结果 | 新结果 |
|-------|------|--------|--------|---------|------|--------|--------|
| skill-vetter | EN | 3 | 4 | 0 | 13 | ❌ 未检测到 | ✅ pass |
| find-skills | EN/ZH | 1 | 0 | 0 | 2 | ❌ | 🟡 仍 warn（确实没写）|
| ppt-generator | ZH | 0 | 0 | 1 | 2 | 🟡 info | 🟡 仍 warn（边缘） |

### 改动 3：方法论评估统一加 AI 免责

**位置**: `halucatch_core.py` → `check_methodology()` 返回值

在返回前追加一行：
```python
issues.append(('📝 以上为结构信号基线，语义判断（分支是否完备、逻辑是否正确）请由 AI 补充', 'info'))
```

替代当前的单个检查项维度末尾追加模式，统一说明脚本的定位。

---

## 影响面分析

| 改动 | 位置 | 影响 | 风险 |
|------|------|------|------|
| 新增 `_branch_density()` | check_methodology | 替换 1 个检查项 | 低，纯增量函数 |
| 新增 `_prohibition_signal()` | check_guardrails | 替换 1 个检查项 | 低，纯增量函数 |
| AI 免责声明 | 方法论返回 | 追加 1 行 | 零风险 |

现有测试（`test_methodology_complete` / `test_methodology_minimal` / `test_guardrails_weak` / `test_guardrails_strong`）需更新预期值——测试用例中的 md 内容需要加入足够的结构信号（清单行/图标）以匹配新的信号阈值。

---

## 设计原则

1. **脚本不下结论** — 只说「看起来有结构化的分支声明」，不说「分支处理正确」
2. **跨语言** — 清单、表格、图标、大写词，任何语言的 SKILL.md 都有这些
3. **可解释** — 输出附带信号来源（清单 X 项、图标 Y 个），比「未检测到关键字」可操作
