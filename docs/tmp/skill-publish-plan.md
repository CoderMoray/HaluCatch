# Skill 一键发布 —— 完整 Plan：AI 控制 vs 脚本化 vs 模板

> 基于前序分析（`skill-publish-analysis.md` + `platform-rules-sources.md`），将 HaluCatch 发布体系 Skill 化的完整分工方案。

---

## 一、总览：三层架构

```
┌────────────────────────────────────────────────────────────────────┐
│  第一层：AI 控制层（推断 + 决策 + 用户交互）                         │
│  负责：理解项目、推断结构、与用户确认、选择策略、处理异常               │
│  载体：SKILL.md 中的指令 + AI 的推理能力                              │
└────────────────────────────────────────────────────────────────────┘
                              ↓ 生成/配置
┌────────────────────────────────────────────────────────────────────┐
│  第二层：脚本模板层（框架固定 + 内容可替换）                           │
│  负责：提供标准化的脚本骨架，AI 填入项目特定内容                         │
│  载体：模板文件（*.template.sh, *.template.json, *.template.yml）       │
└────────────────────────────────────────────────────────────────────┘
                              ↓ 渲染
┌────────────────────────────────────────────────────────────────────┐
│  第三层：脚本执行层（确定性自动化）                                   │
│  负责：无歧义地执行生成后的脚本，无 AI 介入                           │
│  载体：渲染后的实际脚本文件（*.sh, *.json, *.yml）                     │
└────────────────────────────────────────────────────────────────────┘
```

**核心原则**：AI 只做「人类擅长的事」——理解、推断、决策；脚本只做「机器擅长的事」——重复、精确、快速执行。模板是连接两者的桥梁。

---

## 二、AI 控制层：做什么、为什么、怎么做

### 2.1 项目扫描与推断（推断型 AI 任务）

| 推断项 | 推断来源 | 为什么必须是 AI | 输出 |
|--------|---------|----------------|------|
| **项目类型** | 文件扩展名、目录结构、SKILL.md 内容 | 需要语义理解（有 `.py` ≠ 纯代码型，可能是工具类 Skill） | 代码工程型 / 纯方法论型 / 混合型 |
| **语言** | 系统 locale + SKILL.md 正文语言比例 | 需要上下文判断（中文用户用英文描述 = 英语？） | `zh-CN` / `en` / `auto` |
| **必需文件清单** | 扫描项目目录 + 文件内容分析 | 需要判断哪些文件是运行时必需的（如 `.py` 脚本 vs `.md` 文档） | `required_files` 数组 |
| **发布包文件清单** | 在必需文件上追加 README/CHANGELOG | 需要判断哪些增值文件对平台有意义 | `skillhub_files` 数组 |
| **排除文件清单** | 扫描项目目录 + 已知排除模式 | 需要区分开发者文件 vs 运行时文件 | `clawhub_exclude` 数组 |
| **版本同步文件列表** | 全文扫描含版本号引用的文件 | 需要跨文件理解版本号引用模式（regex 匹配 + 上下文验证） | 需要同步的文件列表 |
| **平台目标** | 检测 hooks/ 目录、平台配置文件 | 需要推断项目支持哪些平台（OpenClaw / Cursor / Windsurf 等） | `platforms` 数组 |
| **lint 工具** | 检测 `pyproject.toml`, `.ruff.toml`, `.eslint` 等 | 需要推断配置文件的意图（`[tool.ruff]` → 用 ruff） | `ruff` / `eslint` / `prettier` / 无 |
| **测试框架** | 检测 `tests/`, `pytest.ini`, `pyproject.toml` | 需要推断测试策略 | `pytest` / `jest` / 无 |
| **Git 远程 URL** | `.git/config` 或 `git remote -v` | 需要提取和规范化 URL | `homepage` URL |
| **作者信息** | `_meta.json` > `git config user.name` | 需要判断优先级 | 作者名 |

**为什么必须是 AI 而非脚本**：这些推断都需要**语义理解**和**上下文判断**。脚本可以用正则匹配 `.py` 文件，但无法判断一个 `.py` 文件是核心脚本还是临时测试。AI 可以读取文件内容，判断其在 Skill 中的角色。

### 2.2 平台规则验证与动态获取（验证型 AI 任务）

