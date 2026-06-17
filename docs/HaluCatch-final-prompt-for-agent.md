# HaluCatch 发布前最终修改 Prompt

将此 prompt 发给开发 agent，完成所有修改后由测试 agent 验收。

---

## 任务 A：SKILL.md 前页补中英双语 tags

**文件**: `SKILL.md`

把第 10-13 行的 tags 替换为：

```yaml
tags:
  - "工程质量"
  - "engineering-assurance"
  - "Skill审查"
  - "skill-audit"
  - "可靠性"
  - "reliability"
```

## 任务 B：README 竞品对比表

**文件**: `README.md`

将第 144-152 行的「同类项目对比」章节（跟 CodeQL / ESLint 的对比）替换为：

```markdown
## 同类项目对比

Skill 审查赛道目前仅四个工具，各自切不同的角度：

| | HaluCatch | skill-vetter | SkillGuard | skill-sharpener |
|---|---|---|---|---|
| 切面 | **执行可靠性（工程）** | 安全审查（红队） | 全生命周期守护 | 文案质量（最佳实践） |
| 检查什么 | 数据管线/代码风险/业务规则/解读护栏 | 恶意行为/权限范围/源可信度 | 安装前审查+发布前安检+安装后体检 | 触发描述/结构/简洁度 |
| 评估方式 | 脚本基线 + AI 语义 | 纯 AI 按协议逐项检查 | AI + 规则引擎 | 纯 AI 按 checklist 打分 |
| 输出 | 三版报告 + 修复方案 + 闭环 | SAFE/CAUTION/REJECT 判定 | 风险报告 + 自动修复 | 优化建议报告 |
| 通用性 | ✅ 中/英/日/表格均适用 | ✅ 英文为主 | ✅ 中英文 | 🟡 依赖 AI 理解能力 |
| 闭环 | ✅ 行动版含修复指引 + feedback | ❌ | ✅ 含自动修复 | ❌ |
| skills.sh | — | **19.6K**（唯一上榜） | ❌ 未上榜 | ❌ 未上榜 |
| 平台评分 | — | ★3.690 (clawhub) | v4.2.0 (skillhub) | ★3.607 (clawhub) |

**HaluCatch 的独特优势**：
1. **唯一有骨架脚本的工具** — `halucatch_core.py` 提供可复现的基线检查，不依赖 AI 主观判断
2. **唯一含修复闭环** — 三版报告 + Phase 4 修复决策 + feedback.md 模板，形成「发现→修复→验证」完整链路
3. **唯一跨语言** — 结构信号（清单/图标/表格/否定词密度）替代语义关键词，不绑定特定语言
4. **唯一分层护栏** — 按 Skill 类型（分析型/工具库型/方法论）自动调整检查范围，避免误报
5. **赛道蓝海** — skills.sh 前 287 名中，Skill 审查工具仅 skill-vetter 上榜（19.6K），执行可靠性方向尚无竞品
```

## 任务 C：README 内容修复（5 处）

| # | 位置 | 改什么 |
|---|------|--------|
| 1 | 第 17 行 | 「从这三维度」→「从地基/代码/规则/护栏四维度」 |
| 2 | 第 137 行 | 代码风险描述「浮点/异常/p-value」→「路径拼接/静默覆盖/超时缺失/除零等」 |
| 3 | 第 62-68 行 | 用例 1 的 `skiprows 固定为 6` → `字符串拼接路径、写入模式未警告覆盖、除法未保护` |
| 4 | 第 48 行 | 删除重复的 `## 用法` 行（与「## 快速开始」重复） |
| 5 | 第 116-127 行 | 文件结构图补全 `docs/` 下现有文件 + `tests/test_halucatch.py` 改为「21 个单元测试」 |

## 任务 D：README 「快速开始」重写

**位置**: 替换第 52-99 行

```markdown
## 快速开始

### 对话中调用（推荐）

对 AI 说出目标 Skill 路径，AI 自动跑脚本、做评估、出报告：

```
请用 HaluCatch 审查这个 Skill：/path/to/target-skill
```

审查完成后，当前目录 `reports/` 下生成三份报告：

```
reports/
├── HaluCatch-report-YYYY-MM-DD.md           ← 专业版（工程人员）
├── HaluCatch-report-YYYY-MM-DD-通俗版.md      ← 通俗版（业务方）
└── HaluCatch-report-YYYY-MM-DD-行动版.md      ← 修复指引（含反馈模板）
```

**示例 — 审查一个代码工程型 Skill：**

```
请用 HaluCatch 审查 ~/.workbuddy/skills/xlsx，看这个操作表格的 Skill 稳不稳
```
→ 发现：字符串拼接路径、写入模式未警告覆盖、除法未保护。评级：地基 🟢 稳固，代码 🟠 有风险，护栏 🟡 缺项。

**示例 — 审查一个纯方法论型 Skill：**

```
请用 HaluCatch 审查 ~/.workbuddy/skills/apple-style-ppt-generator，看指令够不够清楚
```
→ 发现：结构化步骤完整、条件分支信号良好。评级：方法论 🟢 可靠，护栏 🟢 到位。

审查完成后 AI 会询问是否按方案修复，支持「执行 / 不执行 / 我有更好建议」三选一闭环。
```

## 任务 E：README 补充

**A. 四维评估框架下方**（第 141 行后）追加：

```markdown
> **分层策略**: 代码工程型 Skill 细分为「分析型」（查全 8 项护栏）和「工具库型」（精简 5 项），
> 纯方法论型精简 5 项。避免对工具库 Skill 检查不必要的「数据时效性/来源」项。
```

**B. 「开发」章节**中，将原 `python3 halucatch_core.py` 调用示例改为「引擎调试」小节：

```markdown
### 引擎调试

`halucatch_core.py` 是底层引擎，直接调用用于调试：

```bash
python3 halucatch_core.py --skill-dir /path/to/skill          # 完整评估
python3 halucatch_core.py --skill-dir /path/to/skill --validate # 仅扫描
```

> 日常使用通过 AI Skill 调用即可，无需手动跑脚本。
```

**C. 「开发」章节后追加「## 测试」**:

```markdown
## 测试

```bash
pytest tests/ -v    # 21 个用例全部通过
```

已对 10 个不同类型 Skill 完成实战验证：纯方法论型 5 个、代码工程型 4 个（含工具库/分析型）、自审查 1 个。
```

---

## 验收标准

修改完成后，确保：
1. `grep "三维度" README.md` 返回空（已改为四维度）
2. `grep "CodeQL" README.md` 返回空（旧竞品表已替换）
3. `grep "方式二" README.md` 返回空（已移入开发章节）
4. `grep "tag" SKILL.md` 返回 7 行（6 个 tag + 1 行 `tags:`）
5. 竞品对比表出现 skill-vetter / SkillGuard / skill-sharpener 三个名称
