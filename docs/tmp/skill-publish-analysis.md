# Skill 一键发布流程 —— 方法论拆解与 Skill 化分析

## 来源

基于 HaluCatch 项目的完整发布体系（`scripts/release.sh` 及其依赖脚本）进行逆向工程，提炼出可复用的「一键发布 Skill」模板与方法论。

---

## 一、发布架构全景图

```
┌─────────────────────────────────────────────────────────────┐
│                    release.sh <X.Y.Z>                        │
│              （7 步一键发布主控脚本）                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐           ┌────▼────┐           ┌────▼────┐
   │SkillHub │           │ ClawHub │           │ GitHub  │
   │  (zip)  │           │ (CLI)   │           │(tag+release)
   └─────────┘           └─────────┘           └─────────┘
```

**核心目标**：一个命令 `release.sh 1.2.3` → 自动完成版本升级、构建、校验、多平台发布、Git 提交+Tag+Push。

---

## 二、内容分类矩阵（三大维度）

| 维度 | 定义 | 代表内容 | 可复用程度 |
|------|------|---------|-----------|
| **🔒 平台规则** | 外部平台强制约束，必须服从 | 文件格式、命名规范、CLI 命令结构 | **100% 复用**（所有 Skill 通用） |
| **🧠 AI 动态填充** | 需要 AI 读取当前项目后智能推断 | 文件清单、版本号、依赖关系、语言检测 | **80% 可复用**（框架固定，数值变化） |
| **🎨 自定义内容** | 开发者根据自身项目需求自由决定 | 项目名称、描述、分类、额外构建步骤、阈值 | **30% 可复用**（高度个性化） |

---

## 三、逐文件 / 逐流程拆解

### 3.1 `SKILL.md` — Skill 核心指令文件

#### 🔒 平台规则（必须服从）

| 规则 | 说明 | 违反后果 |
|------|------|---------|
| **YAML Frontmatter 格式** | 必须存在 `---` 包裹的头部元数据 | SkillHub / ClawHub 解析失败 |
| **字段名规范** | `name`, `version`, `description`, `author`, `tags`, `category` 等 | 平台索引失败 |
| **version 字段** | 必须 `"X.Y.Z"` 双引号字符串格式 | 版本号排序错误 |
| **Markdown 正文** | 必须 `# 标题` 开头，包含执行指南 | AI 加载后行为不可控 |
| **文件编码** | 必须 UTF-8，无 BOM | 解析异常 |
| **尺寸上限** | 建议 ≤ 400 行（HaluCatch 自定） | AI 上下文加载缓慢 |

#### 🧠 AI 动态填充

| 内容 | AI 推断逻辑 | 示例 |
|------|------------|------|
| `description` | 从正文 H1 提取 + 20 字压缩 | `# HaluCatch / 捕幻` → 描述 |
| `tags` | 从正文关键词 + 分类自动推断 | 含 `data` → 加 `data-processing` |
| `category` | 从内容类型判断 | 有 `.py` 代码 → `engineering`；纯文本 → `guide` |
| 正文评估框架 | 扫描正文结构自动生成 | 检测到代码块 → 加「代码风险」章节 |
| 语言标记 | 从正文中英文比例判断 | 中文为主 → `zh-CN` |

#### 🎨 自定义内容

| 内容 | 开发者决定自由度 | 建议 |
|------|-----------------|------|
| 具体评估维度 | 完全自由 | HaluCatch 选了 4 维，其他项目可 3 维或 5 维 |
| 评级 emoji | 完全自由 | 🟢🟡🔴 或 ✅⚠️❌ |
| 输出格式定义 | 半自由 | 三版报告是 HaluCatch 特色，可改为单版 |
| 自检声明模板 | 完全自由 | 末尾固定语句可自定义 |
| 执行流程深度 | 半自由 | Phase 0~4 是框架，内部检查项可增减 |

---

### 3.2 `_meta.json` — 元数据真相源（Single Source of Truth）

#### 🔒 平台规则（必须服从）

| 规则 | 说明 | 来源 |
|------|------|------|
| **文件名** | 必须 `_meta.json`（下划线前缀） | ClawHub / SkillHub 读取约定 |
| **必填字段** | `name`, `version`, `slug`, `displayName`, `description` | 各平台注册表要求 |
| **version 语义** | 必须严格 SemVer `X.Y.Z` | 版本排序与比较逻辑 |
| **JSON 格式** | 标准 JSON，无 trailing comma | 解析器兼容 |
| **时间戳字段** | `publishedAt` 为毫秒级 Unix 时间戳 | 由平台在首次发布时写入 |
| **ownerId** | 由 ClawHub 在首次 `publish` 后自动注入 | 开发者不可预设 |