| 验证项 | 方法 | 为什么必须是 AI | 输出 |
|--------|------|----------------|------|
| **CLI 版本检测** | 运行 `skillhub --version`, `clawhub --version` | 需要理解版本号语义，判断是否在已知 bug 列表中 | 版本号 + 已知 bug 警告 |
| **CLI 参数变化** | 运行 `--help` 并解析输出 | 需要理解帮助文本，提取新参数 | 最新支持的参数列表 |
| **GitHub Actions 权限变化** | 检查 GitHub 官方文档或 API | 需要理解权限语义，判断对 release workflow 的影响 | 权限建议更新 |
| **平台规则缓存** | 读取/更新 `.rules-cache.json` | 需要判断缓存是否过期，决定重新获取 | 最新规则摘要 |
| **fallback 策略选择** | 综合 CLI 版本、已知 bug、用户偏好 | 需要多因素决策（CLI bug → 用 Web；CI 配置缺失 → 提醒本地 lint） | 推荐的发布策略 |

**为什么必须是 AI**：平台规则是**动态变化**的。脚本可以硬编码规则，但无法适应变化。AI 可以在每次使用时动态获取，用自然语言理解帮助文档，判断规则变化的影响。

### 2.3 用户确认与决策（交互型 AI 任务）

| 决策点 | 为什么必须是 AI | 交互方式 |
|--------|---------------|---------|
| **版本号确认** | 用户可能想 patch/minor/major，AI 需要解释差异 | 展示当前版本 → 询问升级类型 → 确认新版本 |
| **发布平台选择** | 用户可能有不同目标（只发 SkillHub，不发 ClawHub） | 展示检测到的平台 → 询问跳过哪些 → 生成 `--skip-*` 参数 |
| **dry-run 确认** | 首次发布或重大版本应建议 dry-run | 自动建议 dry-run → 用户确认是否执行真实发布 |
| **文件清单确认** | AI 推断的 `required_files` 可能出错 | 展示推断的清单 → 用户确认或修改 |
| **异常处理** | 发布失败时，AI 需要诊断并提供选项 | 错误信息 → AI 分析原因 → 提供重试/跳过/修复建议 |
| **CHANGELOG 更新提醒** | 需要人写变更内容，不能自动 | 检测 `[Unreleased]` 状态 → 提醒用户手动更新 |
| **Git 工作区确认** | 未提交改动是否包含在发布中 | 展示 `git status` 摘要 → 确认是否提交 |

**为什么必须是 AI**：这些决策都需要**理解用户意图**和**解释选项含义**。脚本可以展示清单，但无法解释「为什么这个文件应该包含」，也无法根据用户的历史偏好调整推荐。

### 2.4 错误诊断与修复建议（诊断型 AI 任务）

| 错误场景 | AI 诊断能力 | 脚本能做什么 |
|---------|-----------|-------------|
| `clawhub publish` 失败：acceptLicenseTerms | 读取缓存的规则 → 知道是 v0.7.0 已知 bug → 建议 Web 发布 | 只能重试或退出 |
| `skillhub publish` 失败：文件扩展名被拒 | 读取平台白名单 → 推断哪些文件越界 → 建议移除或加入白名单 | 只能展示原始错误 |
| GitHub Actions 发布失败：权限不足 | 检查 workflow 的 permissions → 对比最新 GitHub 权限要求 → 建议更新 | 只能展示日志 |
| 版本号不一致（lint-paths.sh 错误） | 扫描所有含版本号的文件 → 定位不一致的来源 → 建议修复 | 只能报告「不一致」 |
| zip 包含开发者文件 | 读取 zip 内容 → 对比排除清单 → 推断哪些文件不该包含 | 只能列出文件 |
| 文件尺寸超限 | 分析文件角色 → 建议哪些可以拆分（如 SKILL.md 太长 → 拆分为参考文档） | 只能报告「超限」 |

---

## 三、脚本执行层：做什么、为什么、怎么做

### 3.1 确定性操作（脚本化）

以下操作**完全确定**，无需 AI 介入，脚本即可精确执行：

