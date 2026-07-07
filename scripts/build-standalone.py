#!/usr/bin/env python3
"""Build a standalone, single-file HaluCatch page for offline sharing.
Dependencies: python3, node (with javascript-obfuscator installed)."""
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

DOCS = Path(__file__).parent.parent / 'docs'
COMPONENTS = DOCS / 'components' / 'ai-chat-demo'
OUT = DOCS / 'dist' / 'index.html'

# 自动发现 node 路径（支持环境变量覆盖）
NODE = os.environ.get('NODE_BIN') or shutil.which('node') or '/opt/homebrew/bin/node'
NODE_PATH = os.environ.get('NODE_PATH') or str(Path(NODE).parent.parent / 'workspace' / 'node_modules')

def read(p): return Path(p).read_text(encoding='utf-8')

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'HaluCatch-Builder'})
    print(f'  ↓ {url}')
    return urllib.request.urlopen(req).read().decode('utf-8')

def minify_css(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r'\s*([{};:,>+~])\s*', r'\1', css)
    return css.strip()

def obfuscate_js(js: str) -> str:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(js)
        tmp_in = f.name
    tmp_out = tmp_in + '.obf.js'
    try:
        env = os.environ.copy()
        env['NODE_PATH'] = NODE_PATH
        subprocess.run([
            NODE, '-e', f'''
            const obf = require("javascript-obfuscator");
            const fs = require("fs");
            const code = fs.readFileSync("{tmp_in}", "utf8");
            const result = obf.obfuscate(code, {{
                compact: true,
                controlFlowFlattening: true,
                controlFlowFlatteningThreshold: 0.75,
                deadCodeInjection: true,
                deadCodeInjectionThreshold: 0.3,
                identifierNamesGenerator: "hexadecimal",
                renameGlobals: false,
                rotateStringArray: true,
                selfDefending: false,
                stringArray: true,
                stringArrayEncoding: ["base64"],
                stringArrayThreshold: 1,
                stringArrayWrappersCount: 3,
                stringArrayWrappersType: "variable",
                target: "browser",
                transformObjectKeys: false,
                splitStrings: true,
                splitStringsChunkLength: 8,
                unicodeEscapeSequence: true
            }});
            fs.writeFileSync("{tmp_out}", result.getObfuscatedCode());
            '''
        ], env=env, check=True)
        return Path(tmp_out).read_text(encoding='utf-8')
    finally:
        Path(tmp_in).unlink(missing_ok=True)
        Path(tmp_out).unlink(missing_ok=True)

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = read(DOCS / 'index.html')

    # 1. Inline CSS
    print('Inlining CSS...')
    css = read(COMPONENTS / 'ai-chat-demo.css')
    html = html.replace(
        '<link rel="stylesheet" href="components/ai-chat-demo/ai-chat-demo.css">',
        f'<style>{minify_css(css)}</style>'
    )

    # 2. Inline & obfuscate JS
    for name in ['reports-data.js', 'ai-chat-demo.js']:
        print(f'Obfuscating {name}...')
        js = read(COMPONENTS / name)
        tag = f'<script src="components/ai-chat-demo/{name}"></script>'
        html = html.replace(tag, f'<script>{obfuscate_js(js)}</script>')

    # 3. Inline marked (already minified, skip obfuscation for size)
    print('Fetching marked.js...')
    marked = fetch('https://cdn.jsdelivr.net/npm/marked@3.0.8/marked.min.js')
    html = html.replace(
        '<script src="https://cdn.jsdelivr.net/npm/marked@3.0.8/marked.min.js"></script>',
        f'<script>{marked}</script>'
    )

    OUT.write_text(html, encoding='utf-8')
    size = OUT.stat().st_size
    print(f'\n✓ Built: {OUT} ({size / 1024:.0f} KB)')

if __name__ == '__main__':
    main()