#### 🧠 AI 动态填充

| 内容 | AI 推断逻辑 | 示例 |
|------|------------|------|
| `displayName` | `name` 首字母大写 + 空格替换 | `halucatch` → `HaluCatch` |
| `description` | 从 `SKILL.md` 正文首段提取 100 字 | 自动截断 + 加句号 |
| `tags` | 从 `SKILL.md` frontmatter 复制 | 去重 + 补充 |
| `category` | 从 `SKILL.md` frontmatter 读取 | 一致性校验 |
| `platforms` | 扫描项目文件推断 | 有 `hooks/openclaw/` → 加 `openclaw` |
| `homepage` | 从 `.git/config` 或 GitHub remote 推断 | `https://github.com/{user}/{repo}` |

#### 🎨 自定义内容

| 内容 | 自由度 | 示例 |
|------|--------|------|
| `author` | 完全自由 | 个人名、团队名、公司名 |
| `license` | 完全自由 | MIT, Apache-2.0, 或私有 |
| 额外字段 | 完全自由 | 可扩展 `platforms`, `language`, `requires` 等 |

---

### 3.3 `manifest.json` — 构建清单（Build Manifest）

这是 **HaluCatch 项目自定义** 的文件，不属于任何外部平台强制要求，但起到了关键的「构建编排」作用。

#### 🔒 平台规则（间接约束）

| 规则 | 来源 | 说明 |
|------|------|------|
| `required_files` 必须包含 `SKILL.md` | 所有平台共识 | 无 `SKILL.md` = 非 Skill |
| 打包尺寸限制 | SkillHub 隐含规则 | 文件太大可能被拒绝 |
| 排除文件模式 | 平台 SDK 约定 | `*.pyc`, `__pycache__/` |

#### 🧠 AI 动态填充（核心）

这是 AI 最需要智能判断的部分：

| 字段 | AI 推断逻辑 | 复杂度 |
|------|------------|--------|
| `required_files` | 扫描项目根目录，识别哪些文件是 Skill 运行所必需的 | ⭐⭐⭐ |
| `skillhub_files` | 在 `required_files` 基础上，加 `README.md` + `CHANGELOG.md` 等增值文件 | ⭐⭐ |
| `version_sync` | 检测哪些文件内含版本号引用 → 需要同步更新 | ⭐⭐⭐ |
| `clawhub_exclude` | 扫描项目，排除测试、文档、构建脚本等非运行文件 | ⭐⭐ |

**HaluCatch 的 AI 推断规则（可提炼为 Skill 模板）**：

```
required_files 生成规则：
1. 必须包含: SKILL.md
2. 如果存在 .py 入口文件 → 加入
3. 如果存在包目录（含 __init__.py）→ 加入整个目录
4. 如果存在核心数据文件 → 加入
5. 排除: tests/, docs/, scripts/, reports/

skillhub_files 生成规则：
required_files + 可选增值文件（README.md, CHANGELOG.md, LICENSE 等）

version_sync 检测规则：
扫描所有文本文件，正则匹配版本号模式，统计引用次数 ≥2 的文件加入列表
```

#### 🎨 自定义内容

| 内容 | 自由度 | 说明 |
|------|--------|------|
| `language` | 完全自由 | 但应统一为 `zh-CN` 或 `en` |
| 额外构建字段 | 完全自由 | 如 `build_standalone: true` 触发额外构建 |

---

### 3.4 `release.sh` — 一键发布主控流程

#### 整体 7 步流程（🔒 平台规则 + 🧠 AI 智能 + 🎨 自定义）

| 步骤 | 动作 | 分类 | 说明 |
|------|------|------|------|
| **Step 1** | Bump Version（升级版本号） | 🧠 + 🔒 | 以 `_meta.json` 为真相源，同步到所有文件 |
| **Step 2** | Lint（发布前自检） | 🧠 + 🎨 | 检查文件存在性、版本一致性、尺寸 |
| **Step 3** | Build SkillHub Package（构建 zip） | 🔒 + 🧠 | 按 `manifest.json` 的 `skillhub_files` 打包 |
| **Step 4** | Check File Size（文件尺寸检查） | 🧠 + 🎨 | 按预设阈值检查各文件 |
| **Step 5** | Publish to SkillHub（发布） | 🔒 | `skillhub publish <zip>` 命令 |
| **Step 6** | Publish to ClawHub（发布） | 🔒 | `clawhub publish . --version X.Y.Z` 命令 |
| **Step 7** | Git Commit + Tag + Push | 🔒 + 🎨 | 标准 Git 流程，但 `--skip-github` 等开关是自定义 |

#### 🔒 平台规则（命令级）

