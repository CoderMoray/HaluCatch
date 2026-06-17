# Skill 测试报告 — HaluCatch（捕幻）

**日期**: 2026-06-17
**测试人**: 秦测 (Skill 测试专家)
**测试用例数**: 15 | **通过**: 9 | **失败**: 6

---

## 测试概况

对 HaluCatch（AI Skill 执行可靠性审查工具）进行三轮实战测试，分别审查不同类型的目标 Skill，验证其分类准确性、四维评估质量、以及自身执行稳定性。

| 轮次 | 目标 Skill | 类型 | 核心验证点 |
|------|-----------|------|-----------|
| 1 | find-skills | 纯方法论型 | 分类、方法论评估、报告生成 |
| 2 | xlsx | 数据驱动型 | 四维全覆盖、脚本基线、递归扫描 |
| 3 | skill-sharpener | 混合型（同类竞品） | 同类审查质量、类比对判断 |

---

## 测试环境

- **HaluCatch 版本**: `halucatch_core.py` (当前 workspace)
- **Python**: 3.13.12 (managed)
- **运行方式**: `python3 halucatch_core.py --skill-dir <path> --output-dir <path>`

---

## 测试结果卡片

| # | 维度 | 用例 | 预期 | 实际 | 状态 |
|---|------|------|------|------|------|
| 1 | 功能 | Round1: find-skills 分类 | 正确分类为「纯方法论型」 | ✅ 分类正确 | ✅ |
| 2 | 功能 | Round1: 报告生成（3版） | 生成专业版/通俗版/AI行动版 | ✅ 3份报告均成功生成 | ✅ |
| 3 | 功能 | Round1: --validate 模式 | 仅扫描不评估 | ✅ 仅输出文件清单 | ✅ |
| 4 | 功能 | Round2: xlsx 分类 | 正确分类为「数据驱动型」 | ✅ 分类正确 | ✅ |
| 5 | 功能 | Round2: 四维评估 | 地基/代码/规则/护栏全覆盖 | ✅ 四维均输出 | ✅ |
| 6 | 功能 | Round2: 报告生成 | 三版报告全部落盘 | ✅ 成功 | ✅ |
| 7 | 功能 | Round3: skill-sharpener 审查 | 正常执行、生成报告 | ✅ 成功 | ✅ |
| 8 | 功能 | Round3: --validate 模式 | 正常执行 | ✅ 成功 | ✅ |
| 9 | **边界** | Round2: xlsx 子目录 .py 发现 | 应发现 13 个 scripts/ 子目录 .py 文件 | ❌ 仅扫描到 2 个顶层文件 | ❌ |
| 10 | **边界** | Round2: 地基检查准确性 | 应报告「有 .py 脚本」 | ❌ 报告「🔴 无固化 .py 脚本」 | ❌ |
| 11 | **边界** | Round3: skill-sharpener 分类 | 应分类为「数据驱动型」（有 audit_skill.py） | ❌ 错误分类为「纯方法论型」 | ❌ |
| 12 | **一致性** | Round1: find-skills 异常分支检测 | 应检测到「If no relevant skills exist」分支 | ❌ 报告「未检测到异常分支处理」 | ❌ |
| 13 | **一致性** | Round3: skill-sharpener 结构化步骤 | 应检测到「第一步/第二步/.../第五步」 | ❌ 报告「缺少结构化步骤描述」 | ❌ |
| 14 | **一致性** | find-skills 输出格式定义 | 应检测到「Respond immediately with results」等 | ❌ 报告「未明确定义输出格式」 | ❌ |
| 15 | 异常 | 不存在路径的 Skill | 应报错退出 | ✅ 「❌ 路径不存在」 | ✅ |

---

## 问题汇总

### 🔴 P0 — 阻塞性问题

**#1 — `scan_folder()` 不递归扫描子目录**

`halucatch_core.py` 第 32 行使用 `os.listdir(path)` 仅扫描顶层文件，导致所有子目录下的 `.py` 文件完全不可见。

- **影响范围**: 任何含 `scripts/` 或嵌套子目录的 Skill 都会被错误评估
- **实测案例 1**: xlsx 插件有 13 个 `.py` 文件在 `scripts/office/` 子目录（`pack.py`, `validate.py`, `unpack.py`, `recalc.py` 等），HaluCatch 报告「🔴 无固化 .py 脚本」
- **实测案例 2**: skill-sharpener 有 `scripts/audit_skill.py`，HaluCatch 将其错误分类为「纯方法论型」

