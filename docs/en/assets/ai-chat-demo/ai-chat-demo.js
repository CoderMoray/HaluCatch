// AI Chat Demo — HaluCatch Interactive Component
// v2.0: thinking char-by-char, model dropdown, fixed markdown rendering

class AIChatDemo {
  constructor(config) {
    this.container = document.querySelector(config.container);
    if (!this.container) throw new Error('Container not found: ' + config.container);
    
    this.modelName = config.modelName || 'AI Assistant';
    this.avatar = config.avatar || '🤖';
    this.thinkingEnabled = config.thinkingEnabled !== false;
    this.thinkingLabel = config.thinkingLabel || '深度思考';
    this.stages = config.stages || {};
    this.reports = config.reports || {};
    this.endMessage = config.endMessage || '演示结束';
    this.typingSpeed = 30; // ms per character
    
    this.currentStage = 'init';
    this.isTyping = false;
    this.reportVisible = false;
    this.currentAiMessage = null;
    
    this.init();
  }
  
  init() {
    this.container.innerHTML = this.buildHTML();
    this.cacheElements();
    this.bindEvents();
    // startStage deferred — entrance animation triggers begin()
  }
  
  begin() {
    if (this._begun) return Promise.resolve();
    this._begun = true;
    return this.startStage('init');
  }
  
  buildHTML() {
    return `
      <div class="ai-chat-demo">
        <div class="chat-panel">
          <div class="chat-header">
            <div class="chat-header-left">
              <span class="chat-model-name">${this.modelName}</span>
            </div>
          </div>
          <div class="chat-messages"></div>
          <div class="chat-input-area">
            <!-- Toolbar: thinking button + model selector -->
            <div class="chat-input-toolbar">
              <button class="chat-thinking-btn ${this.thinkingEnabled ? 'active' : ''}">
                <span class="brain-icon">🧠</span>
                <span>${this.thinkingLabel}</span>
              </button>
              <div class="chat-model-dropdown-wrapper">
                <button class="chat-model-selector">
                  <span class="model-icon">⚡</span>
                  <span class="model-name">${this.modelName}</span>
                  <span class="dropdown-arrow">▼</span>
                </button>
                <div class="model-dropdown-menu" style="display:none;">
                  <div class="model-dropdown-header">模型选择</div>
                  <div class="model-dropdown-item active" data-model="${this.modelName}">
                    <span class="model-dropdown-icon">⚡</span>
                    <span class="model-dropdown-name">${this.modelName}</span>
                    <span class="model-dropdown-check">✓</span>
                  </div>
                </div>
              </div>
            </div>
            <!-- Input row -->
            <div class="chat-input-row" id="input-row">
              <textarea class="chat-input" rows="1" placeholder="输入消息..." disabled></textarea>
              <button class="chat-send-btn" disabled aria-label="发送">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(-90deg); display: block;">
                  <path d="M3.714 3.048a.498.498 0 0 0-.683.627l2.843 7.627a2 2 0 0 1 0 1.396l-2.842 7.627a.498.498 0 0 0 .682.627l18-8.5a.5.5 0 0 0 0-.904z"/>
                  <path d="M6 12h16"/>
                </svg>
              </button>
            </div>
            <!-- Options area (replaces input row) -->
            <div class="chat-options-area" id="options-area"></div>
          </div>
        </div>
        <div class="report-panel">
          <div class="report-tabs">
            <button class="report-tab" data-report="standard">标准版</button>
            <button class="report-tab" data-report="professional">专业版</button>
            <button class="report-tab" data-report="action">AI 行动版</button>
          </div>
          <div class="report-content"></div>
        </div>
      </div>
    `;
  }
  
  cacheElements() {
    this.el = {
      messages: this.container.querySelector('.chat-messages'),
      inputRow: this.container.querySelector('#input-row'),
      input: this.container.querySelector('.chat-input'),
      sendBtn: this.container.querySelector('.chat-send-btn'),
      optionsArea: this.container.querySelector('#options-area'),
      toolbar: this.container.querySelector('.chat-input-toolbar'),
      thinkingBtn: this.container.querySelector('.chat-thinking-btn'),
      modelSelector: this.container.querySelector('.chat-model-selector'),
      dropdownMenu: this.container.querySelector('.model-dropdown-menu'),
      reportPanel: this.container.querySelector('.report-panel'),
      reportContent: this.container.querySelector('.report-content'),
      reportTabs: this.container.querySelectorAll('.report-tab')
    };
  }
  
