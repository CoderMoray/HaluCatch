#!/usr/bin/env python3
"""HaluCatch — FAQ 独立页面构建脚本
从 FAQ.md + config.yaml + locales/xx.yaml 生成 docs/faq/index.html
用法: python3 build_faq.py [--lang zh-CN] [--all]
"""
import argparse
import re
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
DIST = PROJECT_ROOT / "docs"


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def copy_assets(output_dir, config=None):
    """复制 web/assets/ 全部静态资源到输出目录（含 FAQ 新增文件）"""
    assets_src = ROOT / "assets"
    if assets_src.exists():
        dest = output_dir / "assets"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(assets_src, dest)
        print(f"  📁 assets → {dest}")

    # 替换 theme.js 中的 STORAGE_KEY 占位符
    theme_js = dest / "js" / "theme.js"
    if theme_js.exists() and config:
        content = theme_js.read_text(encoding="utf-8")
        content = content.replace(
            "{{ theme_storage_key }}",
            config.get("theme_storage_key", "halucatch-theme"),
        )
        theme_js.write_text(content, encoding="utf-8")
        print("  🔧 theme.js STORAGE_KEY replaced")

    # 复制 favicon
    favicon = assets_src / "images" / "favicon.svg"
    if favicon.exists():
        shutil.copy2(favicon, output_dir / "favicon.svg")
        print(f"  📄 favicon.svg → {output_dir}")


# ── FAQ.md 解析 ─────────────────────────────────────────

SECTION_ROUTING = {
    "基础": "qa",
    "报错": "table",
    "场景": "scenes",
    "能力": "capabilities",
    "边界": "capabilities",
    "报告": "qa",
    "技术": "qa",
    "反模式": "antipattern",
}


def classify_section(title):
    for keyword, typ in SECTION_ROUTING.items():
        if keyword in title:
            return typ
    return "qa"


def md_to_html(text):
    """简单 Markdown → HTML 转换"""
    # 代码块 ```xxx \n ... \n ```
    text = re.sub(
        r"```(\w*)\n(.*?)```",
        lambda m: f"<pre><code>{m.group(2).strip()}</code></pre>",
        text,
        flags=re.DOTALL,
    )
    # 内联代码 `xxx`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # 粗体 **xxx**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # 行内换行
    text = text.replace("\n", "<br>")
    return text


def parse_faq_md(path):
    """按 ## 分割 FAQ.md → 结构化列表
    注意：先剥离代码块，防止代码块内嵌的 ## 干扰分割。
    """
    content = open(path, encoding="utf-8").read()

    # 剥离代码块（避免其中的 ## 干扰分割）
    # 用占位符替换，分割完成后再恢复
    code_blocks = []
    def stash_code(m):
        code_blocks.append(m.group(0))
        return f"```CODEGUARD_{len(code_blocks)-1}```"
    content_no_code = re.sub(r"```[\w]*\n.*?```", stash_code, content, flags=re.DOTALL)

    raw_sections = re.split(r"^## ", content_no_code, flags=re.MULTILINE)
    sections = []
    for sec in raw_sections:
        if not sec.strip():
            continue
        lines = sec.strip().split("\n")
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        if not title:
            continue
        # 跳过文档主标题（# HaluCatch / 捕幻 — 常见问题）
        if title.startswith("# ") or body in ("---",):
            continue
        # 恢复 body 中的代码块占位符
        for i, block in enumerate(code_blocks):
            body = body.replace(f"```CODEGUARD_{i}```", block)
        sections.append({"title": title, "type": classify_section(title), "body": body})
    return sections


# ── 各区块渲染器 ───────────────────────────────────────

def render_qa(body):
    """Q&A 折叠卡片"""
    items = re.split(r"\n{2,}---\n{2,}", body)
    html = ""
    for item in items:
        item = item.strip()
        if not item:
            continue
        m = re.match(r'\*\*Q:\s*(.+?)\*\*\s*\n+(.*)', item, re.DOTALL)
        if m:
            q = m.group(1).strip()
            a = re.sub(r'-{3,}\s*$', '', m.group(2).strip())
            a = md_to_html(a)
            a = re.sub(r'(?:<br>\s*)+$', '', a)  # 去掉尾部空行
            html += f"""<div class="faq-item">
      <button class="faq-q" onclick="toggleFaqItem(this)">
        <span>{q}</span>
        <svg class="faq-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
      </button>
      <div class="faq-a"><p>{a}</p></div>
    </div>\n"""
    return html


def render_table(body):
    """报错速查表格"""
    lines = body.strip().split("\n")
    html = """<div class="faq-table-wrap">
    <table class="faq-table">
      <thead><tr>"""
    # 找第一个 | 行作为表头
    header_done = False
    header_rows = []
    body_rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if not header_done:
            # 跳过分隔行 |---|---|
            if re.match(r"\|[\s\-:]+\|", stripped):
                header_done = True
                continue
            header_rows.append(stripped)
        else:
            body_rows.append(stripped)

    # 表头（取第一行）
    if header_rows:
        cells = [c.strip() for c in header_rows[0].split("|") if c.strip()]
        for c in cells:
            html += f"<th>{c}</th>"
    html += "</tr></thead>\n<tbody>\n"
    for row in body_rows:
        cells = [c.strip() for c in row.split("|") if c.strip()]
        html += "      <tr>"
        for c in cells:
            html += f"<td>{md_to_html(c)}</td>"
        html += "</tr>\n"
    html += "    </tbody>\n  </table>\n</div>"
    return html


