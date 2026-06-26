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
echo "[1/7] 升级版本号..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行: bump-version.sh $VERSION"
else
  bash "$SCRIPTS/bump-version.sh" "$VERSION"
fi

# ── Step 2: Lint ────────────────────────────────────────────────────
echo "[2/7] 发布前自检..."
bash "$SCRIPTS/lint-paths.sh"

# ── Step 3: Build SkillHub Package ──────────────────────────────────
echo "[3/7] 构建 SkillHub 包..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  [DRY-RUN] 将执行: build-skillhub.sh"
else
  bash "$SCRIPTS/build-skillhub.sh"
fi

# ── Step 4: Check File Size ─────────────────────────────────────────
echo "[4/7] 文件尺寸检查..."
bash "$SCRIPTS/check-file-size.sh"

ZIP_PATH="$ROOT/releases/HaluCatch-${VERSION}-skillhub.zip"

# ── Step 5: Publish to SkillHub ─────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[5/7] DRY-RUN: 将发布到 SkillHub ($ZIP_PATH)"
elif [[ "$SKIP_SKILLHUB" == "false" ]]; then
  echo "[5/7] 发布到 SkillHub..."
  skillhub publish "$ZIP_PATH" || echo "⚠️  SkillHub 发布失败（可手动重试）"
else
  echo "[5/7] 跳过 SkillHub"
fi

# ── Step 6: Publish to ClawHub ──────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[6/7] DRY-RUN: 将发布到 ClawHub (halucatch@$VERSION)"
elif [[ "$SKIP_CLAWHUB" == "false" ]]; then
  echo "[6/7] 发布到 ClawHub..."
  (cd "$ROOT" && clawhub publish . --version "$VERSION") || echo "⚠️  ClawHub 发布失败（可手动重试）"
else
  echo "[6/7] 跳过 ClawHub"
fi

# ── Step 7: Git Commit + Tag + Push ──────────────────────────────────
echo "[7/7] Git 提交 + Tag + Push..."

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
    git add -A
    git commit -m "release: v$VERSION"
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