| 平台 | 命令 | 参数规则 | 失败处理 |
|------|------|---------|---------|
| **SkillHub** | `skillhub publish <zip>` | zip 必须存在，无额外参数 | `|| echo "⚠️ 失败（可手动重试）` |
| **ClawHub** | `clawhub publish . --version X.Y.Z` | 必须带 `--version` | 同上，不阻断流程 |
| **Git** | `git tag vX.Y.Z` + `git push origin vX.Y.Z` | tag 格式 `v*` | 检查 tag 是否已存在，避免重复 |
| **GitHub Actions** | 由 `push tag` 触发 | `.github/workflows/release.yml` | `on: push: tags: - 'v*'` |

#### 🧠 AI 动态填充（命令参数生成）

| 参数 | AI 推断来源 | 示例 |
|------|------------|------|
| `VERSION` | 从 `_meta.json` 读取 | `python3 -c "import json; print(...['version'])"` |
| `ZIP_PATH` | 由 `build-skillhub.sh` 产出 | `releases/{Name}-{VERSION}-skillhub.zip` |
| `--skip-*` 开关 | 根据 CLI 参数传入 | 用户手动选择跳过某平台 |
| `DRY_RUN` | 根据 `--dry-run` 参数 | 模拟执行，不实际修改 |

#### 🎨 自定义内容（HaluCatch 特有）

| 内容 | 自定义程度 | 说明 |
|------|-----------|------|
| 7 步流程命名 | 完全自定义 | 可改为 5 步或 9 步 |
| `--skip-github` 等开关 | 自定义 | 可增删平台（如加 `--skip-gitee`） |
| 失败处理策略 | 自定义 | HaluCatch 用 `|| echo` 警告但不阻断，可改为 `set -e` 严格模式 |
| 本地 vs 远程 tag 策略 | 自定义 | `--skip-github` 时只打本地 tag |
| 提交信息格式 | 自定义 | `"release: v$VERSION"` 可改为 `"chore(release): v$VERSION"` |

---

### 3.5 `build-skillhub.sh` — SkillHub 包构建

#### 🔒 平台规则（SkillHub 包规范）

| 规则 | 说明 | 违反后果 |
|------|------|---------|
| **包名格式** | `{Name}-{VERSION}-skillhub.zip` | 平台可能无法识别 |
| **zip 根目录** | 包内文件直接在根目录，无子文件夹 | 平台解压后路径错误 |
| **不含 `LICENSE`** | SkillHub 明确不接受 LICENSE 文件 | 上传被拒 |
| **不含开发者文件** | 无 `tests/`, `docs/`, `reports/`, `scripts/` | 包体积过大 + 泄露开发信息 |
| **版本号来源** | 必须来自 `_meta.json`（真相源） | 版本不一致 |

#### 🧠 AI 动态填充

| 内容 | AI 推断逻辑 | 示例 |
|------|------------|------|
| 复制文件清单 | 读取 `manifest.json` 的 `skillhub_files` | 自动 `cp` 对应文件到临时目录 |
| 包名生成 | 从 `_meta.json` 的 `name` + `version` 拼接 | `HaluCatch-${VERSION}-skillhub.zip` |
| 验证规则 | 用 `zipinfo` 检查包内不含排除文件 | `grep -qE '^tests/|^docs/'` |

#### 🎨 自定义内容

| 内容 | 自由度 | 说明 |
|------|--------|------|
| 额外包含文件 | 完全自由 | 如 HaluCatch 额外包含 `CHANGELOG.md`（如果存在） |
| 验证规则 | 完全自由 | 可以自定义验证脚本（如检查文件大小） |
| 压缩级别 | 完全自由 | `zip -qr` 参数可调 |

---

### 3.6 `bump-version.sh` — 版本号升级

#### 🔒 平台规则（版本号规范）

| 规则 | 说明 | 来源 |
|------|------|------|
| SemVer `X.Y.Z` | 必须三位数字，点分隔 | 所有平台共识 |
| `SKILL.md` 中 `version: "X.Y.Z"` | 必须带双引号 | YAML 解析兼容 |

#### 🧠 AI 动态填充（核心智能）

| 内容 | AI 推断逻辑 | 复杂度 |
|------|------------|--------|
| 需要升级的文件列表 | 扫描整个项目，正则匹配所有含 `X.Y.Z` 的文件 | ⭐⭐⭐ |
| 每文件的替换模式 | 分析文件类型，选择正确 sed 模式 | ⭐⭐⭐ |
| 手动提醒列表 | 检测无法自动替换的文件（如 CHANGELOG） | ⭐⭐ |

**HaluCatch 的自动替换矩阵**：