| 操作 | 输入 | 输出 | 工具 | 为什么必须是脚本 |
|------|------|------|------|-----------------|
| **版本号替换** | 目标文件 + 旧版本 + 新版本 | 替换后的文件 | `sed` / `python` | 精确匹配，无歧义，批量执行 |
| **文件复制** | 源文件列表 + 目标目录 | 复制后的文件 | `cp` / `rsync` | 纯文件系统操作，无需理解 |
| **zip 打包** | 文件列表 + 输出路径 | `.zip` 文件 | `zip` | 标准压缩，无决策 |
| **zip 内容验证** | zip 路径 + 排除模式 | 验证结果 | `zipinfo` + `grep` | 正则匹配，确定性 |
| **文件尺寸计算** | 文件路径 | 行数/字节数 | `wc -l` / `wc -c` | 纯计算，无推断 |
| **文件存在性检查** | 文件路径 | 存在/不存在 | `test -f` | 布尔判断，无推断 |
| **Git 状态检查** | 仓库路径 | 工作区状态 | `git status --porcelain` | 标准输出，无推断 |
| **Git 提交** | 文件 + 提交信息 | 提交 | `git add` / `git commit` | 标准操作，无决策 |
| **Git 打 tag** | tag 名 + 目标提交 | tag | `git tag` | 标准操作，无决策 |
| **Git push** | 分支/tag | 推送到远程 | `git push` | 标准操作，无决策 |
| **CLI 调用** | 命令 + 参数 | CLI 输出 | `skillhub` / `clawhub` | 直接调用，无推断 |
| **JSON/YAML 读写** | 文件路径 + 字段路径 + 值 | 更新后的文件 | `python -c "import json; ..."` | 结构化数据操作，精确 |
| **日期生成** | 格式模板 | 日期字符串 | `date` | 纯计算 |
| **目录创建** | 路径 | 目录 | `mkdir -p` | 标准操作 |
| **临时文件管理** | 模板 | 临时目录/文件 | `mktemp -d` | 标准操作，自动清理 |

### 3.2 脚本执行的关键原则

```
┌──────────────────────────────────────────────────────────────────┐
│  脚本执行层的设计原则：                                           │
│                                                                  │
│  1. 幂等性：同一脚本执行多次，结果相同（不重复打 tag）               │
│  2. 原子性：失败时回滚（使用临时目录，验证通过后再移动）             │
│  3. 非阻断：多平台命令用 `|| echo` 捕获，不互相影响                 │
│  4. 可观测：每步输出明确状态（✅/❌/⚠️），便于 AI 诊断              │
│  5. 不交互：脚本无交互，所有参数由 AI 层传入                         │
│                                                                  │
│  脚本只负责「执行」，不负责「判断」                                 │
│  判断（是否跳过、是否阻断、是否重试）全部交给 AI 层                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 四、脚本模板层：做什么、为什么、怎么做

### 4.1 模板的定位

模板是**第二层**，连接 AI 推断和脚本执行：

```
AI 层推断结果 ──→ 模板渲染（变量替换）──→ 实际脚本/文件 ──→ 脚本执行

  项目类型：代码型         →  模板选择：代码型模板
  平台目标：SkillHub      →  模板变量：platforms = ["skillhub"]
  语言：zh-CN            →  模板变量：language = "zh-CN"
  工具：ruff              →  模板变量：lint_tool = "ruff"
  版本号：1.2.3           →  模板变量：version = "1.2.3"
