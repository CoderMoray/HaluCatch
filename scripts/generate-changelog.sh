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

# ── 同步版本元数据到标题 ──
# 页面渲染时每个 ## [Vx] 会渲染成一个版本区块，因此把 commit 哈希
# 直接并进标题（## [Vx] - DATE · `hash`），让每个区块自包含、零冗余；
# 同时移除条目体内陈旧的「提交: xxx」行（哈希已上提），并删掉文档尾部的
# 「版本索引」表（页面 TOC 由 build 从标题生成，无需内联）。幂等：已带哈希的标题跳过。
sync_version_meta() {
  echo "📑 同步版本哈希到标题（页面渲染用）..."
  if ! python3 - "$CHANGELOG" <<'PYEOF'
import re, sys, subprocess

path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    text = f.read()

heading_re = re.compile(
    r'^##\s+\[V([0-9]+\.[0-9]+\.[0-9]+)\]\s*-\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
    re.M,
)
any_head_re = re.compile(r'^##\s', re.M)

matches = list(heading_re.finditer(text))
new = text
# 从后往前改写标题（避免位置偏移）；先剥离已有的 · `hash`（可能重复），再补一个，幂等且自愈
for m in reversed(matches):
    ver = m.group(1)
    line_end = text.find('\n', m.start())
    if line_end == -1:
        line_end = len(text)
    full_line = text[m.start(): line_end]
    base = re.sub(r'\s*·.*$', '', full_line)
    # 标题已有哈希则复用（幂等、跨重跑稳定，避免无 tag 旧版本退化为 -）
    eh = re.search(r'·\s*`([0-9a-fA-F-]+)`', full_line)
    if eh:
        h = eh.group(1)
    else:
        nxt = any_head_re.search(text, m.end())
        block = text[m.end(): nxt.start() if nxt else len(text)]
        tag = 'v' + ver
        h = ''
        try:
            h = subprocess.run(['git', 'log', '-1', '--format=%h', tag],
                               capture_output=True, text=True, check=True).stdout.strip()
        except Exception:
            h = ''
        if not h:
            mm = re.search(r'提交:\s*`?([0-9a-fA-F]+)`?', block)
            h = mm.group(1) if mm else '-'
    new_head = f'{base} · `{h}`'
    new = new[:m.start()] + new_head + new[m.start() + len(full_line):]

# 移除条目体内的「提交: xxx」行（哈希已上提至标题，兼容缩进列表项）
new = re.sub(r'\n\s*-?\s*提交:[^\n]*\n', '\n', new)

# 删除文档尾部的「版本索引」段（页面 TOC 由 build 从标题生成）
idx = new.find('## 版本索引')
if idx != -1:
    cut = new.rfind('\n---\n', 0, idx)
    new = (new[:cut] + '\n') if cut != -1 else (new[:idx].rstrip() + '\n')

with open(path, 'w', encoding='utf-8') as f:
    f.write(new)
print(f'  ✅ 已为 {len(matches)} 个版本标题补上提交哈希')
PYEOF
  then
    echo "  ❌ 版本哈希同步失败"
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

    # 幂等：已存在该版本条目则跳过「插入」，但仍会同步版本哈希到标题
    SKIP_INSERT=0
    if [[ -f "$CHANGELOG" ]] && grep -q "^## \[V$VERSION\]" "$CHANGELOG"; then
      echo "  ℹ️  CHANGELOG 已存在 V$VERSION 条目，跳过插入（幂等）"
      SKIP_INSERT=1
    fi

    if [[ "$SKIP_INSERT" -eq 0 ]]; then

    # 找到上一个版本号（优先级：git tag → git release commit → CHANGELOG.md）
    PREV_TAG=""
    SOURCE=""

    # 1) git tag
    set +o pipefail  # 管道 grep 无结果返回非零，set -e 会提前退出
    PREV_TAG=$(git tag --sort=-version:refname --list 'v*' 2>/dev/null | grep -E '^v[0-9]' | head -1)
    set -o pipefail
    if [[ -n "$PREV_TAG" ]]; then
      SOURCE="git tag"
    fi

    # 2) git release commit（无 tag 时从提交记录找）
    if [[ -z "$PREV_TAG" ]]; then
      set +o pipefail
      PREV_VER=$(git log --grep="^release: v" --format="%s" --max-count=1 2>/dev/null | sed -nE 's/^release: (v[0-9.]+).*/\1/p')
      set -o pipefail
      if [[ -n "$PREV_VER" ]]; then
        PREV_TAG="$PREV_VER"
        SOURCE="git commit ($PREV_VER — 无对应 tag)"
      fi
    fi

    # 3) CHANGELOG.md
    if [[ -z "$PREV_TAG" ]]; then
      set +o pipefail
      PREV_VER=$(grep -m1 '^## \[V' "$CHANGELOG" 2>/dev/null | sed -nE 's/^## \[V([0-9.]+)\].*/\1/p')
      set -o pipefail
      if [[ -n "$PREV_VER" ]]; then
        PREV_TAG="v$PREV_VER"
        SOURCE="CHANGELOG.md ($PREV_TAG)"
      fi
    fi

    if [[ -z "$PREV_TAG" ]]; then
      echo "  ⚠️  找不到上一个版本，使用所有提交"
      RANGE="--latest"
    else
      RANGE="${PREV_TAG}..HEAD"
      echo "  📍 上一个版本: $PREV_TAG（来源: $SOURCE）"
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
    # 写入时即用当前 HEAD 短哈希给新版本标题（release 流程中 tag 尚未创建，
    # HEAD 即本版本对应的提交；后续 sync_version_meta 会跳过已带哈希的标题）
    NEW_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo '-')
    python3 -c "
changelog_path = '$CHANGELOG'
version = '$VERSION'
version_date = '$VERSION_DATE'
new_hash = '$NEW_HASH'
new_content = '''$NEW_CONTENT'''

with open(changelog_path, 'r') as f:
    changelog = f.read()

# 构建新条目（标题直接带上 commit 哈希，页面渲染时每个版本区块自包含）
entry = f'\n## [V{version}] - {version_date} · `{new_hash}`\n{new_content}\n\n---\n\n'

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

    # 无论条目是否新插入，都同步版本哈希到标题（移除冗余的「提交:」行与尾部索引表）
    sync_version_meta
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
