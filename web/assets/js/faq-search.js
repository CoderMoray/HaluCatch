/* ============================================================
   HaluCatch — FAQ 页面：搜索过滤 + 回到顶部按钮
   ============================================================ */
(function() {
  'use strict';

  // ── Back to Top ──
  var backBtn = document.getElementById('back-to-top');
  if (backBtn) {
    var ticking = false;
    window.addEventListener('scroll', function() {
      if (!ticking) {
        requestAnimationFrame(function() {
          backBtn.classList.toggle('visible', window.scrollY > 400);
          ticking = false;
        });
        ticking = true;
      }
    });
    backBtn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ── Search Filter ──
  var searchInput = document.querySelector('.faq-search');
  var clearBtn = document.getElementById('faq-search-clear');
  var noResults = document.getElementById('faq-no-results');
  if (!searchInput) return;

  function filterFaq(query) {
    var q = query.trim().toLowerCase();
    // 显示/隐藏清除按钮
    if (clearBtn) clearBtn.classList.toggle('visible', q.length > 0);

    var totalVisible = 0;

    // 遍历所有 faq-section 分类区块
    var sections = document.querySelectorAll('.faq-section');
    sections.forEach(function(section) {
      if (!q) {
        section.classList.remove('hidden');
        // 恢复所有子项可见
        var items = section.querySelectorAll('.faq-item, .faq-table tbody tr, .scene-card, .cap-card');
        items.forEach(function(el) { el.classList.remove('hidden'); });
        totalVisible++;
        return;
      }

      var sectionTitle = (section.querySelector('.faq-section-title') || {}).textContent || '';
      var sectionMatch = sectionTitle.toLowerCase().indexOf(q) !== -1;

      // 处理 Q&A items
      var faqItems = section.querySelectorAll('.faq-item');
      faqItems.forEach(function(item) {
        var match = sectionMatch || item.textContent.toLowerCase().indexOf(q) !== -1;
        item.classList.toggle('hidden', !match);
        if (match) totalVisible++;
      });

      // 处理表格行
      var tableRows = section.querySelectorAll('.faq-table tbody tr');
      tableRows.forEach(function(row) {
        var match = sectionMatch || row.textContent.toLowerCase().indexOf(q) !== -1;
        row.classList.toggle('hidden', !match);
        if (match) totalVisible++;
      });

      // 处理场景卡片
      var sceneCards = section.querySelectorAll('.scene-card');
      sceneCards.forEach(function(card) {
        var match = sectionMatch || card.textContent.toLowerCase().indexOf(q) !== -1;
        card.classList.toggle('hidden', !match);
        if (match) totalVisible++;
      });

      // 处理能力边界卡片
      var capCards = section.querySelectorAll('.cap-card');
      capCards.forEach(function(card) {
        var match = sectionMatch || card.textContent.toLowerCase().indexOf(q) !== -1;
        card.classList.toggle('hidden', !match);
        if (match) totalVisible++;
      });

      // 判断整个 section 是否还有可见项
      var hasVisible = false;
      var checkables = section.querySelectorAll('.faq-item, .faq-table tbody tr, .scene-card, .cap-card');
      checkables.forEach(function(el) {
        if (!el.classList.contains('hidden')) hasVisible = true;
      });
      if (checkables.length > 0 && !hasVisible && !sectionMatch) {
        section.classList.add('hidden');
      } else {
        section.classList.remove('hidden');
      }
    });

    // 无结果提示
    if (noResults) {
      var hasAnyVisible = query.trim() === '' || totalVisible > 0;
      noResults.classList.toggle('visible', query.trim() !== '' && !hasAnyVisible);
    }
  }

  searchInput.addEventListener('input', function() {
    filterFaq(this.value);
  });

  // 清除按钮
  if (clearBtn) {
    clearBtn.addEventListener('click', function() {
      searchInput.value = '';
      filterFaq('');
      searchInput.focus();
    });
  }

  // ── Keyword Chips ──
  document.addEventListener('click', function(e) {
    var chip = e.target.closest('.keyword-chip');
    if (chip) {
      var keyword = chip.getAttribute('data-keyword');
      if (keyword && searchInput) {
        searchInput.value = keyword;
        filterFaq(keyword);
        searchInput.focus();
      }
    }
  });
})();