```

### 4.2 模板清单

| 模板文件 | 模板内容 | 动态变量（AI 填充） | 可配置项（用户自定义） | 渲染后文件 |
|---------|---------|-------------------|---------------------|-----------|
| `SKILL.md.template` | Frontmatter 结构 + 正文框架 | `name`, `displayName`, `description`, `version`, `tags`, `category`, `language` | 评估维度、评级 emoji、Phase 数量、输出格式 | `SKILL.md` |
| `_meta.json.template` | 元数据字段结构 | `name`, `displayName`, `description`, `version`, `author`, `tags`, `category`, `platforms`, `homepage` | 额外字段、license 类型 | `_meta.json` |
| `manifest.json.template` | 构建清单结构 | `required_files`, `skillhub_files`, `clawhub_exclude`, `version_sync`, `language` | 包名模板、额外构建字段 | `manifest.json` |
| `release.sh.template` | 7 步发布流程骨架 | `PROJECT_NAME`, `VERSION_SOURCE`, `SCRIPTS_DIR` | 步数命名、失败策略、开关名称、提交信息格式 | `release.sh` |
| `build-skillhub.sh.template` | zip 构建逻辑 | `PROJECT_NAME`, `SKILLHUB_FILES`, `EXCLUDED_PATTERNS` | 包名格式、验证规则、压缩级别 | `build-skillhub.sh` |
| `check-structure.sh.template` | 结构检查框架 | `CHECK_ITEMS`（检查项列表） | 检查项内容、严格模式开关、警告/错误区分 | `check-structure.sh` |
| `check-size.sh.template` | 尺寸检查框架 | `FILE_PATTERNS`, `THRESHOLDS` | 阈值数值、检查范围、输出格式 | `check-size.sh` |
| `bump-version.sh.template` | 版本号升级框架 | `VERSION_FILES`（需升级的文件列表） | 替换模式、提醒格式、sed 兼容方式 | `bump-version.sh` |
| `sync-version.sh.template` | 版本同步框架 | `SYNC_FILES`（需同步的文件列表） | 同步范围、日期格式、CHANGELOG 检测 | `sync-version.sh` |
| `.github/workflows/release.yml.template` | Release workflow | `PROJECT_NAME`, `RELEASE_FILES`, `BUILD_STEPS` | 触发条件、附件文件、Release body 模板 | `.github/workflows/release.yml` |
| `.github/workflows/ci.yml.template` | CI workflow | `LINT_TOOL`, `TEST_FRAMEWORK`, `PYTHON_VERSION`, `CHECK_PATHS` | 工具链、额外检查、矩阵测试 | `.github/workflows/ci.yml` |
| `.clawhubignore.template` | 忽略模式 | `EXCLUDE_PATTERNS` | 额外排除项 | `.clawhubignore` |

### 4.3 模板变量定义（标准化）

以下变量名在模板中统一使用，AI 层负责填充：

```yaml
# 项目基本信息
{{PROJECT_NAME}}          # 项目名，如 "halucatch"
{{PROJECT_DISPLAY_NAME}}  # 展示名，如 "HaluCatch / 捕幻"
{{DESCRIPTION}}           # 描述，从 SKILL.md 首段提取
{{VERSION}}               # 版本号，如 "1.2.3"
{{VERSION_SOURCE}}        # 版本号真相源文件，如 "_meta.json"
{{AUTHOR}}                # 作者
{{LICENSE}}               # 许可证，如 "MIT"
{{LANGUAGE}}              # 语言，如 "zh-CN"
{{CATEGORY}}              # 分类，如 "engineering"

# 项目结构
{{PROJECT_TYPE}}          # 代码工程型 / 纯方法论型 / 混合型
{{REQUIRED_FILES}}        # 必需文件列表（JSON 数组）
{{SKILLHUB_FILES}}        # SkillHub 发布包文件列表（JSON 数组）
{{CLAWHUB_EXCLUDE}}       # ClawHub 排除模式（JSON 数组）
{{VERSION_SYNC_FILES}}    # 版本同步文件列表（JSON 数组）

# 平台与工具
{{PLATFORMS}}             # 平台列表，如 ["openclaw", "cursor", "windsurf"]
{{LINT_TOOL}}             # lint 工具，如 "ruff"
{{TEST_FRAMEWORK}}        # 测试框架，如 "pytest"
{{PYTHON_VERSION}}        # Python 版本，如 "3.12"

# 发布配置
{{TAG_PREFIX}}            # tag 前缀，如 "v"
{{COMMIT_MESSAGE_TEMPLATE}} # 提交信息模板，如 "release: v{{VERSION}}"
{{PACKAGE_NAME_TEMPLATE}} # 包名模板，如 "{{PROJECT_NAME}}-{{VERSION}}-skillhub.zip"
{{RELEASE_FILES}}         # Release 附件文件列表

# 检查配置
{{SIZE_THRESHOLDS}}       # 尺寸阈值（JSON 对象）
{{CHECK_ITEMS}}           # 结构检查项（JSON 数组）
{{LINT_CHECK_PATHS}}      # lint 检查路径

# 脚本位置
{{SCRIPTS_DIR}}           # 脚本目录，如 "scripts/"
{{RELEASES_DIR}}          # 发布包目录，如 "releases/"
```

### 4.4 模板渲染方式

推荐使用 **Python 模板渲染**（Jinja2 或 string.Template），因为：
- 项目已经有 Python 依赖（ruff、pytest）
- 可以复用已有的 Python 脚本能力
- 比 `sed` 更安全和可读

```python
# 模板渲染示例（使用 string.Template，无额外依赖）
from string import Template
import json

