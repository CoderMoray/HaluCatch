#!/usr/bin/env bash
# check-file-size.sh — HaluCatch 文件尺寸检查
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
warnings=0

echo "📏 HaluCatch 文件尺寸检查..."

# 检查 AI 会加载的关键文件
check_file() {
  local path="$1"
  local name="$2"
  local warn_lines="${3:-500}"

  if [[ ! -f "$path" ]]; then
    echo "  ⚠️  $name 不存在"
    return
  fi

  local lines=$(wc -l < "$path" | tr -d ' ')
  local size=$(wc -c < "$path" | tr -d ' ')

  echo "  📄 $name: $lines 行, $((size / 1024)) KB"

  if [[ $lines -gt $warn_lines ]]; then
    echo "    ⚠️  超过 $warn_lines 行，建议精简"
    warnings=$((warnings + 1))
  fi
}

check_file "$ROOT/SKILL.md" "SKILL.md" 400
check_file "$ROOT/halucatch_core.py" "halucatch_core.py (compat entry)" 50

echo "  📂 halucatch/ package:"
for f in "$ROOT/halucatch"/*.py "$ROOT/halucatch/evaluators"/*.py; do
  name=$(basename "$f")
  check_file "$f" "  halucatch/$name" 250
done

echo ""
if [[ $warnings -eq 0 ]]; then
  echo "✅ 尺寸检查通过"
else
  echo "⚠️  有 $warnings 项超过建议尺寸"
fi
