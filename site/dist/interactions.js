/* Reference-inspired native interactions; no reference data or framework code. */
(() => {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const header = document.querySelector('.site-header');
  if (header) {
    const track = document.createElement('div');
    const fill = document.createElement('span');
    track.className = 'reading-progress';
    track.setAttribute('aria-hidden', 'true');
    track.append(fill); header.append(track);
    let frame = 0;
    const update = () => {
      frame = 0;
      const distance = document.documentElement.scrollHeight - window.innerHeight;
      const progress = distance > 0 ? Math.min(1, Math.max(0, window.scrollY / distance)) : 0;
      fill.style.transform = `scaleX(${progress})`;
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(update); };
    window.addEventListener('scroll', schedule, {passive: true});
    window.addEventListener('resize', schedule);
    window.addEventListener('pageshow', schedule);
    window.addEventListener('load', schedule);
    if ('ResizeObserver' in window) new ResizeObserver(schedule).observe(document.documentElement);
    schedule();
  }

  // Only four dataset summary counts animate. Result values and chart cells do
  // not count up. Their exact source text stays static and accessible throughout.
  const counters = [...document.querySelectorAll('.stat-bar [data-count]')].map(root => ({
    root, display: root.querySelector('.counter-value'), value: Number(root.dataset.count),
    original: root.querySelector('.counter-value')?.textContent, frame: 0, started: false
  })).filter(item => item.display && Number.isSafeInteger(item.value) && item.value >= 0);
  if (reduced.matches || !('IntersectionObserver' in window) || !counters.length) return;
  let observer;
  const finish = item => {
    cancelAnimationFrame(item.frame); item.frame = 0;
    item.display.textContent = item.original; item.started = true;
    if (observer) observer.unobserve(item.root);
  };
  const finishAll = () => { counters.forEach(finish); if (observer) observer.disconnect(); };
  const start = item => {
    if (item.started) return;
    item.started = true; observer.unobserve(item.root);
    if (document.hidden || reduced.matches) { finish(item); return; }
    const duration = 1100;
    let startedAt;
    const tick = now => {
      try {
        if (startedAt === undefined) startedAt = now;
        const progress = Math.min(1, (now - startedAt) / duration);
        const eased = 1 - (1 - progress) ** 4;
        item.display.textContent = Math.round(item.value * eased).toLocaleString('en-US');
        if (progress < 1) item.frame = requestAnimationFrame(tick);
        else finish(item);
      } catch (_) { finish(item); }
    };
    item.frame = requestAnimationFrame(tick);
  };
  try {
    observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const item = counters.find(item => item.root === entry.target);
          if (item) start(item);
        }
      });
    }, {threshold: 0, rootMargin: '0px 0px 24px 0px'});
    counters.forEach(item => {
      // A restored page never replaces a number already on screen with zero.
      if (item.root.getBoundingClientRect().top <= window.innerHeight + 24) finish(item);
      else observer.observe(item.root);
    });
  } catch (_) { finishAll(); return; }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) counters.filter(item => item.started).forEach(finish);
  });
  window.addEventListener('beforeprint', finishAll);
  window.addEventListener('pagehide', () => counters.filter(item => item.started).forEach(finish));
  if (reduced.addEventListener) reduced.addEventListener('change', () => { if (reduced.matches) finishAll(); });
  else if (reduced.addListener) reduced.addListener(() => { if (reduced.matches) finishAll(); });
})();
