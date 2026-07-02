#!/usr/bin/env bash
# generate-changelog.sh — 使用 git-cliff 自动生成 CHANGELOG 条目
# 核心思想：从 git log 自动生成结构化的 changelog，替代手动编写
#
# 用法:
#   bash scripts/generate-changelog.sh              # 生成 unreleased 条目（预览）
#   bash scripts/generate-changelog.sh --preview    # 同上，显式预览模式
#   bash scripts/generate-changelog.sh --write      # 将 unreleased 条目写入 docs/CHANGELOG.md
#   bash scripts/generate-changelog.sh v1.7.2..v1.7.3  # 生成两个 tag 间的 changelog

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLIFF_TOML="$ROOT/cliff.toml"
CHANGELOG="$ROOT/docs/CHANGELOG.md"

# ── 检查依赖 ──
if ! command -v git-cliff &>/dev/null; then
  echo "❌ git-cliff 未安装。请运行: brew install git-cliff"
  exit 1
fi

# ── 解析参数 ──
MODE="${1:---preview}"

case "$MODE" in
  --preview|"")
    echo "🔍 当前 unreleased 变更预览:"
    echo ""
    git-cliff --unreleased --strip header 2>/dev/null | grep -vE '^Warning'
    echo ""
    echo "💡 如需写入 changelog，运行: bash scripts/generate-changelog.sh --write"
    ;;
  --write)
    echo "📝 将 unreleased 变更写入 $CHANGELOG ..."
    # 生成新条目到临时文件（跳过 header 行即 ## [Unreleased]）
    TMP_NEW=$(mktemp)
    git-cliff --unreleased --strip header 2>/dev/null | grep -vE '^Warning' | tail -n +2 > "$TMP_NEW"
    if [[ ! -s "$TMP_NEW" ]]; then
      echo "  ⚠️  没有新的 unreleased 变更"
      rm -f "$TMP_NEW"
      exit 0
    fi
    # 用 Python 处理文件替换
    python3 -c "
import re
changelog_path = '$CHANGELOG'
new_path = '$TMP_NEW'

with open(changelog_path, 'r') as f:
    changelog = f.read()
with open(new_path, 'r') as f:
    new_entry = f.read()

# 找到 [Unreleased] 块并替换其内容（保留标题行）
# 匹配从 ## [Unreleased] 到下一个 --- 或 ## [V
unreleased_match = re.search(
    r'^## \[Unreleased\].*?(?=^---$|^## \[V)',
    changelog,
    re.MULTILINE | re.DOTALL
)
if unreleased_match:
    old_block = unreleased_match.group(0)
    # 保留标题行（## [Unreleased]），替换之后的内容
    header_end = old_block.index('\n')
    new_block = old_block[:header_end] + '\n' + new_entry
    changelog = changelog.replace(old_block, new_block, 1)
    with open(changelog_path, 'w') as f:
        f.write(changelog)
    print('  ✅ CHANGELOG.md [Unreleased] 已更新')
else:
    print('  ⚠️  未找到 [Unreleased] 块，跳过')
" || { echo "  ❌ 写入失败"; exit 1; }
    rm -f "$TMP_NEW"
    ;;
  *)
    # 假设是 git range (e.g. v1.7.2..v1.7.3)
    echo "🔍 生成 $MODE 的变更..."
    echo ""
    git-cliff "$MODE" --strip header 2>/dev/null | grep -vE '^Warning'
    ;;
esac
