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
    this.thinkingBlock = null;
    
    this.init();
  }
  
  init() {
    this.container.innerHTML = this.buildHTML();
    this.cacheElements();
    this.bindEvents();
    this.startStage('init');
  }
  
  buildHTML() {
    return `
      <div class="ai-chat-demo">
        <div class="chat-panel">
          <div class="chat-header">
            <div class="chat-header-left">
              <div class="chat-avatar">${this.avatar}</div>
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
              <button class="chat-send-btn" disabled>↑</button>
            </div>
            <!-- Options area (replaces input row) -->
            <div class="chat-options-area" id="options-area" style="display:none;"></div>
          </div>
        </div>
        <div class="report-panel">
          <div class="report-tabs">
            <button class="report-tab active" data-report="standard">标准版</button>
            <button class="report-tab" data-report="professional">专业版</button>
            <button class="report-tab" data-report="action">行动版</button>
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
  
  startStage(stageName) {
    this.currentStage = stageName;
    const stage = this.stages[stageName];
    if (!stage) return;
    
    if (stage.aiMessage) {
      this.typeMessage(stage.aiMessage, 'ai');
    }
    
    if (stage.options) {
      setTimeout(() => this.showOptionsInInputArea(stage.options), stage.aiMessage ? 100 : 0);
    } else {
      this.showInput();
    }
  }
  
  // ── Input/Options Toggle ─────────────────────────────────────
  
  showOptionsInInputArea(options) {
    this.el.inputRow.style.display = 'none';
    this.el.optionsArea.style.display = 'flex';
    this.el.optionsArea.innerHTML = '';
    
    const hint = document.createElement('div');
    hint.className = 'chat-options-hint';
    hint.textContent = '👆 选择一个选项继续';
    this.el.optionsArea.appendChild(hint);
    
    const list = document.createElement('div');
    list.className = 'chat-options-list';
    
    options.forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'chat-option-btn';
      btn.textContent = opt.text;
      btn.addEventListener('click', () => this.handleOptionClick(opt));
      list.appendChild(btn);
    });
    
    this.el.optionsArea.appendChild(list);
  }
  
  showInput() {
    this.el.optionsArea.style.display = 'none';
    this.el.inputRow.style.display = 'flex';
    this.el.input.disabled = false;
    this.el.sendBtn.disabled = false;
    this.el.input.focus();
  }
  
  // ── Message Rendering — Character by Character ─────────────────
  
  async typeMessage(text, sender) {
    if (this.isTyping) return;
    this.isTyping = true;
    
    const msg = document.createElement('div');
    msg.className = `chat-message ${sender}`;
    msg.innerHTML = `<div class="chat-bubble typing-cursor"></div>`;
    this.el.messages.appendChild(msg);
    this.scrollToBottom();
    
    const bubble = msg.querySelector('.chat-bubble');
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
    
    // 1. Show "thinking..." status message
    const statusBubble = this.createSystemBubble(`${this.thinkingLabel}中...`);
    this.el.messages.appendChild(statusBubble);
    this.scrollToBottom();
    
    await this.delay(800);
    
    // 2. Create thinking block (expanded)
    this.thinkingBlock = document.createElement('div');
    this.thinkingBlock.className = 'chat-thinking expanded';
    this.thinkingBlock.innerHTML = `
      <div class="chat-thinking-header">
        <span class="chat-thinking-icon">▶</span>
        <span>${this.thinkingLabel}</span>
      </div>
      <div class="chat-thinking-body">
        <div class="chat-thinking-lines"></div>
      </div>
    `;
    
    const header = this.thinkingBlock.querySelector('.chat-thinking-header');
    header.addEventListener('click', () => this.thinkingBlock.classList.toggle('expanded'));
    
    this.el.messages.appendChild(this.thinkingBlock);
    this.scrollToBottom();
    
    // 3. Remove status bubble
    statusBubble.remove();
    
    // 4. Type each thinking line character by character
    const linesContainer = this.thinkingBlock.querySelector('.chat-thinking-lines');
    
    for (let i = 0; i < lines.length; i++) {
      const lineEl = document.createElement('div');
      lineEl.className = 'chat-thinking-line typing-cursor';
      lineEl.style.opacity = '1';
      linesContainer.appendChild(lineEl);
      
      // Type this line char by char
      let currentText = '';
      for (let j = 0; j < lines[i].length; j++) {
        await this.delay(20); // slightly faster for thinking lines
        currentText += lines[i][j];
        lineEl.textContent = currentText;
        this.scrollToBottom();
      }
      lineEl.classList.remove('typing-cursor');
      
      // Small delay between lines
      await this.delay(200 + Math.random() * 300);
    }
    
    // 5. Pause, then collapse thinking block
    await this.delay(600);
    this.thinkingBlock.classList.remove('expanded');
    
    setTimeout(() => onComplete(), 400);
  }
  
  createSystemBubble(text) {
    const div = document.createElement('div');
    div.className = 'chat-message ai';
    div.style.opacity = '0.6';
    div.innerHTML = `<div class="chat-bubble">${text}</div>`;
    return div;
  }
  
  // ── User Interaction ────────────────────────────────────
  
  handleOptionClick(option) {
    this.el.optionsArea.innerHTML = '';
    this.el.optionsArea.style.display = 'none';
    
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
    
    if (stage.thinking && stage.thinking.length > 0) {
      this.runThinking(stage.thinking, () => {
        if (stage.aiMessage) {
          this.typeMessage(stage.aiMessage, 'ai');
        }
        if (stage.showReports) {
          this.showReports();
          this.showInput();
        } else if (stage.options) {
          setTimeout(() => this.showOptionsInInputArea(stage.options), 100);
        } else {
          this.showInput();
        }
      });
    } else {
      if (stage.aiMessage) {
        this.typeMessage(stage.aiMessage, 'ai');
      }
      if (stage.showReports) {
        this.showReports();
        this.showInput();
      } else if (stage.options) {
        setTimeout(() => this.showOptionsInInputArea(stage.options), 100);
      } else {
        this.showInput();
      }
    }
  }
  
  // ── Reports Panel ───────────────────────────────────────
  
  showReports() {
    this.reportVisible = true;
    this.el.reportPanel.classList.add('visible');
    this.switchReport('standard');
  }
  
  switchReport(type) {
    this.el.reportTabs.forEach(t => t.classList.toggle('active', t.dataset.report === type));
    
    const content = this.reports[type] || '> 暂无报告内容';
    this.el.reportContent.innerHTML = this.renderMarkdown(content);
  }
  
  renderMarkdown(text) {
    // Try marked.js first
    if (typeof marked !== 'undefined' && marked.parse) {
      try {
        return marked.parse(text);
      } catch (e) {
        console.warn('marked.parse failed, using fallback:', e);
      }
    }
    // Fallback
    return this.simpleMarkdown(text);
  }
  
  simpleMarkdown(text) {
    let html = text
      .replace(/### (.*)/g, '<h3>$1</h3>')
      .replace(/## (.*)/g, '<h2>$1</h2>')
      .replace(/# (.*)/g, '<h1>$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^\[ \] (.*)/gm, '<li><input type="checkbox" disabled> $1</li>')
      .replace(/^\[x\] (.*)/gm, '<li><input type="checkbox" checked disabled> $1</li>')
      .replace(/^- (.*)/gm, '<li>$1</li>')
      .replace(/^\* (.*)/gm, '<li>$1</li>')
      .replace(/^> (.*)/gm, '<blockquote>$1</blockquote>')
      .replace(/^---$/gm, '<hr>');
    
    // Code blocks
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    
    // Tables (simple: | a | b |
    html = html.replace(/\|([^\n|]*)\|([^\n|]*)\|/g, '<td>$1</td><td>$2</td>');
    html = html.replace(/(<td>.*<\/td>)+/g, '<tr>$&</tr>');
    html = html.replace(/(<tr>.*<\/tr>\n?)+/g, '<table>$&</table>');
    
    // Wrap consecutive <li> in <ul>
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    
    // Wrap in paragraphs for plain text lines
    html = html.split('\n').map(line => {
      line = line.trim();
      if (!line) return '';
      if (line.startsWith('<')) return line;
      return '<p>' + line + '</p>';
    }).join('\n');
    
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
