'use strict';
(() => {
  // Hero links and the environment explorer address the same content.
  document.querySelectorAll('[data-open-world]').forEach(link => {
    link.addEventListener('click', () => {
      const button = document.querySelector(`[data-world-select="${link.dataset.openWorld}"]`);
      if (button) button.click();
    });
  });
  // Keep navigation dark with the hero, then switch to the white reading surface.
  const header = document.querySelector('.site-header');
  const hero = document.querySelector('.hero');
  if (header && hero && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      const entry = entries[0];
      header.classList.toggle('on-paper', !entry.isIntersecting && entry.boundingClientRect.bottom <= 80);
    }, { rootMargin: '-80px 0px 0px 0px', threshold: 0 });
    observer.observe(hero);
  }
})();
