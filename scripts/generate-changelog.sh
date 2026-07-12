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

# ── 重建「版本索引」表 ──
# 从 CHANGELOG 中已有的 ## [Vx.y.z] - DATE 标题 + git tag 自动重建一张
# 「版本索引」表（版本 / 发布日期 / 提交哈希），并替换陈旧的「版本统计」
# /「分类统计」手填段。幂等：每次 --write 都重算，永不漂移。
rebuild_index() {
  echo "📊 重建「版本索引」表..."
  if ! python3 - "$CHANGELOG" <<'PYEOF'
import re, sys, subprocess

path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    text = f.read()

# 提取所有 ## [Vx.y.z] - DATE 标题（按文件顺序，即与详细条目一致）
pat = re.compile(
    r'^##\s+\[V([0-9]+\.[0-9]+\.[0-9]+)\]\s*-\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
    re.M,
)
heads = list(pat.finditer(text))
heading_re = re.compile(r'^##\s', re.M)

# 定位版本索引段的起始边界（兼容旧的「版本统计」段）
idx = -1
if '## 版本索引' in text:
    idx = text.index('## 版本索引')
elif '## 版本统计' in text:
    idx = text.index('## 版本统计')

keep = text[:idx].rstrip() if idx != -1 else text.rstrip()
if keep.endswith('---'):
    keep = keep[:keep.rfind('---')].rstrip()

rows = []
for m in heads:
    ver, date = m.group(1), m.group(2)
    # 切出本条目的文本块（到下一个 ## 标题为止）
    nxt = heading_re.search(text, m.end())
    block = text[m.end(): nxt.start() if nxt else len(text)]
    # 优先取 git tag 的提交哈希
    tag = 'v' + ver
    h = ''
    try:
        h = subprocess.run(['git', 'log', '-1', '--format=%h', tag],
                           capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        h = ''
    # 回退：条目内「提交: `xxx`」声明的哈希（适用于无 tag 的旧版本）
    if not h:
        mm = re.search(r'提交:\s*`([0-9a-fA-F]+)`', block)
        h = mm.group(1) if mm else '-'
    rows.append(f'| V{ver} | {date} | `{h}` |')

total = len(rows)
table = (
    '\n## 版本索引\n\n'
    '| 版本 | 发布日期 | 提交哈希 |\n'
    '|------|----------|----------|\n'
    + '\n'.join(rows) + '\n'
    f'\n**总计：{total} 个版本**\n'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(keep + '\n\n---\n' + table + '\n')
print(f'  ✅ 版本索引已重建（{total} 个版本）')
PYEOF
  then
    echo "  ❌ 版本索引重建失败"
    exit 1
  fi
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

    # 幂等：已存在该版本条目则跳过「插入」，但仍会重建底部版本索引表
    SKIP_INSERT=0
    if [[ -f "$CHANGELOG" ]] && grep -q "^## \[V$VERSION\]" "$CHANGELOG"; then
      echo "  ℹ️  CHANGELOG 已存在 V$VERSION 条目，跳过插入（幂等）"
      SKIP_INSERT=1
    fi

    if [[ "$SKIP_INSERT" -eq 0 ]]; then

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
    fi

    # 无论条目是否新插入，都重建底部「版本索引」表（替换陈旧的版本统计/分类统计段）
    rebuild_index
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
