#!/usr/bin/env bash
# release.sh — HaluCatch 一键发布脚本
# 使用 set -uo pipefail（不用 -e，手动处理错误）
set -uo pipefail

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "用法: $0 <X.Y.Z> [--skip-github] [--skip-clawhub] [--skip-skillhub] [--dry-run]"
  exit 1
fi

SKIP_GITHUB=false
SKIP_CLAWHUB=false
SKIP_SKILLHUB=false
DRY_RUN=false

for arg in "${@:2}"; do
  case "$arg" in
    --skip-github)   SKIP_GITHUB=true ;;
    --skip-clawhub)  SKIP_CLAWHUB=true ;;
    --skip-skillhub) SKIP_SKILLHUB=true ;;
    --dry-run)       DRY_RUN=true ;;
    *) echo "未知参数: $arg"; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$ROOT/scripts"

echo "🚀 HaluCatch 发布 v$VERSION"
[[ "$DRY_RUN" == "true" ]] && echo "⚠️  DRY-RUN 模式（不修改任何文件）"
echo ""

# ── 辅助函数：dry-run 感知执行 ────────────────────────────────────────
run() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "  [DRY-RUN] 将执行: $*"
  else
    eval "$@"
  fi
}

# ── Step 1: Bump Version ────────────────────────────────────────────
echo "[1/11] 升级版本号..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行: bump-version.sh $VERSION"
else
  bash "$SCRIPTS/bump-version.sh" "$VERSION"
fi

# ── Step 2: Inject Frontmatter ──────────────────────────────────────
echo "[2/11] 注入 frontmatter 到 SKILL.md..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行: inject-frontmatter.sh"
else
  bash "$SCRIPTS/inject-frontmatter.sh"
fi

# ── Step 3: Build Web ───────────────────────────────────────────────
echo "[3/11] 重新生成网站 docs/..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行: python3 web/build.py --all"
else
  # 优先用 venv Python（有 PyYAML），回退系统 python3
  WEB_PYTHON="python3"
  if command -v /Users/chrismoray/.workbuddy/binaries/python/envs/default/bin/python3 &>/dev/null; then
    WEB_PYTHON="/Users/chrismoray/.workbuddy/binaries/python/envs/default/bin/python3"
  fi
  if ! $WEB_PYTHON "$ROOT/web/build.py" --all; then
    echo "  ❌ web/build.py 执行失败，请先 pip install pyyaml"
    exit 1
  fi
  echo "  ✅ docs/ 已重新生成"
fi

# ── Step 4: Generate Changelog ──────────────────────────────────────
echo "[4/11] 自动生成 CHANGELOG..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行: generate-changelog.sh --write $VERSION"
else
  bash "$SCRIPTS/generate-changelog.sh" --write "$VERSION"
fi

# ── Step 5: Lint ────────────────────────────────────────────────────
echo "[5/11] 发布前自检..."
bash "$SCRIPTS/lint-paths.sh"

# ── Step 6: Check File Size ─────────────────────────────────────────
echo "[6/11] 文件尺寸检查..."
bash "$SCRIPTS/check-file-size.sh"

# ── Step 7: Build SkillHub Package ──────────────────────────────────
echo "[7/11] 构建 SkillHub 包..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行: build-skillhub.sh"
else
  bash "$SCRIPTS/build-skillhub.sh"
fi

ZIP_PATH="$ROOT/releases/HaluCatch-${VERSION}-skillhub.zip"
CLAWHUB_ZIP="$ROOT/releases/HaluCatch-${VERSION}-clawhub.zip"

# ── Step 8: Build ClawHub Package ─────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[8/11] DRY-RUN: 将构建 ClawHub 包"
elif [[ "$SKIP_CLAWHUB" == "false" ]]; then
  echo "[8/11] 构建 ClawHub 发布包..."
  bash "$SCRIPTS/build-clawhub.sh"
else
  echo "[8/11] 跳过 ClawHub 构建"
fi

# ── Step 9: Publish to SkillHub ─────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[9/11] DRY-RUN: 将发布到 SkillHub ($ZIP_PATH)"
elif [[ "$SKIP_SKILLHUB" == "false" ]]; then
  echo "[9/11] 发布到 SkillHub..."
  skillhub publish "$ZIP_PATH" || echo "⚠️  SkillHub 发布失败（可手动重试）"
