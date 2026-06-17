# HaluCatch 实战测试 Prompt

在新会话中选择「Skill 测试官」专家后，粘贴以下内容：

---

我要你测试这个 Skill：/Users/chrismoray/Desktop/Moray/MyOpenSource/HaluCatch

它的核心功能是「审查其他 Skill 的可信度」——扫描一个 Skill 文件夹，从地基/代码/规则/护栏四个维度评估，输出三版报告（专业版/通俗版/AI 行动版）。

帮我按以下顺序执行三轮测试：

## 第一轮：热身 — 测试 find-skills
- 目标路径：~/.workbuddy/skills/find-skills
- 类型：纯方法论型
- 目的：验证 HaluCatch 能正确分类、执行方法论评估、生成报告

## 第二轮：重头戏 — 测试 xlsx
- 目标路径：~/.workbuddy/plugins/marketplaces/codebuddy-plugins-official/plugins/xlsx
- 类型：数据驱动型（含 .py 和数据处理逻辑）
- 目的：验证四维全覆盖（地基/代码/规则/护栏），重点看脚本基线检查是否靠谱

## 第三轮：对比 — 测试 skill-sharpener
- 先安装：`skillhub install skill-sharpener`
- 类型：和 HaluCatch 同类的 skill 审查工具
- 目的：看 HaluCatch 审查同类竞品时的输出质量

## 每轮交付物
1. 该标的的测试报告
2. HaluCatch 自身的任何执行异常（如果有的话）
