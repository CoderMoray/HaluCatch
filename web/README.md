# 🕸️ Skill Website Template

> 配置驱动的多语言 Skill 品牌官网生成器。
> 一份 `config.yaml` + 一份 `locales/xx.yaml` = 一个完整的品牌官网。

## 📁 Directory Structure

```
web/
├── config.yaml              ← 项目配置（名称、版本、链接、特性开关）
├── build.py                 ← 构建脚本
├── locales/                 ← 多语言翻译
│   ├── zh-CN.yaml
│   └── en.yaml
├── templates/
│   └── index.html           ← HTML 模板（含 {{ 占位符 }}）
├── assets/
│   ├── css/
│   │   └── style.css        ← 全局样式
│   ├── js/                  ← JS 模块
│   │   ├── theme.js         ← 暗色/亮色/跟随系统
│   │   ├── nav.js           ← 导航栏智能显隐
│   │   ├── faq.js           ← FAQ 折叠展开
│   │   ├── tabs.js          ← Tab 切换
│   │   ├── install.js       ← 一键复制安装提示词
│   │   ├── entrance.js      ← 入场动画
│   │   └── version.js       ← 版本号注入
│   ├── ai-chat-demo/        ← 在线体验 Chat Demo 组件
│   │   ├── ai-chat-demo.css
│   │   ├── ai-chat-demo.js
│   │   └── reports-data.js  ← 演示报告数据
│   ├── reports/             ← 报告预览 HTML 片段
│   │   ├── standard.html
│   │   ├── pro.html
│   │   └── action.html
│   └── images/
│       ├── favicon.svg
│       └── og-image.png
└── dist/                    ← 构建输出
```

## 🚀 Quick Start

```bash
# 构建中文版（默认）
python3 build.py

# 构建英文版
python3 build.py --lang en

# 构建所有语言
python3 build.py --all
```

输出在 `web/dist/`。GitHub Pages 部署源设为 `web/dist/` 即可。

---

## ⚙️ Configuration Guide

### Architecture: Three Layers

```
config.yaml     → 项目标识 + 区块开关（与语言无关）
locales/xx.yaml → 所有 UI 文案（按语言翻译）
templates/      → HTML 骨架（{{ 占位符 }}）
```

### `config.yaml` — 完整配置参考

#### 1. 基础信息（必填）

```yaml
name: MySkill                    # 项目英文名
name_zh: 我的技能                # 中文名
version: 1.0.0                   # 版本号（完整）
version_short: 1.0               # 短版本号
description: "一句话描述..."     # SEO 描述
author: YourName                 # 作者
lang: zh-CN                      # 默认语言
pages_url: https://example.com/  # 网站域名（末尾带 /）
github_url: https://github.com/user/repo
license: MIT
license_url: https://github.com/user/repo/blob/main/LICENSE
favicon: favicon.svg
og_image: og-image.png
theme_storage_key: myskill-theme  # localStorage key
```

#### 2. 导航

```yaml
nav:
  brand_full: "MySkill / 我的技能"   # 宽屏品牌名
  brand_short: "我的技能"            # 窄屏品牌名
  sections:                          # 导航锚点（与页面 section id 对应）
    - id: demo
      label: 在线体验
    - id: quickstart
      label: 快速开始
    - id: faq
      label: FAQ
```

#### 3. Hero 区域

```yaml
hero:
  title: MySkill 我的技能
  badges:                         # 版本号自动注入，无需手写
    - "🐍 Python"
    - "📦 零依赖"
    - "MIT 开源"
```

#### 4. CTA 按钮（GitHub 始终渲染，其余可选）

```yaml
cta:
  github:
    label: ⭐ GitHub 开源
  skillhub:                       # 不填 = 不渲染
    label: 📦 SkillHub
    url: https://skillhub.cn/skills/myskill
  clawhub:                        # 不填 = 不渲染
    label: 🦞 ClawHub
    url: https://clawhub.ai/user/skills/myskill
```

#### 5. 安全审计标签（可选，不填跳过整块）