def render_template(template_path, output_path, variables):
    with open(template_path) as f:
        template = Template(f.read())
    
    # 将 JSON 数组渲染为 shell 可用格式
    rendered = template.safe_substitute({
        **variables,
        'REQUIRED_FILES_JSON': json.dumps(variables['REQUIRED_FILES']),
        'REQUIRED_FILES_ARRAY': ' '.join(f'"{f}"' for f in variables['REQUIRED_FILES']),
    })
    
    with open(output_path, 'w') as f:
        f.write(rendered)
    
    # 设置执行权限（如果是 shell 脚本）
    if output_path.endswith('.sh'):
        os.chmod(output_path, 0o755)
```

### 4.5 模板与脚本的关系

```
┌──────────────────────────────────────────────────────────────────┐
│  模板 → 渲染 → 脚本                                              │
│                                                                  │
│  release.sh.template                                             │
│  ├── 框架：7 步流程（固定）                                        │
│  ├── 变量：{{PROJECT_NAME}}, {{VERSION_SOURCE}}                  │
│  └── 可配置：失败策略（默认 `|| echo`，可选 `--strict`）           │
│         ↓ 渲染                                                    │
│  release.sh                                                      │
│  ├── 框架：7 步流程（固定）                                        │
│  ├── 值：PROJECT_NAME="halucatch", VERSION_SOURCE="_meta.json"  │
│  └── 选择：失败策略 = `|| echo`（用户选择）                        │
│         ↓ 执行                                                    │
│  bash release.sh 1.2.3                                          │
│  （纯脚本执行，无 AI 介入）                                         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 五、完整分工表

### 5.1 按流程阶段分工

| 发布阶段 | AI 控制 | 脚本模板 | 脚本执行 | 说明 |
|---------|--------|---------|---------|------|
| **Phase 0: 项目扫描** | 推断项目类型、语言、必需文件、平台目标 | — | 文件系统遍历（`find`, `ls`） | AI 读取文件内容做语义推断，脚本只做目录扫描 |
| **Phase 1: 版本确认** | 解释版本差异、询问用户、确认升级类型 | — | 读取 `_meta.json` 当前版本 | AI 做交互决策，脚本做数据读取 |
| **Phase 2: 模板渲染** | 选择模板、填充变量、确认生成清单 | 所有模板文件 | 渲染引擎（Python string.Template） | AI 选择模板，模板定义结构，渲染引擎生成脚本 |
| **Phase 3: 结构检查** | 解释检查项、判断失败影响 | `check-structure.sh` | 执行渲染后的脚本 | AI 判断失败时是否阻断，脚本只执行检查 |
| **Phase 4: 尺寸检查** | 解释超限影响、建议拆分方案 | `check-size.sh` | 执行渲染后的脚本 | AI 提供建议，脚本做测量 |
| **Phase 5: 版本升级** | 确认升级范围、提醒手动更新项 | `bump-version.sh` | 执行渲染后的脚本 | AI 确认清单，脚本执行替换 |
| **Phase 6: 构建包** | 确认包内容、验证 zip 结果 | `build-skillhub.sh` | 执行渲染后的脚本 | AI 确认内容，脚本执行打包 |
| **Phase 7: 多平台发布** | 选择发布策略（CLI vs Web）、处理失败、提供 fallback | — | `skillhub publish` / `clawhub publish` / `git` | AI 做策略选择，脚本执行命令 |
| **Phase 8: 后处理** | 生成发布摘要、提醒手动操作、更新缓存 | — | 写入 `.rules-cache.json` | AI 生成摘要，脚本写文件 |

### 5.2 按文件类型分工

