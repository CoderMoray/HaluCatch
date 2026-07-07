/* ============================================================
   HaluCatch — 入场动画
   首屏 staggered delay，下方 scroll-triggered IntersectionObserver
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

  document.querySelectorAll('.anim-item[data-anim]').forEach(function(el) {
    var delay = parseInt(el.getAttribute('data-anim')) || 0;
    setTimeout(function() { el.classList.add('in'); }, delay);
  });

  setTimeout(function() {
    if (window.halucatchDemo) window.halucatchDemo.begin();
  }, 2500);

  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.anim-item.scroll-anim').forEach(function(el) {
    observer.observe(el);
  });
})();