  bindEvents() {
    this.el.sendBtn.addEventListener('click', () => this.handleUserInput());
    this.el.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleUserInput();
      }
    });
    
    // Thinking toggle
    this.el.thinkingBtn.addEventListener('click', () => {
      this.thinkingEnabled = !this.thinkingEnabled;
      this.el.thinkingBtn.classList.toggle('active', this.thinkingEnabled);
    });
    
    // Model dropdown toggle
    this.el.modelSelector.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleDropdown();
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
      this.el.dropdownMenu.style.display = 'none';
    });
    
    // Report tabs
    this.el.reportTabs.forEach(tab => {
      tab.addEventListener('click', () => this.switchReport(tab.dataset.report));
    });
  }
  
  toggleDropdown() {
    const isVisible = this.el.dropdownMenu.style.display === 'block';
    this.el.dropdownMenu.style.display = isVisible ? 'none' : 'block';
  }
  
  // ── Stage Management ──────────────────────────────────────
  
  async startStage(stageName) {
    this.currentStage = stageName;
    const stage = this.stages[stageName];
    if (!stage) return;
    
    // 兼容 snake_case (JSON) 和 camelCase (JS)
    const aiMsg = stage.aiMessage || stage.ai_message;
    const opts = stage.options;
    const showRep = stage.showReports || stage.show_reports;
    const think = stage.thinking;
    
    if (aiMsg) {
      await this.typeMessage(aiMsg, 'ai');
    }
    
    if (opts) {
      this.showOptionsInInputArea(opts);
    } else {
      this.showInput();
    }
    
    if (showRep) {
      this.showReports();
    }
  }
  
  // ── Input/Options Toggle ─────────────────────────────────────
  
  showOptionsInInputArea(options) {
    this.el.inputRow.classList.add('hidden');
    this.el.optionsArea.classList.add('visible');
    this.el.optionsArea.innerHTML = '';
    
    const hint = document.createElement('span');
    hint.className = 'chat-options-hint';
    hint.textContent = '👇 选择一个选项继续';
    this.el.toolbar.insertBefore(hint, this.el.toolbar.firstChild);
    requestAnimationFrame(() => hint.classList.add('visible'));
    
    const list = document.createElement('div');
    list.className = 'chat-options-list';
    
    options.forEach((opt, i) => {
      const btn = document.createElement('button');
      btn.className = 'chat-option-btn';
      btn.textContent = opt.text;
      btn.style.transitionDelay = (i * 0.08) + 's';
      btn.addEventListener('click', () => this.handleOptionClick(opt));
      list.appendChild(btn);
    });
    
    this.el.optionsArea.appendChild(list);
    requestAnimationFrame(() => {
      list.querySelectorAll('.chat-option-btn').forEach(b => b.classList.add('visible'));
    });
  }
  
  showInput() {
    const hint = this.el.toolbar.querySelector('.chat-options-hint');
    if (hint) {
      hint.classList.remove('visible');
      setTimeout(() => hint.remove(), 300);
    }
    this.el.optionsArea.classList.remove('visible');
    setTimeout(() => { this.el.optionsArea.innerHTML = ''; }, 350);
    this.el.inputRow.classList.remove('hidden');
    this.el.input.disabled = false;
    this.el.sendBtn.disabled = false;
    this.el.input.focus();
  }
  
  // ── Message Rendering — Character by Character ─────────────────
  
  async typeMessage(text, sender) {
    if (this.isTyping) return;
    this.isTyping = true;
    
    let msg;
    if (sender === 'ai' && this.currentAiMessage) {
      msg = this.currentAiMessage;
      this.currentAiMessage = null;
    } else {
      msg = document.createElement('div');
      msg.className = `chat-message ${sender}`;
      if (sender === 'ai') {
        msg.innerHTML = this.aiMessageHeader();
      }
      this.el.messages.appendChild(msg);
    }
    
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble typing-cursor';
    msg.appendChild(bubble);
    this.scrollToBottom();
    
    let currentText = '';
    
    for (let i = 0; i < text.length; i++) {
      await this.delay(this.typingSpeed);
      currentText += text[i];
      bubble.textContent = currentText;
      this.scrollToBottom();
    }
    
    bubble.classList.remove('typing-cursor');
    this.isTyping = false;
  }
  
  addMessage(text, sender) {
    const msg = document.createElement('div');
    msg.className = `chat-message ${sender}`;
    msg.innerHTML = `<div class="chat-bubble"></div>`;
    msg.querySelector('.chat-bubble').textContent = text;
    this.el.messages.appendChild(msg);
    this.scrollToBottom();
  }
  
  // ── Thinking Flow — Character by Character ─────────────────
  
  async runThinking(lines, onComplete) {
    if (!this.thinkingEnabled) {
      onComplete();
      return;
    }
    
    // Create AI message container with avatar + name
    const msg = document.createElement('div');
    msg.className = 'chat-message ai';
    msg.innerHTML = this.aiMessageHeader();
    
    // Create thinking block inside this message
    const thinkingBlock = document.createElement('div');
    thinkingBlock.className = 'chat-thinking expanded';
    thinkingBlock.innerHTML = `
      <div class="chat-thinking-header">
        <span class="chat-thinking-icon">▶</span>
        <span>${this.thinkingLabel}</span>
      </div>
      <div class="chat-thinking-body">
        <div class="chat-thinking-lines"></div>
      </div>
    `;
    msg.appendChild(thinkingBlock);
    this.el.messages.appendChild(msg);
    this.scrollToBottom();
    
    // Store for typeMessage to reuse
    this.currentAiMessage = msg;
    
    const header = thinkingBlock.querySelector('.chat-thinking-header');
    header.addEventListener('click', () => thinkingBlock.classList.toggle('expanded'));
    
    // Type each thinking line
    const linesContainer = thinkingBlock.querySelector('.chat-thinking-lines');
    
    for (let i = 0; i < lines.length; i++) {
      const lineEl = document.createElement('div');
      lineEl.className = 'chat-thinking-line typing-cursor';
      lineEl.style.opacity = '1';
      linesContainer.appendChild(lineEl);
      
      let currentText = '';
      for (let j = 0; j < lines[i].length; j++) {
        await this.delay(20);
        currentText += lines[i][j];
        lineEl.textContent = currentText;
        this.scrollToBottom();
      }
      lineEl.classList.remove('typing-cursor');
      await this.delay(200 + Math.random() * 300);
    }
    
    // Pause, then collapse
    await this.delay(600);
    thinkingBlock.classList.remove('expanded');
    
    setTimeout(() => onComplete(), 400);
  }
  
  aiMessageHeader() {
    return `<div class="chat-message-header">
      <div class="chat-message-avatar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" /></svg></div>
      <span class="chat-message-name">HaluCatch Agent</span>
    </div>`;
  }
  
  // ── User Interaction ────────────────────────────────────
  
  handleOptionClick(option) {
    if (this.isTyping) return;
    const hint = this.el.toolbar.querySelector('.chat-options-hint');
    if (hint) { hint.classList.remove('visible'); setTimeout(() => hint.remove(), 300); }
    
    const btns = this.el.optionsArea.querySelectorAll('.chat-option-btn');
    btns.forEach(b => b.classList.remove('visible'));
    this.el.optionsArea.classList.remove('visible');
    
    this.addMessage(option.text, 'user');
    
    setTimeout(() => this.transitionTo(option.next), 400);
  }
  
  async handleUserInput() {
    const text = this.el.input.value.trim();
    if (!text || this.isTyping) return;
    
    this.addMessage(text, 'user');
    this.el.input.value = '';
    
    await this.delay(300);
    this.typeMessage(this.endMessage, 'ai');
  }
  
  transitionTo(stageName) {
    const stage = this.stages[stageName];
    if (!stage) return;
    
    const aiMsg = stage.aiMessage || stage.ai_message;
    const opts = stage.options;
    const showRep = stage.showReports || stage.show_reports;
    const think = stage.thinking;
    
    if (think && think.length > 0) {
      this.runThinking(think, async () => {
        if (aiMsg) {
          await this.typeMessage(aiMsg, 'ai');
        }
        if (showRep) {
          this.showReports();
          this.showInput();
        } else if (opts) {
          this.showOptionsInInputArea(opts);
        } else {
          this.showInput();
        }
      });
    } else {
      (async () => {
        if (aiMsg) {
          await this.typeMessage(aiMsg, 'ai');
        }
        if (showRep) {
          this.showReports();
          this.showInput();
        } else if (opts) {
          this.showOptionsInInputArea(opts);
        } else {
          this.showInput();
        }
      })();
    }
  }
  
  // ── Reports Panel ───────────────────────────────────────
  
  showReports() {
    this.reportVisible = true;

    var indicator = document.createElement('div');
    indicator.className = 'report-tab-indicator';
    this.el.reportPanel.querySelector('.report-tabs').appendChild(indicator);
    this.el.reportTabIndicator = indicator;

    this.el.reportPanel.classList.add('visible');
    setTimeout(() => this.switchReport('standard'), 520);
  }
  
  switchReport(type) {
    const tabs = this.el.reportTabs;
    const idxMap = { standard: 0, professional: 1, action: 2 };
    const oldIdx = Array.from(tabs).findIndex(t => t.classList.contains('active'));
    const newIdx = idxMap[type];
    if (oldIdx === newIdx) return;

    tabs.forEach(t => t.classList.toggle('active', t.dataset.report === type));

    // Slide tab indicator
    const activeTab = this.el.reportPanel.querySelector('.report-tab.active');
    if (this.el.reportTabIndicator && activeTab) {
      this.el.reportTabIndicator.style.left = activeTab.offsetLeft + 'px';
      this.el.reportTabIndicator.style.width = activeTab.offsetWidth + 'px';
    }

    // Two-phase content slide
    if (oldIdx === -1) {
      // First load: just show
      const c = this.reports[type] || '> 暂无报告内容';
      this.el.reportContent.innerHTML = this.renderMarkdown(c);
      return;
    }

    const dir = newIdx > oldIdx ? 'left' : 'right';
    const rev = dir === 'left' ? 'right' : 'left';

    // Lock container to current height during slide animation
    const demoEl = this.container.querySelector('.ai-chat-demo');
    var oldH = demoEl.offsetHeight;
    demoEl.style.height = oldH + 'px';
    demoEl.style.overflow = 'hidden';

    // Phase 1: slide old content out
    this.el.reportContent.classList.add('slide-out-' + dir);
    setTimeout(() => {
      const c = this.reports[type] || '> 暂无报告内容';
      this.el.reportContent.innerHTML = this.renderMarkdown(c);
      this.el.reportContent.classList.remove('slide-out-right', 'slide-out-left');
      this.el.reportContent.classList.add('slide-in-' + rev);
      this.el.reportContent.offsetHeight;
      this.el.reportContent.classList.remove('slide-in-right', 'slide-in-left');

      // Measure new height, then transition from old to new
      demoEl.style.height = '';    // unlock to get natural height
      var newH = demoEl.offsetHeight;
      demoEl.style.height = oldH + 'px';  // re-lock
      demoEl.offsetHeight;                // force reflow
      demoEl.style.height = newH + 'px';  // transition to new height

      setTimeout(function() {
        demoEl.style.height = '';
        demoEl.style.overflow = '';
      }, 350);
    }, 550);
  }
  
  renderMarkdown(text) {
    try {
      // marked v3/v4: try sync parse first
      if (typeof marked !== 'undefined') {
        const result = marked.parse(text, { async: false });
        if (typeof result === 'string') return result;
        // If async result (Promise), handle it
        if (result && typeof result.then === 'function') {
          result.then(html => {
            this.el.reportContent.innerHTML = html;
          }).catch(() => {
            this.el.reportContent.innerHTML = this.simpleMarkdown(text);
          });
          return this.simpleMarkdown(text); // Show fallback immediately
        }
      }
    } catch (e) {
      console.warn('Markdown render fallback:', e);
    }
    return this.simpleMarkdown(text);
  }
  
  simpleMarkdown(text) {
    // Escape HTML first
    let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    // Code blocks (must be before inline code)
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Headers
    html = html.replace(/^#{3}\s+(.*)/gm, '<h3>$1</h3>');
    html = html.replace(/^#{2}\s+(.*)/gm, '<h2>$1</h2>');
    html = html.replace(/^#{1}\s+(.*)/gm, '<h1>$1</h1>');
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Checkboxes
    html = html.replace(/^\[ \]\s+(.*)/gm, '<li><input type="checkbox" disabled> $1</li>');
    html = html.replace(/^\[x\]\s+(.*)/gm, '<li><input type="checkbox" checked disabled> $1</li>');
    
    // List items
    html = html.replace(/^-\s+(.*)/gm, '<li>$1</li>');
    html = html.replace(/^\*\s+(.*)/gm, '<li>$1</li>');
    
    // Blockquote
    html = html.replace(/^>\s+(.*)/gm, '<blockquote>$1</blockquote>');
    
    // HR
    html = html.replace(/^---$/gm, '<hr>');
    
    // Tables: detect lines starting with |
    const lines = html.split('\n');
    let result = [];
    let inTable = false;
    let tableRows = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        // Table row
        if (!inTable) inTable = true;
        const cells = trimmed.slice(1, -1).split('|').map(c => c.trim());
        const rowHtml = '<tr>' + cells.map(c => '<td>' + c + '</td>').join('') + '</tr>';
        tableRows.push(rowHtml);
      } else if (inTable) {
        // End of table
        result.push('<table>' + tableRows.join('') + '</table>');
        tableRows = [];
        inTable = false;
        if (trimmed) result.push('<p>' + trimmed + '</p>');
      } else {
        if (trimmed) {
          if (trimmed.startsWith('<')) {
            result.push(trimmed);
          } else {
            result.push('<p>' + trimmed + '</p>');
          }
        }
      }
    }
    if (inTable) {
      result.push('<table>' + tableRows.join('') + '</table>');
    }
    
    html = result.join('\n');
    
    // Wrap consecutive <li> in <ul>
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    
    return html;
  }
  
  // ── Utilities ───────────────────────────────────────────
  
  scrollToBottom() {
    this.el.messages.scrollTop = this.el.messages.scrollHeight;
  }
  
  delay(ms) {
    return new Promise(r => setTimeout(r, ms));
  }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AIChatDemo;
}