```yaml
security_audits:
  items:
    - icon: https://example.com/favicon.ico   # 机构图标 URL
      name: 某安全机构                          # 显示名称
      status: pass                              # pass | warn
      status_text: 安全                         # 状态标签文字
      url: https://example.com/report           # 跳转链接
```

#### 6. 在线体验 Demo（可选，不填跳过整块）

```yaml
demo:
  avatar: 🔮                      # AI 头像 emoji
  stages:                         # 对话流程（4 个阶段）
    init:                         # 初始阶段：欢迎消息 + 快捷选项
      ai_message: "你好！我可以帮你..."      # AI 的第一句话
      options:                               # 快捷选项按钮
        - text: 好的，开始体验
          next: audit                        # 点击后跳转到哪个阶段
        - text: 这是什么？
          next: explain

    explain:                      # 解释阶段：介绍工具
      thinking:                   # 深度思考动画文案（可选）
        - "🤔 用户想了解工具..."
        - "📋 正在整理说明..."
      ai_message: "这是一个..."
      options:
        - text: 明白了，开始吧
          next: audit

    prepare:                      # 准备阶段
      thinking:
        - "📂 正在准备..."
      ai_message: "请准备以下内容..."
      options:
        - text: 准备好了
          next: audit

    audit:                        # 执行阶段：展示结果
      thinking:
        - "🔍 正在扫描..."
        - "✅ 扫描完成"
      ai_message: "审查完成！结果如下..."
      show_reports: true          # 设为 true 会在右侧展示报告面板
```

**字段命名注意**：stages 配置使用 **snake_case**（`ai_message`、`show_reports`），构建时会自动兼容 JS 端的 camelCase。

#### 7. 痛点卡片

```yaml
problem_cards:
  cards:
    - icon: 🤷                    # emoji 图标
      title: 问题标题
      desc: 问题描述
      tags:                       # 风险标签
        - label: 逻辑漏洞
          class: logic            # 可用 class: hallucination / unstable / security / logic / reuse / noprogress / nocheck / dependency
```

#### 8. 报告预览（可选，不填跳过整块）

```yaml
report_preview:
  tabs:
    - id: standard
      label: 📗 标准版
    - id: pro
      label: 📊 专业版
    - id: action
      label: 🤖 AI 行动版
  content_standard: web/assets/reports/standard.html   # HTML 文件路径（相对项目根目录）
  content_pro: web/assets/reports/pro.html
  content_action: web/assets/reports/action.html
```

> 报告内容支持两种方式：
> - **文件路径**（不含 `<` 标签）：从文件读取 HTML 内联
> - **内联 HTML**（含 `<` 标签）：直接作为 HTML 渲染

#### 9. 快速开始

```yaml
quickstart:
  user:                           # 普通用户标签页
    skillhub:                     # 国内安装方案（可选）
      title: 🇨🇳 国内用户方案
      subtitle: 描述文字
      note: 中文环境 · 免费
      prompt: |                   # 一键复制的安装提示词
        请先检查是否已安装 SkillHub...
    clawhub:                      # 国际安装方案（可选）
      title: 🌐 国际用户方案
      subtitle: 描述文字
      note: Global marketplace
      prompt: |
        Before installing anything...

  dev:                            # 开发者标签页
    clone_cmd: |
      git clone https://github.com/user/repo.git
      cd repo
    run_cmds:                     # 运行命令列表
      - comment: 自动检测语言
        cmd: python3 main.py --skill-dir /path/to/skill
      - comment: 强制英文
        cmd: python3 main.py --skill-dir /path/to/skill --lang en
    report_output: |              # 输出说明
      reports/report-YYYY-MM-DD.md
```

#### 10. Blog 文章（可选，不填跳过整块）

```yaml
blog_posts:
  items:
    - platform: 掘金              # 平台名（显示为标签）
      title: 文章标题
      desc: 文章摘要
      url: https://juejin.cn/post/xxx
```

#### 11. FAQ（可选，不填跳过整块）

```yaml
faq:
  full_link_url: FAQ.md           # "查看完整 FAQ" 链接
  items:
    - q: 这个问题是什么？
      a: 这是答案。支持多行，<br>用 br 换行。
```

