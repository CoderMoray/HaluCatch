# Skill 决策流程图生成 Prompt

把这个 prompt 发给 AI，它会读取你的 SKILL.md 后自动生成一个决策流程图。

---

## 任务

为我的 Skill 生成一个 **AI 执行决策流程图**（SVG 格式），展示 AI 调用该 Skill 后的完整决策分支——从用户触发到最终输出的每一条路径。

## 步骤

1. 先读取 `SKILL.md`，理解 Skill 的核心功能、输入类型、执行阶段、分支条件、输出方式
2. 分析并列出所有决策节点（如：分类判定 / 输入校验 / 模式选择 / 修复决策）
3. 生成一个 **680×720 的 SVG 流程图**，要求：
   - 从上到下布局，主流程走中轴，分支向两侧展开
   - 使用 5 种颜色区分节点角色：入口节点 / 决策菱形 / 脚本执行 / 输出节点 / 终止节点
   - 每个节点标注执行方（如 `[脚本]` / `[AI]` / `[Phase N]`）
   - 底部加颜色图例
   - 样式参考：圆角矩形、0.5px 描边、sans-serif 字体、简洁扁平
4. 将 SVG 保存为 `docs/decision-flowchart.html`（独立 HTML，可直接浏览器渲染）

## 输出格式

HTML 文件结构：
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>【Skill名称】执行决策流程图</title>
  <style>
    body { font-family: system-ui; background: #fff; padding: 40px; }
    svg { max-width: 680px; width: 100%; }
    .legend { display: flex; gap: 12px; margin-top: 16px; font-size: 12px; color: #888; }
  </style>
</head>
<body>
  <h1>【Skill名称】· 执行决策流程图</h1>
  <p class="subtitle">从用户调用到最终输出的完整决策树</p>
  <svg viewBox="0 0 680 720">...</svg>
  <div class="legend">
    <span>🔵 AI执行</span> <span>🟣 输出节点</span> <span>🟡 决策点</span> <span>🟢 脚本</span> <span>🔴 终止</span>
  </div>
</body>
</html>
```

## 颜色规范

| 角色 | 填充色 | 描边色 |
|------|--------|--------|
| AI 执行节点 | `#E6F1FB` | `#185FA5` |
| 输出/报告节点 | `#EEEDFE` | `#534AB7` |
| 决策菱形 | `#FAEEDA` | `#854F0B` |
| 脚本执行节点 | `#E1F5EE` | `#0F6E56` |
| 终止/报错节点 | `#FCEBEB` | `#A32D2D` |

## 示例：HaluCatch 的决策流程图

可参考 `docs/decision-flowchart.html` 的 SVG 结构。该图包含 7 个节点层次：
1. 入口（用户调用）
2. 路径存在？（决策）→ 否 → 报错退出
3. 执行模式？（决策）→ validate → 脚本扫描 → 结束
4. 技能分类（决策）→ 代码工程型 / 纯方法论型
5. 评估层（脚本 + AI 协作）
6. 报告生成（输出）
7. 修复决策（决策）→ 修 / 不修

## 重要

- SVG 代码直接内嵌在 HTML 中，不依赖外部文件
- 如果 Skill 执行流程简单（<4 个决策点），viewBox 高度可压缩到 500-600
- 复杂流程（>6 个决策点）保持 720 高度即可
- 所有节点文字用中文，除非 Skill 本身是英文
