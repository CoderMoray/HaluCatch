#!/usr/bin/env bash
# build-skillhub.sh — HaluCatch SkillHub 发布包构建
# 注意：使用 Python zipfile 代替系统 zip，确保中文文件名正确编码（不出现乱码）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 读取版本号
VERSION=$(grep '^version:' "$ROOT/config.yaml" | sed 's/^version: *"//;s/"$//')
if [[ -z "$VERSION" ]]; then
  echo "❌ 无法从 config.yaml 读取版本号"
  exit 1
fi

echo "📦 构建 SkillHub 发布包 (v$VERSION)..."

TMPDIR=$(mktemp -d)
ZIP_NAME="HaluCatch-${VERSION}-skillhub.zip"
ZIP_PATH="$ROOT/releases/$ZIP_NAME"

# 确保 releases/ 目录存在
mkdir -p "$ROOT/releases"

# 复制 SkillHub 清单文件
echo "  复制文件..."
cp "$ROOT/SKILL.md" "$TMPDIR/"
cp "$ROOT/halucatch_core.py" "$TMPDIR/"
cp -r "$ROOT/halucatch" "$TMPDIR/"
cp "$ROOT/README.md" "$TMPDIR/"
[[ -f "$ROOT/docs/CHANGELOG.md" ]] && cp "$ROOT/docs/CHANGELOG.md" "$TMPDIR/CHANGELOG.md"
[[ -f "$ROOT/docs/FAQ.md" ]] && cp "$ROOT/docs/FAQ.md" "$TMPDIR/FAQ.md"
# SkillHub 不接受 LICENSE 文件

# 清理包内不应存在的目录（如 halucatch/reports/ — HaluCatch 自我审查的产物）
if [[ -d "$TMPDIR/halucatch/reports" ]]; then
  rm -rf "$TMPDIR/halucatch/reports"
  echo "  🧹 清理 halucatch/reports/"
fi

# 使用 Python zipfile 打包（保证中文文件名 UTF-8 编码，不产生乱码）
echo "  打包（Python zipfile，UTF-8 编码）..."
cd "$TMPDIR"
python3 -c "
import zipfile, os
with zipfile.ZipFile('$ZIP_PATH', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('.'):
        for f in files:
            fpath = os.path.join(root, f)
            # 排除隐藏目录和缓存目录
            parts = fpath.split(os.sep)
            skip = any(p.startswith('.') or p == '__pycache__' for p in parts[1:])  # parts[0] 是 '.'
            if skip:
                continue
            arcname = fpath[2:] if fpath.startswith('./') else fpath  # 去掉 './' 前缀
            zf.write(fpath, arcname)
"

# 验证 zip 不包含开发者文件
echo "  验证 zip 内容..."
python3 -c "
import zipfile
with zipfile.ZipFile('$ZIP_PATH', 'r') as zf:
    names = zf.namelist()
    bad = [n for n in names if n.startswith(('tests/', 'docs/', 'reports/', 'scripts/'))]
    if bad:
        print('  ❌ zip 包含开发者文件:', bad)
        exit(1)
    print('  ✅ zip 内容纯净，共', len(names), '个文件')
"

rm -rf "$TMPDIR"

echo "✅ 生成: releases/$ZIP_NAME ($(du -h "$ZIP_PATH" | cut -f1))"