### `locales/xx.yaml` — 翻译文件

翻译文件有 **11 个命名空间**，键结构必须与 `zh-CN.yaml` 完全一致（仅值不同）：

| 命名空间 | 覆盖范围 |
|---------|---------|
| `seo` | `<title>`、`<meta description>` |
| `a11y` | 无障碍标签（skip link） |
| `nav` | 导航链接、主题切换、分享菜单 |
| `hero` | 副标题、CTA 按钮文字 |
| `security` | 安全审计标题 |
| `demo` | 在线体验标题、思考标签、结束语 |
| `problem` | 痛点区域标题和底部文案 |
| `report_preview` | 报告预览标题和副标题 |
| `quickstart` | 安装步骤、对话流程、报告卡片、开发者标签 |
| `faq` | FAQ 标题 |
| `footer` | 版权信息、链接标签 |

**特殊占位符**：`{name}` 会被自动替换为 `config.name`。

**添加新语言**：复制 `en.yaml` → 翻译 → 运行 `python3 build.py --lang xx`。

---

## 🧩 Component Architecture

### 页面区块渲染规则

每个区块按以下逻辑决定是否渲染：

```
config 中该区块存在且有内容 → 渲染
config 中该区块不存在或为空 → 整块跳过
```

例如：
- `security_audits.items: []` → 安全审计行不显示
- `cta.skillhub` 不填 → Hero 和 Footer 都不显示 SkillHub 按钮
- `demo` 不填 → 在线体验区块和 Chat Demo JS 都不生成

### Demo 组件的关键行为

1. **初始化**：`AIChatDemo` 构造函数渲染 HTML 骨架，`begin()` 启动初始对话
2. **阶段流转**：`init` → 用户点击选项 → `transitionTo('explain')` → ...
3. **思考动画**：阶段配置了 `thinking` 数组时，先逐行打字展示思考过程，收起后再显示 `ai_message`
4. **报告面板**：`show_reports: true` 时，右侧展示 `reports-data.js` 中的三份报告
5. **幂等保护**：`begin()` 多次调用安全，只执行一次

### JS 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| `theme.js` | 主题切换（亮/暗/跟随系统） | 无 |
| `nav.js` | 导航栏显隐 + 汉堡菜单 + 品牌动画 | 无 |
| `faq.js` | FAQ 折叠展开 | 无 |
| `tabs.js` | Tab 切换（报告预览、快速开始） | 无 |
| `install.js` | 一键复制安装提示词 | 无 |
| `entrance.js` | 入场动画 + Demo 延迟启动 | `ai-chat-demo.js` |
| `version.js` | 版本号注入 + JSON-LD | 无 |
| `ai-chat-demo.js` | Chat Demo 对话引擎 | `marked.js` CDN、`reports-data.js` |

---

## 🔧 Customization

### 替换品牌色

编辑 `assets/css/style.css` 中的 CSS 变量：

```css
:root {
  --accent: #6c63ff;      /* 主色调 */
  --accent2: #00d4aa;     /* 辅助色 */
  --h1-from: #6c63ff;     /* 标题渐变起点 */
  --h1-to: #00d4aa;       /* 标题渐变终点 */
}
```

### 替换 Logo SVG

修改 `templates/index.html` 中 `{{ brand_svg }}` 和 `{{ hero_svg }}` 的 SVG 代码。

### 自定义 Demo 报告数据

编辑 `assets/ai-chat-demo/reports-data.js`，修改 `REPORTS_DATA` 对象。

---

## ✅ Checklist for New Projects

1. 复制 `web/` 目录到你的项目
2. 替换 `assets/images/favicon.svg` 和 `og-image.png`
3. 填写 `config.yaml`（name、urls、hero、badges）
4. 决定开启哪些可选区块（填内容 = 开启，留空 = 跳过）
5. 编辑 `assets/ai-chat-demo/reports-data.js` 替换演示报告数据
6. 编辑 `assets/reports/*.html` 替换报告预览内容
7. 翻译 `locales/en.yaml`
8. 运行 `python3 build.py --all`
9. 部署 `dist/` 到 GitHub Pages / Vercel / 任意静态托管
