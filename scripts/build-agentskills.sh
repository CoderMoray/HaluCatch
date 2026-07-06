#!/usr/bin/env bash
# build-agentskills.sh — 构建并推送 agentskills 分支
#   分支内容是纯 skill 文件，不包含 docs/ tests/ scripts/ 等开发资源
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

VERSION=$(grep '^version:' "$ROOT/config.yaml" | sed 's/^version: *"//;s/"$//')
if [[ -z "$VERSION" ]]; then
  echo "❌ 无法从 config.yaml 读取版本号"
  exit 1
fi

BRANCH="agentskills"
DRY_RUN="${1:-}"

echo "📦 构建 $BRANCH v$VERSION..."

# 0) 确保 SKILL.md frontmatter 已同步
if [[ "$DRY_RUN" != "--dry-run" ]]; then
  bash "$ROOT/scripts/inject-frontmatter.sh"
fi

# 0.1) agentskills.sh 官方格式校验
if command -v skills-ref &>/dev/null; then
  echo "🔍 skills-ref validate..."
  skills-ref validate "$ROOT" || echo "⚠️  skills-ref validation failed (non-blocking)"
else
  echo "⚠️  skills-ref 未安装，跳过校验 (pip install skills-ref)"
fi

# 1) 创建临时目录，复制核心文件到 halucatch/ 子目录
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

SKILL_DIR="$TMP/halucatch"
mkdir -p "$SKILL_DIR"

cp "$ROOT/SKILL.md"          "$SKILL_DIR/"
cp "$ROOT/halucatch_core.py" "$SKILL_DIR/"
cp -r "$ROOT/halucatch"       "$SKILL_DIR/"
cp "$ROOT/README.md"          "$SKILL_DIR/"
cp "$ROOT/config.yaml"        "$SKILL_DIR/"
cp "$ROOT/manifest.json"      "$SKILL_DIR/"
cp "$ROOT/LICENSE"            "$SKILL_DIR/" 2>/dev/null || true

# docs 下只保留 FAQ 和 CHANGELOG
[[ -f "$ROOT/docs/CHANGELOG.md" ]] && cp "$ROOT/docs/CHANGELOG.md" "$SKILL_DIR/CHANGELOG.md"
[[ -f "$ROOT/docs/FAQ.md" ]]      && cp "$ROOT/docs/FAQ.md"      "$SKILL_DIR/FAQ.md"

# 清理 halucatch/reports
if [[ -d "$SKILL_DIR/halucatch/reports" ]]; then
  rm -rf "$SKILL_DIR/halucatch/reports"
fi

# 2) 推送到 agentskills 分支
if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "  [DRY-RUN] 将推送到 $BRANCH"
  echo "  [DRY-RUN] 文件列表:"
  ls -la "$SKILL_DIR"
  exit 0
fi

cd "$TMP"
git init -q
git checkout -b main
git config user.email "release-bot@halucatch.dev"
git config user.name "HaluCatch Release Bot"

cat > .gitignore << 'EOF'
__pycache__/
*.pyc
reports/
*.zip
.DS_Store
EOF

git add -A
git commit -m "agentskills v$VERSION" -q

REMOTE_URL=$(cd "$ROOT" && git remote get-url origin)

# CI 环境用 GITHUB_TOKEN 认证；本地用 SSH
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  REPO_PATH=$(echo "$REMOTE_URL" | sed 's|https://github.com/||')
  REMOTE_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${REPO_PATH}"
fi

git remote add origin "$REMOTE_URL"
git push origin main:"$BRANCH" --force -q

echo "✅ $BRANCH v$VERSION 已推送"
