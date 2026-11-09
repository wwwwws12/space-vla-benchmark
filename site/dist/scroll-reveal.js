/* One-time entrances, progressively enhanced with native browser APIs.
 * Nothing is hidden while waiting for the observer. A failed script, disabled
 * JavaScript or unsupported API therefore leaves the entire page readable.
 */
(() => {
  'use strict';
  if (!('IntersectionObserver' in window) || !window.matchMedia ||
      typeof Element.prototype.animate !== 'function') return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduced.matches) return;

  // Animate content blocks, never individual letters, table cells, video cards,
  // chart marks, SVG paths or the fixed navigation. Preserve their own motion.
  const selectors = [
    '.numbers-band .stat-bar', '.demo-heading', '.demo-carousel',
    'main .section-head', '.reading-column > .prose > p',
    '.inline-resources', '.environment-nav',
    '.environment-panel > .environment-description', '.environment-pair',
    '.environment-meta', '.dataset-description', '.dataset-table',
    '.dataset-contents', '.stop-example', '.architecture-map', '.input-boundary',
    '.timing-detail', '.rule-definitions', '#protocol > .container > .small',
    '.protocol-notes > div', '.finding-strip', '.chart-card',
    '.result-observations > p', '.data-detail', '.method-explorer',
    '.grid-section > .chart-heading', '.grid-section > .small',
    '.heatmap-grid > .heatmap', '.heatmap-legend', '.resource-links',
    '.download-intro', '.download-toolbar', '.download-status',
    '.download-catalog', '.dataset-downloads > .download-scope',
    '.download-guide', '.release-link', '.code-panel', '.repository-files',
    '.validation-details > details', '.reading-column > .text-link',
    '.footer-main', '.footer-bottom'
  ].join(',');
  const visual = '.demo-carousel,.environment-pair,.dataset-table,' +
    '.stop-example,.architecture-map,.chart-card,.method-explorer,.heatmap,.download-catalog,.code-panel';
  const candidates = [...document.querySelectorAll(selectors)];
  const chosen = new Set(candidates);
  const targets = candidates.filter(element => {
    // A block is revealed once, not again inside a revealed parent.
    for (let parent = element.parentElement; parent; parent = parent.parentElement) {
      if (chosen.has(parent)) return false;
    }
    return true;
  });
  if (!targets.length) return;

  const seen = new WeakSet();
  const running = new Map();
  let observer;
  let disabled = false;

  function finish(element) {
    seen.add(element);
    if (observer) observer.unobserve(element);
    const animation = running.get(element);
    running.delete(element);
    element.removeAttribute('data-scroll-reveal');
    // Remove the animation effect, leaving the original styles in control.
    if (animation) animation.cancel();
  }

  function showAll() {
    disabled = true;
    if (observer) observer.disconnect();
    targets.forEach(finish);
  }

  function showAround(node) {
    if (!(node instanceof Element)) return;
    targets.forEach(element => {
      if (element === node || element.contains(node) || node.contains(element)) finish(element);
    });
  }

  function showFragment(hash) {
    if (!hash || hash === '#') return;
    try { showAround(document.getElementById(decodeURIComponent(hash.slice(1)))); }
    catch (_) { /* Malformed anchors must not interrupt native navigation. */ }
  }

  function showCurrentViewport() {
    const boundary = window.innerHeight + 24;
    targets.forEach(element => {
      const rect = element.getBoundingClientRect();
      if (rect.height && rect.width && rect.top <= boundary && !element.closest('[hidden]')) {
        finish(element);
      }
    });
  }

  function enter(element, delay) {
    finish(element);
    if (disabled || reduced.matches || document.hidden ||
        element.contains(document.activeElement)) return;
    try {
      const tokens = getComputedStyle(document.documentElement);
      const style = getComputedStyle(element);
      const duration = parseFloat(tokens.getPropertyValue(element.matches(visual)
        ? '--reveal-media-duration' : '--reveal-text-duration')) || 440;
      const distance = parseFloat(tokens.getPropertyValue('--reveal-distance')) || 16;
      const easing = tokens.getPropertyValue('--reveal-easing').trim() || 'ease-out';
      const opacity = Number.parseFloat(style.opacity);
      const from = { opacity: 0 };
      const to = { opacity: Number.isFinite(opacity) ? opacity : 1 };
      // Do not overwrite a transform already owned by another component.
      if (!style.transform || style.transform === 'none') {
        from.transform = `translateY(${distance}px)`;
        to.transform = 'translateY(0px)';
      }
      const animation = element.animate([from, to], {
        duration, delay, easing, fill: 'backwards'
      });
      running.set(element, animation);
      element.setAttribute('data-scroll-reveal', 'playing');
      const cleanup = () => {
        if (running.get(element) === animation) finish(element);
      };
      animation.finished.then(cleanup, cleanup);
    } catch (_) {
      // Fail open: errors never leave paragraphs or controls transparent.
      finish(element);
    }
  }

  try {
    observer = new IntersectionObserver(entries => {
      try {
        const entering = entries.filter(entry => entry.isIntersecting &&
          !seen.has(entry.target) && entry.boundingClientRect.width > 0 &&
          entry.boundingClientRect.height > 0 && !entry.target.closest('[hidden]'));
        entering.sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top ||
          a.boundingClientRect.left - b.boundingClientRect.left);
        entering.forEach((entry, index) => {
          if (entry.boundingClientRect.bottom <= 0) finish(entry.target);
          else enter(entry.target, Math.min(index, 2) * 45);
        });
      } catch (_) { showAll(); }
    }, { threshold: 0, rootMargin: '0px 0px 24px 0px' });
    // Above-the-fold content and restored reading positions never blink on load.
    showFragment(location.hash);
    showCurrentViewport();
    targets.forEach(element => { if (!seen.has(element)) observer.observe(element); });
  } catch (_) { showAll(); return; }

  // Keyboard focus, native anchors, browser search and printing take precedence.
  document.addEventListener('focusin', event => showAround(event.target));
  document.addEventListener('pointerdown', event => showAround(event.target), { passive: true });
  document.addEventListener('click', event => {
    if (!(event.target instanceof Element) || event.defaultPrevented ||
        event.button > 0 || event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) return;
    const link = event.target.closest('a[href]');
    if (!link) return;
    try {
      const url = new URL(link.href, location.href);
      if (url.origin === location.origin && url.pathname === location.pathname &&
          url.search === location.search) showFragment(url.hash);
    } catch (_) { /* Keep native link behavior. */ }
  });
  document.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'f') showAll();
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) [...running.keys()].forEach(finish);
  });
  window.addEventListener('hashchange', () => showFragment(location.hash));
  window.addEventListener('beforeprint', showAll);
  window.addEventListener('pagehide', () => [...running.keys()].forEach(finish));
  window.addEventListener('pageshow', event => {
    if (event.persisted) { [...running.keys()].forEach(finish); showCurrentViewport(); }
  });
  if (reduced.addEventListener) reduced.addEventListener('change', () => {
    if (reduced.matches) showAll();
  });
  else if (reduced.addListener) reduced.addListener(() => { if (reduced.matches) showAll(); });
})();
