/* ============================================================
   HaluCatch — Tab 切换（报告预览 + 快速开始）+ KaTeX 渲染
   ============================================================ */
(function() {
  function renderMathInElement(el) {
    if (typeof katex === 'undefined') return;
    // 查找 $...$ 并替换为 KaTeX HTML
    el.innerHTML = el.innerHTML.replace(/\$([^\$]+)\$/g, function(match, math) {
      try {
        return katex.renderToString(math.trim(), { throwOnError: false, displayMode: false });
      } catch(e) {
        return match;
      }
    });
    // 整个 KaTeX 公式字号继承父级（抵消默认 1.21em 缩放）
    el.querySelectorAll('.katex').forEach(function(k) {
      k.style.setProperty('font-size', 'inherit', 'important');
    });
    // KaTeX 中文使用页面字体
    el.querySelectorAll('.cjk_fallback').forEach(function(span) {
      span.style.setProperty('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif', 'important');
    });
  }

  window.switchTab = function(name, el) {
    document.querySelectorAll('.preview-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.preview-body .report-content').forEach(function(c) { c.classList.remove('active'); });
    if (el) el.classList.add('active');
    document.getElementById('tab-' + name).classList.add('active');
    var activeContent = document.getElementById('tab-' + name);
    if (activeContent) renderMathInElement(activeContent);
  };

  // 初始加载时渲染所有 tab 中的 KaTeX
  function initRender() {
    if (typeof katex === 'undefined') {
      // KaTeX 还没加载好，延迟重试
      return setTimeout(initRender, 50);
    }
    document.querySelectorAll('.preview-body .report-content').forEach(function(el) {
      renderMathInElement(el);
    });
  }
  initRender();

  window.switchQsTab = function(name, el) {
    document.querySelectorAll('.qs-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.qs-panel').forEach(function(p) { p.classList.remove('active'); });
    if (el) el.classList.add('active');
    document.getElementById('qs-' + name).classList.add('active');
  };
})();
