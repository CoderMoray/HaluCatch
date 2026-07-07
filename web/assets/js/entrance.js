/* ============================================================
   HaluCatch — 入场动画
   首屏 staggered delay，下方 scroll-triggered IntersectionObserver
   所有 section 按滚动顺序进入
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

  // 首屏 hero 元素：保留 staggered delay
  document.querySelectorAll('.anim-item[data-anim]').forEach(function(el) {
    var delay = parseInt(el.getAttribute('data-anim')) || 0;
    setTimeout(function() { el.classList.add('in'); }, delay);
  });

  // 所有 section：IntersectionObserver 统一处理
  // requestAnimationFrame 确保浏览器 commit 了初始 opacity:0 再触发 transition
  var demoStarted = false;
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        requestAnimationFrame(function() {
          entry.target.classList.add('in');
        });
        if (entry.target.id === 'demo' && !demoStarted && window.halucatchDemo) {
          demoStarted = true;
          setTimeout(function() { window.halucatchDemo.begin(); }, 400);
        }
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.anim-item.scroll-anim').forEach(function(el) {
    observer.observe(el);
  });
})();