| 文件 | 模式 | 方法 |
|------|------|------|
| `SKILL.md` | `version: "X.Y.Z"` | `sed` 替换 frontmatter |
| `_meta.json` | `"version": "X.Y.Z"` | Python `json` 库重写 |

**需要 AI 提醒手动更新的**（无法自动推断）：

| 文件 | 原因 | 处理方式 |
|------|------|---------|
| `docs/CHANGELOG.md` | 需要新增条目，不是简单替换 | 提醒追加版本段落 |
| `README.md` | 可能有版本引用，但位置不定 | 提醒全文搜索 `X.Y.Z` |
| `halucatch/__init__.py` | 被 `sync-version.sh` 处理，非 `bump-version.sh` | 归属不同脚本 |

#### 🎨 自定义内容

| 内容 | 自由度 | 说明 |
|------|--------|------|
| 提醒消息格式 | 完全自由 | 可改为中文、英文、或更详细的指引 |
| 自动替换的文件范围 | 自定义 | 可扩展更多文件 |
| sed 参数（macOS vs Linux） | 自定义 | `sed -i ''` 是 macOS 兼容写法 |

---

### 3.7 `sync-version.sh` — 版本同步（以 `_meta.json` 为真相源）

这是 `bump-version.sh` 的进阶版，用于**已发布后的版本同步**，而非**升级到新版本**。

#### 🧠 AI 动态填充（核心智能）

| 文件 | AI 推断模式 | 方法 |
|------|------------|------|
| `halucatch/__init__.py` | `__version__ = 'X.Y.Z'` | `sed` 替换 |
| `manifest.json` | `"version": "X.Y.Z"` | Python `json` 重写 |
| `SKILL.md` | `version: "X.Y.Z"` | `sed` 替换 |
| `docs/PROGRESS.md` | `| 最新版本 | **vX.Y.Z** |` | `sed` 替换 |
| `docs/PROGRESS.md` | `| 发布日期 | YYYY-MM-DD |` | `date` 生成 + `sed` 替换 |

#### 🧠 智能判断（CHANGELOG 处理）

```bash
UNRELEASED=$(sed -n '/## \[Unreleased\]/,/---/p' ... | grep -c '###' || true)
if [[ "$UNRELEASED" -gt 0 ]]; then
  echo "⚠️ [Unreleased] 有内容，请手动添加 v$VERSION 条目"
```

这是关键 AI 行为：不是盲目替换，而是**检测内容状态 → 分情况处理**。

#### 🎨 自定义内容

| 内容 | 自由度 | 说明 |
|------|--------|------|
| 同步文件范围 | 完全自定义 | 可增减目标文件 |
| 日期格式 | 自定义 | `date +%Y-%m-%d` 可改 |
| `.bak` 临时文件处理 | 自定义 | `sed -i.bak` + `rm *.bak` 是 macOS 兼容模式 |

---

### 3.8 `lint-paths.sh` — 发布前自检

#### 🔒 平台规则（检查标准）

| 检查项 | 标准 | 违反后果 |
|--------|------|---------|
| `manifest.json` 存在 | 必须存在 | 无法构建 |
| `required_files` 全部存在 | 清单中每个文件都必须在磁盘上 | 运行时缺失 |
| 版本号一致 | `_meta.json` == `SKILL.md` | 平台展示版本混乱 |
| CHANGELOG 版本匹配（可选） | `docs/CHANGELOG.md` 最新版本与 `_meta.json` 一致 | 用户困惑 |

#### 🧠 AI 动态填充

| 内容 | AI 推断 | 说明 |
|------|---------|------|
| `required_files` 清单 | 读取 `manifest.json` 动态获取 | 不同项目清单不同 |
| 版本号提取模式 | 每文件用不同正则 | `SKILL.md` 用 YAML regex，`_meta.json` 用 JSON |
| 错误计数与退出码 | 智能判断 | `--strict` 时 `exit 1`，否则 `exit 0` |

#### 🎨 自定义内容

| 内容 | 自由度 | 说明 |
|------|--------|------|
| 检查项列表 | 完全自定义 | 可添加新检查（如 `ruff check`） |
| 严格模式开关 | 自定义 | `--strict` 可改 `--fail-fast` |
| 警告 vs 错误区分 | 自定义 | CHANGELOG 不匹配是 `⚠️` 警告而非 `❌` 错误 |

---

### 3.9 `check-file-size.sh` — 文件尺寸检查

#### 🧠 AI 动态填充（核心智能）

| 内容 | AI 推断 | 说明 |
|------|---------|------|
| 检查文件清单 | 扫描项目目录动态生成 | 遍历 `halucatch/*.py` 和 `halucatch/evaluators/*.py` |
| 阈值设定 | 基于文件角色分类 | SKILL.md: 400行, 核心 py: 50行, 模块 py: 250行 |
| 尺寸计算 | `wc -l` 行数 + `wc -c` 字节数 | 动态计算 |

