/* ============================================================
   HaluCatch — 主题切换
   暗色 / 亮色 / 跟随系统，滑动药丸指示器，3 段渐变光晕
   ============================================================ */
(function() {
  var STORAGE_KEY = '{{ theme_storage_key }}';
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
    var resolved = resolveTheme(t);
    document.documentElement.setAttribute('data-theme', resolved);
    btns.forEach(function(b) {
      var active = b.dataset.theme === t;
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

  function updateIndicator() {
    var saved = getTheme();
    btns.forEach(function(b) {
      if (b.dataset.theme === saved) {
        indicator.style.left = b.offsetLeft + 'px';
        indicator.style.width = b.offsetWidth + 'px';
      }
    });
  }

  var tracking = false;
  function scheduleIndicator() {
    if (!tracking) { tracking = true; requestAnimationFrame(trackLoop); }
  }
  function trackLoop() {
    updateIndicator();
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

  // 初始同步
  var saved = getTheme();
  btns.forEach(function(b) {
    var active = b.dataset.theme === saved;
    b.classList.toggle('active', active);
    if (active) {
      indicator.style.left = b.offsetLeft + 'px';
      indicator.style.width = b.offsetWidth + 'px';
    }
  });
})();
