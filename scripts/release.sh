#!/usr/bin/env bash
# release.sh — HaluCatch 一键发布脚本 (12 步)
# 严格模式：任何未捕获的错误都会立即中止，禁止静默失败
set -euo pipefail

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

fail() {
  echo "❌ $1" >&2
  exit 1
}

echo "🚀 HaluCatch 发布 v$VERSION"
[[ "$DRY_RUN" == "true" ]] && echo "⚠️  DRY-RUN 模式（不修改任何文件）"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Steps 1-3: 构建产物（bump / frontmatter / docs）
# ═══════════════════════════════════════════════════════════════════

# ── Step 1: Bump Version ──────────────────────────────────────
echo "[1/12] 升级版本号..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行: bump-version.sh $VERSION"
else
  bash "$SCRIPTS/bump-version.sh" "$VERSION" || fail "bump-version.sh 执行失败"
fi

# ── Step 2: Inject Frontmatter ────────────────────────────────
echo "[2/12] 注入 frontmatter 到 SKILL.md..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行: inject-frontmatter.sh"
else
  bash "$SCRIPTS/inject-frontmatter.sh" || fail "inject-frontmatter.sh 执行失败"
fi

# ── Step 3: Build Web ─────────────────────────────────────────
echo "[3/12] 重新生成网站 docs/..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行: python3 web/build.py --all"
else
  WEB_PYTHON="python3"
  if command -v /Users/chrismoray/.workbuddy/binaries/python/envs/default/bin/python3 &>/dev/null; then
    WEB_PYTHON="/Users/chrismoray/.workbuddy/binaries/python/envs/default/bin/python3"
  fi
  $WEB_PYTHON "$ROOT/web/build.py" --all || fail "web/build.py 执行失败"
  $WEB_PYTHON "$ROOT/web/build_faq.py" --all || fail "web/build_faq.py 执行失败"
  echo "  ✅ docs/ 已重新生成"
fi

# ═══════════════════════════════════════════════════════════════════
# Steps 4-8: 质量检查 + Git + CHANGELOG
#   commit 先于 CHANGELOG → tag 存在 → hash 直接从 tag 拿
# ═══════════════════════════════════════════════════════════════════

# ── Step 4: Lint ──────────────────────────────────────────────
echo "[4/12] 发布前自检..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] lint-paths.sh --strict"
else
  bash "$SCRIPTS/lint-paths.sh" --strict || fail "lint-paths.sh 自检失败"
fi

# ── Step 5: Check File Size ───────────────────────────────────
echo "[5/12] 文件尺寸检查..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] check-file-size.sh"
else
  bash "$SCRIPTS/check-file-size.sh" || fail "check-file-size.sh 执行失败"
fi

# ── Step 6: Git Commit (bump + docs only) ─────────────────────
echo "[6/12] Git 提交（仅 bump + docs）..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] git commit"
elif [[ "$SKIP_GITHUB" == "false" ]]; then
  if [[ -n $(git status --porcelain) ]]; then
    git add -A || fail "git add 失败"
    git commit -m "release: v$VERSION (bump + docs)" || fail "git commit 失败"
    echo "  ✅ 已提交"
  else
    echo "  工作区干净，跳过"
  fi
else
  echo "  跳过"
fi

# ── Step 7: Generate Changelog ────────────────────────────────
echo "[7/12] 自动生成 CHANGELOG..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] generate-changelog.sh --write $VERSION"
else
  bash "$SCRIPTS/generate-changelog.sh" --write "$VERSION" \
    || fail "generate-changelog.sh 执行失败（发布中止）"
fi

# ── Step 8: Amend + Tag + Push ────────────────────────────────
echo "[8/12] 补 CHANGELOG + 打 tag + 推送..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] amend + tag v$VERSION + push"
elif [[ "$SKIP_GITHUB" == "false" ]]; then
  if [[ -n $(git status --porcelain) ]]; then
    git add -A || fail "git add 失败"
    git commit --amend -m "release: v$VERSION" --no-edit || fail "git commit --amend 失败"
    echo "  ✅ 已 amend（含 CHANGELOG）"
  fi
  if git rev-parse "v$VERSION" >/dev/null 2>&1; then
    echo "  ⚠️  tag v$VERSION 已存在，跳过"
  else
    git tag "v$VERSION" || fail "git tag 失败"
    echo "  ✅ 已打 tag v$VERSION"
  fi
  echo "  推送到 GitHub..."
  git push --follow-tags || fail "git push 失败"
  echo "  ✅ 已推送"
else
  echo "  跳过"
fi

# ═══════════════════════════════════════════════════════════════════
# Steps 9-12: 打包 + 发布平台
# ═══════════════════════════════════════════════════════════════════

ZIP_PATH="$ROOT/releases/HaluCatch-${VERSION}-skillhub.zip"
CLAWHUB_ZIP="$ROOT/releases/HaluCatch-${VERSION}-clawhub.zip"

# ── Step 9: Build SkillHub ────────────────────────────────────
echo "[9/12] 构建 SkillHub 包..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] build-skillhub.sh"
else
  bash "$SCRIPTS/build-skillhub.sh" || fail "build-skillhub.sh 执行失败"
fi

# ── Step 10: Build ClawHub ──────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[10/12] DRY-RUN: build-clawhub.sh"
elif [[ "$SKIP_CLAWHUB" == "false" ]]; then
  echo "[10/12] 构建 ClawHub 发布包..."
  bash "$SCRIPTS/build-clawhub.sh" || fail "build-clawhub.sh 执行失败"
else
  echo "[10/12] 跳过 ClawHub 构建"
fi

# ── Step 11: Publish SkillHub ─────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[11/12] DRY-RUN: skillhub publish"
elif [[ "$SKIP_SKILLHUB" == "false" ]]; then
  echo "[11/12] 发布到 SkillHub..."
  [[ -f "$ZIP_PATH" ]] || fail "Zip 不存在: $ZIP_PATH"
  skillhub publish "$ZIP_PATH" || fail "SkillHub 发布失败"
else
  echo "[11/12] 跳过 SkillHub"
fi

# ── Step 12: Publish ClawHub ──────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[12/12] DRY-RUN: clawhub publish halucatch@$VERSION"
elif [[ "$SKIP_CLAWHUB" == "false" ]]; then
  echo "[12/12] 发布到 ClawHub..."
  [[ -f "$CLAWHUB_ZIP" ]] || fail "Zip 不存在: $CLAWHUB_ZIP"
  TMP_CLAWHUB="/tmp/halucatch-publish"
  rm -rf "$TMP_CLAWHUB" && mkdir -p "$TMP_CLAWHUB"
  unzip -q "$CLAWHUB_ZIP" -d "$TMP_CLAWHUB"
  (cd "$TMP_CLAWHUB" && clawhub publish . --slug halucatch --name "HaluCatch / 捕幻" --version "$VERSION") \
    || fail "ClawHub 发布失败"
  rm -rf "$TMP_CLAWHUB"
else
  echo "[12/12] 跳过 ClawHub"
fi

echo ""
echo "✅ HaluCatch v$VERSION 发布完成"