| 文件 | AI 控制 | 脚本模板 | 脚本执行 | 说明 |
|------|--------|---------|---------|------|
| `SKILL.md` | 推断内容、填充 frontmatter、组织正文结构 | `SKILL.md.template` | 渲染生成文件 | AI 写核心内容，模板定义格式 |
| `_meta.json` | 推断字段值、验证一致性 | `_meta.json.template` | 渲染生成文件 | AI 填充元数据，模板定义结构 |
| `manifest.json` | 推断文件清单、排除模式 | `manifest.json.template` | 渲染生成文件 | AI 推断清单，模板定义结构 |
| `release.sh` | 选择流程步数、失败策略 | `release.sh.template` | 渲染后执行 | AI 配置流程，模板定义骨架 |
| `build-skillhub.sh` | 确认文件清单、验证结果 | `build-skillhub.sh.template` | 渲染后执行 | AI 确认清单，模板定义打包逻辑 |
| `check-structure.sh` | 配置检查项、区分警告/错误 | `check-structure.sh.template` | 渲染后执行 | AI 配置检查项，模板定义检查框架 |
| `check-size.sh` | 配置阈值、检查范围 | `check-size.sh.template` | 渲染后执行 | AI 配置阈值，模板定义检查框架 |
| `bump-version.sh` | 确认文件范围、提醒手动项 | `bump-version.sh.template` | 渲染后执行 | AI 确认范围，模板定义替换逻辑 |
| `sync-version.sh` | 确认同步文件、检测 CHANGELOG 状态 | `sync-version.sh.template` | 渲染后执行 | AI 确认文件，模板定义同步逻辑 |
| `.github/workflows/*.yml` | 选择工具链、配置矩阵 | CI/Release workflow 模板 | 渲染生成文件 | AI 配置工具，模板定义 workflow 结构 |
| `.clawhubignore` | 确认排除模式 | `.clawhubignore.template` | 渲染生成文件 | AI 确认模式，模板定义格式 |
| `.rules-cache.json` | 更新规则缓存、标注来源 | — | 读写 JSON 文件 | AI 更新内容，脚本读写文件 |

### 5.3 按能力维度分工

| 能力维度 | AI 控制 | 脚本模板 | 脚本执行 | 示例 |
|---------|--------|---------|---------|------|
| **理解** | ✅ 完全 AI | — | — | 理解项目类型、判断文件角色 |
| **推断** | ✅ 完全 AI | — | — | 推断必需文件、推断平台目标 |
| **决策** | ✅ 完全 AI | — | — | 选择发布策略、选择 fallback |
| **交互** | ✅ 完全 AI | — | — | 询问用户确认、解释选项 |
| **解释** | ✅ 完全 AI | — | — | 解释错误原因、提供修复建议 |
| **格式定义** | — | ✅ 模板 | — | 模板定义文件结构、变量占位 |
| **内容生成** | ✅ AI 填充变量 | — | — | AI 填充模板变量 |
| **渲染** | — | — | ✅ 脚本 | 模板引擎将变量替换为实际内容 |
| **确定性操作** | — | — | ✅ 脚本 | 复制文件、打 zip、执行 sed |
| **计算** | — | — | ✅ 脚本 | 计算行数、比较版本号、生成日期 |
| **验证** | AI 判断结果 | — | 脚本执行 | 脚本执行检查，AI 判断通过/失败/警告 |
| **缓存** | AI 更新策略 | — | 脚本读写 | 脚本读写 `.rules-cache.json` |

---

## 六、技能化后的交互示例

### 6.1 首次使用（全新项目）

```
用户：帮我准备这个项目的发布

AI（Skill 激活）：
  1. 扫描项目... 检测到：
     - 项目类型：代码工程型（含 .py 脚本）
     - 语言：中文（SKILL.md 含中文，系统 locale zh_CN）
     - 必需文件：SKILL.md, _meta.json, manifest.json, halucatch_core.py, halucatch/
     - 发布包文件：必需文件 + README.md + CHANGELOG.md
     - 排除文件：tests/, docs/, reports/, scripts/, .github/, .git/, *.zip
     - 平台目标：SkillHub, ClawHub, GitHub
     - Lint 工具：ruff（从 pyproject.toml 检测）
     - 测试框架：pytest（从 pyproject.toml 检测）

  2. 生成模板文件（渲染到 scripts/ 目录）...
     - release.sh ✓
     - build-skillhub.sh ✓
     - check-structure.sh ✓
     - check-size.sh ✓
     - bump-version.sh ✓
     - sync-version.sh ✓

  3. 当前版本：1.0.0。请问要发布什么版本？
     - 1.0.1 (patch) — 修复小 bug
     - 1.1.0 (minor) — 新增功能
     - 2.0.0 (major) — 重大变更
     - 自定义：___

  4. 建议先执行 dry-run 验证。是否继续？
     [ ] dry-run（推荐，先验证）
     [ ] 直接发布
     [ ] 查看生成的脚本再决定
```