#### 🎨 自定义内容

| 内容 | 自由度 | 说明 |
|------|--------|------|
| 阈值数值 | 完全自定义 | 大型项目可放宽到 600 行 |
| 检查范围 | 自定义 | 可扩展更多目录 |
| 输出格式 | 自定义 | 当前是表格形式，可改 JSON |

---

### 3.10 `.github/workflows/release.yml` — GitHub 自动发布

#### 🔒 平台规则（GitHub Actions 语法）

| 规则 | 说明 | 来源 |
|------|------|------|
| `on.push.tags: - 'v*'` | 只有 `v` 开头的 tag 触发 | GitHub Actions 文档 |
| `permissions: contents: write` | 必须有写入权限才能创建 Release | 权限模型 |
| `softprops/action-gh-release@v2` | 标准第三方 action | 社区最佳实践 |
| `fetch-depth: 0` | 需要完整历史才能生成 changelog | action 要求 |
| 附件文件路径 | 必须从工作区引用 | 文件路径规则 |

#### 🧠 AI 动态填充

| 内容 | AI 推断 | 说明 |
|------|---------|------|
| 构建包中的文件列表 | 读取 `manifest.json` 的 `required_files` | 确保一致 |
| Release 名称格式 | `"{Name} ${{ github.ref_name }}"` | 动态替换 |
| 附件文件 | 匹配 `releases/*-skillhub.zip` + 动态 `full.zip` | 正则匹配 |

#### 🎨 自定义内容

| 内容 | 自由度 | 说明 |
|------|--------|------|
| 额外构建步骤 | 完全自定义 | 如 `build-standalone.py` 可加入 |
| 附件文件范围 | 自定义 | 可加更多附件 |
| Release body 模板 | 自定义 | 当前只引用了 CHANGELOG |
| draft/prerelease 开关 | 自定义 | 当前 `false` |

---

### 3.11 `.github/workflows/ci.yml` — 持续集成

#### 🔒 平台规则

| 规则 | 说明 | 来源 |
|------|------|------|
| `on.push.branches: [main]` | main 分支 push 触发 | 标准 |
| `on.pull_request.branches: [main]` | PR 到 main 触发 | 标准 |
| `astral-sh/setup-uv@v5` | UV 工具链 | 现代 Python 工具链 |

#### 🧠 AI 动态填充

| 内容 | AI 推断 | 说明 |
|------|---------|------|
| Python 版本 | 从 `pyproject.toml` 或 `.python-version` 推断 | `3.12` |
| 测试目录 | 扫描项目目录 | `tests/` |
| lint 范围 | 扫描 Python 包 | `halucatch/`, `tests/` |

#### 🎨 自定义内容

| 内容 | 自由度 | 说明 |
|------|--------|------|
| 工具选择 | 完全自定义 | `pytest` + `ruff` 可改 `pytest` + `black` + `mypy` |
| 额外检查 | 自定义 | 可加入 `mypy`, `bandit` 等 |
| 矩阵测试 | 自定义 | 可多版本 Python 测试 |

---

### 3.12 `.clawhubignore` / `.clawhub/` — ClawHub 平台

#### 🔒 平台规则（ClawHub 忽略文件）

| 规则 | 说明 | 来源 |
|------|------|------|
| 文件格式 | 类似 `.gitignore` 的 glob 模式 | ClawHub CLI 约定 |
| 排除目录 | `tests/`, `docs/`, `reports/`, `scripts/` 等 | 发布包规范 |
| `origin.json` | 由 ClawHub 在首次 `publish` 后创建 | 记录 origin 信息，不可手动修改 |

#### 🧠 AI 动态填充

| 内容 | AI 推断 | 说明 |
|------|---------|------|
| 忽略模式 | 读取 `manifest.json` 的 `clawhub_exclude` | 自动同步 |
| `.clawhub/` 目录创建 | 首次 `clawhub publish` 时自动 | 开发者无需手动创建 |

---

## 四、AI 需智能推断的完整清单（按优先级）

### P0 — 必须准确推断（否则发布失败）

| # | 推断项 | 推断来源 | 方法 |
|---|--------|---------|------|
| 1 | **版本号** | `_meta.json` 作为唯一真相源 | `python3 -c "import json; print(...['version'])"` |
| 2 | **必需文件清单** | 扫描项目 + `manifest.json` | 读取 `required_files` |
| 3 | **SkillHub 包文件清单** | `required_files` + 增值文件 | `skillhub_files` |
| 4 | **项目名称** | `_meta.json` 的 `name` | 直接读取 |
| 5 | **语言** | 系统 locale 或 `SKILL.md` 内容检测 | `locale` 或正则 |

