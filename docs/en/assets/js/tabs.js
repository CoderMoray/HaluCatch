/* ============================================================
   HaluCatch — Tab 切换（报告预览 + 快速开始）
   ============================================================ */
(function() {
  window.switchTab = function(name) {
    document.querySelectorAll('.preview-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.preview-body .report-content').forEach(function(c) { c.classList.remove('active'); });
    event.currentTarget.classList.add('active');
    document.getElementById('tab-' + name).classList.add('active');
  };

  window.switchQsTab = function(name) {
    document.querySelectorAll('.qs-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.qs-panel').forEach(function(p) { p.classList.remove('active'); });
    event.currentTarget.classList.add('active');
    document.getElementById('qs-' + name).classList.add('active');
  };
})();
