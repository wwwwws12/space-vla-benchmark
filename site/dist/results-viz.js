/* V22. Presentation only: all values come from the frozen result export. */
(function (global) {
  'use strict';
  const worlds = ['mars', 'moon', 'cabin'];
  const models = ['qwen', 'lance', 'nova'];
  const methods = ['TRACE', 'delay_only', 'oracle_visibility', 'Baseline'];
  const names = {qwen: 'Qwen2.5-VL-3B', lance: 'Lance_3B', nova: 'Nova Lite 1.0'};
  const short = {qwen: 'Qwen', lance: 'Lance', nova: 'Nova'};
  const colors = {baseline: '#29475c', second: '#a45132', TRACE: '#29475c', delay_only: '#a45132', oracle_visibility: '#347466', Baseline: '#727a80'};
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
  const pct = x => (x * 100).toFixed(2);
  const delta = x => `${x >= 0 ? '+' : '−'}${Math.abs(x).toFixed(2)}`;
  const locale = lang => lang === 'zh-CN';
  const worldName = (w, lang) => locale(lang) ? {mars:'火星',moon:'月球',cabin:'太空舱'}[w] : {mars:'Mars',moon:'Moon',cabin:'Cabin'}[w];
  const methodName = (m, lang) => ({TRACE:'TRACE',delay_only:'delay-only',oracle_visibility:locale(lang)?'可见性 Oracle':'Visibility Oracle',Baseline:locale(lang)?'脚本终点':'Script endpoint'})[m];
  const row = (d, w, m, l, rule='TRACE') => {
    const found = d.primary.filter(r => r.world === w && r.model === m && r.lighting === l && r.method === rule);
    if (found.length !== 1) throw new Error('Missing or duplicated frozen result');
    return found[0];
  };
  function validate(d) {
    if (!d || d.primary.length !== 72) throw new Error('Expected 72 primary records');
    for (const w of worlds) for (const m of models) for (const l of ['baseline','second']) for (const rule of methods) {
      const r = row(d,w,m,l,rule);
      if (r.routes !== 240 || !Number.isInteger(r.successes) || Math.abs(r.SR - r.successes / r.routes) > 1e-10 ||
          !Number.isFinite(r.SPL) || r.SPL < 0 || r.SPL > 1) throw new Error('Invalid result values');
      if (rule !== 'Baseline' && (r.K !== d.frozen[w][0] || r.q !== d.frozen[w][1])) throw new Error('Frozen K/q mismatch');
    }
    return true;
  }
  function text(x,y,s,extra='') {
    const axis=extra.includes('class="axis"'), heavy=extra.includes('class="heavy"');
    const fill=extra.includes('class="baseline"')?colors.baseline:extra.includes('class="second"')?colors.second:axis?'#626b73':heavy?'#20272e':'#353d45';
    // Presentation attributes also survive offline SVG/PDF renderers.
    const size=/font-size=/.test(extra)?'':`font-size="${axis?14:16}"`;
    return `<text x="${x}" y="${y}" font-family="sans-serif" ${size} fill="${fill}" font-weight="${heavy?600:400}" ${extra}>${esc(s)}</text>`;
  }
  function svgStart(width,height,id,title,desc) {
    return `<svg class="rv-result-chart" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="${id}-title ${id}-desc"><title id="${id}-title">${esc(title)}</title><desc id="${id}-desc">${esc(desc)}</desc><style>svg.rv-result-chart text{font-family:Arial,'Microsoft YaHei',sans-serif;font-size:16px;fill:#353d45;font-variant-numeric:tabular-nums}svg.rv-result-chart .axis{fill:#626b73;font-size:14px}svg.rv-result-chart .heavy{font-weight:600;fill:#20272e}svg.rv-result-chart .baseline{fill:#29475c}svg.rv-result-chart .second{fill:#a45132}</style>`;
  }
  function pairedSVG(d,lang,selected='all',compact=false) {
    const chosen = selected === 'all' ? worlds : [selected];
    if (!chosen.every(w=>worlds.includes(w))) throw new Error('Unknown world');
    const zh=locale(lang), width=compact?380:1100, left=compact?100:244, right=compact?290:874;
    const step=compact?70:60, gap=compact?50:34, top=compact?82:78;
    const height=top+chosen.length*(3*step+gap)-gap+28;
    const title=zh?'TRACE：两种光照的成功率':'TRACE success rate under paired lighting';
    let s=svgStart(width,height,`rv-pair-${selected}-${compact?'small':'wide'}`,title,zh?'圆点为基准光照，菱形为第二光照。每组240条test路线；变化以百分点表示。':'Circles: baseline light. Diamonds: second light. Each group has 240 test routes; changes are in percentage points.');
    s+='<rect width="100%" height="100%" fill="#fff"/>';
    s+=text(left,compact?22:23,zh?'成功率 SR (%)':'Success rate (%)','class="axis"');
    s+=text(compact?367:1066,compact?22:23,compact?'Δ pp':zh?'变化（百分点）':'Change (pp)','class="axis" text-anchor="end"');
    const x=value=>left+(right-left)*value/.6;
    for(let tick=0;tick<=60;tick+=compact?20:10) {
      const xx=x(tick/100);
      s+=`<path d="M${xx} 38V${height-39}" stroke="#e7ebed" stroke-width="1"/>`;
      s+=text(xx,height-13,tick,'class="axis" text-anchor="middle"');
    }
    chosen.forEach((w,wi)=>{
      const start=top+wi*(3*step+gap);
      if(compact) s+=text(14,start-24,worldName(w,lang),'class="heavy"');
      else {
        s+=text(18,start,worldName(w,lang),'class="heavy"');
        s+=text(18,start+25,`K${d.frozen[w][0]} / q${d.frozen[w][1]}`,'class="axis"');
      }
      if(wi) s+=`<path d="M14 ${start-(compact?43:30)}H${width-14}" stroke="#dfe4e7"/>`;
      models.forEach((m,mi)=>{
        const a=row(d,w,m,'baseline'),b=row(d,w,m,'second'),y=start+mi*step,xa=x(a.SR),xb=x(b.SR),change=(b.SR-a.SR)*100;
        const desc=`${worldName(w,lang)} · ${names[m]}: ${a.successes}/${a.routes} (${pct(a.SR)}%) → ${b.successes}/${b.routes} (${pct(b.SR)}%); ${delta(change)} pp`;
        s+=`<g class="rv-pair-row"><title>${esc(desc)}</title>`;
        s+=text(compact?14:133,y+5,short[m],compact?'font-size="14"':'');
        s+=`<path d="M${xa} ${y-4}L${xb} ${y+4}" fill="none" stroke="#a8b5bd" stroke-width="3"/>`;
        s+=`<circle cx="${xa}" cy="${y-4}" r="5.5" fill="${colors.baseline}" stroke="#fff" stroke-width="1.4"/>`;
        s+=`<path d="M${xb} ${y-3}l7 7-7 7-7-7Z" fill="${colors.second}" stroke="#fff" stroke-width="1.4"/>`;
        s+=text(xa,y-17,pct(a.SR),'class="baseline" text-anchor="middle"');
        s+=text(xb,y+29,pct(b.SR),'class="second" text-anchor="middle"');
        s+=text(compact?367:1066,y+6,delta(change),`text-anchor="end" style="font-weight:600;fill:${change<0?colors.second:colors.oracle_visibility}"`);
        s+='</g>';
      });
    });
    return s+'</svg>';
  }
  function pairedNarrative(d,lang,selected='all') {
    const zh=locale(lang);
    if(selected==='all') return zh
      ? '月球与太空舱的三个模型均下降；火星上，Qwen 下降，而 Lance 和 Nova 上升。九组中降幅最大的是太空舱的 Lance：从 28.33% 降至 15.42%，相差 12.92 个百分点。光照改变的影响并不在各个模型和环境中保持一致。'
      : 'All three models decline on Moon and Cabin. On Mars, Qwen declines while Lance and Nova improve. The largest drop is Lance on Cabin: 28.33% to 15.42%, a decrease of 12.92 percentage points. The effect of lighting differs across both models and environments.';
    const changes=models.map(m=>{const a=row(d,selected,m,'baseline'),b=row(d,selected,m,'second');return `${short[m]} ${delta((b.SR-a.SR)*100)}${zh?' 个百分点':' pp'}`;});
    const lighting=zh?{mars:'火星由 35° 太阳高度角改为 8°。',moon:'月球使用各场景对应的配对光照条件；Moon C 的开启太阳光属于人工控制对照。',cabin:'太空舱切换至配对的暗光条件。'}[selected]:{mars:'Mars changes solar elevation from 35° to 8°.',moon:'Moon uses the paired lighting setup for each scene; solar-on in Moon C is an artificial controlled comparison.',cabin:'Cabin switches to the paired dim-light condition.'}[selected];
    return `${lighting} ${changes.join(zh?'；':'; ')}${zh?'。路线、目标、相机和停止参数保持不变。':'. Routes, targets, cameras and stopping parameters stay fixed.'}`;
  }
  function pairedExportSVG(d,lang,selected='all') {
    const svg=pairedSVG(d,lang,selected,false);
    const legend=`<circle cx="463" cy="19" r="5" fill="${colors.baseline}"/>${text(476,24,locale(lang)?'基准光照':'Baseline','class="axis"')}<path d="M610 12l7 7-7 7-7-7Z" fill="${colors.second}"/>${text(625,24,locale(lang)?'第二光照':'Second lighting','class="axis"')}`;
    return svg.replace('<rect width="100%" height="100%" fill="#fff"/>','<rect width="100%" height="100%" fill="#fff"/>'+legend);
  }
  function methodSVG(d,lang,w,l,metric,m) {
    const zh=locale(lang), unit=metric==='SR'?'%':'',value=r=>metric==='SR'?pct(r.SR):r.SPL.toFixed(3);
    const records=methods.map(rule=>row(d,w,m,l,rule));
    let s=svgStart(356,292,`rv-method-${w}-${l}-${metric}-${m}`,`${names[m]} · ${metric}`,records.map(r=>`${methodName(r.method,lang)}: ${value(r)}${unit}; ${r.successes}/${r.routes}`).join('; '));
    s+='<rect width="100%" height="100%" fill="#fff"/>';
    const left=121,right=285,top=31;
    for(const tick of [0,.25,.5,.75,1]) {
      const x=left+(right-left)*tick;
      s+=`<path d="M${x} 10V237" stroke="#e5e9eb"/>`;
      s+=text(x,261,metric==='SR'?Math.round(tick*100):tick.toFixed(2),'class="axis" text-anchor="middle"');
    }
    records.forEach((r,i)=>{
      const y=top+i*57,v=r[metric],length=(right-left)*v,rule=r.method;
      const label=rule==='oracle_visibility'?(zh?'可见性 Oracle':'Vis. Oracle'):rule==='Baseline'?(zh?'脚本终点':'Script end'):methodName(rule,lang);
      s+=`<g><title>${esc(`${methodName(rule,lang)} · ${value(r)}${unit} · ${r.successes}/${r.routes}`)}</title>`;
      s+=text(4,y+5,label,'style="font-size:14px"');
      if(v>0) s+=`<rect x="${left}" y="${y-9}" width="${length}" height="18" rx="3" fill="${colors[rule]}"/>`;
      else s+=`<circle cx="${left}" cy="${y}" r="3" fill="${colors[rule]}"/>`;
      s+=text(350,y+5,value(r)+unit,'text-anchor="end" style="font-size:14px;font-weight:600"');
      s+='</g>';
    });
    s+=text((left+right)/2,287,metric==='SR'?(zh?'成功率 SR (%)':'Success rate (%)'):'SPL (0–1)','class="axis" text-anchor="middle"');
    return s+'</svg>';
  }
  function methodsHTML(d,lang,w='mars',l='baseline',metric='SR') {
    return models.map(m=>`<article class="rv-model-panel"><h4>${names[m]}</h4>${methodSVG(d,lang,w,l,metric,m)}</article>`).join('');
  }
  function methodTable(d,lang,w='mars',l='baseline') {
    const zh=locale(lang);
    return `<table><caption>${esc(worldName(w,lang))} · ${zh?(l==='baseline'?'基准光照':'第二光照'):(l==='baseline'?'Baseline lighting':'Second lighting')}</caption><thead><tr>${(zh?['模型','停止规则','成功路线','SR','SPL']:['Judger','Stop rule','Successful routes','SR','SPL']).map(t=>`<th scope="col">${t}</th>`).join('')}</tr></thead><tbody>`+models.map(m=>methods.map(rule=>{
      const r=row(d,w,m,l,rule);return `<tr><th scope="row">${names[m]}</th><td>${methodName(rule,lang)}</td><td>${r.successes} / ${r.routes}</td><td>${pct(r.SR)}%</td><td>${r.SPL.toFixed(6)}</td></tr>`;
    }).join('')).join('')+'</tbody></table>';
  }
  function methodNarrative(d,lang,w,l,metric) {
    const zh=locale(lang), count=models.filter(m=>row(d,w,m,l,'TRACE')[metric]<row(d,w,m,l,'delay_only')[metric]).length;
    const light=zh?(l==='baseline'?'基准光照':'第二光照'):(l==='baseline'?'baseline lighting':'second lighting');
    const n=row(d,w,'nova',l,'TRACE'),nd=row(d,w,'nova',l,'delay_only');
    let s=zh?`${worldName(w,lang)} · ${light}：delay-only 的 ${metric} 高于 TRACE 的模型有 ${count}/3 个。`:`${worldName(w,lang)}, ${light}: delay-only exceeds TRACE on ${metric} for ${count} of the 3 models.`;
    if(w==='cabin' && l==='second') s+=zh?` Nova 是例外：TRACE 的 SR 为 ${pct(n.SR)}%，delay-only 为 ${pct(nd.SR)}%。`:` Nova is the exception: TRACE SR is ${pct(n.SR)}%, versus ${pct(nd.SR)}% for delay-only.`;
    else s+=zh?' 在这些结果中，多次视觉确认并没有带来更高的停止成功率。':' In these results, repeated visual confirmation does not deliver a higher stopping success rate.';
    return s;
  }
  function onlineSVG(d,lang,compact=false) {
    const zh=locale(lang),width=compact?380:1100,left=compact?80:162,right=compact?275:800,height=238;
    let s=svgStart(width,height,`rv-online-${compact?'small':'wide'}`,zh?'Qwen 在线与离线的停止帧一致性':'Qwen online/offline stop-frame agreement',zh?'各世界60条dev路线，显示停止帧相同的路线数。':'60 dev routes per world. Counts show routes with an identical stopping frame.');
    s+='<rect width="100%" height="100%" fill="#fff"/>';
    worlds.forEach((w,i)=>{
      const a=d.online[w].stop_agreement,y=40+i*66,total=right-left,agree=total*a.rate;
      s+=text(12,y+6,worldName(w,lang),'class="heavy"');
      s+=`<rect x="${left}" y="${y-11}" width="${total}" height="22" rx="4" fill="#dce2e5"/><rect x="${left}" y="${y-11}" width="${agree}" height="22" rx="4" fill="#29475c"/>`;
      s+=text(compact?369:1068,y+6,compact?`${a.numerator}/${a.denominator}`:`${a.numerator} / ${a.denominator} · ${(a.rate*100).toFixed(1)}%`,'class="heavy" text-anchor="end"');
    });
    for (const tick of [0,20,40,60]) s+=text(left+(right-left)*tick/60,223,tick,'class="axis" text-anchor="middle"');
    return s+'</svg>';
  }
  const API={validate,pairedSVG,pairedExportSVG,pairedNarrative,methodSVG,methodsHTML,methodTable,methodNarrative,onlineSVG};
  if(typeof module!=='undefined' && module.exports) {module.exports=API;return;}
  const root=global.document?.getElementById('results');
  if(!root || !global.BENCHMARK_RESULTS) return;
  const d=global.BENCHMARK_RESULTS, lang=document.documentElement.lang;
  try {validate(d);} catch(error) {return; /* Keep the verified static content. */}
  const pairSelect=root.querySelector('#rv-world');
  const worldSelect=root.querySelector('#rv-method-world');
  const lightSelect=root.querySelector('#rv-light');
  const metricButtons=[...root.querySelectorAll('[data-rv-metric]')];
  let metric='SR';
  const urls=new Map();
  function download(id,svg) {
    const a=root.querySelector(id);if(!a || !global.Blob || !global.URL?.createObjectURL) return;
    if(urls.has(id)) URL.revokeObjectURL(urls.get(id));
    const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml;charset=utf-8'}));urls.set(id,url);a.href=url;
  }
  function refreshPair(){
    const w=pairSelect.value;
    root.querySelector('#rv-pair-desktop').innerHTML=pairedSVG(d,lang,w,false);
    root.querySelector('#rv-pair-mobile').innerHTML=pairedSVG(d,lang,w,true);
    root.querySelector('#rv-pair-reading').textContent=pairedNarrative(d,lang,w);
    download('#rv-pair-export',pairedExportSVG(d,lang,w));
  }
  function refreshMethods(){
    const w=worldSelect.value,l=lightSelect.value;
    root.querySelector('#rv-method-plots').innerHTML=methodsHTML(d,lang,w,l,metric);
    root.querySelector('#rv-method-values').innerHTML=methodTable(d,lang,w,l);
    root.querySelector('#rv-method-reading').textContent=methodNarrative(d,lang,w,l,metric);
    root.querySelector('#rv-method-context').textContent=locale(lang)?`${worldName(w,lang)} · 每个模型 240 条 test 路线 · K${d.frozen[w][0]} / q${d.frozen[w][1]}`:`${worldName(w,lang)} · 240 test routes per model · K${d.frozen[w][0]} / q${d.frozen[w][1]}`;
    metricButtons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.rvMetric===metric)));
  }
  pairSelect.addEventListener('change',refreshPair);
  worldSelect.addEventListener('change',refreshMethods);
  lightSelect.addEventListener('change',refreshMethods);
  metricButtons.forEach(b=>b.addEventListener('click',()=>{metric=b.dataset.rvMetric;refreshMethods();}));
  root.querySelectorAll('[data-rv-controls]').forEach(e=>e.hidden=false);
  root.dataset.resultsEnhanced='true';
})(typeof window!=='undefined'?window:globalThis);
