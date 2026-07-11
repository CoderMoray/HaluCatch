#!/usr/bin/env bash
# bump-version.sh — HaluCatch 版本号升级
set -euo pipefail

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "用法: $0 X.Y.Z"
  echo "  更新 config.yaml 和 web/config.yaml 的版本号"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHORT=$(echo "$VERSION" | sed 's/\.[0-9]*$//')

# 1) 根 config.yaml version（skill 元信息）
sed -i '' "s/^version: \".*\"/version: \"$VERSION\"/" "$ROOT/config.yaml" && echo "✅ config.yaml → $VERSION"

# 2) web/config.yaml（网站源头）
sed -i '' "s/^version: .*/version: $VERSION/" "$ROOT/web/config.yaml"
sed -i '' "s/^version_short: .*/version_short: $SHORT/" "$ROOT/web/config.yaml"
echo "✅ web/config.yaml → $VERSION (short: $SHORT)"

# 3) halucatch/__init__.py（Python 包版本）
sed -i '' "s/^__version__ = '.*'/__version__ = '$VERSION'/" "$ROOT/halucatch/halucatch/__init__.py"
echo "✅ halucatch/halucatch/__init__.py → $VERSION"

# 3) docs/ 由 release.sh 中的 web/build.py 重新生成
# 4) Changelog 由 generate-changelog.sh 自动处理
echo ""
echo "✅ 版本号已更新。CHANGELOG 和 docs/ 将在 release.sh 中自动生成。"
