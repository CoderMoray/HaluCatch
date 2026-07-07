/* ============================================================
   HaluCatch — 主题切换
   暗色 / 亮色 / 跟随系统，滑动药丸指示器，3 段渐变光晕
   ============================================================ */
(function() {
  var STORAGE_KEY = 'halucatch-theme';
  var pill = document.getElementById('theme-pill');
  var btns = pill.querySelectorAll('.theme-pill-btn');
  var mql = window.matchMedia('(prefers-color-scheme: dark)');

  var indicator = document.createElement('div');
  indicator.className = 'theme-pill-indicator';
  pill.insertBefore(indicator, pill.firstChild);

  function getTheme() { return localStorage.getItem(STORAGE_KEY) || 'system'; }

  function setTheme(t) {
    document.documentElement.style.setProperty('--glow-opacity', '0');
    setTimeout(function() {
      localStorage.setItem(STORAGE_KEY, t);
      applyThemeInternal();
      setTimeout(function() {
        document.documentElement.style.setProperty('--glow-opacity', '1');
      }, 600);
    }, 300);
  }

  function resolveTheme(t) {
    if (t === 'system') return mql.matches ? 'dark' : 'light';
    return t;
  }

  function applyThemeInternal() {
    var t = getTheme();
    document.documentElement.setAttribute('data-theme', resolveTheme(t));
    syncIndicator(t);
  }

  function syncIndicator(saved) {
    btns.forEach(function(b) {
      var active = b.dataset.theme === saved;
      b.classList.toggle('active', active);
      if (active) {
        indicator.style.left = b.offsetLeft + 'px';
        indicator.style.width = b.offsetWidth + 'px';
      }
    });
  }

  btns.forEach(function(b) {
    b.addEventListener('click', function() { setTheme(b.dataset.theme); });
  });

  mql.addEventListener('change', function() {
    if (getTheme() === 'system') applyThemeInternal();
  });

  // ── 首次加载 ──
  // 页面已用 Dark 渲染，data-theme="dark"
  // 药丸固定在 system
  function initTheme() {
    var saved = getTheme();
    syncIndicator(saved);  // 药丸 → system

    var actual = resolveTheme(saved);
    // 系统是 Dark → 不动；系统是 Light → 暗→亮渐变
    if (actual !== 'dark') {
      requestAnimationFrame(function() {
        requestAnimationFrame(function() {
          document.documentElement.setAttribute('data-theme', actual);
        });
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }

  // ── Indicator 平滑跟踪 ──
  var tracking = false;
  function scheduleIndicator() {
    if (!tracking) { tracking = true; requestAnimationFrame(trackLoop); }
  }
  function trackLoop() {
    syncIndicator(getTheme());
    requestAnimationFrame(trackLoop);
  }
  var idleTimer;
  function resetIdle() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function() { tracking = false; }, 150);
  }

  if (typeof ResizeObserver !== 'undefined') {
    var ro = new ResizeObserver(function() { scheduleIndicator(); resetIdle(); });
    ro.observe(pill);
    ro.observe(document.querySelector('.nav-inner'));
  }
  window.addEventListener('resize', function() { scheduleIndicator(); resetIdle(); });
})();