### 6.2 常规发布（已有模板）

```
用户：发布新版本 1.2.3

AI（Skill 激活）：
  1. 读取现有模板和缓存... 模板已存在，规则缓存 3 天前更新
  2. 验证平台规则：
     - SkillHub CLI v1.2.3 ✓
     - ClawHub CLI v0.7.0 ⚠️ 已知 bug：acceptLicenseTerms 无效
       → 建议：Web-only 发布（或已手动接受 license）
  3. 执行 dry-run... 
     [Step 1] Bump version: 1.0.0 → 1.2.3 ✓
     [Step 2] Check structure: 5/5 passed ✓
     [Step 3] Check size: 3/4 passed, 1 warning ⚠️
              → SKILL.md: 420 行（超过 400 行阈值）
              → 建议：拆分为参考文档？
     [Step 4] Build: releases/HaluCatch-1.2.3-skillhub.zip (12KB) ✓
     [Step 5] Publish SkillHub: [DRY-RUN] 将执行 skillhub publish ...
     [Step 6] Publish ClawHub: [DRY-RUN] 将执行 clawhub publish ...
     [Step 7] Git: [DRY-RUN] 将执行 git commit + tag + push

  4. dry-run 完成。检测到 1 项警告。是否继续真实发布？
     [ ] 继续发布
     [ ] 修复 SKILL.md 尺寸后再发布
     [ ] 修改配置（跳过某平台、调整阈值）
```

### 6.3 错误处理（AI 诊断）

```
用户：发布失败了

AI（Skill 激活）：
  1. 读取最近发布日志... 找到最后执行记录
  2. 诊断：
     - Step 5 (SkillHub) 失败：错误 "File extension .sh not in allowlist"
     - 原因：SkillHub 扩展名白名单默认不包含 .sh 文件
     - 来源：SkillHub 安全策略（可覆盖 SKILLHUB_PUBLISH_ALLOWED_FILE_EXTENSIONS）
  3. 提供选项：
     [ ] 移除 .sh 文件从发布包（建议：scripts/ 已在排除列表，检查 manifest.json）
     [ ] 设置环境变量扩展白名单：export SKILLHUB_PUBLISH_ALLOWED_FILE_EXTENSIONS=...
     [ ] 改用 ClawHub 发布（不受扩展名限制）
     [ ] 查看详细日志
```

---

## 七、模板文件存放结构

```
skills/skill-publish-kit/                  # Skill 根目录
├── SKILL.md                               # Skill 指令（AI 控制层）
├── _meta.json                             # Skill 元数据
├── manifest.json                          # Skill 构建清单（自描述）
├── templates/                             # 脚本模板层
│   ├── SKILL.md.template                  # Skill 核心指令模板
│   ├── _meta.json.template                # 元数据模板
│   ├── manifest.json.template             # 构建清单模板
│   ├── release.sh.template               # 一键发布主控模板
│   ├── build-skillhub.sh.template        # SkillHub 包构建模板
│   ├── build-standalone.py.template      # 独立包构建模板（可选）
│   ├── check-structure.sh.template       # 结构检查模板
│   ├── check-size.sh.template            # 尺寸检查模板
│   ├── check-health.sh.template          # 发布健康度检查模板（新增）
│   ├── bump-version.sh.template          # 版本升级模板
│   ├── sync-version.sh.template          # 版本同步模板
│   ├── .clawhubignore.template            # ClawHub 排除模板
│   ├── .github/
│   │   ├── workflows/
│   │   │   ├── release.yml.template      # Release workflow 模板
│   │   │   └── ci.yml.template           # CI workflow 模板
│   └── pyproject.toml.template           # Python 项目配置模板（可选）
├── scripts/                               # Skill 自身的辅助脚本
│   ├── render-templates.py               # 模板渲染引擎
│   ├── discover-project.py               # 项目扫描脚本（AI 调用）
│   └── verify-rules.py                   # 平台规则验证脚本（AI 调用）
└── references/                            # 参考文档
    ├── platform-rules.md                  # 平台规则速查（内置）
    ├── template-variables.md              # 模板变量定义文档
    └── common-patterns.md                 # 常见发布模式
```

---

## 八、关键设计决策

