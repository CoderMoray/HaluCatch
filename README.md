# HaluCatch / 捕幻

<p align="center">
  <a href="README.md">
    <img src="https://img.shields.io/badge/语言-中文-blue?style=for-the-badge" alt="中文">
  </a>
  <a href="README.en.md">
    <img src="https://img.shields.io/badge/Language-English-slategray?style=for-the-badge" alt="English">
  </a>
</p>

AI Skill **执行可靠性审查**工具。评估一个 Skill 被 AI 执行时，结果是否可信、是否可复现、是否经得起业务推敲。

> **Halu** = Hallucination（幻觉） | **Catch** = 捕获

---

## 动机

AI 执行 Skill 时，最常见的问题不是「不会做」，而是**以为自己会做但做错了**。原因有三：

1. **地基不稳** — 数据路径写死、格式未验证、没有骨架脚本
2. **规则歧义** — 自然语言描述的业务逻辑能被多种理解
3. **缺解读护栏** — AI 产出自信的错误结论，用户无从分辨

HaluCatch 扫描一个 Skill 包，从地基/代码/规则/护栏四维度给出评级与修复建议。

---

## 执行流程

```mermaid
flowchart TD
  A["用户调用 HaluCatch"] --> B{"目标路径存在?"}
  B -->|否| C["报错退出"]
  B -->|是| D{"执行模式?"}
  D -->|validate| E["L1: --validate 脚本扫描"]
  E --> F["文件清单 → 结束"]
  D -->|标准审查| G["L1: 获取文件清单"]
  G --> H{"Phase 0: 技能分类"}
  H -->|代码工程型| I["L2: 四维评估<br/>(地基/代码/规则/护栏)"]
  H -->|纯方法论型| J["L2: 方法论+护栏评估"]
  H -->|不确定| K["询问用户"]
  K --> H
  I --> N["Phase 3: 三版报告 → 落盘"]
  J --> N
  N --> O{"Phase 4: 用户要修复?"}
  O -->|修| P["生成修复方案"]
  O -->|不修| Q["结束"]
  P --> R{"用户选择?"}
  R -->|执行| S["用户让 AI 应用修复"]
  R -->|不执行| Q
  R -->|建议| P
  S -.->|重新审查| A
```