### P1 — 建议智能推断（提升质量）

| # | 推断项 | 推断来源 | 方法 |
|---|--------|---------|------|
| 6 | **文件尺寸阈值** | 文件角色 + 项目类型 | SKILL.md: 400行, 核心 py: 50行, 模块: 250行 |
| 7 | **版本同步文件列表** | 全文扫描含版本号的文件 | `grep -r` + 正则 |
| 8 | **CHANGELOG 状态** | 检测 `[Unreleased]` 段是否为空 | `sed -n` + `grep -c` |
| 9 | **Git 状态** | `git status --porcelain` | 是否有未提交改动 |
| 10 | **Tag 是否已存在** | `git rev-parse vX.Y.Z` | 避免重复打 tag |
| 11 | **Skill 类型** | 扫描文件类型 | 有 `.py` → 代码工程型，纯 `.md` → 纯方法论型 |
| 12 | **平台列表** | 扫描 hooks/ 目录 | 有 `hooks/openclaw/` → 加 `openclaw` |

### P2 — 可选智能推断（锦上添花）

| # | 推断项 | 推断来源 | 方法 |
|---|--------|---------|------|
| 13 | **homepage URL** | `git remote -v` 或 `.git/config` | 提取 GitHub URL |
| 14 | **author** | `git config user.name` 或 `_meta.json` | 优先 `_meta.json` |
| 15 | **description** | `SKILL.md` 正文首段 | 截断 100 字 |
| 16 | **tags** | 关键词提取 + 文件类型推断 | 含 `xlsx` → `spreadsheet` 等 |
| 17 | **category** | 文件类型 + 内容分析 | 有 `.py` + 数据 → `engineering` |
| 18 | **Python 版本** | `pyproject.toml` 或 `uv` lock 文件 | 读取 `requires-python` |
| 19 | **测试目录** | 扫描 `tests/` 或 `test/` | 自动发现 |
| 20 | **lint 工具** | 检测配置文件 | `.ruff.toml` → `ruff`, `pyproject.toml` 配置 → 推断 |

---

## 五、自定义内容的自由度分级

### 🟢 高度自由（完全可改）

| 内容 | 说明 | 建议默认值 |
|------|------|-----------|
| 项目名称/作者/描述 | 品牌信息 | 从 git 或交互式询问获取 |
| 额外发布平台 | 如 Gitee, GitLab, AtomGit | 根据目标用户选择 |
| 评级 emoji 系统 | 视觉标识 | 🟢🟡🔴 或 ✅⚠️❌ |
| 报告版本数量 | 单版 / 双版 / 三版 | 建议默认三版（专业/通俗/行动） |
| 检查项深度 | 5 步 vs 7 步 vs 9 步 | 建议 7 步（已验证） |
| 尺寸阈值 | 文件行数警告线 | SKILL.md: 400, py: 250 |
| 提交信息格式 | Git commit message | `"release: vX.Y.Z"` |
| 失败处理策略 | 警告继续 vs 严格退出 | 默认警告继续（多平台互不影响） |

### 🟡 中度自由（有推荐模式）

| 内容 | 说明 | 推荐模式 |
|------|------|---------|
| 版本号来源 | 哪个文件是真相源 | 强烈建议 `_meta.json` |
| 包名格式 | zip 文件命名 | `{Name}-{VERSION}-skillhub.zip` |
| tag 格式 | Git tag 命名 | `vX.Y.Z`（触发 GitHub Actions） |
| 忽略文件模式 | `.clawhubignore` 内容 | 与 `manifest.json` 的 `clawhub_exclude` 同步 |
| CI 工具链 | `pytest` + `ruff` vs 其他 | `pytest` + `ruff`（现代 Python） |
| GitHub Actions 触发条件 | push 分支 / tag | `main` 分支 + `v*` tag |

### 🔴 低度自由（建议遵守平台规范）

| 内容 | 说明 | 约束 |
|------|------|------|
| `SKILL.md` 存在 | 所有平台强制 | 无则非 Skill |
| YAML Frontmatter 格式 | `SKILL.md` 头部 | 必须 `---` 包裹 |
| `_meta.json` 文件名 | 元数据文件 | 必须下划线前缀 |
| `version` 语义格式 | 版本号 | 必须 `X.Y.Z` |
| `skillhub publish` 命令 | SkillHub CLI | 必须 `skillhub publish <zip>` |
| `clawhub publish` 命令 | ClawHub CLI | 必须 `clawhub publish . --version X.Y.Z` |
| GitHub Actions 权限 | `contents: write` | 必须才能创建 Release |
| zip 内不含 LICENSE | SkillHub 规则 | 平台拒绝含 LICENSE 的包 |

