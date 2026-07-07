#!/usr/bin/env python3
"""HaluCatch — 官网构建脚本
从 config.yaml + locales/xx.yaml 生成 docs/ 目录下的多语言 index.html
用法: python3 build.py [--lang zh-CN] [--all]
"""
import argparse
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
DIST = PROJECT_ROOT / "docs"      # 输出到 docs/（GitHub Pages 部署目录）


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def merge_config(config, locale):
    """合并项目配置 + 翻译文本，返回可直接用于模板渲染的扁平+嵌套混合 dict"""
    data = {}

    # ── 基础 ──
    data["name"] = config["name"]
    data["version"] = config["version"]
    data["version_short"] = config["version_short"]
    data["author"] = config["author"]
    data["lang"] = config["lang"]
    data["pages_url"] = config["pages_url"]
    data["github_url"] = config["github_url"]
    data["license_url"] = config.get("license_url", config["github_url"] + "/blob/main/LICENSE")
    data["og_image"] = config.get("og_image", "og-image.png")
    data["favicon"] = config.get("favicon", "favicon.svg")
    data["theme_storage_key"] = config.get("theme_storage_key", f"{config['name'].lower()}-theme")

    # ── SEO (嵌套路径 seo.title / seo.description 供模板用) ──
    data["seo"] = {
        "title": locale["seo"]["title"].format(name=data["name"]),
        "description": locale["seo"]["description"].format(name=data["name"]),
    }

    # ── A11y (嵌套) ──
    data["a11y"] = {"skip_to_content": locale["a11y"]["skip_to_content"]}

    # ── 导航 (嵌套 nav.xxx) ──
    nav_locale = locale["nav"]
    data["nav"] = {
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

    # 导航链接
    nav_links = ""
    for s in config["nav"]["sections"]:
        label = next((item["label"] for item in nav_locale["sections"] if item["id"] == s["id"]), s["label"])
        nav_links += f'<a href="#{s["id"]}" class="nav-link">{label}</a>\n'
    data["nav_links"] = nav_links.strip()

    # ── Brand SVG ──
    data["brand_svg"] = """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>"""

    # ── Hero ──
    hero_cfg = config["hero"]
    hero_i18n = locale["hero"]
    data["hero"] = {
        "title": hero_cfg["title"],
        "subtitle": hero_i18n["subtitle"].strip(),
        "cta_github": hero_i18n["cta_github"],
    }
    data["hero_svg"] = """<svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;position:relative;top:-4px;"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><circle cx="12" cy="12" r="3"/><path d="m16 16-1.9-1.9"/></svg>"""

    # Hero badges
    badges = ""
    for b in hero_cfg.get("badges", []):
        badges += f'<span class="badge">{b}</span>\n'
    data["hero_badges"] = badges.strip()

    # CTA
    cta = config.get("cta", {})
    cta_extra = ""
    if cta.get("skillhub"):
        cta_extra += f'<a href="{cta["skillhub"]["url"]}" class="btn btn-outline" target="_blank">{hero_i18n.get("cta_skillhub", "SkillHub")}</a>\n'
    if cta.get("clawhub"):
        cta_extra += f'<a href="{cta["clawhub"]["url"]}" class="btn btn-outline" target="_blank">{hero_i18n.get("cta_clawhub", "ClawHub")}</a>\n'
    data["hero_cta_extra"] = cta_extra.strip()

    # ── 分享按钮内联 script（含国际化文本）──
    share_locale = nav_locale["share"]
    data["share_script"] = f"""<script>
(function() {{
  var URL = '{data["pages_url"]}';
  var toast = document.createElement('div');
  toast.className = 'share-toast';
  document.body.appendChild(toast);
  function showToast(msg) {{
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(function() {{ toast.classList.remove('show'); }}, 2000);
  }}
  document.querySelectorAll('.nav-share-item').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      var platform = btn.getAttribute('data-platform');
      if (platform === 'twitter') {{
        window.open('https://x.com/intent/post?url=' + encodeURIComponent(URL) + '&text=' + encodeURIComponent('{data["seo"]["title"]}'), '_blank');
        return;
      }}
      navigator.clipboard.writeText(URL).then(function() {{
        var labels = {{ feishu: '{share_locale["share_to_feishu"]}', url: '' }};
        var msg = '{share_locale["toast_copied"]}';
        showToast(msg.replace('{{platform}}', labels[platform] || platform));
      }}).catch(function() {{
        showToast('{share_locale["toast_failed"]}');
      }});
    }});
  }});
}})();
</script>"""

    # ── 安装复制按钮标签 ──
    data["copy_label"] = locale.get("copy_label", "一键复制")
    data["copied_label"] = locale.get("copied_label", "复制成功")

    # ── 安全审计 ──
    audits = config.get("security_audits", {})
    if audits and audits.get("items"):
        items_html = ""
        for item in audits["items"]:
            items_html += f"""<a href="{item['url']}" target="_blank" class="safety-badge">
      <img src="{item['icon']}" alt="{item.get('alt', item['name'])}" loading="lazy">
      {item['name']}
      <span class="status {item['status']}">{item['status_text']}</span>
    </a>\n"""
        data["security_audit_section"] = f"""<section class="anim-item scroll-anim" style="text-align:center;padding:0 20px 40px;">">
  <h3 style="font-size:1.2rem;margin-bottom:14px;text-align:center;font-weight:600;color:var(--text2);">{locale["security"]["title"]}</h3>
  <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
    {items_html.strip()}
  </div>
</section>"""
    else:
        data["security_audit_section"] = ""

    # ── Demo 区块 ──
    demo = config.get("demo")
    if demo:
        demo_i18n = locale.get("demo", {})
        data["demo_section"] = f"""<section id="demo" class="anim-item scroll-anim">
  <h2>{demo_i18n.get("title", "Live Demo").format(name=data['name'])}</h2>
  <div id="ai-chat-demo-container"></div>
</section>"""

        # 序列化 demo stages 为 JavaScript 对象字面量
        import json
        stages_js = json.dumps(demo.get("stages", {}), ensure_ascii=False, indent=2)

        data["demo_init_script"] = f"""<script>
window.halucatchDemo = new AIChatDemo({{
  container: '#ai-chat-demo-container',
  modelName: 'HaluCatch ' + HC_VER_SHORT,
  avatar: '{demo.get("avatar", "🔮")}',
  thinkingEnabled: true,
  thinkingLabel: '{demo_i18n.get("thinking_label", "Deep Thinking")}',
  endMessage: '{demo_i18n.get("end_message", "").format(name=data["name"])}',
  stages: {stages_js},
  reports: {{
    standard: REPORTS_DATA.standard,
    professional: REPORTS_DATA.professional,
    action: REPORTS_DATA.action
  }}
}});
setTimeout(function() {{ window.halucatchDemo.begin(); }}, 100);
</script>"""
    else:
        data["demo_section"] = ""
        data["demo_init_script"] = ""

    # ── 痛点 ──
    problem = config.get("problem_cards", {})
    if problem:
        prob_i18n = locale["problem"]
        cards_html = ""
        for card in problem.get("cards", []):
            tags_html = ""
            for tag in card.get("tags", []):
                tags_html += f'<span class="risk-tag {tag["class"]}">{tag["label"]}</span>\n'
            cards_html += f"""<div class="problem-card">
      <div class="icon">{card['icon']}</div>
      <h3>{card['title']}</h3>
      <p>{card['desc']}</p>
      <div class="problem-tags">
        {tags_html.strip()}
      </div>
    </div>\n"""
        issue_url = config["github_url"] + "/issues"
        data["problem_section"] = f"""<section class="anim-item scroll-anim">
  <h2>{prob_i18n["title"]}</h2>
  <div class="problem-grid">
    {cards_html.strip()}
  </div>
  <p style="text-align:center;margin-top:40px;font-size:0.85rem;color:var(--text2);">
    {prob_i18n["footer"]}
    <a href="{issue_url}" target="_blank" style="color:var(--accent);text-decoration:none;font-weight:600;">
      {prob_i18n["footer_link"]}
    </a>
  </p>
</section>"""
    else:
        data["problem_section"] = ""

    # ── 报告预览 ──
    rp = config.get("report_preview")
    if rp:
        rp_i18n = locale["report_preview"]
        tabs_html = ""
        for i, tab in enumerate(rp["tabs"]):
            active = " active" if i == 0 else ""
            tabs_html += f'<div class="preview-tab{active}" onclick="switchTab(\'{tab["id"]}\')">{tab["label"]}</div>\n'

        # 报告内容：支持内联 HTML 字符串或引用文件路径
        def load_content(key, tab_id):
            val = rp.get(key, "")
            if not val:
                return ""
            # 如果是文件路径（不含 <），读取文件内容
            if "<" not in str(val):
                content_path = ROOT.parent / val
                if content_path.exists():
                    return open(content_path, encoding="utf-8").read()
            return str(val)

        content_standard = load_content("content_standard", rp['tabs'][0]['id'])
        content_pro = load_content("content_pro", rp['tabs'][1]['id'])
        content_action = load_content("content_action", rp['tabs'][2]['id'])

        data["report_preview_section"] = f"""<section id="report-preview" class="anim-item scroll-anim">
  <h2>{rp_i18n["title"]}</h2>
  <p style="text-align:center;color:var(--text2);margin-bottom:24px;">{rp_i18n["subtitle"]}</p>
  <div class="preview-container">
    <div class="preview-tabs">
      {tabs_html.strip()}
    </div>
    <div class="preview-body">
      <div class="report-content active" id="tab-{rp['tabs'][0]['id']}">{content_standard}</div>
      <div class="report-content" id="tab-{rp['tabs'][1]['id']}">{content_pro}</div>
      <div class="report-content" id="tab-{rp['tabs'][2]['id']}">{content_action}</div>
    </div>
  </div>
</section>"""
    else:
        data["report_preview_section"] = ""

    # ── 快速开始 ──
    qs = config.get("quickstart")
    if qs:
        qs_i18n = locale["quickstart"]
        user_tab = qs_i18n["tab_user"]
        dev_tab = qs_i18n["tab_dev"]

        # 安装卡片
        install_cards = ""
        user = qs.get("user", {})
        if user.get("skillhub"):
            skillhub = user["skillhub"]
            install_cards += f"""<div class="install-card">
              <p class="install-title">{skillhub['title']}</p>
              <p class="install-subtitle">{skillhub['subtitle']}</p>
              <div class="install-note-wrap"><span class="install-note">{skillhub['note']}</span></div>
              <button class="install-copy-btn" onclick="copyInstall(this, `{skillhub['prompt'].strip()}`)"><span class="install-copy-text"><span class="copy-label">{data["copy_label"]}</span><span class="copied-label">{data["copied_label"]}</span></span></button>
            </div>\n"""
        if user.get("clawhub"):
            clawhub = user["clawhub"]
            install_cards += f"""<div class="install-card">
              <p class="install-title"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:4px;color:var(--accent);"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>{clawhub['title']}</p>
              <p class="install-subtitle">{clawhub['subtitle']}</p>
              <div class="install-note-wrap"><span class="install-note">{clawhub['note']}</span></div>
              <button class="install-copy-btn" onclick="copyInstall(this, `{clawhub['prompt'].strip()}`)"><span class="install-copy-text"><span class="copy-label">{data["copy_label"]}</span><span class="copied-label">{data["copied_label"]}</span></span></button>
            </div>\n"""

        # 审查对话
        chat_user = qs_i18n["audit_chat"]["user_msg"].format(name=data["name"])
        chat_scan = qs_i18n["audit_chat"]["ai_scan_msg"].strip()
        chat_done = qs_i18n["audit_chat"]["ai_done_msg"].strip()

        # 流程步骤
        flow_steps = ""
        for i, step in enumerate(qs_i18n["audit_flow"]["steps"]):
            icons = ["folder", "search", "file", "edit"]
            svg_map = {
                "folder": '<svg class="flow-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
                "search": '<svg class="flow-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M11 8v6M8 11h6"/></svg>',
                "file": '<svg class="flow-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
                "edit": '<svg class="flow-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>',
            }
            icon_svg = svg_map.get(icons[i] if i < len(icons) else "folder", svg_map["folder"])
            arrow = '<svg class="flow-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'
            flow_steps += f"""<div class="flow-step">
                {icon_svg}
                <span class="flow-label">{step['label']}</span>
              </div>"""
            if i < len(qs_i18n["audit_flow"]["steps"]) - 1:
                flow_steps += f"\n              {arrow}\n              "

        # 报告卡片
        rc = qs_i18n["report_cards"]
        report_cards = f"""<div class="report-card">
              <h4><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-4px;margin-right:6px;"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/><path d="M9 7h6"/><path d="M9 11h6"/><path d="M9 15h4"/></svg>{rc['standard']['title']}</h4>
              <div class="rc-audience">{rc['standard']['audience']}</div>
              <p>{rc['standard']['desc']}</p>
            </div>
            <div class="report-card">
              <h4><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-4px;margin-right:6px;"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>{rc['pro']['title']}</h4>
              <div class="rc-audience">{rc['pro']['audience']}</div>
              <p>{rc['pro']['desc']}</p>
            </div>
            <div class="report-card">
              <h4><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-4px;margin-right:6px;"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>{rc['action']['title']}</h4>
              <div class="rc-audience">{rc['action']['audience']}</div>
              <p>{rc['action']['desc']}</p>
            </div>"""

        repair_tip = rc.get("repair_tip", "")

        # 开发者
        dev = qs.get("dev", {})
        dev_i18n = qs_i18n.get("dev", {})

        data["quickstart_section"] = f"""<section id="quickstart" class="anim-item scroll-anim">
  <h2>{qs_i18n['title']}</h2>
  <div class="qs-tabs">
    <button class="qs-tab active" onclick="switchQsTab('user')">{user_tab}</button>
    <button class="qs-tab" onclick="switchQsTab('dev')">{dev_tab}</button>
  </div>

  <div id="qs-user" class="qs-panel active">
    <div class="install-steps">
      <div class="step">
        <div class="step-num">1</div>
        <div class="step-content">
          <h3>{qs_i18n['install']['step1_title']}</h3>
          <p>{qs_i18n['install']['step1_desc'].format(name=data['name'])}</p>
          <div class="install-cards">
            {install_cards.strip()}
          </div>
        </div>
      </div>
      <div class="step">
        <div class="step-num">2</div>
        <div class="step-content">
          <h3>{qs_i18n['install']['step2_title']}</h3>
          <p>{qs_i18n['install']['step2_desc']}</p>
          <div class="intro-chat">
            <div class="intro-msg user">
              <div class="intro-bubble">{chat_user}</div>
            </div>
            <div class="intro-msg ai">
              <div class="intro-msg-head">
                <span class="intro-avatar"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg></span>
                <span class="intro-name">{data['name']}</span>
              </div>
              <div class="intro-bubble">{chat_scan}</div>
            </div>
            <div class="intro-msg ai">
              <div class="intro-bubble">{chat_done}</div>
            </div>
          </div>
          <div class="audit-flow-wrap">
            <p class="flow-desc">{qs_i18n['audit_flow']['desc']}</p>
            <div class="audit-flow">
              {flow_steps.strip()}
            </div>
          </div>
        </div>
      </div>
      <div class="step">
        <div class="step-num">3</div>
        <div class="step-content">
          <h3>{qs_i18n['install']['step3_title']}</h3>
          <p>{qs_i18n['install']['step3_desc']}</p>
          <div class="report-cards">
            {report_cards.strip()}
          </div>
          <p style="margin-top:12px;color:var(--text2);">{repair_tip}</p>
        </div>
      </div>
    </div>
  </div>

  <div id="qs-dev" class="qs-panel">
    <div class="install-steps">
      <div class="step">
        <div class="step-num">1</div>
        <div class="step-content">
          <h3>{dev_i18n.get('step1_title', 'Clone')}</h3>
          <pre>{dev.get('clone_cmd', f'git clone {config["github_url"]}.git\ncd {config["name"]}').strip()}</pre>
        </div>
      </div>
      <div class="step">
        <div class="step-num">2</div>
        <div class="step-content">
          <h3>{dev_i18n.get('step2_title', 'Run')}</h3>
          <pre>{chr(10).join([f'<span class="comment">#{c["comment"]}</span>\n{c["cmd"]}' if c.get("comment") else c["cmd"] for c in dev.get("run_cmds", [])])}</pre>
        </div>
      </div>
      <div class="step">
        <div class="step-num">3</div>
        <div class="step-content">
          <h3>{dev_i18n.get('step3_title', 'View')}</h3>
          <pre>{dev.get('report_output', '').strip()}</pre>
        </div>
      </div>
    </div>
  </div>
</section>"""
    else:
        data["quickstart_section"] = ""

    # ── Blog ──
    blog = config.get("blog_posts")
    if blog and blog.get("items"):
        blog_i18n = locale.get("blog", {})
        items_html = ""
        for post in blog["items"]:
            items_html += f"""<a href="{post['url']}" target="_blank" class="blog-card">
      <div class="blog-platform">{post['platform']}</div>
      <h3>{post['title']}</h3>
      <p>{post['desc']}</p>
    </a>\n"""
        data["blog_section"] = f"""<section id="blog" class="anim-item scroll-anim">
  <h2><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:8px;position:relative;top:-2px;"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>{blog_i18n.get("title", blog.get("title", "Blogs"))}</h2>
  <div class="blog-grid">
    {items_html.strip()}
  </div>
</section>"""
    else:
        data["blog_section"] = ""

    # ── FAQ ──
    faq = config.get("faq")
    if faq and faq.get("items"):
        faq_i18n = locale["faq"]
        items_html = ""
        for item in faq["items"]:
            q = item["q"]
            a = item["a"].strip().replace("\n", "<br>")
            items_html += f"""<div class="faq-item glass">
      <button class="faq-q" onclick="toggleFaqItem(this)">
        <span>{q}</span>
        <svg class="faq-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
      </button>
      <div class="faq-a"><p>{a}</p></div>
    </div>\n"""
        full_link = ""
        if faq.get("full_link_url"):
            full_link = f"""<p style="text-align:center;margin-top:20px;">
    <a href="{faq['full_link_url']}" class="btn btn-outline">{faq_i18n.get('view_all', 'View Full FAQ →')}</a>
  </p>"""
        data["faq_section"] = f"""<section id="faq" class="anim-item scroll-anim">
  <h2><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:8px;position:relative;top:-2px;"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>{faq_i18n.get('title', faq.get('title', 'FAQ'))}</h2>
  <div class="faq-list">
    {items_html.strip()}
  </div>
  {full_link}
</section>"""
    else:
        data["faq_section"] = ""

    # ── Footer ──
    footer_i18n = locale["footer"]
    footer_links = ""
    for link in footer_i18n.get("links", []):
        footer_links += f'<a href="{config["github_url"]}">{link["label"]}</a>\n'
    # skillhub / clawhub footer
    if cta.get("skillhub"):
        footer_links += f'<a href="{cta["skillhub"]["url"]}" target="_blank">SkillHub</a>\n'
    if cta.get("clawhub"):
        footer_links += f'<a href="{cta["clawhub"]["url"]}" target="_blank">ClawHub</a>\n'
    data["footer_links"] = footer_links.strip()

    data["footer"] = {
        "copyright": footer_i18n["copyright"].format(
            name=data["name"],
            license=config.get("license", "MIT")
        ),
    }

    return data


def render_template(template_path, context, output_path):
    """简单的模板渲染：替换 {{ key }} 或 {{ a.b.c }} 占位符"""
    import re

    with open(template_path, encoding="utf-8") as f:
        html = f.read()

    def resolve(path):
        """支持点号路径：seo.title → context['seo']['title']"""
        parts = path.strip().split(".")
        val = context
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                return None
        return str(val) if val is not None else ""

    def replacer(m):
        path = m.group(1)
        return resolve(path)

    html = re.sub(r"\{\{ ([a-z0-9_.]+) \}\}", replacer, html)

    # 也保留扁平键名兼容（无点号）
    for key, value in context.items():
        if not isinstance(value, (dict, list)):
            html = html.replace(f"{{{{ {key} }}}}", str(value))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ {output_path}")


def copy_assets(output_dir, config=None):
    """复制 web/assets/ 全部静态资源到输出目录"""
    assets_src = ROOT / "assets"
    if assets_src.exists():
        dest = output_dir / "assets"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(assets_src, dest)
        print(f"  📁 assets → {dest}")

    # 替换 theme.js 中的 STORAGE_KEY 占位符
    theme_js = dest / "js" / "theme.js"
    if theme_js.exists():
        content = theme_js.read_text(encoding="utf-8")
        content = content.replace("{{ theme_storage_key }}", config.get("theme_storage_key", "halucatch-theme"))
        theme_js.write_text(content, encoding="utf-8")
        print("  🔧 theme.js STORAGE_KEY replaced")

    # 复制 favicon 到输出根目录（浏览器默认从 / 加载）
    favicon = assets_src / "images" / "favicon.svg"
    if favicon.exists():
        shutil.copy2(favicon, output_dir / "favicon.svg")
        print(f"  📄 favicon.svg → {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Build HaluCatch website")
    parser.add_argument("--lang", default="zh-CN", help="Target language (default: zh-CN)")
    parser.add_argument("--all", action="store_true", help="Build all languages")
    args = parser.parse_args()

    config = load_yaml(ROOT / "config.yaml")
    template = ROOT / "templates" / "index.html"

    if not template.exists():
        print("❌ Template not found:", template)
        return

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
        context = merge_config(config, locale)

        # 输出路径：docs/index.html (zh-CN) 或 docs/{lang}/index.html
        out_dir = DIST if lang == "zh-CN" else DIST / lang

        render_template(template, context, out_dir / "index.html")
        copy_assets(out_dir, config)

    print(f"\n🎉 Done! Output in {DIST}/")


if __name__ == "__main__":
    main()
