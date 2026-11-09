/* Native SVG motion: pause offscreen, on hidden tabs, and for reduced motion. */
(() => {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const narrow = window.matchMedia('(max-width: 720px)');
  document.querySelectorAll('[data-architecture]').forEach(root => {
    const diagrams = [...root.querySelectorAll('[data-architecture-svg]')];
    const button = root.querySelector('[data-architecture-toggle]');
    const label = root.querySelector('[data-architecture-label]');
    const icon = root.querySelector('[data-architecture-icon]');
    const supported = diagrams.every(svg => ['pauseAnimations','unpauseAnimations','setCurrentTime','getCurrentTime'].every(name => typeof svg[name] === 'function'));
    if (!button || !label || !supported) return;
    let enabled = !reduced.matches;
    let onscreen = !('IntersectionObserver' in window);
    diagrams.forEach(svg => { svg.pauseAnimations(); svg.setCurrentTime(0); });
    const update = () => {
      const allowed = enabled && !reduced.matches;
      const playing = allowed && onscreen && !document.hidden;
      root.dataset.state = playing ? 'playing' : 'static';
      diagrams.forEach(svg => {
        const visible = svg.dataset.architectureSvg === (narrow.matches ? 'mobile' : 'desktop');
        svg.setAttribute('aria-hidden', String(!visible));
        if (playing && visible) svg.unpauseAnimations();
        else svg.pauseAnimations();
      });
      button.hidden = reduced.matches;
      button.setAttribute('aria-pressed', String(allowed));
      label.textContent = allowed ? button.dataset.pause : button.dataset.play;
      if (icon) icon.textContent = allowed ? 'Ⅱ' : '▶';
    };
    button.addEventListener('click', () => { enabled = !enabled; update(); });
    document.addEventListener('visibilitychange', update);
    reduced.addEventListener('change', () => { enabled = !reduced.matches; update(); });
    narrow.addEventListener('change', () => {
      // Both responsive layouts resume from the same point in the cycle.
      const former = diagrams.find(svg => svg.dataset.architectureSvg !== (narrow.matches ? 'mobile' : 'desktop'));
      const time = former ? former.getCurrentTime() : 0;
      diagrams.forEach(svg => svg.setCurrentTime(time));
      update();
    });
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(entries => {
        onscreen = entries.some(entry => entry.isIntersecting);
        update();
      }, { threshold: 0.08 });
      observer.observe(root);
    }
    update();
  });
})();
