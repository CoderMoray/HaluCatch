#!/usr/bin/env bash
# generate-changelog.sh — 使用 git-cliff 自动生成 CHANGELOG 条目
# 核心思想：从 git log 自动生成结构化的 changelog，替代手动编写
#
# 用法:
#   bash scripts/generate-changelog.sh                 # 生成 unreleased 条目（预览）
#   bash scripts/generate-changelog.sh --preview       # 同上，显式预览模式
#   bash scripts/generate-changelog.sh --write 1.8.5   # 生成 v1.8.5 条目并写入 CHANGELOG
#   bash scripts/generate-changelog.sh v1.7.2..v1.7.3  # 生成两个 tag 间的 changelog
#
# 重要：git-cliff 的任何错误都必须显式暴露并以非零状态退出，禁止静默失败。
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
VERSION="${2:-}"

# 统一运行 git-cliff：错误打到 stderr 并显式返回非零，绝不 2>/dev/null 吞掉
run_cliff() {
  if ! git-cliff "$@" >/tmp/cliff.out 2>/tmp/cliff.err; then
    echo "  ❌ git-cliff 执行失败（命令: git-cliff $*）:" >&2
    sed 's/^/      /' /tmp/cliff.err >&2
    return 1
  fi
  cat /tmp/cliff.out
  return 0
}

case "$MODE" in
  --preview|"")
    echo "🔍 当前 unreleased 变更预览:"
    echo ""
    if ! run_cliff --unreleased --strip header >/dev/null; then
      exit 1
    fi
    # 重新运行仅用于显示（过滤 Warning 行），失败不影响上面的错误判定
    git-cliff --unreleased --strip header 2>/dev/null | grep -vE '^Warning' || true
    echo ""
    echo "💡 如需写入 changelog，运行: bash scripts/generate-changelog.sh --write <版本号>"
    ;;
  --write)
    if [[ -z "$VERSION" ]]; then
      echo "❌ --write 需要版本号参数，例如: bash $0 --write 1.8.5"
      exit 1
    fi
    echo "📝 生成 v$VERSION CHANGELOG 条目..."

    # 幂等：已存在该版本条目则跳过，避免重复插入
    if [[ -f "$CHANGELOG" ]] && grep -q "^## \[V$VERSION\]" "$CHANGELOG"; then
      echo "  ℹ️  CHANGELOG 已存在 V$VERSION 条目，跳过写入（幂等）"
      exit 0
    fi

    # 找到上一个 tag
    PREV_TAG=$(git tag --sort=-version:refname | grep -E '^v[0-9]' | head -1) || true
    if [[ -z "$PREV_TAG" ]]; then
      echo "  ⚠️  找不到上一个 tag，使用最新提交"
      RANGE="--latest"
    else
      RANGE="${PREV_TAG}..HEAD"
      echo "  📍 上一个 tag: $PREV_TAG，扫描范围: $RANGE"
    fi

    # 生成条目（失败立即退出，绝不静默）
    TMP_NEW=$(mktemp)
    if [[ "$RANGE" == "--latest" ]]; then
      run_cliff --latest --strip header > "$TMP_NEW" \
        || { rm -f "$TMP_NEW"; exit 1; }
    else
      run_cliff "$RANGE" --strip header > "$TMP_NEW" \
        || { rm -f "$TMP_NEW"; exit 1; }
    fi

    if [[ ! -s "$TMP_NEW" ]]; then
      echo "  ❌ git-cliff 未生成任何内容（确认 commit 是否符合 conventional commits 规范）"
      rm -f "$TMP_NEW"
      exit 1
    fi

    # 去掉重复的 header 行（cliff.toml 自带的）
    NEW_CONTENT=$(grep -vE '^#|^$|^---|^版本号规则|中间版本号|小版本号|每个 commit|^本文档记录' "$TMP_NEW" | sed '/^## \[V/d' | sed '/^$/d') || true
    if [[ -z "$NEW_CONTENT" ]]; then
      echo "  ❌ 内容过滤后为空（commit 可能不符合 conventional commits）"
      rm -f "$TMP_NEW"
      exit 1
    fi

    # 构建版本条目并插入到 [Unreleased] 之后
    VERSION_DATE=$(date +%Y-%m-%d)
    python3 -c "
changelog_path = '$CHANGELOG'
version = '$VERSION'
version_date = '$VERSION_DATE'
new_content = '''$NEW_CONTENT'''

with open(changelog_path, 'r') as f:
    changelog = f.read()

# 构建新条目
entry = f'\n## [V{version}] - {version_date}\n{new_content}\n\n---\n\n'

# 插入到 ## [Unreleased] 段之后（即第一个 --- 之后）
idx = changelog.find('## [Unreleased]')
if idx == -1:
    print('  ❌ 未找到 [Unreleased] 块，无法插入')
    exit(1)

# 找到 [Unreleased] 后的第一个 ---
end_idx = changelog.find('---', idx)
if end_idx == -1:
    print('  ❌ 未找到分隔符，无法插入')
    exit(1)

# 在 --- 所在行之后插入
insert_idx = changelog.find('\n', end_idx) + 1
changelog = changelog[:insert_idx] + entry + changelog[insert_idx:]

with open(changelog_path, 'w') as f:
    f.write(changelog)
print('  ✅ CHANGELOG.md 已更新 (v' + version + ')')
" || { echo "  ❌ CHANGELOG 写入失败"; rm -f "$TMP_NEW"; exit 1; }
    rm -f "$TMP_NEW"
    ;;
  *)
    # 假设是 git range (e.g. v1.7.2..v1.7.3)
    echo "🔍 生成 $MODE 的变更..."
    echo ""
    if ! run_cliff "$MODE" --strip header >/dev/null; then
      exit 1
    fi
    git-cliff "$MODE" --strip header 2>/dev/null | grep -vE '^Warning' || true
    ;;
esac
