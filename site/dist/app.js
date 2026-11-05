'use strict';
const data = window.BENCHMARK_RESULTS;
const zh = document.documentElement.lang === 'zh-CN';
const worlds = ['mars','moon','cabin'];
const labels = zh ? {mars:'火星',moon:'月球',cabin:'太空舱'} : {mars:'Mars',moon:'Moon',cabin:'Cabin'};
const models = {qwen:'Qwen2.5-VL-3B',lance:'Lance_3B',nova:'Nova Lite 1.0'};
document.querySelectorAll('[data-world]').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('[data-world]').forEach(b => b.setAttribute('aria-pressed', String(b===button)));
    document.querySelectorAll('[data-pair]').forEach(p => { p.hidden = p.dataset.pair !== button.dataset.world; });
  });
});
function updateResults() {
  const method = document.getElementById('method').value;
  document.getElementById('results-caption').textContent = (zh?'当前显示：':'Showing: ') + method + (zh?' · 每格240条test，参数保持冻结。':' · 240 test routes per cell; parameters remain frozen.');
  const rows = [];
  worlds.forEach(world => {
    const panel = document.getElementById('bars-'+world);
    panel.replaceChildren();
    const title=document.createElement('h3'); title.textContent=labels[world];
    const kq=document.createElement('small');kq.textContent=method==='Baseline'?'Script end':`K${data.frozen[world][0]} / q${data.frozen[world][1]}`;
    title.append(kq);panel.append(title);
    Object.keys(models).forEach(model => {
      const base=data.primary.find(r=>r.world===world&&r.model===model&&r.method===method&&r.lighting==='baseline');
      const second=data.primary.find(r=>r.world===world&&r.model===model&&r.method===method&&r.lighting==='second');
      const item=document.createElement('div');item.className='bar-item';
      const name=document.createElement('div');name.className='model-name';name.textContent=models[model];item.append(name);
      [base,second].forEach((r,i)=>{
        const line=document.createElement('div');line.className='bar-line'+(i?' second':'');
        const track=document.createElement('div');track.className='track';track.setAttribute('aria-hidden','true');
        const fill=document.createElement('span');fill.className='fill';fill.style.width=(100*r.SR)+'%';track.append(fill);
        const num=document.createElement('b');num.textContent=(100*r.SR).toFixed(2)+'%';
        line.append(track,num);item.append(line);
      });panel.append(item);rows.push({world,model,base,second});
    });
  });
  const body=document.getElementById('result-rows');body.replaceChildren();
  rows.forEach(({world,model,base,second})=>{
    const tr=document.createElement('tr');const delta=(second.SR-base.SR)*100;
    [labels[world],models[model],`${base.successes}/240 (${(base.SR*100).toFixed(2)}%)`,`${second.successes}/240 (${(second.SR*100).toFixed(2)}%)`,`${delta>=0?'+':''}${delta.toFixed(2)}`,base.SPL.toFixed(3),second.SPL.toFixed(3)].forEach((value,i)=>{
      const td=document.createElement('td');td.textContent=value;if(i===4)td.className=delta<0?'negative':'positive';tr.append(td);
    });body.append(tr);
  });
}
document.getElementById('method').addEventListener('change',updateResults);
updateResults();
const config=window.RELEASE_CONFIG || {};
if(config.repository_url && /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/.test(config.repository_url)) {
  document.querySelectorAll('[data-repository]').forEach(a=>{a.href=config.repository_url;a.hidden=false;});
}
if(config.authors) document.getElementById('byline').textContent=config.authors;
