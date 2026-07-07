/* ============================================================
   HaluCatch — 版本号注入 + JSON-LD
   ============================================================ */
(function() {
  var badge = document.getElementById('badge-version');
  if (badge) badge.textContent = 'v' + window.HC_VER;

  var ld = document.createElement('script');
  ld.type = 'application/ld+json';
  ld.textContent = JSON.stringify(window.buildJSONLD());
  document.head.appendChild(ld);
})();
