'use strict';
(() => {
  const zh = document.documentElement.lang === 'zh-CN';
  const nav = document.querySelector('.site-nav');
  const toggle = document.querySelector('.nav-toggle');
  const compact = matchMedia('(max-width: 800px)');
  function setMenu(open) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', zh ? (open ? '关闭导航' : '打开导航') : (open ? 'Close navigation' : 'Open navigation'));
    nav.hidden = compact.matches && !open;
  }
  toggle.hidden = false;
  setMenu(false);
  toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  compact.addEventListener('change', () => setMenu(false));
  nav.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && compact.matches && toggle.getAttribute('aria-expanded') === 'true') {
      setMenu(false); toggle.focus();
    }
  });
  // navigation.js owns the current-section state and its moving indicator.
  const worldButtons = [...document.querySelectorAll('[data-world-select]')];
  const worldPanels = [...document.querySelectorAll('[data-world-panel]')];
  function selectWorld(world) {
    worldButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.worldSelect === world)));
    worldPanels.forEach(panel => { panel.hidden = panel.dataset.worldPanel !== world; });
  }
  worldButtons.forEach(button => button.addEventListener('click', () => selectWorld(button.dataset.worldSelect)));
  selectWorld('mars');
  worldPanels.forEach(panel => {
    const buttons = [...panel.querySelectorAll('[data-light]')];
    const frames = [...panel.querySelectorAll('[data-light-frame]')];
    const select = light => {
      buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.light === light)));
      frames.forEach(frame => { frame.hidden = frame.dataset.lightFrame !== light; });
    };
    buttons.forEach(button => button.addEventListener('click', () => select(button.dataset.light)));
    select('baseline');
  });
  const language = document.querySelector('[data-language]');
  if (language) language.addEventListener('click', () => {
    // Both pages expose the same section IDs; language changes retain reading position.
    language.href = language.getAttribute('href').split('#')[0] + location.hash;
  });
  document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
    const code = document.getElementById(button.dataset.copy);
    const status = button.closest('.code-panel').querySelector('[data-copy-status]');
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(code.textContent);
      status.textContent = zh ? '命令已复制。' : 'Commands copied.';
    } catch (_) {
      const range = document.createRange(); range.selectNodeContents(code);
      const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
      status.textContent = zh ? '命令已选中，请按 Ctrl/Cmd+C 复制。' : 'Commands selected. Press Ctrl/Cmd+C to copy.';
    }
  }));
  // The video component owns playback and focus state. Do not toggle its
  // preference when a pointer click focuses the native video or scene selector.
})();
