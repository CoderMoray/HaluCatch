/* ============================================================
   HaluCatch — FAQ 折叠展开 + 连续右旋箭头动画
   ============================================================ */
(function() {
  var faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach(function(item) {
    item.addEventListener('transitionend', function(e) {
      if (e.target === item.querySelector('.faq-a') && !item.classList.contains('open')) {
        item.querySelector('.faq-a').style.maxHeight = '';
      }
    });
  });

  window.toggleFaqItem = function(btn) {
    var item = btn.parentElement;
    var arrow = item.querySelector('.faq-arrow');
    var isOpen = item.classList.contains('open');

    if (isOpen) {
      arrow.style.transition = 'transform 0.4s ease';
      arrow.style.transform = 'rotate(360deg)';
      var done = false;
      arrow.addEventListener('transitionend', function reset() {
        if (done) return;
        done = true;
        arrow.removeEventListener('transitionend', reset);
        arrow.style.transition = 'none';
        arrow.style.transform = '';
        arrow.offsetHeight;
      });
      item.classList.remove('open');
      var body = item.querySelector('.faq-a');
      body.style.maxHeight = body.scrollHeight + 'px';
      body.offsetHeight;
      body.style.maxHeight = '0px';
    } else {
      arrow.style.cssText = '';
      item.classList.add('open');
      var body = item.querySelector('.faq-a');
      body.style.maxHeight = body.scrollHeight + 'px';
    }
  };
})();
