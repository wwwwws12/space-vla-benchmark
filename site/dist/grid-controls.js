'use strict';
(() => {
  const section = document.querySelector('.grid-section');
  if (!section) return;
  const controls = section.querySelector('.grid-controls');
  const buttons = [...controls.querySelectorAll('[data-grid-select]')];
  const panels = [...section.querySelectorAll('[data-grid-panel]')];
  function select(value) {
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.gridSelect === value)));
    panels.forEach(panel => { panel.hidden = panel.dataset.gridPanel !== value; });
  }
  buttons.forEach(button => button.addEventListener('click', () => select(button.dataset.gridSelect)));
  select('baseline');
  controls.hidden = false;
})();