**建议修复**:
```python
# 将 scan_folder() 中的 os.listdir() 改为 os.walk()
for root, dirs, filenames in os.walk(path):
    for fname in filenames:
        fpath = os.path.join(root, fname)
        ...
```

---

### 🟠 P1 — 功能缺陷（正则匹配不准确）

**#2 — `_check_exception_handling()` 仅匹配中文条件句**

第 369 行：`r'(如果|若|当|如果.*不|except)'` 不匹配英文 "if"、"when"、"in case" 等。find-skills 的 SKILL.md 用英文写了 `If no relevant skills exist`，但未被检测到。

**建议修复**: 在正则中添加 `if\s|when\s|in\s+case`

**#3 — `_check_output_format()` 匹配面过窄**

第 376 行：`r'(输出|产出|结果|report|生成)'` — find-skills SKILL.md 使用 `Respond immediately with the results` 和结构化示例，但不含这些关键词。

**建议修复**: 改为检测 `code block` 出现频率 → 如果 SKILL.md 中有 ≥2 个 fenced code block，则视为有输出格式定义。

**#4 — `_check_structured_steps()` 不识别「第X步」**

第 362 行：`r'(步骤|Step|##\s+\d)'` — skill-sharpener 使用「第一步/第二步/.../第五步」格式，正则未覆盖。

**建议修复**: 添加 `第[一二三四五六七八九十\d+]+步`

---

### 🟡 P2 — 设计改进建议

**#5 — 护栏评估对方法论型 Skill 过于刚性**

对于 find-skills（技能搜索工具），检查「数据来源限制」「数据时效性约束」「前提假设」意义不大。HaluCatch 对所有 Skill 类型使用同一套护栏检查模板，导致大量本不需要应用的检查项产生误报。

**建议**: 根据 Skill 类型（数据驱动/方法论）分层护栏规则——方法论型 Skill 侧重输出约束和边界定义，数据驱动型 Skill 侧重数据来源和时效性。

**#6 — 通俗版报告信息密度过低**

通俗版仅列出问题清单，没有语境解释（例如：「未检测到异常分支处理」对业务方来说不可操作）。

**建议**: 通俗版每个问题附带一句话的通俗解释（如：「这意味着在意外情况下，AI 不知道该怎么处理，可能会给出错误结果」）。

---

## 总体评级

| 维度 | 评级 | 说明 |
|------|------|------|
| 功能正确性 | 🟡 | 核心流程（分类→评估→报告）跑得通，但 P0 子目录扫描缺陷严重影响数据驱动型 Skill 的评估准确性 |
| 边界健壮性 | 🔴 | 子目录递归扫描缺失是硬伤——现代 Skill 几乎都有 `scripts/` 子目录结构 |
| 输出一致性 | 🟡 | 三版报告格式一致、都正常落盘，但正则匹配存在多处误判 |
| 护栏有效性 | 🟢 | HaluCatch 自身护栏设计良好：路径校验、自检输出、--validate 安全模式都有效 |

---

## 附录：各轮次详细输出

### Round 1 — find-skills
```
分类: 纯方法论型 ✅
文件数: 3
方法论: 2/5 (结构+示例通过，异常/输出格式误判)
护栏: 2/8 (薄弱)
```

### Round 2 — xlsx ⚠️
```
分类: 数据驱动型 ✅
文件数: 2 (实际有 13 个 .py 在子目录，未计入) ❌
地基: 1/6 (🔴 无地基) —— 误报，实际有 13 个 .py
代码: 🟡 无嵌入式代码 —— 误报
规则: 3/6 (有歧义)
护栏: 2/8 (薄弱)
```

### Round 3 — skill-sharpener ⚠️
```
分类: 纯方法论型 —— 误报，实际有 audit_skill.py
文件数: 3 (scripts/ 子目录未扫描)
方法论: 4/5 (结构化步骤误判)
护栏: 3/8 (薄弱)
```

---

> 本报告基于 HaluCatch v1.0 当前版本。最致命的问题是 `scan_folder()` 的非递归设计——修复后可消除 #9~#11 三个失败用例。
