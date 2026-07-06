#!/usr/bin/env bash
# lint-paths.sh — HaluCatch 发布前自检
set -euo pipefail

STRICT=false
[[ "${1:-}" == "--strict" ]] && STRICT=true

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
errors=0

echo "🔍 HaluCatch 发布前自检..."

# 1) manifest.json 存在
if [[ -f "$ROOT/manifest.json" ]]; then
  echo "  ✅ manifest.json 存在"
else
  echo "  ❌ manifest.json 缺失"
  errors=$((errors + 1))
fi

# 2) 必需文件存在性
if [[ -f "$ROOT/manifest.json" ]]; then
  required=$(python3 -c "import json; print('\n'.join(json.load(open('$ROOT/manifest.json'))['required_files']))" 2>/dev/null || echo "")
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    if [[ -e "$ROOT/$f" ]]; then
      echo "  ✅ $f 存在"
    else
      echo "  ❌ $f 缺失"
      errors=$((errors + 1))
    fi
  done <<< "$required"
fi

# 3) agentskills.sh 官方格式校验（skills-ref）
if command -v skills-ref &>/dev/null; then
  if skills-ref validate "$ROOT" &>/dev/null; then
    echo "  ✅ skills-ref validate 通过"
  else
    echo "  ❌ skills-ref validate 失败"
    echo "     运行 skills-ref validate $ROOT 查看详情"
    errors=$((errors + 1))
  fi
else
  echo "  ⚠️  skills-ref 未安装，跳过校验 (pip install skills-ref)"
fi

# 4) 版本号一致性
config_ver=$(grep '^version:' "$ROOT/config.yaml" | sed 's/^version: *"//;s/"$//' 2>/dev/null || echo "?")
skill_ver=$(python3 -c "
import re
with open('$ROOT/SKILL.md') as f:
    m = re.search(r'^version:\s*\"(.+)\"', f.read(), re.MULTILINE)
    print(m.group(1) if m else '?')
" 2>/dev/null || echo "?")

echo "  ⚙️  config.yaml:    $config_ver"
echo "  📄 SKILL.md:       $skill_ver"

if [[ "$config_ver" == "$skill_ver" ]] && [[ "$config_ver" != "?" ]]; then
  echo "  ✅ 版本号一致"
else
  echo "  ❌ 版本号不一致!"
  errors=$((errors + 1))
fi

# 5) CHANGELOG 最新版本匹配
if [[ -f "$ROOT/docs/CHANGELOG.md" ]]; then
  changelog_ver=$(grep -oE 'V[0-9]+\.[0-9]+\.[0-9]+' "$ROOT/docs/CHANGELOG.md" | head -1 | sed 's/^V//')
  echo "  📋 CHANGELOG 最新: $changelog_ver"
  if [[ "$config_ver" != "$changelog_ver" ]]; then
    echo "  ⚠️  CHANGELOG 版本 ($changelog_ver) 与 config.yaml ($config_ver) 不一致"
  fi
else
  echo "  ⚠️  CHANGELOG.md 不存在"
fi

echo ""
if [[ $errors -eq 0 ]]; then
  echo "✅ 自检通过"
  exit 0
else
  echo "❌ 自检失败 ($errors 项)"
  [[ "$STRICT" == "true" ]] && exit 1
  exit 0
fi
