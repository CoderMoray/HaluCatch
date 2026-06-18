# HaluCatch TRACE 反馈分析与修复计划

**日期**: 2026-06-18 | **来源**: skillhub TRACE 报告

---

## 反馈逐条鉴别与处理

### 🟡 1. 异常提示不够操作化

**反馈**: 「提示不够清晰，遇到问题时不太容易知道怎么解决」

**判定**: 真实。`halucatch_core.py` 只在路径不存在时输出 `❌ 路径不存在`，报告里的 warn 项也只给类别标签（如「🟠 有 .py 但缺少输入验证」），没有 actionable 的下一步。

**修复**: `check_foundation` 和 `check_code_risks` 的 warn 项追加一句话指引：

| 现状 | 改为 |
|------|------|
| 🟠 有 .py 但缺少输入验证 | 🟠 有 .py 但缺少输入验证 → 建议在 `--validate` 模式下添加 `check_columns()` 预检 |
| 🟠 有 .py 但缺少 --validate 验证模式 | 🟠 有 .py 但缺少 --validate 验证模式 → 建议在 argparse 中添加 `--validate` 参数 |
| 🟡 未声明默认值策略 | 🟡 未声明默认值策略 → 建议在 SKILL.md 中声明 fallback 行为（如「缺省使用最近 30 天数据」） |

改动范围：3 处，纯文本追加，零风险。

---

### 🟡 2. 批量处理缺失

**反馈**: 「想批量处理多个 skill 时不太方便」

**判定**: 真实功能缺口。但竞品也都没有。建议列入 roadmap 而非本次修。

**未来方案**（本次不实现）:
```bash
python3 halucatch_core.py --batch /path/to/skills-dir
# 扫描目录下所有含 SKILL.md 的子目录，每个生成独立报告
```

---

### 🟢 3. 触发方式不直观

**判定**: 已在昨天的 README 重写方案中解决（「快速开始」改为单入口，说明对话调用是推荐方式）。

---

### 🟢 4. 反模式/FAQ 散落

**判定**: 真实问题。能力边界表在 SKILL.md、护栏说明在评估框架里、修复清单在行动版里——分布在三个地方。

**修复**: 在 README 末尾追加「## 常见问题」：

```markdown
## 常见问题

**Q: HaluCatch 需要联网吗？**
A: 不需要。全程离线运行，仅扫描本地文件夹中的 SKILL.md 和 .py 文件。

**Q: 我的 Skill 没有 .py 文件，能用吗？**
A: 可以。HaluCatch 会自动分类为「纯方法论型」并跳过地基/代码检查，只评估方法论和护栏。

**Q: 审查结果说「护栏薄弱」，怎么修？**
A: 看同目录下的 `-行动版.md` 报告，它包含具体修复方案和 feedback.md 模板。

**Q: 为什么工具库型 Skill 的护栏分数比分析型低？**
A: 护栏检查按类型分层——工具库型只查 5 项核心项（跳过不必要的数据来源/时效性检查），分母不同，分数不可直接比较。
```

---

### 🔴 5. 「网络问题可能会卡住」（误判）

**判定**: HaluCatch 是纯本地文件扫描，不发起任何网络请求。此反馈可能是用户对 AI 执行环境的误解。

**处理**: 已在 FAQ 第一条澄清「全程离线运行」，不修改代码。

---

### 🟡 6. 「检测手段比较常规」

**判定**: V7 的结构信号检测（清单密度/图标计数/否定词密度）是差异化创新，但文档没突出这一点。

**修复**: 在 README 「四维评估框架」表格下方，将现有描述改为：

```markdown
前三项可靠，第四项需要目标 Skill 作者自觉配合。

> **跨语言设计**: 方法论和护栏检查不使用关键词正则，而是通过结构信号密度
> （条件清单行数、警示图标数、表格数、否定词密度）跨语言评估分支覆盖和护栏完整度。
> 中文「如果…则…」和英文「REJECT IMMEDIATELY IF」都能正确识别。
```

---

## 修复清单

| # | 任务 | 文件 | 类型 |
|---|------|------|------|
| 1 | warn 项追加 actionable 指引 | `halucatch_core.py` | 代码 |
| 2 | 四维框架描述突出结构信号 | `README.md` | 文档 |
| 3 | 新增「常见问题」章节 | `README.md` | 文档 |
| 4 | 批量处理列入 roadmap | 本次不实现 | — |

---

## 关于 .github/workflows

**问题**: 是否必须上传 GitHub 才触发？会被上传到 skillhub/clawhub 吗？

**回答**:
- `release.yml`: 是的，`push tags v*` 触发 → 自动 lint + 构建 skillhub 包 + 创建 Release。必须在 GitHub 上推 tag 才执行。
- `sync-to-atomgit.yml`: 是的，`push main` 触发 → 自动同步到国内 AtomGit 仓库。
- **不会被上传到 skillhub/clawhub**: `release.yml` 第 31 行构建 skillhub zip 时只打包了 `SKILL.md halucatch_core.py README.md LICENSE docs/CHANGELOG.md`，不包含 `.github/`、`tests/`、`.workbuddy/`。Skill 包是干净的。
