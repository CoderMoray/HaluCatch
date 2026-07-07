/* ============================================================
   HaluCatch — 一键复制安装提示词
   ============================================================ */
(function() {
  window.copyInstall = function(btn, text) {
    navigator.clipboard.writeText(text).then(function() {
      btn.classList.add('copied');
      setTimeout(function() { btn.classList.remove('copied'); }, 2000);
    });
  };
})();
