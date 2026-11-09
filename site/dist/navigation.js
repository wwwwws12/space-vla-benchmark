'use strict';
(() => {
  const header = document.querySelector('.site-header');
  const nav = document.querySelector('.site-nav');
  if (!header || !nav) return;

  const links = [...nav.querySelectorAll('a[href^="#"]')];
  const byId = new Map(links.map(link => [link.hash.slice(1), link]));
  // Dataset and Downloads have distinct anchors in the same order as the body.
  const aliases = { limitations: 'reproduce' };
  const sections = [...document.querySelectorAll('main > section[id]')]
    .map(section => ({ section, link: byId.get(aliases[section.id] || section.id) }))
    .filter(item => item.link);
  if (!links.length || !sections.length) return;

  const compact = matchMedia('(max-width: 800px)');
  const indicator = document.createElement('span');
  indicator.className = 'nav-indicator';
  indicator.setAttribute('aria-hidden', 'true');
  nav.append(indicator);
  nav.classList.add('has-moving-indicator');

  let current = null;
  let pending = null;
  let frame = 0;
  let snapNext = true;
  let positioned = false;
  let idleTimer = 0;
  let releaseTimer = 0;
  const round = value => Math.round(value * 100) / 100;

  function schedule(snap = false) {
    snapNext = snapNext || snap;
    if (!frame) frame = requestAnimationFrame(update);
  }

  function update() {
    frame = 0;
    const snap = snapNext;
    snapNext = false;
    // Read geometry before changing classes. Work is coalesced to one animation frame.
    const headerRect = header.getBoundingClientRect();
    const readingLine = headerRect.bottom + Math.min(140, window.innerHeight * 0.18);
    let selected = links[0];
    for (const item of sections) {
      if (item.section.getBoundingClientRect().top > readingLine) break;
      selected = item.link;
    }
    if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4) {
      selected = sections[sections.length - 1].link;
    }
    if (pending) selected = pending;

    let transform = null;
    if (!nav.hidden) {
      const navRect = nav.getBoundingClientRect();
      const linkRect = selected.getBoundingClientRect();
      if (navRect.width && linkRect.width) {
        transform = compact.matches
          ? `translate3d(${round(linkRect.left - navRect.left - 4)}px, ${round(linkRect.top - navRect.top + 11)}px, 0) scaleY(${Math.max(12, linkRect.height - 22) / 100})`
          : `translate3d(${round(linkRect.left - navRect.left)}px, ${round(headerRect.bottom - navRect.top - 3)}px, 0) scaleX(${linkRect.width / 100})`;
      }
    }

    header.classList.toggle('is-scrolled', window.scrollY > 12);
    if (selected !== current) {
      links.forEach(link => {
        if (link === selected) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
      current = selected;
    }
    if (!transform) {
      indicator.classList.remove('is-visible');
      positioned = false;
      return;
    }
    const instant = snap || !positioned;
    if (instant) indicator.classList.add('is-positioning');
    if (indicator.style.transform !== transform) indicator.style.transform = transform;
    indicator.classList.add('is-visible');
    positioned = true;
    if (instant) requestAnimationFrame(() => indicator.classList.remove('is-positioning'));
  }

  function finishNavigation() {
    if (!pending) return;
    pending = null;
    clearTimeout(idleTimer);
    clearTimeout(releaseTimer);
    schedule();
  }

  nav.addEventListener('click', event => {
    if (event.defaultPrevented || event.button > 0 || event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) return;
    const link = event.target.closest('a[href^="#"]');
    if (!links.includes(link)) return;
    // Preserve native anchors, keyboard focus, history and CSS smooth scrolling.
    // During a long anchor jump, move directly to the requested item.
    pending = link;
    clearTimeout(idleTimer);
    clearTimeout(releaseTimer);
    releaseTimer = setTimeout(finishNavigation, 1800);
    schedule();
  });

  window.addEventListener('scroll', () => {
    schedule();
    if (pending) {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(finishNavigation, 160);
    }
  }, { passive: true });
  document.addEventListener('scrollend', finishNavigation);
  // Manual input takes precedence over an in-flight anchor jump.
  window.addEventListener('wheel', finishNavigation, { passive: true });
  window.addEventListener('touchstart', finishNavigation, { passive: true });
  window.addEventListener('pointerdown', finishNavigation, { passive: true });
  document.addEventListener('keydown', event => {
    if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '].includes(event.key)) finishNavigation();
  });
  window.addEventListener('resize', () => schedule(true));
  window.addEventListener('pageshow', () => schedule(true));
  window.addEventListener('hashchange', () => schedule());
  compact.addEventListener('change', () => schedule(true));

  if ('ResizeObserver' in window) {
    const resize = new ResizeObserver(() => schedule(true));
    [header, nav, document.querySelector('main')].filter(Boolean).forEach(element => resize.observe(element));
  }
  if ('MutationObserver' in window) {
    new MutationObserver(() => schedule(true)).observe(nav, { attributes: true, attributeFilter: ['hidden'] });
  }
  if (document.fonts) document.fonts.ready.then(() => schedule(true));
  schedule(true);
})();
