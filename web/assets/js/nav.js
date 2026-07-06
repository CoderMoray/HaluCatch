/* ============================================================
   HaluCatch — 导航栏智能显隐 + 汉堡菜单
   ============================================================ */
(function() {
  var nav = document.querySelector('.nav');
  var demoSection = document.getElementById('demo');
  var threshold, mouseNearTop = false, scrollPast = false;

  function updateThreshold() {
    threshold = demoSection
      ? demoSection.getBoundingClientRect().top + window.scrollY - (window.innerHeight / 2)
      : 800;
  }
  updateThreshold();
  window.addEventListener('resize', updateThreshold);

  function shouldShow() { return !scrollPast || mouseNearTop; }

  function refresh() {
    scrollPast = window.scrollY > threshold && window.scrollY > 100;
    if (shouldShow()) nav.classList.remove('hidden');
    else nav.classList.add('hidden');
  }

  window.addEventListener('scroll', refresh, { passive: true });

  document.addEventListener('mousemove', function(e) {
    var near = e.clientY < 60;
    if (near !== mouseNearTop) {
      mouseNearTop = near;
      refresh();
    }
  });

  // 汉堡菜单
  var hamburger = document.getElementById('nav-hamburger');
  var navLinks = document.getElementById('nav-links');
  hamburger.addEventListener('click', function() {
    navLinks.classList.toggle('open');
  });
  navLinks.addEventListener('click', function(e) {
    if (e.target.classList.contains('nav-link')) navLinks.classList.remove('open');
  });

  // 品牌文字 clip-path 滑动动画
  (function() {
    var full = document.querySelector('.brand-full');
    var short = document.querySelector('.brand-short');
    function calcShift() {
      if (!full || !short) return;
      var targetW = short.offsetWidth;
      var totalW = full.offsetWidth;
      document.documentElement.style.setProperty('--brand-shift', (totalW - targetW) + 'px');
    }
    window.addEventListener('resize', calcShift);
    setTimeout(calcShift, 200);
  })();
})();