---

## 六、发布流程中的关键决策点

### 决策 1：是否执行（DRY_RUN）

```
--dry-run → 只打印「将执行」，不修改任何文件
├─ 适合：首次配置验证、测试脚本逻辑
└─ 不影响：所有外部平台（Git/SkillHub/ClawHub）
```

### 决策 2：平台跳过（SKIP_*）

```
--skip-github → 本地 commit + tag，不 push
├─ 适合：内网环境、GitHub 不可用、测试阶段
└─ 提醒：需手动执行 git push

--skip-skillhub → 不执行 skillhub publish
├─ 适合：未安装 skillhub CLI、无 SkillHub 账号
└─ 提醒：需手动上传 zip

--skip-clawhub → 不执行 clawhub publish
├─ 适合：未安装 clawhub CLI、无 ClawHub 账号
└─ 提醒：需手动发布
```

### 决策 3：版本号状态（Tag 存在性）

```
if git rev-parse "v$VERSION" 存在:
  → 警告「tag 已存在，跳过打 tag」
  → 仍 push 代码（代码可能已更新）
else:
  → 正常打 tag + push tag
```

### 决策 4：Git 工作区状态

```
if git status --porcelain 非空:
  → 自动 git add -A + git commit -m "release: vX.Y.Z"
else:
  → 跳过 commit（无改动）
```

### 决策 5：CHANGELOG 状态

```
if [Unreleased] 段有内容:
  → 提醒手动添加版本条目
else:
  → 无需操作
```

---

## 七、提炼为 Skill 的方法论模板

### 如果将此发布流程 Skill 化，核心结构应为：

```markdown
---
name: skill-publish-kit
version: "1.0.0"
description: |
  一键发布 Skill 到多平台（SkillHub / ClawHub / GitHub）。
  自动推断项目结构、同步版本号、构建发布包、执行多平台发布。
---

# Skill 发布工具包

## 触发条件

当用户说：「发布这个 Skill」、「一键发布」、「准备发版」、
「更新到 X.Y.Z」等。

## 前提检查

1. 项目根目录必须有 `SKILL.md`
2. 项目根目录必须有 `_meta.json`（或协助创建）
3. 建议有 `manifest.json`（定义构建清单）

## 执行流程

### Phase 1: 项目扫描（AI 推断）

- 读取 `_meta.json` 获取版本号（真相源）
- 扫描项目文件结构，推断：
  - `required_files`（运行时必需）
  - `skillhub_files`（发布包包含）
  - `clawhub_exclude`（排除文件）
  - 版本同步文件列表
- 检测语言（从系统 locale 或 SKILL.md 内容）
- 检测项目类型（代码工程型 / 纯方法论型）

### Phase 2: 版本确认

- 如果用户未指定版本 → 读取当前版本，询问是否升级
- 如果用户指定版本 → 验证 SemVer 格式，询问确认
- 展示即将更新的文件清单（P0/P1/P2 推断结果）
- 用户确认后执行 `bump-version`

### Phase 3: 质量检查

- 检查必需文件存在性
- 检查版本号一致性（跨文件）
- 检查文件尺寸（阈值可配置）
- 执行项目级 lint（如有配置）

### Phase 4: 构建发布包

- 按 `skillhub_files` 构建 zip 包
- 验证 zip 不含排除文件
- 检查 zip 尺寸
- 可选：构建其他格式包（standalone 等）

### Phase 5: 多平台发布

- 发布到 SkillHub（`skillhub publish`）
- 发布到 ClawHub（`clawhub publish`）
- 可选：Git commit + tag + push
- 可选：触发 GitHub Actions Release

### Phase 6: 后处理

- 生成发布摘要
- 提醒手动操作项（CHANGELOG 更新等）
- 提供 dry-run 报告（如果是测试模式）

## 平台规则速查

| 平台 | 关键命令 | 必填前提 | 包格式 |
|------|---------|---------|--------|
| SkillHub | `skillhub publish <zip>` | skillhub CLI 登录 | `.zip`，无 LICENSE |
| ClawHub | `clawhub publish . --version X.Y.Z` | clawhub CLI 登录 | 整目录，`.clawhubignore` 过滤 |
| GitHub | `git push origin vX.Y.Z` | GitHub 远程配置 | Actions 自动构建 Release |

## 自定义配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `version_source` | `_meta.json` | 版本号真相源文件 |
| `skillhub_package_name` | `{Name}-{VERSION}-skillhub.zip` | 包名模板 |
| `tag_prefix` | `v` | Git tag 前缀 |
| `commit_message_template` | `release: v{VERSION}` | 提交信息模板 |
| `size_thresholds` | `{SKILL.md: 400, core_py: 50, module_py: 250}` | 尺寸警告阈值 |
| `skip_platforms` | `[]` | 默认不禁用任何平台 |
| `dry_run_default` | `false` | 是否默认模拟模式 |
```

