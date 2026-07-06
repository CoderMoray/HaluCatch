#!/usr/bin/env bash
# build-clawhub.sh — 构建 ClawHub 发布包（ZIP）
#   纯 skill 文件，不包含 docs/ tests/ scripts/ 等开发资源
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

VERSION=$(grep '^version:' "$ROOT/config.yaml" | sed 's/^version: *"//;s/"$//')
if [[ -z "$VERSION" ]]; then
  echo "❌ 无法从 config.yaml 读取版本号"
  exit 1
fi

DRY_RUN="${1:-}"

echo "📦 构建 ClawHub 发布包 v$VERSION..."

# 0) 确保 SKILL.md frontmatter 已同步
if [[ "$DRY_RUN" != "--dry-run" ]]; then
  bash "$ROOT/scripts/inject-frontmatter.sh"
fi

# 1) 创建临时目录，复制核心文件
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

cp "$ROOT/SKILL.md"          "$TMP/"
cp "$ROOT/halucatch_core.py" "$TMP/"
cp -r "$ROOT/halucatch"       "$TMP/"
cp "$ROOT/README.md"          "$TMP/"
cp "$ROOT/config.yaml"        "$TMP/"
cp "$ROOT/manifest.json"      "$TMP/"
cp "$ROOT/LICENSE"            "$TMP/" 2>/dev/null || true

# docs 下只保留 FAQ 和 CHANGELOG
[[ -f "$ROOT/docs/CHANGELOG.md" ]] && cp "$ROOT/docs/CHANGELOG.md" "$TMP/CHANGELOG.md"
[[ -f "$ROOT/docs/FAQ.md" ]]      && cp "$ROOT/docs/FAQ.md"      "$TMP/FAQ.md"

# 清理 halucatch/reports
if [[ -d "$TMP/halucatch/reports" ]]; then
  rm -rf "$TMP/halucatch/reports"
fi

# 2) 打包 ZIP
mkdir -p "$ROOT/releases"
ZIP_NAME="HaluCatch-${VERSION}-clawhub.zip"
ZIP_PATH="$ROOT/releases/$ZIP_NAME"

cd "$TMP"
python3 -c "
import zipfile, os
with zipfile.ZipFile('$ZIP_PATH', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('.'):
        for f in files:
            fpath = os.path.join(root, f)
            arcname = fpath[2:] if fpath.startswith('./') else fpath
            zf.write(fpath, arcname)
"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "  [DRY-RUN] 文件列表:"
  ls -la "$TMP"
else
  echo "✅ ZIP: releases/$ZIP_NAME"
fi
