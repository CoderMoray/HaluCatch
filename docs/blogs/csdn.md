# 【教程】如何检查你的 AI Skill 是否可靠？HaluCatch 使用指南

> 项目地址：https://github.com/CoderMoray/HaluCatch  
> 适用人群：AI 工具使用者、Skill 开发者、对 AI 输出质量有要求的数据/产品同学

---

## 前言：AI 执行的 Skill，你敢信吗？

现在很多人用 AI 助手（WorkBuddy、Claude、Cursor 等）来完成数据分析、文档处理、代码生成等任务。

这些 AI 助手有一个共同机制：**Skill**（技能包）——相当于给 AI 预置一套执行指令和工具脚本。

但问题来了：

> **AI 执行 Skill 的时候，会不会偷偷做错？**

答案是：**会。而且它不会告诉你。**

比如：
- 数据路径写死了，换个电脑就跑不通
- "活跃用户"的定义没写清楚，AI 按自己的理解算了一个，你没发现
- AI 在分析结果里写了"显著提升"，但其实统计上并不显著

这些问题，**运行不报错，结果看起来正常，但答案是错的。**

本文介绍一个工具——**HaluCatch**，专门用来检查 AI Skill 的执行可靠性。

---

## 一、HaluCatch 是什么？

**HaluCatch（捕幻）** 是一个 AI Skill 执行可靠性审查工具。

它的作用是：**评估一个 Skill 被 AI 执行时，结果是否可信、是否可复现。**

### 核心功能

- ✅ 扫描 Skill 包的全部文件
- ✅ 从四个维度评估可靠性
- ✅ 生成三版报告（专业版 / 通俗版 / 行动版）
- ✅ 可选：生成修复方案并验证

---

## 二、四维评估框架（核心原理）

> *[四维框架矩阵图](https://raw.githubusercontent.com/CoderMoray/HaluCatch/main/docs/blogs/assets/halucatch-4d-framework.png)*

HaluCatch 从一个核心问题出发：

> **AI 执行这个 Skill，会在哪些地方出错？**

它将答案归纳为四个维度：

| 维度 | 检查什么 | 为什么重要 |
|------|---------|-----------|
| 🏗️ **地基** | 数据管线是否稳固（路径是否硬编码、有无输入校验、依赖是否声明） | 地基不稳，AI 每次执行都可能出错 |
| 🤖 **代码** | 代码质量风险（路径拼接方式、是否有静默覆盖、除零保护等） | AI 复现代码时可能"好心办坏事"改错细节 |
| 📝 **规则** | 业务口径是否明确（定义是否固化，还是让 AI 自己猜） | 口径不固化 = 每次执行结果不一样 |
| 🛡️ **护栏** | 解读规则是否到位（有没有禁止 AI 说"因果结论"、有没有效应量框架） | 护栏缺失 = AI 会自信地输出错误解读 |

---

## 三、安装与使用

### 3.1 获取 HaluCatch

```bash
git clone https://github.com/CoderMoray/HaluCatch.git
cd HaluCatch
```

**零依赖**：HaluCatch 的核心包 `halucatch/` 只使用 Python 标准库，不需要安装任何第三方包。

### 3.2 方式一：在 AI 对话中使用（推荐）

如果你用的是 WorkBuddy 或支持 Skill 机制的 AI 助手，可以直接在对话里调用：

```
请用 HaluCatch 审查这个 Skill：~/.workbuddy/skills/xlsx
```

AI 会自动：
1. 运行扫描脚本
2. 做四维评估
3. 生成三版报告
4. 询问你是否要修复

### 3.3 方式二：命令行直接运行

```bash
# 审查一个 Skill（自动检测语言）
python3 halucatch_core.py --skill-dir /path/to/your-skill

# 强制中文输出
python3 halucatch_core.py --skill-dir /path/to/your-skill --lang zh-CN

# 仅扫描文件清单，不做评估
python3 halucatch_core.py --skill-dir /path/to/your-skill --validate
```

---

## 四、报告怎么看？

> *[三版报告对比图](https://raw.githubusercontent.com/CoderMoray/HaluCatch/main/docs/blogs/assets/halucatch-report-comparison.png)*

审查完成后，在 `reports/` 目录下生成三份报告：

```
reports/
├── HaluCatch-report-2025-06-17.md           ← 专业版（给开发者）
├── HaluCatch-report-2025-06-17-通俗版.md      ← 通俗版（给业务方）
└── HaluCatch-report-2025-06-17-行动版.md      ← 行动版（含修复方案）
```

### 通俗版示例（节选）

> **地基检查：🟢 稳固**  
> 这个 Skill 有固化的 Python 脚本，数据路径使用了参数化配置，输入有校验。地基没问题。
>
> **代码风险：🟠 有风险**  
> 发现脚本里有字符串拼接路径的操作（第 47 行），在 Windows 上可能出错。建议改为 `os.path.join()`。
>
> **护栏检查：🟡 缺项**  
> 这个 Skill 会让 AI 输出数据分析结论，但没有约束 AI 不能说"因果结论"。如果数据只是相关性，AI 可能会误读。

---

## 五、实战：审查一个真实 Skill

以 `xlsx` Skill（Excel 处理工具）为例：

**输入：**
```
请用 HaluCatch 审查 ~/.workbuddy/skills/xlsx
```

**HaluCatch 发现：**
- 🟢 地基稳固：有 `.py` 骨架脚本，路径参数化
- 🟠 代码风险：写入 Excel 时未警告覆盖（可能丢数据）
- 🟡 护栏缺项：未禁止 AI 修改单元格格式

**修复后重新审查**：护栏评分提升，风险项减少。

---

## 六、常见问题 FAQ

**Q：HaluCatch 需要联网吗？**  
A：不需要。全程离线运行，只扫描本地文件。

**Q：我的 Skill 没有 Python 代码，能用吗？**  
A：可以。HaluCatch 会自动分类为"纯方法论型"，跳过地基/代码检查，只评估指令清晰度和护栏。

**Q：审查结果能自动修复吗？**  
A：HaluCatch 是诊断工具，不是自动修复工具。它会给出修复方案，但需要你（或 AI）手动执行。

**Q：支持英文 Skill 吗？**  
A：支持。HaluCatch 会根据你的系统语言自动切换输出语言，也可以手动指定 `--lang en`。

---

## 七、项目资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/CoderMoray/HaluCatch |
| 在线流程图 | https://codermoray.github.io/HaluCatch/decision-flowchart.html |
| 问题反馈 | https://github.com/CoderMoray/HaluCatch/issues |

---

## 结语

AI Skill 让 AI 助手变得更强大，但**能力越大，出错的影响也越大**。

HaluCatch 不是要让 Skill 完美无缺，而是让**不可见的风险变得可见**。

如果你正在开发或使用 AI Skill，建议跑一次 HaluCatch 审查。你可能会发现一些意想不到的问题。

欢迎 Star / Fork / 提 Issue，一起完善 AI Skill 的质量基准。

---

*作者简介：Moray，数据开发团队 Leader，开源项目 HaluCatch 作者，关注 AI Agent 可靠性工程。*

*Tags: #AI #AIAgent #Skill开发 #Python教程 #开源工具 #数据分析*
