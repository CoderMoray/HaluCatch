#!/usr/bin/env bash
# sync-version.sh — 以 config.yaml 为唯一真相源，同步所有文件的版本号
# 用法: bash scripts/sync-version.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$ROOT/config.yaml"

if [[ ! -f "$CONFIG" ]]; then
  echo "❌ config.yaml 不存在: $CONFIG"
  exit 1
fi

VERSION=$(grep '^version:' "$CONFIG" | sed 's/^version: *"//;s/"$//')
if [[ -z "$VERSION" ]]; then
  echo "❌ 无法从 config.yaml 读取版本号"
  exit 1
fi

TODAY=$(date +%Y-%m-%d)

echo "📌 当前版本: v$VERSION (日期: $TODAY)"
echo ""

# 1. halucatch/__init__.py
echo "  🔄 halucatch/__init__.py"
sed -i.bak "s/__version__ = '[^']*'/__version__ = '$VERSION'/" "$ROOT/halucatch/halucatch/__init__.py" && rm "$ROOT/halucatch/halucatch/__init__.py.bak"

# 2. manifest.json
echo "  🔄 manifest.json"
python3 -c "
import json
path = '$ROOT/manifest.json'
with open(path) as f:
    data = json.load(f)
data['version'] = '$VERSION'
with open(path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
"

# 3. SKILL.md (通过 inject-frontmatter.sh 重新生成)
echo "  🔄 SKILL.md (via inject-frontmatter.sh)"
bash "$ROOT/scripts/inject-frontmatter.sh"

# 4. docs/PROGRESS.md (最新版本 + 发布日期)
echo "  🔄 docs/PROGRESS.md"
sed -i.bak "s/| 最新版本 | \*\*v[^*]*\*\*/| 最新版本 | **v$VERSION** |/" "$ROOT/docs/PROGRESS.md" && rm "$ROOT/docs/PROGRESS.md.bak"
sed -i.bak "s/| 发布日期 | [0-9-]*/| 发布日期 | $TODAY/" "$ROOT/docs/PROGRESS.md" && rm "$ROOT/docs/PROGRESS.md.bak"

# 5. docs/CHANGELOG.md (Unreleased 标记)
UNRELEASED=$(sed -n '/## \[Unreleased\]/,/---/p' "$ROOT/docs/CHANGELOG.md" | grep -c '###' || true)
if [[ "$UNRELEASED" -gt 0 ]]; then
  echo ""
  echo "⚠️  docs/CHANGELOG.md 的 [Unreleased] 有内容，请手动添加 v$VERSION 条目"
else
  echo "  ✅ docs/CHANGELOG.md [Unreleased] 为空，无需操作"
fi

echo ""
echo "✅ 版本同步完成: v$VERSION"