---

## 八、常见陷阱与经验总结

### 陷阱 1：版本号不一致

- **原因**：`SKILL.md` 和 `_meta.json` 手动更新，容易遗漏
- **解决**：始终以 `_meta.json` 为唯一真相源，用脚本同步到所有文件
- **HaluCatch 经验**：`lint-paths.sh` 在发布前强制校验一致性

### 陷阱 2：zip 包含开发者文件

- **原因**：ClawHub 用 `.clawhubignore`，但 SkillHub 用 zip 构建清单，两者不同步
- **解决**：`manifest.json` 的 `clawhub_exclude` 和 `skillhub_files` 统一设计，用脚本互相验证
- **HaluCatch 经验**：`build-skillhub.sh` 用 `zipinfo` 验证排除文件

### 陷阱 3：macOS vs Linux sed 差异

- **原因**：`sed -i ''` 是 macOS 写法，Linux 是 `sed -i`
- **解决**：使用 `.bak` 临时文件 + 删除兼容模式，或统一用 Python 处理 JSON/YAML
- **HaluCatch 经验**：`bump-version.sh` 和 `sync-version.sh` 都用 `sed -i.bak` + `rm *.bak`

### 陷阱 4：CHANGELOG 未更新

- **原因**：版本升级后 CHANGELOG 没追加条目，用户找不到变更说明
- **解决**：`sync-version.sh` 检测 `[Unreleased]` 是否为空，非空则提醒手动处理
- **HaluCatch 经验**：不强制自动写入 CHANGELOG（需要人写变更内容），但强制提醒

### 陷阱 5：Git tag 重复

- **原因**：重新发布同一版本时 tag 已存在
- **解决**：发布脚本先检查 `git rev-parse vX.Y.Z`，存在则跳过打 tag 但继续 push 代码
- **HaluCatch 经验**：`release.sh` 用 `TAG_EXISTS` 变量控制分支逻辑

### 陷阱 6：多平台失败相互影响

- **原因**：SkillHub 发布失败 → 脚本退出 → ClawHub 和 Git 都没执行
- **解决**：每个平台命令用 `|| echo "⚠️ 失败"` 捕获错误，不阻断后续流程
- **HaluCatch 经验**：`release.sh` 不用 `set -e`，手动控制错误处理

---

## 九、文件清单映射

| 文件 | 角色 | 平台归属 | 分类 | 可否 Skill 化 |
|------|------|---------|------|--------------|
| `SKILL.md` | 核心指令 | 所有平台 | 🔒 + 🧠 + 🎨 | 框架固定，内容 AI 生成 |
| `_meta.json` | 元数据真相源 | 所有平台 | 🔒 + 🧠 | 框架固定，内容 AI 填充 |
| `manifest.json` | 构建清单 | HaluCatch 自定义 | 🧠 + 🎨 | 核心可 Skill 化（AI 推断） |
| `release.sh` | 一键发布主控 | HaluCatch 自定义 | 🔒 + 🧠 + 🎨 | 核心可 Skill 化（流程模板） |
| `build-skillhub.sh` | SkillHub 包构建 | SkillHub | 🔒 + 🧠 | 核心可 Skill 化（AI 推断文件清单） |
| `bump-version.sh` | 版本号升级 | HaluCatch 自定义 | 🧠 + 🎨 | 可 Skill 化（推断+同步） |
| `sync-version.sh` | 版本同步 | HaluCatch 自定义 | 🧠 + 🎨 | 可 Skill 化（推断+同步） |
| `lint-paths.sh` | 发布前自检 | HaluCatch 自定义 | 🧠 + 🎨 | 可 Skill 化（检查框架） |
| `check-file-size.sh` | 尺寸检查 | HaluCatch 自定义 | 🧠 + 🎨 | 可 Skill 化（阈值可配置） |
| `.clawhubignore` | ClawHub 排除 | ClawHub | 🔒 | 可从 `manifest.json` 生成 |
| `.github/workflows/*.yml` | CI/CD | GitHub | 🔒 + 🎨 | 框架模板固定，项目信息 AI 填充 |
| `README.md` | 项目说明 | 通用 | 🎨 | 辅助性，非发布必需 |
| `CHANGELOG.md` | 变更日志 | 通用 | 🎨 | 辅助性，需手动维护 |

---

*文档生成时间：基于 HaluCatch v1.7.1 发布体系分析*
*分析范围：scripts/ 目录下全部脚本 + GitHub Actions + 平台配置文件*