> 详细决策分支见 [在线流程图](https://codermoray.github.io/HaluCatch/decision-flowchart.html)。

---

## 快速开始

两种调用方式，底层同一套引擎：

### 对话中调用（推荐）

对 AI 说出目标 Skill 路径即可，AI 自动跑脚本、做评估、出报告：

```
请用 HaluCatch 审查这个 Skill：/path/to/target-skill
```

审查完成后，当前目录 `reports/` 下生成三份报告：

```
reports/
├── HaluCatch-report-2026-06-17.md           ← 专业版（工程人员）
├── HaluCatch-report-2026-06-17-通俗版.md      ← 通俗版（业务方）
└── HaluCatch-report-2026-06-17-行动版.md      ← 修复指引（含反馈模板）
```

| 版本 | 目标读者 | 内容 |
|------|---------|------|
| 专业版 | 工程人员 | 逐项检查结果 + 分数 + 修复建议 |
| 通俗版 | 业务方 | 白话 paraphrase，无术语 |
| 行动版 | 下次执行的 AI | 修复指引 + feedback 模板 |

**示例 — 审查一个代码工程型 Skill：**

```
请用 HaluCatch 审查 ~/.workbuddy/skills/xlsx，看这个操作表格的 Skill 稳不稳
```
→ 发现：字符串拼接路径、写入模式未警告覆盖、除法未保护。评级：地基 🟢 稳固，代码 🟠 有风险，护栏 🟡 缺项。

**示例 — 审查一个纯方法论型 Skill：**

```
请用 HaluCatch 审查 ~/.workbuddy/skills/find-skills，看指令够不够清楚
```
→ 发现：结构化步骤完整、条件分支信号良好（清单 13 项/图标 7）。评级：方法论 🟢 可靠，护栏 🟡 缺项 3/5。

> `find-skills` 是 Skill 生态中的搜索工具，详见 [vercel-labs/skills](https://github.com/vercel-labs/skills)。

审查完成后 AI 会询问是否按方案修复，详见 [在线流程图](https://codermoray.github.io/HaluCatch/decision-flowchart.html)。

---

## 文件结构

```
HaluCatch/
├── SKILL.md                  ← 流程指令（AI 读）
├── halucatch_core.py         ← 骨架脚本（标准化评估 + --validate）
├── README.md                 ← 项目说明（含 Mermaid 流程图）
├── docs/
│   ├── decision-flowchart.html              ← 决策流程图（本地渲染）
│   ├── decision-flowchart-prompt.md         ← 流程图生成指令
│   ├── test-prompt.md                       ← 测试计划
│   ├── HaluCatch-v6-to-v7-plan-2026-06-17.md
│   └── HaluCatch-readme-v7-update-2026-06-17.md
├── tests/
│   ├── __init__.py
│   └── test_halucatch.py     ← 21 个单元测试（6 函数 + 4 边界 + 1 分层）
└── .gitignore
```

---

## 四维评估框架

| 维度 | 检查什么 | 类型 |
|------|---------|------|
| 🏗️ **地基** | 数据管线是否稳固（.py/路径/validate） | 代码化扫描 |
| 🤖 **代码** | 代码质量风险（路径拼接/静默覆盖/超时缺失/除零等） | 代码化扫描 |
| 📝 **规则** | 业务口径有无歧义（映射/分类/边界） | AI 判断 |
| 🛡️ **护栏** | 解读规则是否到位（禁令/框架/自检） | AI 判断 |

前三项可靠，第四项需要目标 Skill 作者自觉配合。

> **跨语言设计**: 方法论和护栏检查不使用关键词正则，而是通过结构信号密度
> （条件清单行数、警示图标数、表格数、否定词密度）跨语言评估分支覆盖和护栏完整度。
> 中文「如果…则…」和英文「REJECT IMMEDIATELY IF」都能正确识别。

> **分层策略**: 代码工程型 Skill 细分为三档——分析型（全 8 项护栏，含数据来源/时效性/置信度）、工具库型（精简 5 项）、纯方法论型（精简 5 项）。避免对 xlsx/pptx 等工具库 Skill 检查不必要的「数据时效性/来源」项。

---

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
| skills.sh | — | **19.6K** | ❌ 未上榜 | ❌ 未上榜 |
| 平台评分 | — | ★3.690 (clawhub) | v4.2.0 (skillhub) | ★3.607 (clawhub) |

**HaluCatch 的独特优势**：
1. **唯一有骨架脚本的工具** — `halucatch_core.py` 提供可复现的基线检查，不依赖 AI 主观判断
2. **唯一含修复闭环** — 三版报告 + Phase 4 修复决策 + feedback.md 模板，形成「发现→修复→验证」完整链路
3. **唯一跨语言** — 结构信号（清单/图标/表格/否定词密度）替代语义关键词，不绑定特定语言
4. **唯一分层护栏** — 按 Skill 类型（分析型/工具库型/方法论）自动调整检查范围，避免误报
5. **赛道蓝海** — skills.sh 前 287 名中，Skill 审查工具仅 skill-vetter 上榜（19.6K），执行可靠性方向尚无竞品

---

## 开发

```bash
git clone https://github.com/CoderMoray/HaluCatch.git
cd HaluCatch
# 编辑 SKILL.md 或 halucatch_core.py
git commit -m "your change"
git push
```

### 引擎调试

`halucatch_core.py` 是底层引擎，直接调用用于调试：

```bash
python3 halucatch_core.py --skill-dir /path/to/skill          # 完整评估
python3 halucatch_core.py --skill-dir /path/to/skill --validate # 仅扫描
```

> 日常使用通过 AI Skill 调用即可，无需手动跑脚本。

---

## 测试

```bash
pytest tests/ -v    # 21 个用例全部通过
```

已对 10 个不同类型 Skill 完成实战验证：

| Skill | 类型 | 护栏 |
|-------|------|------|
| find-skills / agent-browser / edgeone-deploy | 方法论 | 🟡 缺项 3/5 |
| xlsx / pptx | 工具库型 | 🟡 缺项 3/5 |
| skill-sharpener (ClawHub) | 分析型 | 🟡 缺项 5/8 |
| neodata-financial-search | 分析型 | 🟢 到位 7/8 |
| data-validation | 嵌入式 Python | 🟡 缺项 5/8 |
| HaluCatch (自审查) | 代码工程 | 🟡 缺项 5/8 |

---

## 常见问题

**Q: HaluCatch 需要联网吗？**
A: 不需要。全程离线运行，仅扫描本地文件夹中的 SKILL.md 和 .py 文件。

**Q: 我的 Skill 没有 .py 文件，能用吗？**
A: 可以。HaluCatch 会自动分类为「纯方法论型」并跳过地基/代码检查，只评估方法论和护栏。

**Q: 审查结果说「护栏薄弱」，怎么修？**
A: 看同目录下的 `-行动版.md` 报告，它包含具体修复方案和 feedback.md 模板。

**Q: 为什么工具库型 Skill 的护栏分数比分析型低？**
A: 护栏检查按类型分层——工具库型只查 5 项核心项（跳过不必要的数据来源/时效性检查），分母不同，分数不可直接比较。

**Q: 审查结果能自动修复吗？**
A: 不能。HaluCatch 是诊断工具，不是自动修复工具。行动版报告提供修复指引，但修改需要你（或 AI）手动执行。

**Q: 能一次审查多个 Skill 吗？**
A: 当前版本暂不支持批量模式。你可以逐个运行，批量功能已在 roadmap 中。

**Q: 出现「网络问题卡住」是 HaluCatch 的问题吗？**
A: 不是。HaluCatch 是纯本地工具，不走网络。如果执行卡住，大概率是 AI 对话环境超时或目标路径过大导致扫描耗时。

---

## 许可

MIT