else
  echo "[9/11] 跳过 SkillHub"
fi

# ── Step 10: Publish to ClawHub ──────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[10/11] DRY-RUN: 将发布到 ClawHub (halucatch@$VERSION)"
elif [[ "$SKIP_CLAWHUB" == "false" ]]; then
  echo "[10/11] 发布到 ClawHub..."
  TMP_CLAWHUB="/tmp/halucatch-publish"
  rm -rf "$TMP_CLAWHUB" && mkdir -p "$TMP_CLAWHUB"
  unzip -q "$CLAWHUB_ZIP" -d "$TMP_CLAWHUB"
  (cd "$TMP_CLAWHUB" && clawhub publish . --slug halucatch --name "HaluCatch / 捕幻" --version "$VERSION") || echo "⚠️  ClawHub 发布失败（可手动重试）"
  rm -rf "$TMP_CLAWHUB"
else
  echo "[10/11] 跳过 ClawHub"
fi

# ── Step 11: Git Commit + Tag + Push ─────────────────────────────────
echo "[11/11] Git 提交 + Tag + Push..."

# 检查 tag 是否已存在
TAG_EXISTS=false
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
  echo "  ⚠️  tag v$VERSION 已存在，将跳过打 tag"
  TAG_EXISTS=true
fi

if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行 git 操作（commit + tag + push）"

elif [[ "$SKIP_GITHUB" == "false" ]]; then
  # 检查是否有未提交的改动
  if [[ -n $(git status --porcelain) ]]; then
    echo "  检测到未提交改动，执行 commit..."

    # 从 CHANGELOG.md 提取最新版本条目作为 commit body
    COMMIT_MSG="release: v$VERSION"
    if [[ -f "$ROOT/docs/CHANGELOG.md" ]]; then
      CHANGELOG_BODY=$(sed -n "/^## \[V$VERSION\]/,/^---/p" "$ROOT/docs/CHANGELOG.md" | sed '1d;$d' | sed '/^$/d')
      if [[ -n "$CHANGELOG_BODY" ]]; then
        COMMIT_MSG="$COMMIT_MSG"$'\n\n'"$CHANGELOG_BODY"
      fi
    fi

    git add -A
    git commit -m "$COMMIT_MSG"
    echo "  ✅ 已提交"
  else
    echo "  工作区干净，跳过 commit"
  fi

  # 打 tag（如果不存在）
  if [[ "$TAG_EXISTS" == "false" ]]; then
    git tag "v$VERSION"
    echo "  ✅ 已打 tag v$VERSION"
  fi

  # 推送
  echo "  推送到 GitHub..."
  git push origin main
  if [[ "$TAG_EXISTS" == "false" ]]; then
    git push origin "v$VERSION"
  fi
  echo "  ✅ 已推送，GitHub Actions 将自动创建 Release"

else
  # --skip-github 模式：本地 commit + tag，不 push
  if [[ -n $(git status --porcelain) ]]; then
    git add -A
    git commit -m "release: v$VERSION"
    echo "  ✅ 已提交（本地）"
  else
    echo "  工作区干净，跳过 commit"
  fi
  if [[ "$TAG_EXISTS" == "false" ]]; then
    git tag "v$VERSION"
    echo "  ✅ 已打 tag v$VERSION（本地）"
  fi
  echo "  ⚠️  跳过 git push（需手动: git push origin v$VERSION && git push origin main）"
fi

echo ""
echo "✅ HaluCatch v$VERSION 发布完成"

# ── AI 提醒：mcpmarket / agentskills 用同一个分支 ───────────────────
if [[ "$DRY_RUN" != "true" ]]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🤖 AI ACTION REQUIRED — 告诉用户:"
  echo ""
  echo "   发布完成！手动操作："
  echo "   1. mcpmarket → https://app.mcpmarket.com/<用户名>/skills"
  echo "   2. agentskills.sh → https://agentskill.sh/submit"
  echo ""
  echo "   两个平台都填:"
  echo "   https://github.com/CoderMoray/HaluCatch/tree/agentskills/halucatch"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi
