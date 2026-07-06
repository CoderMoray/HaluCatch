#!/usr/bin/env bash
# build-mcpmarket.sh — 构建并推送 release/mcpmarket 分支
#   分支内容是纯 skill 文件，不包含 docs/ tests/ scripts/ 等开发资源
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

VERSION=$(grep '^version:' "$ROOT/config.yaml" | sed 's/^version: *"//;s/"$//')
if [[ -z "$VERSION" ]]; then
  echo "❌ 无法从 config.yaml 读取版本号"
  exit 1
fi

BRANCH="release/mcpmarket"
DRY_RUN="${1:-}"

echo "📦 构建 $BRANCH v$VERSION..."

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

# 清理 halucatch/reports（不应打包自我审查产物）
if [[ -d "$TMP/halucatch/reports" ]]; then
  rm -rf "$TMP/halucatch/reports"
fi

# 2) 推送到 release/mcpmarket 分支
if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "  [DRY-RUN] 将推送到 $BRANCH"
  echo "  [DRY-RUN] 文件列表:"
  ls -la "$TMP"
  exit 0
fi

cd "$TMP"
git init -q
git checkout -b main
git config user.email "release-bot@halucatch.dev"
git config user.name "HaluCatch Release Bot"

# 添加 .gitignore（精简版，只排除运行时产物）
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
reports/
*.zip
.DS_Store
EOF

git add -A
git commit -m "release/mcpmarket v$VERSION" -q

# 强制推送到目标分支
REMOTE_URL=$(cd "$ROOT" && git remote get-url origin)
git remote add origin "$REMOTE_URL"
git push origin main:"$BRANCH" --force -q

echo "✅ $BRANCH v$VERSION 已推送"

# 3) 同时生成 ZIP 包用于手动上传
mkdir -p "$ROOT/releases"
ZIP_NAME="HaluCatch-${VERSION}-mcpmarket.zip"
ZIP_PATH="$ROOT/releases/$ZIP_NAME"

python3 -c "
import zipfile, os
with zipfile.ZipFile('$ZIP_PATH', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('.'):
        # 跳过 .git
        dirs[:] = [d for d in dirs if d != '.git']
        for f in files:
            fpath = os.path.join(root, f)
            parts = fpath.split(os.sep)
            skip = any(p.startswith('.') or p == '__pycache__' for p in parts[1:])
            if skip:
                continue
            arcname = fpath[2:] if fpath.startswith('./') else fpath
            zf.write(fpath, arcname)
"

echo "✅ ZIP: releases/$ZIP_NAME"
echo ""
