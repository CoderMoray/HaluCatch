# 🕸️ HaluCatch Website Builder

> 配置驱动、多语言支持的 Skill 官网生成器。  
> 一份 `config.yaml` + 一份 `locales/xx.yaml` = 一个完整的品牌官网。

## 📁 Directory Structure

```
web/
├── config.yaml              ← 项目标识配置（名称、版本、链接、特性开关）
├── build.py                 ← 构建脚本
├── locales/                 ← 多语言翻译（键结构严格对齐）
│   ├── zh-CN.yaml
│   └── en.yaml
├── templates/
│   └── index.html           ← HTML 模板（含 {{ 占位符 }}）
├── assets/
│   ├── css/
│   │   └── style.css        ← 全局样式（变量、布局、组件、响应式）
│   └── js/                  ← 按功能拆分的 JS 模块
│       ├── theme.js         ← 主题切换（亮/暗/跟随系统）
│       ├── nav.js           ← 导航栏智能显隐 + 汉堡菜单
│       ├── faq.js           ← FAQ 折叠展开
│       ├── tabs.js          ← Tab 切换
│       ├── install.js       ← 一键复制安装提示词
│       ├── entrance.js      ← 入场动画
│       └── version.js       ← 版本号注入 + JSON-LD
├── dist/                    ← 构建输出（gitignore）
│   ├── index.html           ← 默认语言（zh-CN）
│   ├── en/index.html        ← 英文版
│   └── assets/              ← 复制的静态资源
└── README.md                ← 你在这里
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

输出在 `dist/` 目录下，直接部署即可。

## ⚙️ Configuration Layers

### 1. `config.yaml` — 项目标识 + 特性开关

控制**项目独有的标识信息**和**区块显隐**，与语言无关：

```yaml
# 基础
name: HaluCatch
version: 1.7.1
github_url: https://github.com/CoderMoray/HaluCatch
pages_url: https://codermoray.github.io/HaluCatch/

# Hero
hero:
  title: HaluCatch 捕幻
  badges: ["🐍 Python", "📋 3 份报告", ...]

# 可选区块：不填或留空则整块不渲染
security_audits:    # 安全审计标签行
demo:               # 在线体验 Chat Demo
problem_cards:      # 痛点卡片
report_preview:     # 报告预览
quickstart:         # 快速开始
blog_posts:         # Blog 文章
faq:                # FAQ 问答
```

### 2. `locales/{lang}.yaml` — 多语言翻译

**所有 UI 文案**，11 个命名空间，键结构必须完全一致：

```
seo       → <title>, <meta description>
a11y      → 无障碍标签
nav       → 导航链接、主题切换、分享菜单
hero      → 副标题、CTA 按钮
security  → 安全审计标题
demo      → 在线体验文案
problem   → 痛点区域
report_preview → 报告预览
quickstart→ 安装步骤、对话流程、报告卡片
faq       → FAQ 标题
footer    → 版权信息、链接标签
```

> `{name}` 占位符会被自动替换为 `config.name`

### 3. `templates/index.html` — HTML 骨架

使用 `{{ key }}` 或 `{{ a.b.c }}` 点号路径占位符，由 `build.py` 渲染替换。

## 🌍 Adding a New Language

```bash
# 1. 复制英文翻译文件
cp locales/en.yaml locales/ja.yaml

# 2. 翻译内容（保持键结构不变）

# 3. 构建
python3 build.py --lang ja

# 输出：dist/ja/index.html
```

## 🔧 How It Works

```
config.yaml ─┐
             ├─→ merge_config() → context dict ─→ render_template() → dist/index.html
locales/zh-CN.yaml ─┘
```

`merge_config()` 将配置和翻译合并为扁平+嵌套混合的 context 字典，`render_template()` 用正则替换 `{{ }}` 占位符（支持点号路径 `seo.title`）。

## 📋 Checklist for New Projects

- [ ] 填写 `config.yaml` 基础信息（name, version, urls）
- [ ] 填写 `hero` 区块（badges, CTA）
- [ ] 决定开启哪些可选区块（填内容 = 开启，留空 = 跳过）
- [ ] 翻译 `locales/en.yaml`
- [ ] 运行 `python3 build.py --all`
- [ ] 部署 `dist/` 目录

## 🧪 Test

```bash
# 确保 YAML 合法
python3 -c "import yaml; yaml.safe_load(open('config.yaml')); print('✅')"

# 检查 locale 键结构对齐
python3 -c "
import yaml
zh = yaml.safe_load(open('locales/zh-CN.yaml'))
en = yaml.safe_load(open('locales/en.yaml'))
print('Match' if zh.keys() == en.keys() else 'Mismatch')
"

# 验证构建无残留占位符
python3 build.py --all
grep -r '{{ ' dist/
```
