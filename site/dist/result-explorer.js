'use strict';
(() => {
  const select = document.getElementById('method');
  const rows = document.getElementById('explorer-rows');
  const data = window.BENCHMARK_RESULTS;
  if (!select || !rows || !data) return;
  const zh = document.documentElement.lang === 'zh-CN';
  const labels = zh ? {mars:'火星', moon:'月球', cabin:'太空舱'} : {mars:'Mars', moon:'Moon', cabin:'Cabin'};
  const names = {qwen:'Qwen2.5-VL-3B', lance:'Lance_3B', nova:'Nova Lite 1.0'};
  function update() {
    rows.replaceChildren();
    for (const world of ['mars','moon','cabin']) {
      for (const model of ['qwen','lance','nova']) {
        const match = lighting => data.primary.find(r => r.world === world && r.model === model && r.method === select.value && r.lighting === lighting);
        const a = match('baseline'), b = match('second');
        if (!a || !b) continue;
        const delta = (b.SR - a.SR) * 100;
        const tr = document.createElement('tr');
        for (const value of [labels[world], names[model], `${a.successes}/240 · ${(100*a.SR).toFixed(2)}%`, `${b.successes}/240 · ${(100*b.SR).toFixed(2)}%`, `${delta>=0?'+':''}${delta.toFixed(2)}`, a.SPL.toFixed(3), b.SPL.toFixed(3)]) {
          const td = document.createElement('td'); td.textContent = value; tr.append(td);
        }
        rows.append(tr);
      }
    }
  }
  select.addEventListener('change', update);
  update();
})();
