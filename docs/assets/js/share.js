/* ============================================================
   HaluCatch — 分享按钮（复制链接 / 飞书 / X）
   ============================================================ */
(function() {
  var URL = '{{ pages_url }}';
  var toast = document.createElement('div');
  toast.className = 'share-toast';
  document.body.appendChild(toast);

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(function() { toast.classList.remove('show'); }, 2000);
  }

  document.querySelectorAll('.nav-share-item').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var platform = btn.getAttribute('data-platform');
      if (platform === 'twitter') {
        window.open('https://x.com/intent/post?url=' + encodeURIComponent(URL) + '&text=' + encodeURIComponent('{{ share_text }}'), '_blank');
        return;
      }
      navigator.clipboard.writeText(URL).then(function() {
        var labels = { feishu: '{{ share_toast_feishu }}', url: '' };
        showToast('{{ share_toast_prefix }}' + (labels[platform] || platform) + '{{ share_toast_suffix }}');
      }).catch(function() {
        showToast('{{ share_toast_failed }}');
      });
    });
  });
})();
