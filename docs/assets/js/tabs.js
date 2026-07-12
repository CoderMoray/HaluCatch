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
  }

  window.switchTab = function(name, el) {
    document.querySelectorAll('.preview-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.preview-body .report-content').forEach(function(c) { c.classList.remove('active'); });
    if (el) el.classList.add('active');
    document.getElementById('tab-' + name).classList.add('active');
    var activeContent = document.getElementById('tab-' + name);
    if (activeContent) renderMathInElement(activeContent);
  };

  // 初始加载时渲染所有 tab 中的 KaTeX（即使隐藏）
  document.querySelectorAll('.preview-body .report-content').forEach(function(el) {
    renderMathInElement(el);
  });

  window.switchQsTab = function(name, el) {
    document.querySelectorAll('.qs-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.qs-panel').forEach(function(p) { p.classList.remove('active'); });
    if (el) el.classList.add('active');
    document.getElementById('qs-' + name).classList.add('active');
  };
})();
