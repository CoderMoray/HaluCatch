#!/usr/bin/env bash
# sync-version.sh — 以 _meta.json 为唯一真相源，同步所有文件的版本号
# 用法: bash scripts/sync-version.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
META="$ROOT/_meta.json"

if [[ ! -f "$META" ]]; then
  echo "❌ _meta.json 不存在: $META"
  exit 1
fi

VERSION=$(python3 -c "import json; print(json.load(open('$META'))['version'])")
if [[ -z "$VERSION" ]]; then
  echo "❌ 无法从 _meta.json 读取版本号"
  exit 1
fi

TODAY=$(date +%Y-%m-%d)

echo "📌 当前版本: v$VERSION (日期: $TODAY)"
echo ""

# 1. halucatch/__init__.py
echo "  🔄 halucatch/__init__.py"
sed -i.bak "s/__version__ = '[^']*'/__version__ = '$VERSION'/" "$ROOT/halucatch/__init__.py" && rm "$ROOT/halucatch/__init__.py.bak"

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

# 3. SKILL.md (frontmatter version: "X.Y.Z")
echo "  🔄 SKILL.md"
sed -i.bak "s/^version: \"[^\"]*\"/version: \"$VERSION\"/" "$ROOT/SKILL.md" && rm "$ROOT/SKILL.md.bak"

# 4. docs/PROGRESS.md (最新版本 + 发布日期)
echo "  🔄 docs/PROGRESS.md"
sed -i.bak "s/| 最新版本 | \*\*v[^*]*\*\*/| 最新版本 | **v$VERSION** |/" "$ROOT/docs/PROGRESS.md" && rm "$ROOT/docs/PROGRESS.md.bak"
sed -i.bak "s/| 发布日期 | [0-9-]*/| 发布日期 | $TODAY/" "$ROOT/docs/PROGRESS.md" && rm "$ROOT/docs/PROGRESS.md.bak"

# 5. docs/CHANGELOG.md (Unreleased 标记)
# 如果 Unreleased 不为空，提示需要手动添加版本条目
UNRELEASED=$(sed -n '/## \[Unreleased\]/,/---/p' "$ROOT/docs/CHANGELOG.md" | grep -c '###' || true)
if [[ "$UNRELEASED" -gt 0 ]]; then
  echo ""
  echo "⚠️  docs/CHANGELOG.md 的 [Unreleased] 有内容，请手动添加 v$VERSION 条目"
else
  echo "  ✅ docs/CHANGELOG.md [Unreleased] 为空，无需操作"
fi

echo ""
echo "✅ 版本同步完成: v$VERSION"
