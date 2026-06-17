# HaluCatch 优化报告

**日期**: 2026-06-17 | **来源**: V2 回归测试 | **状态**: 建议优化，非阻塞

---

## 背景

V2 修复后，P0+P1 全部通过（6/6 用例）。以下 3 项为基于测试观察提出的优化建议，不涉及功能正确性。

---

## 优化项 1：代码行数统计改用最大单文件行数

### 位置

`halucatch_core.py` → `check_code_risks()` 第 195 行

### 现状

```python
lines = len(info['py'].splitlines())
```

`scan_folder()` 将多个 .py 文件拼接为单一字符串 `'\n'.join(py_contents)`，导致行数是所有文件的**总和**。xlsx 插件（13 个 .py）被报告「嵌入代码 3007 行」，但单个文件最大不过 500 余行，不存在「AI 复现遗漏」风险。

### 建议

在 `scan_folder()` 返回值中增加 `max_py_lines` 字段（取各 .py 文件的最大行数），`check_code_risks()` 使用该字段而非全量拼接后的行数。同时保留文件个数信息辅助判断。

### 预期效果

xlsx 插件从「嵌入代码 3007 行」修正为类似「嵌入代码 13 个 .py 文件，最大单文件 512 行」。

---

## 优化项 2：护栏检查按 Skill 类型分层

### 位置

`halucatch_core.py` → `check_guardrails()` 第 276-353 行

### 现状

所有 Skill 类型使用同一套 8 项护栏检查模板。两轮测试中：
- 方法论型 Skill（find-skills）护栏 = 🔴 薄弱 2/8
- 数据驱动型 Skill（xlsx）护栏 = 🔴 薄弱 2/8

对于 find-skills（技能搜索工具），检查「数据来源限制」「数据时效性约束」无实际意义——它不处理数据，只是搜索市集并返回结果。这些误报警降低了护栏维度的区分度。

### 建议

在 `check_guardrails(info, skill_type)` 增加 `skill_type` 参数，按类型分两层：

**数据驱动型（全 8 项）**：
1. 输出格式 | 2. 禁令 | 3. 自检 | 4. 置信度 | 5. 数据来源 | 6. 错误回退 | 7. 时效性 | 8. 前提假设

**纯方法论型（精简 5 项）**：
1. 输出格式 | 2. 禁令 | 3. 自检 | 4. 错误回退 | 5. 前提假设

移除对方法论型无意义的 3 项：置信度（通常不适用）、数据来源限制、时效性约束。

### 预期效果

方法论型 Skill 的护栏评分更合理，不至于全部沦陷在「不适用但被扣分」的检查项上。

---

## 优化项 3：自洽检查改用完整相对路径匹配

### 位置

`halucatch_core.py` → `check_methodology()` 第 397-407 行

### 现状

```python
existing_names = {f['name'] for f in info.get('files', [])}
missing = [m for m in mentioned_files if os.path.basename(m) not in existing_names ...]
```

这里只用 `f['name']`（basename）做存在性判断。如果 SKILL.md 引用 `scripts/audit_skill.py`，实际只检查文件夹里有没有任何名为 `audit_skill.py` 的文件。两个不同子目录有同名文件时会误判为通过。

### 建议

改为用完整相对路径精确匹配。在 `scan_folder()` 中为每个文件记录 `rel_path`（相对于 Skill 根目录的路径），自洽检查时用 `rel_path` 做精确比对。

```python
# scan_folder 中增加
fpath_rel = os.path.relpath(fpath, path)
files.append({..., 'rel_path': fpath_rel})
```

### 预期效果

消除同名文件在不同子目录的歧义风险。对绝大多数只有一个 scripts/ 目录的 Skill 无影响，但提升了极端情况下的准确性。

---

## 优先级排序

| 优先级 | 优化项 | 改动量 | 影响面 |
|--------|--------|--------|--------|
| 🟡 中 | #1 行数统计 | 2 处（scan_folder + check_code_risks） | 数据驱动型 Skill 评估准确性 |
| 🟢 低 | #2 护栏分层 | 1 处（check_guardrails 加参数） | 方法论型 Skill 的护栏可读性 |
| 🟢 低 | #3 路径匹配 | 2 处（scan_folder + check_methodology） | 极端情况的边界防护 |

**建议实施顺序**: 1 → 2 → 3。三项均可独立修改，互不依赖。
