# HaluCatch / 捕幻

AI Skill **执行可靠性审查**工具。评估一个 Skill 被 AI 执行时，结果是否可信、是否可复现、是否经得起业务推敲。

> **Halu** = Hallucination（幻觉） | **Catch** = 捕获

---

## 动机

AI 执行 Skill 时，最常见的问题不是「不会做」，而是**以为自己会做但做错了**。原因有三：

1. **地基不稳** — 数据路径写死、格式未验证、没有骨架脚本
2. **规则歧义** — 自然语言描述的业务逻辑能被多种理解
3. **缺解读护栏** — AI 产出自信的错误结论，用户无从分辨

HaluCatch 扫描一个 Skill 包，从这三维度给出评级与修复建议。

---

## 用法

### 作为 AI Skill 使用

向 AI 提供目标 Skill 文件夹路径：

```
请用 HaluCatch 审查这个 Skill：/path/to/target-skill
```

HaluCatch 将输出三份报告：

| 版本 | 受众 | 内容 |
|------|------|------|
| 专业版 | 数据分析师/工程人员 | 结构化审查发现、风险矩阵、行动清单 |
| 通俗版 | 业务方/非技术人员 | 白话 paraphrase，无术语 |
| AI 行动版 | 下次执行的 AI | 修复指引 + feedback 模板 |

### 直接运行骨架脚本

```bash
python3 halucatch_core.py --skill-dir "/path/to/target-skill" [--validate]
```

`--validate` 模式仅检查文件完整性，不执行评估。

---

## 文件结构

```
HaluCatch/
├── SKILL.md              ← 流程指令（AI 读）
├── halucatch_core.py     ← 骨架脚本（标准化评估 + --validate）
├── README.md             ← 项目说明
└── .gitignore
```

---

## 四维评估框架

| 维度 | 检查什么 | 类型 |
|------|---------|------|
| 🏗️ **地基** | 数据管线是否稳固（.py/路径/validate） | 代码化扫描 |
| 🤖 **代码** | AI 复现篡改点（浮点/异常/p-value） | 代码化扫描 |
| 📝 **规则** | 业务口径有无歧义（映射/分类/边界） | AI 判断 |
| 🛡️ **护栏** | 解读规则是否到位（禁令/框架/自检） | AI 判断 |

前三项可靠，第四项需要目标 Skill 作者自觉配合。

---

## 同类项目对比

| | HaluCatch | CodeQL | ESLint |
|---|---|---|---|
| 审查对象 | AI Skill（markdown + python） | 源代码 | JavaScript |
| 检查范围 | 执行可靠性 + 业务规则 | 安全漏洞 | 代码规范 |
| 输出 | 三版报告 + 修复建议 | 告警列表 | 错误/警告 |
| 闭环 | ✅ 含修复指南 | ❌ 仅标记 | ❌ 仅标记 |

---

## 开发

```bash
git clone https://github.com/CoderMoray/HaluCatch.git
cd HaluCatch
# 编辑 SKILL.md 或 halucatch_core.py
git commit -m "your change"
git push
```

---

## 许可

MIT
