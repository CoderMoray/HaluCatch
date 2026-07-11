/* ============================================================
   HaluCatch — 入场动画
   全页面 data-anim 交错延迟，按顺序逐个出现
   ============================================================ */
(function() {
  var nav = document.querySelector('.nav');
  var isTop = window.scrollY < 200;

  if (!isTop) {
    nav.classList.remove('entering');
    document.documentElement.style.setProperty('--glow-opacity', '1');
    document.querySelectorAll('.anim-item').forEach(function(el) { el.classList.add('in'); });
    if (window.halucatchDemo) window.halucatchDemo.begin();
    return;
  }

  setTimeout(function() {
    document.documentElement.style.setProperty('--glow-opacity', '1');
  }, 0);

  setTimeout(function() {
    nav.classList.remove('entering');
  }, 200);

  // 全页面 data-anim 交错延迟
  var demoDelay = 0;
  document.querySelectorAll('.anim-item[data-anim]').forEach(function(el) {
    var delay = parseInt(el.getAttribute('data-anim')) || 0;
    setTimeout(function() { el.classList.add('in'); }, delay);
    // 记录 demo section 的延迟，在它之后启动 demo
    if (el.id === 'demo') { demoDelay = delay; }
  });

  // Demo 启动：紧跟 demo section 入场之后
  if (demoDelay > 0 && window.halucatchDemo) {
    setTimeout(function() { window.halucatchDemo.begin(); }, demoDelay + 400);
  }
})();