def render_scenes(body):
    """使用场景卡片"""
    # 按 **场景 X：** 分割
    scenes = re.split(r"\*\*场景\s*\d+\s*[:：]", body)
    html = '<div class="scenes-grid">\n'
    for scene in scenes:
        scene = scene.strip()
        if not scene:
            continue
        # 第一行是标题（到 ** 或换行）
        lines = scene.split("\n")
        title_line = lines[0].strip().rstrip("**").strip()
        # 后续是描述
        desc_lines = [l.strip() for l in lines[1:] if l.strip() and l.strip() != "---"]
        desc = "\n".join(desc_lines)
        html += f"""    <div class="scene-card">
      <h4>{md_to_html(title_line)}</h4>
      <p>{md_to_html(desc)}</p>
    </div>\n"""
    html += "  </div>"
    return html


def render_capabilities(body):
    """能力边界三栏"""
    # 按 **能/**不能/**硬性** 分割
    parts = re.split(r"\*\*(能做什么|不能做什么|硬性限制)[：:]?\*\*", body)
    buckets = {"能做什么": "", "不能做什么": "", "硬性限制": ""}
    current_key = None
    for part in parts:
        part = part.strip()
        if part in buckets:
            current_key = part
        elif current_key:
            buckets[current_key] += "\n" + part

    icon_map = {"能做什么": "✅", "不能做什么": "❌", "硬性限制": "📏"}
    color_map = {"能做什么": "cap-green", "不能做什么": "cap-red", "硬性限制": "cap-orange"}

    html = '<div class="caps-grid">\n'
    for key in ["能做什么", "不能做什么", "硬性限制"]:
        content = buckets.get(key, "")
        # 提取列表项（以 - ✅ / - ❌ 或 - 开头）
        items = re.findall(r"[-•]\s*(.+?)(?:<br>|$)", md_to_html(content))
        items = [item.strip() for item in items if item.strip() and item.strip() != "--"]
        items_html = "\n".join(f"      <li>{item}</li>" for item in items)
        html += f"""    <div class="cap-card {color_map[key]}">
      <div class="cap-icon">{icon_map[key]}</div>
      <h4>{key}</h4>
      <ul>{items_html}</ul>
    </div>\n"""
    html += "  </div>"
    return html


def render_antipattern(body):
    """常见反模式 — 多表格依次排列"""
    # 按 ### 分割子板块
    subs = re.split(r"^###\s+", body, flags=re.MULTILINE)
    html = ""
    for sub in subs:
        sub = sub.strip()
        if not sub:
            continue
        lines = sub.split("\n")
        sub_title = lines[0].strip()
        sub_body = "\n".join(lines[1:]).strip()
        # 跳过没有实际正文的子板块（如开头的引言段落）
        if not sub_body and "|" not in sub_body:
            continue
        # 渲染子板块内的表格
        table_html = render_table(sub_body) if "|" in sub_body else f"<p>{md_to_html(sub_body)}</p>"
        html += f"""  <div class="antipattern-sub">
    <h4>{sub_title}</h4>
    {table_html}
  </div>\n"""
    return html


SECTION_RENDERERS = {
    "qa": render_qa,
    "table": render_table,
    "scenes": render_scenes,
    "capabilities": render_capabilities,
    "antipattern": render_antipattern,
}


ICONS = {
    "基础": "💡",
    "报错": "🔍",
    "场景": "📋",
    "能力": "⚡",
    "边界": "⚡",
    "报告": "📊",
    "技术": "🛠️",
    "反模式": "🚫",
}

# 用于去重的 emoji 前缀（FAQ.md 的 ## 标题可能自带 emoji）
TITLE_EMOJI_PREFIXES = {"🔍", "🚫", "📋", "⚡", "💡", "📊", "🛠️"}


def section_icon(title):
    for keyword, ico in ICONS.items():
        if keyword in title:
            return ico
    return "💡"


def strip_title_emoji(title):
    """去掉标题开头的 emoji 前缀（防止与 ICONS 重复）"""
    for emoji in TITLE_EMOJI_PREFIXES:
        if title.startswith(emoji):
            return title[len(emoji):].strip()
    return title


def render_section(section):
    renderer = SECTION_RENDERERS.get(section["type"], render_qa)
    body_html = renderer(section["body"])
    icon = section_icon(section["title"])
    clean_title = strip_title_emoji(section["title"])
    return f"""<section class="faq-section {section['type']}-section">
  <h3 class="faq-section-title"><span class="fs-icon">{icon}</span> {clean_title}</h3>
  {body_html}
</section>\n"""


# ── 模板渲染 ─────────────────────────────────────────

def resolve_value(path, context):
    parts = path.strip().split(".")
    val = context
    for p in parts:
        if isinstance(val, dict) and p in val:
            val = val[p]
        else:
            return None
    return str(val) if val is not None else ""