### 决策 1：为什么用模板而非 AI 直接生成脚本？

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **AI 直接生成脚本** | 灵活，可适应任何项目 | 可能生成不一致的代码，难以维护 | 一次性任务 |
| **模板 + 变量** | 结构一致，可维护，可验证 | 需要预定义模板，适应性稍弱 | 标准化 Skill 发布（本方案） |
| **纯脚本硬编码** | 最可靠，无变化 | 不可定制，无法适应不同项目 | 固定项目 |

选择**模板 + 变量**的原因：
1. **一致性**：所有使用此 Skill 发布的项目，脚本结构相同，易于维护
2. **可验证**：模板可以预先验证（语法正确性），变量填充是安全的替换
3. **可升级**：平台规则变化时，只需更新模板，不用重新生成
4. **AI 负担减轻**：AI 只需填充变量，不用写完整脚本，降低出错率

### 决策 2：为什么 AI 不直接执行脚本？

AI 执行脚本 vs AI 生成脚本后用户执行：

| 维度 | AI 直接执行 | AI 生成后用户执行 | 本方案 |
|------|-----------|----------------|--------|
| 可控性 | 低（AI 可能误判） | 中（用户可审查） | 高（dry-run 先验证） |
| 安全性 | 低（可能误删/误发布） | 中 | 高（dry-run 不修改） |
| 透明度 | 低（用户不知道做了什么） | 中 | 高（每步输出明确） |
| 效率 | 高 | 中 | 高（dry-run 快速验证） |
| 错误恢复 | 难 | 中 | 中（临时目录原子操作） |

本方案：**AI 生成脚本 → dry-run 验证 → AI 展示结果 → 用户确认 → 执行**

### 决策 3：平台规则缓存策略

| 策略 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| 每次对话重新获取 | 最新 | 慢（每次调用 CLI） | 否 |
| 缓存 7 天 | 平衡 | 可能过时 | **是**（默认） |
| 缓存 30 天 | 快 | 可能过时 | 备选 |
| 永不缓存（硬编码） | 最快 | 必然过时 | 否 |

缓存策略：
- 默认 7 天
- 用户可强制刷新 `--refresh-rules`
- 发布失败时自动触发规则刷新（可能是规则变化导致）

---

## 九、执行顺序（Plan 的实施步骤）

### 步骤 1：编写模板文件（最优先）

将所有模板文件写入 `templates/` 目录，每个模板：
1. 包含完整的框架结构（固定部分）
2. 包含 `{{VARIABLE}}` 占位符（动态部分）
3. 包含注释说明每个变量的含义和默认值
4. 包含可配置区块（用 `## CONFIG_START` / `## CONFIG_END` 标注）

### 步骤 2：编写渲染引擎

`scripts/render-templates.py`：
1. 读取模板文件
2. 读取变量（从 AI 传入的 JSON 或配置文件）
3. 执行模板渲染（Python string.Template 或 Jinja2）
4. 设置脚本执行权限
5. 输出渲染后的文件清单

### 步骤 3：编写项目扫描脚本

`scripts/discover-project.py`：
1. 扫描项目目录
2. 检测文件类型、平台配置、lint 工具、测试框架
3. 输出 JSON 格式的项目扫描报告（供 AI 推断使用）

### 步骤 4：编写规则验证脚本

`scripts/verify-rules.py`：
1. 检测本地安装的 CLI 版本
2. 检查已知 bug 列表
3. 更新 `.rules-cache.json`
4. 输出规则验证报告（供 AI 决策使用）

### 步骤 5：编写 SKILL.md（AI 控制层）

`SKILL.md`：
1. 定义触发条件
2. 定义 AI 推断逻辑（Phase 0-8）
3. 定义与用户的交互模式（确认、选择、解释）
4. 定义错误诊断和修复建议
5. 定义模板渲染的调用方式

### 步骤 6：自验证（用 HaluCatch 测试）

1. 用此 Skill 重新生成 HaluCatch 的发布脚本
2. 对比现有脚本，验证功能等价性
3. 执行 dry-run，验证流程正确
4. 执行真实发布，验证各平台正常

### 步骤 7：迭代优化

根据使用反馈：
- 调整模板变量（添加/删除/改名）
- 调整 AI 推断逻辑（提升准确率）
- 调整规则缓存策略（平衡新鲜度和效率）
- 添加新平台支持（如新增 Skill 仓库）

---

*文档生成时间：2026-06-30*
*基础：skill-publish-analysis.md + platform-rules-sources.md*
