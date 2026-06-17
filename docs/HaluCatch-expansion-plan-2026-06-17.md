# HaluCatch 场景扩展计划

**日期**: 2026-06-17 | **来源**: V3 回归测试后规划

---

## 当前覆盖状态

| 场景 | 覆盖 | 标的 |
|------|------|------|
| 纯方法论型（无代码） | ✅ | find-skills |
| 数据驱动型（多 .py 子目录） | ✅ | xlsx (13 .py) |
| 数据驱动型（单 .py 子目录） | ✅ | skill-sharpener (audit_skill.py) |
| 嵌入式 Python（SKILL.md 内嵌代码） | ❌ | — |
| 带数据文件（.csv/.xlsx） | ❌ | — |
| 空文件夹 / 缺 SKILL.md / 极简 Skill | ❌ | — |
| 代码风险模式库（通用场景） | ❌ | 当前仅金融 pattern |

---

## 阶段 1：质量下限（异常/边界用例）

**目标**：验证 HaluCatch 在输入不完整时的行为是否正确

| 用例 | 输入 | 预期 |
|------|------|------|
| 空文件夹 | 新建空目录作为 target | `scan_folder` 返回 info，文件数 0，SKILL.md 为 None |
| 只有 SKILL.md | 仅含 SKILL.md 的目录 | 文件数 1，纯方法论型，方法论/护栏评估正常 |
| 缺 SKILL.md 但有 .py | 只有 .py 无 SKILL.md | 文件数 ≥1，数据驱动型，`check_rules` 报「🟡 无 SKILL.md」 |
| 嵌套多层的 .py | 至少 3 层子目录的 .py | `os.walk` 递归正确，`rel_path` 字段正确 |

**验证方式**：创建临时目录作为测试夹具，运行后清理。

---

## 阶段 2：嵌入式 Python 路径（`has_md_py`）

**目标**：验证 `classify_skill` 的 `has_md_py` 分支

**推荐标的**：`neodata-financial-search`（`~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/plugins/finance-data/skills/neodata-financial-search/`）

这是一个金融数据搜索 Skill，SKILL.md 长达数千行且包含多个 `\`\`\`python` 代码块。虽无独立 .py，但 `has_md_py` 应将其分类为数据驱动型，后续地基检查报「无固化 .py 脚本」。

**关注点**：
- 分类是否正确触发 `has_md_py` 分支
- 地基检查对「无独立 .py」的警告是否准确（非误报，该类 Skill 确实无骨架脚本）
- `py_content` 应为 `None`，代码风险扫描跳过

---

## 阶段 3：代码风险模式库扩展

**目标**：让 `check_code_risks` 对通用型 Skill 也有意义（当前 3 个标的全是「未检测到篡改点」）

### 新增通用 pattern

```python
patterns = [
    # === 现有：金融专用 ===
    ('异常处理', r'except\s*:\s*pass', '...'),
    ('浮点比较', r'(p_pool|p_val)\s*==\s*0', '...'),
    ('统计函数', r'(math\.exp|scipy\.stats)', '...'),
    ('硬编码阈值', r'skiprows\s*=\s*\d', '...'),
    ('除零风险', r'/\s*store_weeks', '...'),

    # === 新增：通用安全 ===
    ('shell注入', r'os\.system\(|subprocess\.call\(.*shell\s*=\s*True', '直接执行系统命令'),
    ('路径拼接', r'[\'\"\w]+\s*\+\s*[\'\"\/]|[\'\"\/]\s*\+\s*[\'\"\w]+', '字符串拼接路径，建议用 os.path.join'),
    ('静默覆盖', r'open\([^)]*,\s*[\'\"]w[\'\"]', '写模式打开文件未警告覆盖'),
    ('超时缺失', r'requests\.(get|post|put|delete)\([^)]*\)(?!.*timeout)', 'HTTP 请求未设置超时'),
]
```

### 验证方式

用现有代码风险测试用例扩展覆盖，确认新 pattern 不产生误报（false positive）。

---

## 优先级与排期

| 阶段 | 优先级 | 估计改动量 | 依赖 |
|------|--------|-----------|------|
| 1 质量下限 | 🟡 中 | 测试用例 + 潜在 0~2 处修复 | 无 |
| 2 嵌入式 Python | 🟢 低 | 仅测试，预期零改动 | 无 |
| 3 模式库扩展 | 🟢 低 | `check_code_risks` 新增 4 pattern + 测试更新 | 无 |

三项独立，可并行执行。
