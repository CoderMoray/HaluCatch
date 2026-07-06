#!/usr/bin/env bash
# inject-frontmatter.sh — 读取 config.yaml，注入到 SKILL.md 头部
# 用法: inject-frontmatter.sh [--output <path>] [--config <path>]
#   默认输出到 $ROOT/SKILL.md，默认读 $ROOT/config.yaml
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$ROOT/SKILL.md"
CONFIG="$ROOT/config.yaml"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

if [[ ! -f "$CONFIG" ]]; then
  echo "❌ config.yaml 不存在: $CONFIG"
  exit 1
fi

if [[ ! -f "$OUTPUT" ]]; then
  echo "❌ SKILL.md 不存在: $OUTPUT"
  exit 1
fi

python3 -c "
import sys, re

# 读取 config.yaml，保留原始结构
with open('$CONFIG', 'r') as f:
    config_text = f.read()

# 去掉注释行（# 开头），保留有效的 YAML 内容
lines = []
for line in config_text.split('\n'):
    stripped = line.lstrip()
    if stripped.startswith('#') or stripped == '':
        # 保留空行分隔但跳过纯注释行
        if stripped == '':
            lines.append('')
        continue
    lines.append(line)

config_yaml = '\n'.join(lines).strip()

# 读取 SKILL.md body（去掉旧 frontmatter）
with open('$OUTPUT', 'r') as f:
    content = f.read()

# 匹配 Frontmatter: 第一个 --- 到第二个 ---
m = re.match(r'^---\s*\n.*?\n---\s*\n', content, re.DOTALL)
if m:
    body = content[m.end():]
else:
    body = content

# 组装新 SKILL.md
new_content = '---\n' + config_yaml.strip() + '\n---\n' + body.lstrip('\n')
with open('$OUTPUT', 'w') as f:
    f.write(new_content)

print('✅ Frontmatter 已注入: $OUTPUT')
"
