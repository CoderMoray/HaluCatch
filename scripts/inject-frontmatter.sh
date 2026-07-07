#!/usr/bin/env bash
# inject-frontmatter.sh — 读取 config.yaml，注入到 SKILL.md 头部
# 用法: inject-frontmatter.sh [--output <path>] [--config <path>] [--strict]
#   --strict  仅输出 Anthropic 标准字段，其余移入 metadata（给 agentskill.sh 用）
#   默认输出到 $ROOT/SKILL.md，默认读 $ROOT/config.yaml
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT="$ROOT/skill/SKILL.md"
CONFIG="$ROOT/config.yaml"
STRICT=""
MINIMAL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --config) CONFIG="$2"; shift 2 ;;
    --strict) STRICT="1"; shift ;;
    --minimal) MINIMAL="1"; shift ;;
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

# 使用 venv 的 Python（有 PyYAML），回退到系统 python3
PYTHON="python3"
if command -v /Users/chrismoray/.workbuddy/binaries/python/envs/default/bin/python3 &>/dev/null; then
  PYTHON="/Users/chrismoray/.workbuddy/binaries/python/envs/default/bin/python3"
fi

$PYTHON -c "
import sys, re, yaml

# Anthropic Agent Skills 标准字段
STANDARD_FIELDS = {'name', 'description', 'license', 'compatibility', 'allowed-tools', 'metadata'}

with open('$CONFIG', 'r') as f:
    config = yaml.safe_load(f)

strict = '$STRICT' == '1'
minimal = '$MINIMAL' == '1'

if minimal:
    # 仅保留 name + description（agentskill.sh 实际只接受这两个）
    config = {k: v for k, v in config.items() if k in ('name', 'description')}
elif strict:
    # 建立新的 metadata，合并原有的 metadata 和移入的自定义字段
    new_metadata = {}
    existing_meta = config.get('metadata', {})
    if existing_meta and isinstance(existing_meta, dict):
        new_metadata.update(existing_meta)

    # 移入非标准字段
    for key in list(config.keys()):
        if key not in STANDARD_FIELDS:
            new_metadata[key] = config.pop(key)

    if new_metadata:
        config['metadata'] = new_metadata

# 序列化为 YAML，保持 description 的多行格式
class LiteralStr(str):
    pass

def represent_literal(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(LiteralStr, represent_literal)

# 输出 YAML
output_lines = []
for key, value in config.items():
    if key == 'description' and isinstance(value, str) and '\n' in value:
        # 多行 description 用 | 块字面量
        output_lines.append(f'{key}: |')
        for line in value.strip().split('\n'):
            output_lines.append(f'  {line}')
    elif key == 'metadata' and isinstance(value, dict):
        output_lines.append(yaml.dump({'metadata': value}, default_flow_style=False, allow_unicode=True, sort_keys=False).rstrip())
    elif isinstance(value, list):
        output_lines.append(f'{key}:')
        for item in value:
            output_lines.append(f'  - {item}')
    elif isinstance(value, str):
        if '\n' in value:
            output_lines.append(f'{key}: |')
            for line in value.strip().split('\n'):
                output_lines.append(f'  {line}')
        else:
            output_lines.append(f'{key}: {value}')
    else:
        output_lines.append(f'{key}: {value}')

config_yaml = '\n'.join(output_lines).strip() + '\n'

# 读取 SKILL.md body（去掉旧 frontmatter）
with open('$OUTPUT', 'r') as f:
    content = f.read()

m = re.match(r'^---\s*\n.*?\n---\s*\n', content, re.DOTALL)
body = content[m.end():] if m else content

new_content = '---\n' + config_yaml + '---\n' + body.lstrip('\n')
with open('$OUTPUT', 'w') as f:
    f.write(new_content)

if minimal:
    mode = 'minimal'
elif strict:
    mode = 'strict'
else:
    mode = 'extended'
print(f'✅ Frontmatter 已注入 ({mode}): $OUTPUT')
"