def render_template(template_path, context, output_path):
    with open(template_path, encoding="utf-8") as f:
        html = f.read()

    def replacer(m):
        return resolve_value(m.group(1), context) or ""

    html = re.sub(r"\{\{ ([a-z0-9_.]+) \}\}", replacer, html)

    # 扁平键名兼容
    for key, value in context.items():
        if not isinstance(value, (dict, list)):
            html = html.replace("{{ " + key + " }}", str(value))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ {output_path}")


def build_faq_page(config, locale, output_dir):
    """构建一个语言的 FAQ 页面"""
    faq_md_path = ROOT.parent / "halucatch" / "FAQ.md"
    if not faq_md_path.exists():
        print(f"  ⚠️ FAQ.md not found at {faq_md_path}")
        return

    # 解析 FAQ.md
    sections = parse_faq_md(faq_md_path)
    faq_content = "\n".join(render_section(s) for s in sections)

    # 构建模板上下文
    ctx = {}
    ctx["lang"] = config["lang"]
    ctx["pages_url"] = config["pages_url"]
    ctx["github_url"] = config["github_url"]
    ctx["license_url"] = config.get("license_url", config["github_url"] + "/blob/main/LICENSE")
    ctx["favicon"] = config.get("favicon", "favicon.svg")
    ctx["version"] = config["version"]
    ctx["version_short"] = config["version_short"]
    ctx["name"] = config["name"]
    ctx["author"] = config["author"]
    ctx["theme_storage_key"] = config.get("theme_storage_key", "halucatch-theme")

    # Brand SVG
    ctx["brand_svg"] = """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>"""

    # Nav
    nav_locale = locale["nav"]
    ctx["nav"] = {
        "brand_full": config["nav"]["brand_full"],
        "brand_short": config["nav"]["brand_short"],
        "theme_light": nav_locale["theme"]["light"],
        "theme_dark": nav_locale["theme"]["dark"],
        "theme_auto": nav_locale["theme"]["auto"],
        "share_label": nav_locale["share"]["label"],
        "share_copy_link": nav_locale["share"]["copy_link"],
        "share_to_feishu": nav_locale["share"]["share_to_feishu"],
        "share_to_x": nav_locale["share"]["share_to_x"],
        "hamburger": nav_locale["hamburger"],
    }

    # SEO
    fp = config.get("faq_page", {})
    fpl = locale.get("faq_page", {})
    ctx["seo"] = {
        "title": fpl.get("title", fp.get("title", "FAQ")).format(name=config["name"]),
        "description": fpl.get("description", fp.get("description", "")),
    }

    # A11y
    ctx["a11y"] = {"skip_to_content": locale["a11y"]["skip_to_content"]}

    # FAQ page i18n
    ctx["faq_page"] = {
        "title": fpl.get("title", fp.get("title", "FAQ")).format(name=config["name"]),
        "back_label": fpl.get("back_label", "Back to Home"),
        "back_label_short": fpl.get("back_label_short", "Back"),
        "search_placeholder": fpl.get("search_placeholder", "Search..."),
        "back_to_top": fpl.get("back_to_top", "Back to Top"),
        "no_results_msg": fpl.get("no_results_msg", "No results found"),
        "no_results_hint": fpl.get("no_results_hint", "Try different keywords or browse the categories above"),
        "keyword_chips": "".join(
            f'<button class="keyword-chip" data-keyword="{kw}">{kw}</button>'
            for kw in fpl.get("suggested_keywords", fp.get("suggested_keywords", []))
        ),
    }

    # Footer
    footer_i18n = locale["footer"]
    ctx["footer"] = {
        "copyright": footer_i18n["copyright"].format(
            name=config["name"], license=config.get("license", "MIT")
        ),
    }

    # FAQ content (from parsed markdown)
    ctx["faq_content"] = faq_content

    # 加载模板
    template_path = ROOT / "templates" / "faq.html"
    render_template(template_path, ctx, output_dir / "faq" / "index.html")

    # 复制资源
    copy_assets(output_dir, config)


def main():
    parser = argparse.ArgumentParser(description="Build HaluCatch FAQ page")
    parser.add_argument("--lang", default="zh-CN", help="Target language (default: zh-CN)")
    parser.add_argument("--all", action="store_true", help="Build all languages")
    args = parser.parse_args()

    config = load_yaml(ROOT / "config.yaml")

    langs = [args.lang]
    if args.all:
        locales_dir = ROOT / "locales"
        langs = [p.stem for p in locales_dir.glob("*.yaml")]

    for lang in langs:
        locale_path = ROOT / "locales" / f"{lang}.yaml"
        if not locale_path.exists():
            print(f"⚠️  Locale not found: {locale_path}, skipping")
            continue

        locale = load_yaml(locale_path)

        # 先临时设置 config.lang 供上下文使用
        config["lang"] = lang

        out_dir = DIST if lang == "zh-CN" else DIST / lang
        build_faq_page(config, locale, out_dir)

    print(f"\n🎉 FAQ page built! Output in {DIST}/faq/")


if __name__ == "__main__":
    main()
