# Skill 发布平台规则来源与动态获取机制 — 补充分析

> 基于 kimi_search_v2 搜索结果，补充各平台规则限制的具体来源、版本变化、以及 AI 获取最新规则的机制设计。

---

## 一、平台规则总览与来源

### 1. SkillHub（自托管 Registry / 开源）

| 规则 | 具体内容 | 来源 | 变化风险 |
|------|---------|------|---------|
| **SKILL.md 必需** | 发布包必须包含 `SKILL.md` | [SkillHub 发布指南](https://iflytek.github.io/skillhub/guide/skill-publish.html) | 低 |
| **YAML frontmatter** | `SKILL.md` 需包含 `name`, `description`, `version`, `category`, `platforms` 等元数据 | [SkillHub 发布指南](https://cloud.tencent.com/developer/techpedia/2618/20637) | 低 |
| **CLI 命令** | `skillhub publish <path> --namespace <ns>` 或 `skillhub publish <zip>` | [SkillHub CLI 文档](https://github.com/iflytek/skillhub/blob/main/docs/skillhub/en/guide/cli.md) | 中（v2 可能改命令格式） |
| **zip 支持** | 支持直接发布 `.zip` 文件或目录（自动打包） | [SkillHub CLI 文档](https://github.com/iflytek/skillhub/blob/main/docs/skillhub/en/guide/cli.md) | 低 |
| **Visibility 选项** | `public` (默认) / `namespace-only` / `private` | [SkillHub CLI 文档](https://github.com/iflytek/skillhub/blob/main/docs/skillhub/en/guide/cli.md) | 中 |
| **文件扩展名白名单** | 默认只允许 `.md`, `.json`, `.xsd`, `.xsl`, `.dtd`, `.docx`, `.xlsx`, `.pptx` 等；可覆盖 `SKILLHUB_PUBLISH_ALLOWED_FILE_EXTENSIONS` | [SkillHub 源码](https://github.com/iflytek/skillhub) | **高**（可配置，但默认白名单可能变化） |
| **安全扫描** | 发布后自动扫描安全风险 | [SkillHub 发布指南](https://iflytek.github.io/skillhub/guide/skill-publish.html) | 中 |
| **审核机制** | 如命名空间开启审核，需管理员通过后发布 | [SkillHub 发布指南](https://iflytek.github.io/skillhub/guide/skill-publish.html) | 中 |
| **命名空间坐标** | `@global/my-skill` → 对应 `clawhub` 的 `my-skill`；`@team-name/my-skill` → `team-name--my-skill` | [SkillHub Registry Skill](https://github.com/iflytek/skillhub/blob/main/web/src/docs/skill.md) | 高（坐标映射规则可能变化） |
| **Package Contract** | 期望 OpenSkills-style 包，`SKILL.md` 为入口点 | [SkillHub Registry Skill](https://github.com/iflytek/skillhub/blob/main/web/src/docs/skill.md) | 低 |
| **Skills 替代** | `package.json` 或 `skillhub.skill.yaml` 可用于定义技能结构（多目标输出） | [cloudvalley-tech/skillhub](https://github.com/cloudvalley-tech/skillhub) | **高**（新生态可能在演进） |

**关键发现**：SkillHub 是一个**开源项目**（`iflytek/skillhub`），有自托管能力。它的 CLI 和 registry 都在 GitHub 上公开维护，这意味着规则变化可以通过关注 repo 的 release 和 PR 来跟踪。但不同部署实例（self-hosted）可能有自定义规则（如扩展名白名单）。

**风险**：`skills.json` 作为新的 package manifest 格式正在提出（[agentskills/agentskills Discussion #210](https://github.com/agentskills/agentskills/discussions/210)），未来可能替代或补充 `SKILL.md` 的发布方式。

---

### 2. ClawHub（OpenClaw 的官方 Registry）

| 规则 | 具体内容 | 来源 | 变化风险 |
|------|---------|------|---------|
| **SKILL.md 必需** | 发布包必须包含 `SKILL.md` | [ClawHub Publish Skill](https://clawhub.ai/skills/clawhub-publish-mai) | 低 |
| **CLI 命令** | `clawhub publish <path> --version <X.Y.Z>` | [ClawHub 官方](https://clawhub.ai/skills/clawhub-publish-mai), [OpenClaw clawhub repo](https://github.com/openclaw/clawhub) | 中 |
| **CLI 额外参数** | `--slug`, `--name`, `--version`, `--changelog` | [ClawHub 发布 Skill](https://clawhub.ai/jini92/clawhub-publish-mai) | 中 |
| **Slug 规则** | 全小写，仅 hyphens，全局唯一 | [ClawHub 发布 Skill](https://clawhub.ai/jini92/clawhub-publish-mai) | 低 |
| **License 强制** | 所有技能默认 **MIT-0** 发布；CLI v0.7.0 需发送 `acceptLicenseTerms: true`，但 CLI 未实现此 flag，导致发布阻塞 | [GitHub Issue #43774](https://github.com/openclaw/openclaw/issues/43774), [GitHub Issue #660](https://github.com/openclaw/clawhub/issues/660), [GitHub Issue #641](https://github.com/openclaw/clawhub/issues/641) | **高**（CLI 版本兼容性 bug） |
| **Web 发布替代** | 如果 CLI 不可用，可通过 https://clawhub.ai/upload 手动上传文件夹 | [ClawHub Web-Only Publish](https://lobehub.com/skills/openclaw-skills-clawhub-web-only-publish) | 中 |
| **软删除/恢复** | 技能使用软删除（`clawhub delete <skill>` / `clawhub undelete <skill>`），硬删除仅管理员 | [OpenClaw clawhub repo](https://github.com/openclaw/clawhub) | 低 |
| **Owner 合并/重命名** | 重命名保持旧 slug 为别名；合并后隐藏源 listing 并重定向 | [OpenClaw clawhub repo](https://github.com/openclaw/clawhub) | 中 |
| **ClawHub CLI 版本** | v0.7.0（npm 最新），已知 `acceptLicenseTerms` bug | [GitHub Issues](https://github.com/openclaw/clawhub/issues/660) | **高**（CLI 版本迭代） |
| **代码插件额外要求** | 代码插件 manifest 需包含 `openclaw.compat.pluginApi` 和 `openclaw.build.openclawVersion` | [OpenClaw clawhub repo](https://github.com/openclaw/clawhub) | **高**（平台特化） |

**关键发现**：
- ClawHub CLI 有**已知的 bug**：`acceptLicenseTerms: invalid value` 阻塞所有 CLI 发布（2026-03 报告）。Workaround 是先通过 Web 端接受 license，或者使用 Web-only 发布方式。
- 这意味着发布脚本必须**检测 CLI 版本和已知 bug**，并准备 fallback（Web 发布）。
- 搜索结果显示 ClawHub 有 `clawhub whoami`（验证登录）、`clawhub login`（认证）等命令，且支持 `--device` 远程认证。

**风险**：CLI 版本迭代可能导致命令格式变化。`acceptLicenseTerms` 的问题在后续版本可能修复，但当前版本可能仍被用户使用。

---

### 3. GitHub Actions（CI/CD 发布）

| 规则 | 具体内容 | 来源 | 变化风险 |
|------|---------|------|---------|
| **触发条件** | `on: push: tags: - 'v*'` 或 `on: push: branches: [main]` | [GitHub Actions Workflow Syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions) | 低 |
| **Release 权限** | `permissions: contents: write` 必须授予才能创建 release 和 tag | [GitHub Actions Permissions](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions#permissions) | 中 |
| **Permissions 模型** | 2026-01-13 新增 `artifact-metadata` 权限，替代 `contents:read/write` 用于 artifact 元数据 API；`contents: write` 仍用于创建 release | [GitHub Blog Changelog](https://github.blog/changelog/2026-01-13-new-fine-grained-permission-for-artifact-metadata-is-now-generally-available/) | **高**（权限粒度在演进） |
| **Release 创建** | 使用 `softprops/action-gh-release@v2` 或 `actions/create-release` | [GitHub Actions Marketplace](https://github.com/softprops/action-gh-release) | 中（action 版本可能更新） |
| **Release 附件** | 通过 `files:` 字段指定文件路径，支持 glob 匹配 | [GitHub Actions Workflow Syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions) | 低 |
| **Artifact 大小限制** | 单个 artifact 最大 2GB（默认），zip 包最大 5GB | [GitHub Actions Docs](https://docs.github.com/en/actions/managing-workflow-runs/downloading-workflow-artifacts) | 低 |
| **Token 权限** | `GITHUB_TOKEN` 默认权限取决于仓库设置；可改为 `permissions: write-all` 或细粒度控制 | [GitHub Actions Permissions](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions#permissions) | 中 |
| **Fine-grained 权限** | 2026 年新增 `artifact-metadata`, `attestations`, `code-quality`, `models` 等权限；`contents: write` 创建 release 的权限较宽泛 | [GitHub Blog Changelog](https://github.blog/changelog/2026-01-13-new-fine-grained-permission-for-artifact-metadata-is-now-generally-available/) | **高**（权限体系在演进） |

**关键发现**：
- GitHub Actions 的 permissions 体系在 2026 年有重大变化，新增了 `artifact-metadata` 权限，但 `contents: write` 仍然是创建 release 的必需权限。
- 社区有讨论要求更细粒度的 `releases: write` 权限（而非宽泛的 `contents: write`），但 GitHub 尚未实现。
- `artifact-metadata` 的权限分离意味着发布脚本需要考虑 Actions 版本和权限兼容性。

**风险**：GitHub Actions 的权限模型在快速演进，2026 年的配置到 2027 年可能需要更新。`artifact-metadata` 的引入和 `contents: write` 的存续状态需要持续关注。

---

### 4. Git（版本控制）

| 规则 | 具体内容 | 来源 | 变化风险 |
|------|---------|------|---------|
| **Tag 格式** | 语义化标签 `vX.Y.Z`（Git 本身不强制，但 Actions 触发约定） | Git 文档 + GitHub Actions 触发约定 | 低 |
| **Tag 存在性检查** | `git rev-parse vX.Y.Z` 检测 tag 是否存在 | Git CLI | 无（Git 稳定） |
| **未提交改动** | `git status --porcelain` 检测工作区状态 | Git CLI | 无 |
| **Commit 信息** | 无强制格式，但项目通常约定（如 `release: vX.Y.Z`） | 项目自定义 | 低 |
| **Push 策略** | `git push origin main` + `git push origin vX.Y.Z` | Git CLI | 无 |

**Git 本身无变化风险**，但项目可能使用 Git 的不同工作流（如 squash merge、rebase 等）。

---

## 二、规则变化风险分级

| 风险级别 | 规则 | 变化原因 | 影响 |
|---------|------|---------|------|
| **🔴 高** | `artifact-metadata` 权限替代 `contents: write` | GitHub Actions 演进 | 发布 Actions 可能失效 |
| **🔴 高** | `acceptLicenseTerms` bug / CLI 版本 | ClawHub CLI 迭代 | 发布完全阻塞 |
| **🔴 高** | `skills.json` 新 manifest 格式 | 生态演进（agentskills Discussion #210） | 可能替代 `SKILL.md` 发布方式 |
| **🟠 中** | SkillHub 扩展名白名单 | 安全策略调整 | 发布文件被拒 |
| **🟠 中** | ClawHub CLI 命令格式 | 版本迭代 | 脚本命令失效 |
| **🟠 中** | SkillHub 坐标映射规则（`@ns/skill` → `ns--skill`） | 兼容性层演进 | 安装/发布引用混乱 |
| **🟠 中** | 代码插件 manifest 要求（`openclaw.compat.pluginApi`） | 平台能力扩展 | 代码插件发布失败 |
| **🟡 低** | SKILL.md 格式要求 | 标准稳定 | 格式基本不变 |
| **🟡 低** | 版本号语义（SemVer） | 标准稳定 | 无变化 |
| **🟢 极低** | Git 基本操作 | 工具稳定 | 无变化 |

---

## 三、AI 获取最新规则的机制设计

### 设计目标

Skill 使用者（AI agent）需要：
1. **获取最新规则** — 而非依赖硬编码的过时规则
2. **检测版本兼容性** — 当前工具版本是否支持最新规则
3. **fallback 处理** — 当规则变化或工具 bug 时自动切换方案

### 三层规则获取架构

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: 动态获取（Run-time）                                   │
│  - 查询平台 API / CLI 帮助文档                                  │
│  - 检查 GitHub repo 最新 release 和 changelog                   │
│  - 在对话中提醒用户确认规则变化                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: 缓存规则（Session-level）                             │
│  - 在对话开始时 fetch 平台最新规则（1次/对话）                   │
│  - 缓存到 session context（skill memory）                       │
│  - 标记上次获取时间，超时后重新获取                               │
└─────────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: 基础规则（Built-in）                                  │
│  - SKILL.md 中包含「最小可用规则集」                              │
│  - 标注版本号和来源                                             │
│  - 包含 fallback 机制（当无法获取最新规则时）                   │
└─────────────────────────────────────────────────────────────────┘
```

### 具体机制

#### 机制 A：内置规则 + 版本标注（Layer 1）

在 `SKILL.md` 中嵌入规则，但明确标注来源和版本：

```markdown
## 平台规则速查（内置规则，定期验证）

> ⚠️ 规则可能变化。以下规则基于 **SkillHub CLI v1.x**（2026-06）和 **ClawHub CLI v0.7.0**（2026-06）的最新稳定版本。
> 来源：[SkillHub CLI 文档](https://github.com/iflytek/skillhub/tree/main/docs) | [ClawHub CLI 文档](https://github.com/openclaw/clawhub/tree/main/docs)

### 当前已知限制

- **ClawHub CLI v0.7.0**: `acceptLicenseTerms` 字段未正确发送，导致发布阻塞。Workaround：先通过 Web 端接受 license，或使用 Web-only 发布。
  - 来源：[GitHub Issue #660](https://github.com/openclaw/clawhub/issues/660)
  - 检测：运行 `clawhub --version` 确认版本

- **GitHub Actions permissions (2026-01)**: `artifact-metadata` 新权限已推出，但 `contents: write` 仍是创建 release 的必需权限。
  - 来源：[GitHub Blog Changelog](https://github.blog/changelog/2026-01-13-new-fine-grained-permission-for-artifact-metadata-is-now-generally-available/)
  - 检测：检查 `.github/workflows/release.yml` 中的 `permissions` 字段

### 规则获取 fallback

如果无法获取最新规则，遵循以下保守策略：
1. 使用最通用的命令格式（如 `clawhub publish <path> --version X.Y.Z`）
2. 添加 `--dry-run` 先验证
3. 失败时提供 Web 发布作为 fallback
```

#### 机制 B：Session 开始时动态验证（Layer 2）

AI 在首次使用 Skill 时执行一次规则验证：

```bash
# 验证 SkillHub CLI 版本和可用性
skillhub --version 2>/dev/null || echo "SkillHub CLI 未安装"
# 检查是否有 --namespace 等新参数
skillhub publish --help 2>/dev/null | grep -A2 "namespace"

# 验证 ClawHub CLI 版本和已知 bug
clawhub --version 2>/dev/null || echo "ClawHub CLI 未安装"
# 检查 acceptLicenseTerms 相关参数
clawhub publish --help 2>/dev/null | grep -i "accept\|license"

# 验证 GitHub Actions 最新权限要求
# 通过 GitHub API 或本地缓存获取最新 permissions 文档
```

AI 根据验证结果动态调整：
- 如果 ClawHub CLI 是 v0.7.0 且未修复 bug → 自动推荐 Web-only 发布
- 如果检测到新参数（如 `--accept-license-terms`）→ 使用新参数
- 如果检测到权限变化 → 提醒更新 `.github/workflows/release.yml`

#### 机制 C：对话中用户确认（Layer 3）

当 AI 检测到规则可能变化时：

```
AI 检测到可能影响发布的规则变化：
1. 您的 ClawHub CLI 版本为 v0.7.0，已知 bug 可能导致发布阻塞
2. GitHub Actions 在 2026-01 更新了权限模型

请确认：
- 是否已手动接受 ClawHub license（通过 Web 端）？
- 是否需要更新 `.github/workflows/release.yml` 的 permissions 字段？
```

#### 机制 D：rules-cache 文件（本地缓存）

在项目目录下维护一个 `.rules-cache.json`：

```json
{
  "version": "1.0.0",
  "last_updated": "2026-06-30T10:00:00Z",
  "platforms": {
    "skillhub": {
      "cli_version_detected": "1.2.3",
      "publish_command": "skillhub publish <path> --namespace <ns>",
      "required_files": ["SKILL.md"],
      "known_issues": [],
      "source": "https://github.com/iflytek/skillhub"
    },
    "clawhub": {
      "cli_version_detected": "0.7.0",
      "publish_command": "clawhub publish <path> --version <X.Y.Z>",
      "required_files": ["SKILL.md"],
      "known_issues": [
        {
          "id": "acceptLicenseTerms",
          "severity": "blocking",
          "workaround": "web-only-publish"
        }
      ],
      "source": "https://github.com/openclaw/clawhub"
    },
    "github_actions": {
      "permissions": "contents: write",
      "release_action": "softprops/action-gh-release@v2",
      "known_changes": [
        {
          "date": "2026-01-13",
          "change": "artifact-metadata permission introduced",
          "impact": "low for release workflows"
        }
      ],
      "source": "https://docs.github.com/actions"
    }
  }
}
```

这个文件由 AI 在首次运行时生成，后续对话中复用。当用户运行发布时，AI 检查缓存时间，如果超过 7 天则重新验证。

---

## 四、规则变化应对策略表

| 规则变化 | 检测方式 | 自动应对 | 需要用户确认 |
|---------|---------|---------|------------|
| ClawHub CLI 新 bug | `clawhub --version` + 已知 issue 列表 | 自动切换 Web-only 发布 | 是（告知用户） |
| ClawHub CLI 修复 bug | `clawhub publish --help` 查看新参数 | 自动使用 CLI 发布 | 否 |
| SkillHub CLI 新增参数 | `skillhub --help` 解析 | 自动使用新参数 | 否 |
| GitHub Actions 权限变化 | 检查 `permissions:` 字段是否匹配 | 提醒更新 workflow 文件 | 是（提供修改建议） |
| 文件扩展名白名单变化 | 发布失败时的错误信息 | 自动调整打包文件 | 是（告知哪些文件被排除） |
| `skills.json` 新格式 | 检测项目中的 `skills.json` 或 `skillhub.skill.yaml` | 提醒新格式可用 | 是（是否迁移） |
| 版本号语义变化 | 平台文档 | 遵循新语义 | 是（告知变化） |

---

## 五、已收集的来源链接汇总

| 平台 | 文档/来源 | URL | 类型 |
|------|----------|-----|------|
| SkillHub | 发布指南（iflytek） | https://iflytek.github.io/skillhub/guide/skill-publish.html | 官方文档 |
| SkillHub | CLI 文档（GitHub） | https://github.com/iflytek/skillhub/blob/main/docs/skillhub/en/guide/cli.md | 源码文档 |
| SkillHub | Registry Skill | https://github.com/iflytek/skillhub/blob/main/web/src/docs/skill.md | 源码文档 |
| SkillHub | 技能包规范（腾讯云） | https://cloud.tencent.com/developer/techpedia/2618/20637 | 第三方汇总 |
| SkillHub | 项目配置（cloudvalley） | https://github.com/cloudvalley-tech/skillhub | 第三方扩展 |
| SkillHub | skills.json RFC | https://github.com/agentskills/agentskills/discussions/210 | 社区 RFC |
| ClawHub | 官方发布 Skill | https://clawhub.ai/skills/clawhub-publish-mai | 平台 Skill |
| ClawHub | 发布 Skill（jini92） | https://clawhub.ai/jini92/clawhub-publish-mai | 社区 Skill |
| ClawHub | Web-only 发布 | https://lobehub.com/skills/openclaw-skills-clawhub-web-only-publish | 社区 Skill |
| ClawHub | 开源仓库 | https://github.com/openclaw/clawhub | 源码 |
| ClawHub | CLI bug (acceptLicenseTerms) | https://github.com/openclaw/openclaw/issues/43774 | GitHub Issue |
| ClawHub | CLI bug (acceptLicenseTerms) | https://github.com/openclaw/clawhub/issues/660 | GitHub Issue |
| ClawHub | CLI bug (acceptLicenseTerms) | https://github.com/openclaw/clawhub/issues/641 | GitHub Issue |
| GitHub Actions | Workflow 语法 | https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions | 官方文档 |
| GitHub Actions | Permissions | https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions#permissions | 官方文档 |
| GitHub Actions | artifact-metadata 变更 | https://github.blog/changelog/2026-01-13-new-fine-grained-permission-for-artifact-metadata-is-now-generally-available/ | 官方 Blog |
| GitHub | 创建 release 权限讨论 | https://github.com/orgs/community/discussions/68252 | 社区讨论 |
| GitHub | tag 权限问题 | https://github.com/orgs/community/discussions/116660 | 社区讨论 |

---

*文档生成时间：2026-06-30*
*数据来源：kimi_search_v2 实时搜索 + 已有项目文件分析*
