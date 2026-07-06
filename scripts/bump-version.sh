#!/usr/bin/env bash
# bump-version.sh — HaluCatch 版本号升级
set -euo pipefail

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "用法: $0 X.Y.Z"
  echo "  更新 config.yaml 和 docs/index.html 的版本号"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 1) config.yaml version
sed -i '' "s/^version: \".*\"/version: \"$VERSION\"/" "$ROOT/config.yaml" && echo "✅ config.yaml → $VERSION"

# 2) docs/index.html 版本号变量（唯一源头）
INDEX_HTML="$ROOT/docs/index.html"
# 完整版本 HC_VER
sed -i '' "s/var HC_VER = '[0-9.]*'/var HC_VER = '$VERSION'/" "$INDEX_HTML"
# 简短版本 HC_VER_SHORT（取前两段）
SHORT=$(echo "$VERSION" | sed 's/\.[0-9]*$//')
sed -i '' "s/var HC_VER_SHORT = '[0-9.]*'/var HC_VER_SHORT = '$SHORT'/" "$INDEX_HTML"
echo "✅ docs/index.html → $VERSION (short: $SHORT)"

# 3) Changelog 由 generate-changelog.sh 自动处理（release.sh Step 2）
echo ""
echo "✅ 版本号已更新。CHANGELOG 将在 release.sh 中自动生成。"
echo "ℹ️  构建前请运行 inject-frontmatter.sh 同步 SKILL.md"
