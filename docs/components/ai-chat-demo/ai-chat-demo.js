// AI Chat Demo — HaluCatch Interactive Component
// Configurable, reusable, zero-dependency (except marked.js for Markdown)

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
    
    this.currentStage = 'init';
    this.isTyping = false;
    this.reportVisible = false;
    
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
            <label class="chat-thinking-toggle">
              <input type="checkbox" ${this.thinkingEnabled ? 'checked' : ''}>
              <span>${this.thinkingLabel}</span>
            </label>
          </div>
          <div class="chat-messages"></div>
          <div class="chat-input-area">
            <textarea class="chat-input" rows="1" placeholder="输入消息..."></textarea>
            <button class="chat-send-btn">➤</button>
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
      input: this.container.querySelector('.chat-input'),
      sendBtn: this.container.querySelector('.chat-send-btn'),
      thinkingToggle: this.container.querySelector('.chat-thinking-toggle input'),
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
    
    this.el.reportTabs.forEach(tab => {
      tab.addEventListener('click', () => this.switchReport(tab.dataset.report));
    });
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
      setTimeout(() => this.showOptions(stage.options), stage.aiMessage ? 600 : 0);
    }
  }
  
  // ── Message Rendering ───────────────────────────────────────
  
  async typeMessage(text, sender) {
    if (this.isTyping) return;
    this.isTyping = true;
    
    // Show typing indicator
    const indicator = document.createElement('div');
    indicator.className = 'chat-message ai';
    indicator.innerHTML = `
      <div class="chat-bubble">
        <div class="typing-indicator"><span></span><span></span><span></span></div>
      </div>
    `;
    this.el.messages.appendChild(indicator);
    this.scrollToBottom();
    
    // Simulate typing delay
    await this.delay(800 + text.length * 8);
    
    // Remove indicator, show real message
    indicator.remove();
    this.addMessage(text, sender);
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
  
  showOptions(options) {
    const container = document.createElement('div');
    container.className = 'chat-options';
    
    options.forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'chat-option-btn';
      btn.textContent = opt.text;
      btn.addEventListener('click', () => this.handleOptionClick(opt));
      container.appendChild(btn);
    });
    
    this.el.messages.appendChild(container);
    this.scrollToBottom();
  }
  
  // ── Thinking Flow ─────────────────────────────────────────
  
  async runThinking(lines, onComplete) {
    if (!this.el.thinkingToggle.checked) {
      onComplete();
      return;
    }
    
    const block = document.createElement('div');
    block.className = 'chat-thinking';
    block.innerHTML = `
      <div class="chat-thinking-header">
        <span class="chat-thinking-icon">▶</span>
        <span>${this.thinkingLabel}</span>
      </div>
      <div class="chat-thinking-body">
        <div class="chat-thinking-lines"></div>
      </div>
    `;
    
    // Click to toggle
    const header = block.querySelector('.chat-thinking-header');
    header.addEventListener('click', () => block.classList.toggle('expanded'));
    
    this.el.messages.appendChild(block);
    block.classList.add('expanded');
    this.scrollToBottom();
    
    const linesContainer = block.querySelector('.chat-thinking-lines');
    
    for (let i = 0; i < lines.length; i++) {
      await this.delay(400 + Math.random() * 600);
      const line = document.createElement('div');
      line.className = 'chat-thinking-line';
      line.style.animationDelay = '0s';
      line.textContent = lines[i];
      linesContainer.appendChild(line);
      this.scrollToBottom();
    }
    
    await this.delay(600);
    block.classList.remove('expanded');
    
    setTimeout(() => {
      onComplete();
    }, 400);
  }
  
  // ── User Interaction ────────────────────────────────────
  
  handleOptionClick(option) {
    // Remove option buttons
    const optionsContainer = this.container.querySelector('.chat-options');
    if (optionsContainer) optionsContainer.remove();
    
    // Show user message
    this.addMessage(option.text, 'user');
    
    // Transition to next stage
    setTimeout(() => {
      this.transitionTo(option.next);
    }, 400);
  }
  
  async handleUserInput() {
    const text = this.el.input.value.trim();
    if (!text || this.isTyping) return;
    
    this.addMessage(text, 'user');
    this.el.input.value = '';
    
    // End stage: always show end message
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
        }
      });
    } else {
      if (stage.aiMessage) {
        this.typeMessage(stage.aiMessage, 'ai');
      }
      if (stage.showReports) {
        this.showReports();
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
    if (typeof marked !== 'undefined') {
      this.el.reportContent.innerHTML = marked.parse(content);
    } else {
      // Fallback: simple line-based rendering
      this.el.reportContent.innerHTML = this.simpleMarkdown(content);
    }
  }
  
  simpleMarkdown(text) {
    // Minimal markdown parser for fallback
    let html = text
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
      .replace(/^\*(.*$)/gim, '<li>$1</li>')
      .replace(/^- (.*$)/gim, '<li>$1</li>')
      .replace(/^\[ \] (.*$)/gim, '<li><input type="checkbox" disabled> $1</li>')
      .replace(/^\[x\] (.*$)/gim, '<li><input type="checkbox" checked disabled> $1</li>')
      .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^---$/gim, '<hr>')
      .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>');
    
    // Wrap lists
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

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AIChatDemo;
}
