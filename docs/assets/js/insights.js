(() => {
  'use strict';
  const root = document.querySelector('[data-q25-insights]');
  if (!root) return;
  const $ = (s, scope = root) => scope.querySelector(s);
  const $$ = (s, scope = root) => Array.from(scope.querySelectorAll(s));
  const isNum = (v) => v !== null && v !== '' && Number.isFinite(Number(v));
  const n = (v) => isNum(v) ? Number(v) : null;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const svgEl = (name, attrs = {}) => { const el = document.createElementNS('http://www.w3.org/2000/svg', name); Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k, v)); return el; };
  const fmt = (v, d = 3) => isNum(v) ? Number(v).toFixed(d) : '—';
  const pct = (v, d = 1) => isNum(v) ? `${(Number(v) * 100).toFixed(d)}%` : '—';
  const signFmt = (v, d=3) => isNum(v) ? `${Number(v) > 0 ? '+' : ''}${Number(v).toFixed(d)}` : '—';
  const human = (k) => String(k || '').replace(/^__/, '').replace(/_/g, ' ').replace(/\b\w/g, m => m.toUpperCase());
  const metrics = [
    {key:'dev_sharpe_12', label:'Dev Sharpe @12%', dir:'max', type:'num'},
    {key:'research_sharpe_12', label:'Research Sharpe @12%', dir:'max', type:'num'},
    {key:'dev_cagr_12', label:'Dev CAGR @12%', dir:'max', type:'pct'},
    {key:'dev_sortino_12', label:'Dev Sortino @12%', dir:'max', type:'num'},
    {key:'dev_calmar_12', label:'Dev Calmar @12%', dir:'max', type:'num'},
    {key:'__causalMargin', label:'Control margin', dir:'max', type:'num'},
    {key:'evidence_completeness', label:'Evidence completeness', dir:'max', type:'pct'},
    {key:'__absDecay', label:'|Research→Dev Sharpe gap|', dir:'min', type:'num'},
    {key:'__costDrag', label:'Cost drag SR0→SR12', dir:'min', type:'num'},
    {key:'mean_turnover_12', label:'Mean turnover @12%', dir:'min', type:'pct'},
    {key:'__drawdownMag', label:'Drawdown magnitude @12%', dir:'min', type:'pct'}
  ];
  const metricMap = new Map(metrics.map(m => [m.key, m]));
  const pairMetricKeys = ['dev_sharpe_12','__causalMargin','__absDecay','__costDrag','mean_turnover_12','__drawdownMag','dev_calmar_12'];
  const heatMetricKeys = ['dev_sharpe_12','research_sharpe_12','__causalMargin','__absDecay','__costDrag','mean_turnover_12','__drawdownMag'];
  const fingerprintKeys = [['dev_sharpe_12','Economics'],['__causalMargin','Control resilience'],['__absDecay','Dev stability'],['__costDrag','Cost resilience'],['mean_turnover_12','Turnover efficiency'],['__drawdownMag','Drawdown resilience']];
  let rows = [], decisions = [], controlPlane = {}, learning = {}, backtest = {}, attribution = null;
  let selectedCampaign = '', selectedFamily = '', selectedKey = null;
  let xKey = 'mean_turnover_12', yKey = 'dev_sharpe_12', baseOnly = true;
  let currentRows = [], currentPareto = [];

  function pathContext(path, row) {
    let campaign = row.campaign || row.campaign_id || row.experiment || '';
    let lane = row.lane || '';
    if (!lane && path.length) lane = String(path[0]);
    if (!campaign && path[0] === 'additional_campaigns' && path[1]) campaign = String(path[1]);
    if (!campaign) {
      const hit = path.find(p => typeof p === 'string' && /^(?:frontier|ebenezar|campaign|topology|historical|development)/i.test(p));
      if (hit) campaign = String(hit);
    }
    return {campaign: campaign || lane || 'unscoped', lane: lane || 'unscoped'};
  }
  function looksLikeResult(obj) {
    if (!obj || Array.isArray(obj) || typeof obj !== 'object' || typeof obj.id !== 'string') return false;
    const keys = Object.keys(obj);
    return keys.some(k => /(sharpe|score|cagr|sortino|calmar|drawdown|turnover|hit_rate|volatility|return)/i.test(k) && (isNum(obj[k]) || obj[k] === null)) || typeof obj.status === 'string';
  }
  function extractMatrix(data) {
    const out = [], ds = [], seen = new Set(), seenD = new Set();
    function walk(node, path=[]) {
      if (Array.isArray(node)) { node.forEach((v,i) => walk(v, path.concat(i))); return; }
      if (!node || typeof node !== 'object') return;
      if (looksLikeResult(node)) {
        const c = pathContext(path,node), r = {...node,__campaign:c.campaign,__lane:c.lane,__path:path.join('.')};
        r.__key = [r.__campaign,r.__lane,r.id,r.mode || '',r.__path].join('|');
        if (!seen.has(r.__key)) { seen.add(r.__key); out.push(r); }
      } else if (typeof node.family === 'string' && typeof node.decision === 'string' && ('best_score' in node || 'decision_code' in node)) {
        const c = pathContext(path,node), k = [c.campaign,node.family,node.decision_code || node.decision].join('|');
        if (!seenD.has(k)) { seenD.add(k); ds.push({...node,__campaign:c.campaign,__lane:c.lane}); }
      }
      Object.entries(node).forEach(([k,v]) => walk(v,path.concat(k)));
    }
    walk(data,[]);
    return {rows:out, decisions:ds};
  }
  function attachDecision(row) {
    const exact = decisions.filter(d => d.__campaign === row.__campaign && d.family === row.family);
    if (exact.length === 1) return exact[0];
    const global = decisions.filter(d => d.family === row.family);
    return global.length === 1 ? global[0] : null;
  }
  function enrich() {
    const destructive = new Set(['control','ablation','falsifier']);
    rows.forEach(r => { r.__decision = attachDecision(r); });
    rows.forEach(r => {
      r.__absDecay = isNum(r.dev_sharpe_12) && isNum(r.research_sharpe_12) ? Math.abs(Number(r.dev_sharpe_12)-Number(r.research_sharpe_12)) : null;
      r.__devMinusResearch = isNum(r.dev_sharpe_12) && isNum(r.research_sharpe_12) ? Number(r.dev_sharpe_12)-Number(r.research_sharpe_12) : null;
      r.__costDrag = isNum(r.dev_sharpe_0) && isNum(r.dev_sharpe_12) ? Number(r.dev_sharpe_0)-Number(r.dev_sharpe_12) : null;
      r.__drawdownMag = isNum(r.worst_drawdown_12) ? Math.abs(Number(r.worst_drawdown_12)) : null;
      r.__causalMargin = null; r.__challenger = null;
      if (String(r.mode).toLowerCase() === 'base' && r.family) {
        const challengers = rows.filter(c => c.__campaign === r.__campaign && c.family === r.family && destructive.has(String(c.mode || '').toLowerCase()) && isNum(c.dev_sharpe_12));
        if (challengers.length && isNum(r.dev_sharpe_12)) {
          challengers.sort((a,b) => Number(b.dev_sharpe_12)-Number(a.dev_sharpe_12));
          r.__challenger = challengers[0];
          r.__causalMargin = Number(r.dev_sharpe_12)-Number(challengers[0].dev_sharpe_12);
        }
      }
    });
  }
  function formatMetric(key, value) { const m = metricMap.get(key); if (!m) return fmt(value); return m.type === 'pct' ? pct(value) : fmt(value); }
  function desirable(v, m) { return m.dir === 'max' ? Number(v) : -Number(v); }
  function dominates(a,b,mx,my) { const ax=desirable(a[mx.key],mx), bx=desirable(b[mx.key],mx), ay=desirable(a[my.key],my), by=desirable(b[my.key],my); return ax >= bx && ay >= by && (ax > bx || ay > by); }
  function pareto(input, xk=xKey, yk=yKey) {
    const mx=metricMap.get(xk), my=metricMap.get(yk); if (!mx || !my) return [];
    const valid=input.filter(r=>isNum(r[xk])&&isNum(r[yk]));
    return valid.filter(r=>!valid.some(o=>o!==r && dominates(o,r,mx,my)));
  }
  function dominanceCount(row, input) { const mx=metricMap.get(xKey), my=metricMap.get(yKey); if (!mx||!my||!isNum(row[xKey])||!isNum(row[yKey])) return 0; return input.filter(o=>o!==row&&isNum(o[xKey])&&isNum(o[yKey])&&dominates(row,o,mx,my)).length; }
  function percentile(row, key, input) {
    const m=metricMap.get(key), val=n(row[key]); if (!m || val===null) return null;
    const vals=input.map(r=>n(r[key])).filter(v=>v!==null); if (!vals.length) return null;
    const d=desirable(val,m), ds=vals.map(v=>desirable(v,m)); if (ds.length===1) return 100;
    const lower=ds.filter(v=>v<d).length, equal=ds.filter(v=>v===d).length;
    return ((lower + .5*Math.max(0,equal-1))/(ds.length-1))*100;
  }
  function campaignRows() { return rows.filter(r=>r.__campaign===selectedCampaign && (!baseOnly || String(r.mode).toLowerCase()==='base') && (!selectedFamily || r.family===selectedFamily)); }
  function allCampaignBase() { return rows.filter(r=>r.__campaign===selectedCampaign && String(r.mode).toLowerCase()==='base'); }
  function metricOptions(select, selected) { select.innerHTML=metrics.map(m=>`<option value="${esc(m.key)}">${esc(m.label)} · ${m.dir==='max'?'maximize':'minimize'}</option>`).join(''); select.value=selected; }
  function defaultCampaign() {
    const preferred=controlPlane?.surface_debt?.latest_full_matrix_campaign;
    const campaigns=[...new Set(rows.map(r=>r.__campaign))]; if (preferred && campaigns.includes(preferred)) return preferred;
    const counts=new Map(); rows.filter(r=>String(r.mode).toLowerCase()==='base').forEach(r=>counts.set(r.__campaign,(counts.get(r.__campaign)||0)+1));
    return [...counts.entries()].sort((a,b)=>b[1]-a[1])[0]?.[0] || campaigns[0] || '';
  }
  function initControls() {
    selectedCampaign=defaultCampaign(); const campaigns=[...new Set(rows.map(r=>r.__campaign).filter(Boolean))].sort();
    const cs=$('[data-control="campaign"]'); cs.innerHTML=campaigns.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join(''); cs.value=selectedCampaign;
    metricOptions($('[data-control="x"]'),xKey); metricOptions($('[data-control="y"]'),yKey); updateFamilyOptions();
  }
  function updateFamilyOptions() {
    const fs=[...new Set(rows.filter(r=>r.__campaign===selectedCampaign).map(r=>r.family).filter(Boolean))].sort(); const s=$('[data-control="family"]'), old=selectedFamily;
    s.innerHTML='<option value="">All families</option>'+fs.map(f=>`<option value="${esc(f)}">${esc(f)}</option>`).join(''); selectedFamily=fs.includes(old)?old:''; s.value=selectedFamily;
  }
  function niceTicks(min,max,count=5) { if(!Number.isFinite(min)||!Number.isFinite(max))return[]; if(min===max)return[min]; const raw=(max-min)/Math.max(1,count-1), pow=Math.pow(10,Math.floor(Math.log10(Math.abs(raw)||1))), frac=raw/pow; const nice=(frac<=1?1:frac<=2?2:frac<=5?5:10)*pow,start=Math.ceil(min/nice)*nice,out=[]; for(let v=start;v<=max+nice*.25;v+=nice)out.push(v); return out; }
  function selectedRow() { return rows.find(r=>r.__key===selectedKey) || null; }
  function selectRow(r) { selectedKey=r?.__key || null; renderPareto(); renderInspector(); renderIncidence(); renderDominance(); renderCausal(); renderFragility(); renderHeatmap(); }
  function tooltipShow(evt, html) { const t=$('[data-tooltip]'); if(!t)return; t.innerHTML=html;t.hidden=false;const shell=t.parentElement,box=shell.getBoundingClientRect();t.style.left=`${clamp(evt.clientX-box.left+12,8,Math.max(8,box.width-315))}px`;t.style.top=`${clamp(evt.clientY-box.top+12,8,Math.max(8,box.height-150))}px`; }
  function tooltipHide(){const t=$('[data-tooltip]');if(t)t.hidden=true;}

  function renderContext() {
    currentRows=campaignRows(); currentPareto=pareto(currentRows); const bases=allCampaignBase();
    $('[data-context-campaign]').textContent=selectedCampaign || '—'; $('[data-context-state]').textContent=controlPlane?.surface_debt?.latest_full_matrix_campaign===selectedCampaign?'LATEST FULL MATRIX':'SELECTED CONTEXT';
    $('[data-context-note]').textContent=`${bases.length} measured base cells in this context. Formal decisions and missing fields remain separate from Pareto membership.`;
    const set=(k,v)=>{const el=$(`[data-kpi="${k}"]`);if(el)el.textContent=v;}; set('bases',bases.length.toLocaleString()); set('front',currentPareto.length.toLocaleString()); set('families',new Set(bases.map(r=>r.family).filter(Boolean)).size.toLocaleString()); set('pairs',(pairMetricKeys.length*(pairMetricKeys.length-1)/2).toLocaleString());
    $('[data-pareto-count]').textContent=`${currentPareto.length} / ${currentRows.filter(r=>isNum(r[xKey])&&isNum(r[yKey])).length} NON-DOMINATED`;
    const mx=metricMap.get(xKey),my=metricMap.get(yKey); $('[data-pareto-title]').textContent=`${my.label} vs ${mx.label}`; $('[data-pareto-note]').textContent=`${mx.dir==='max'?'Higher':'Lower'} ${mx.label.toLowerCase()} and ${my.dir==='max'?'higher':'lower'} ${my.label.toLowerCase()} define the current non-dominated edge. This is descriptive within ${selectedCampaign}.`; $('[data-context-warning]').textContent=`Pareto dominance is evaluated only inside ${selectedCampaign}. No scalar rank is computed across campaigns or evidence lanes.`;
  }
  function drawScatter(svg, points, xk, yk, options={}) {
    const shell=svg.parentElement; svg.replaceChildren(); if(!points.length)return false;
    const width=Math.max(350,shell.clientWidth||700),height=options.height||455,m={t:26,r:24,b:60,l:72},pw=width-m.l-m.r,ph=height-m.t-m.b; svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
    let xs=points.map(r=>Number(r[xk])),ys=points.map(r=>Number(r[yk])),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys); const xp=Math.max((xmax-xmin)*.09,Math.abs(xmax||1)*.02,.0001),yp=Math.max((ymax-ymin)*.09,Math.abs(ymax||1)*.02,.0001);xmin-=xp;xmax+=xp;ymin-=yp;ymax+=yp; if(options.xZero){xmin=Math.min(xmin,0);xmax=Math.max(xmax,0)} if(options.yOne){ymin=Math.min(ymin,1);ymax=Math.max(ymax,1)}
    const x=v=>m.l+(Number(v)-xmin)/(xmax-xmin||1)*pw, y=v=>m.t+(ymax-Number(v))/(ymax-ymin||1)*ph;
    niceTicks(xmin,xmax,6).forEach(t=>{const xx=x(t);svg.append(svgEl('line',{x1:xx,y1:m.t,x2:xx,y2:height-m.b,class:'grid'}));const tx=svgEl('text',{x:xx,y:height-30,'text-anchor':'middle'});tx.textContent=formatMetric(xk,t);svg.append(tx);});
    niceTicks(ymin,ymax,6).forEach(t=>{const yy=y(t);svg.append(svgEl('line',{x1:m.l,y1:yy,x2:width-m.r,y2:yy,class:'grid'}));const tx=svgEl('text',{x:m.l-10,y:yy+3,'text-anchor':'end'});tx.textContent=formatMetric(yk,t);svg.append(tx);});
    svg.append(svgEl('line',{x1:m.l,y1:height-m.b,x2:width-m.r,y2:height-m.b,class:'axis'}));svg.append(svgEl('line',{x1:m.l,y1:m.t,x2:m.l,y2:height-m.b,class:'axis'})); if(options.xZero&&xmin<=0&&xmax>=0){const xx=x(0);svg.append(svgEl('line',{x1:xx,y1:m.t,x2:xx,y2:height-m.b,class:'zero'}));} if(options.yOne&&ymin<=1&&ymax>=1){const yy=y(1);svg.append(svgEl('line',{x1:m.l,y1:yy,x2:width-m.r,y2:yy,class:'threshold'}));}
    const xl=svgEl('text',{x:m.l+pw/2,y:height-8,'text-anchor':'middle'});xl.textContent=metricMap.get(xk)?.label||human(xk);svg.append(xl); const yl=svgEl('text',{x:14,y:m.t+ph/2,transform:`rotate(-90 14 ${m.t+ph/2})`,'text-anchor':'middle'});yl.textContent=metricMap.get(yk)?.label||human(yk);svg.append(yl);
    if(options.frontier?.length>1){const f=options.frontier.slice().sort((a,b)=>Number(a[xk])-Number(b[xk]));svg.append(svgEl('polyline',{points:f.map(r=>`${x(r[xk])},${y(r[yk])}`).join(' '),class:'frontier-line'}));}
    const fset=new Set((options.frontier||[]).map(r=>r.__key)); points.forEach(r=>{const c=svgEl('circle',{cx:x(r[xk]),cy:y(r[yk]),r:fset.has(r.__key)?6:4.5,class:`point ${fset.has(r.__key)?'frontier':''} ${r.__key===selectedKey?'selected':''}`});c.addEventListener('mouseenter',e=>tooltipShow(e,`<strong>${esc(r.id)}</strong><span>${esc(metricMap.get(xk)?.label||xk)} <b>${esc(formatMetric(xk,r[xk]))}</b></span><span>${esc(metricMap.get(yk)?.label||yk)} <b>${esc(formatMetric(yk,r[yk]))}</b></span><span>Family <b>${esc(r.family||'—')}</b></span><span>Decision <b>${esc(r.__decision?.decision_code||r.__decision?.decision||'—')}</b></span>`));c.addEventListener('mousemove',e=>tooltipShow(e,$('[data-tooltip]').innerHTML));c.addEventListener('mouseleave',tooltipHide);c.addEventListener('click',()=>selectRow(r));svg.append(c);}); return true;
  }
  function renderPareto() { const svg=$('[data-chart="pareto"]'), valid=currentRows.filter(r=>isNum(r[xKey])&&isNum(r[yKey])); const ok=drawScatter(svg,valid,xKey,yKey,{frontier:currentPareto,height:455}); $('[data-empty="pareto"]').hidden=ok; }
  function frontierIncidence() {
    const base=allCampaignBase(), result=new Map(base.map(r=>[r.__key,{row:r,front:0,eligible:0}]));
    for(let i=0;i<pairMetricKeys.length;i++)for(let j=i+1;j<pairMetricKeys.length;j++){const a=pairMetricKeys[i],b=pairMetricKeys[j],eligible=base.filter(r=>isNum(r[a])&&isNum(r[b])); if(eligible.length<2)continue; const f=new Set(pareto(eligible,a,b).map(r=>r.__key)); eligible.forEach(r=>{const q=result.get(r.__key);q.eligible++;if(f.has(r.__key))q.front++;});}
    return [...result.values()].filter(q=>q.eligible>0).map(q=>({...q,rate:q.front/q.eligible})).sort((a,b)=>b.rate-a.rate||b.front-a.front||String(a.row.id).localeCompare(String(b.row.id)));
  }
  function renderIncidence() { const host=$('[data-incidence]'), vals=frontierIncidence().slice(0,12); if(!vals.length){host.innerHTML='<div class="qi-empty-inline">No eligible objective pairs.</div>';return;} host.innerHTML=vals.map(q=>`<div class="qi-incidence-row ${q.row.__key===selectedKey?'selected':''}" data-key="${esc(q.row.__key)}"><strong>${esc(q.row.id)}</strong><div class="qi-mini-track"><i style="width:${clamp(q.rate*100,2,100)}%"></i></div><em>${Math.round(q.rate*100)}% · ${q.front}/${q.eligible}</em></div>`).join(''); $$('.qi-incidence-row',host).forEach(el=>el.addEventListener('click',()=>{const r=rows.find(x=>x.__key===el.dataset.key);if(r)selectRow(r);})); }
  function renderDominance() { const host=$('[data-dominance]'), valid=currentRows.filter(r=>isNum(r[xKey])&&isNum(r[yKey])).map(r=>({r,c:dominanceCount(r,currentRows)})).sort((a,b)=>b.c-a.c||String(a.r.id).localeCompare(String(b.r.id))).slice(0,14),max=Math.max(1,...valid.map(x=>x.c)); $('[data-dominance-badge]').textContent=`${metricMap.get(xKey)?.label} × ${metricMap.get(yKey)?.label}`; host.innerHTML=valid.length?valid.map(q=>`<div class="qi-dominance-row" data-key="${esc(q.r.__key)}"><strong>${esc(q.r.id)}</strong><div class="qi-mini-track"><i style="width:${Math.max(2,q.c/max*100)}%"></i></div><em>${q.c}</em></div>`).join(''):'<div class="qi-empty-inline">No comparable rows.</div>'; $$('.qi-dominance-row',host).forEach(el=>el.addEventListener('click',()=>{const r=rows.find(x=>x.__key===el.dataset.key);if(r)selectRow(r);})); }
  function renderCausal() { const base=allCampaignBase().filter(r=>isNum(r.__causalMargin)&&isNum(r.dev_sharpe_12)), svg=$('[data-chart="causal"]'); const ok=drawScatter(svg,base,'__causalMargin','dev_sharpe_12',{xZero:true,yOne:true,height:310}); $('[data-empty="causal"]').hidden=ok; }
  function renderFragility() { const base=allCampaignBase().filter(r=>isNum(r.__absDecay)&&isNum(r.__costDrag)), svg=$('[data-chart="fragility"]'); const ok=drawScatter(svg,base,'__absDecay','__costDrag',{height:310}); $('[data-empty="fragility"]').hidden=ok; }
  function renderHeatmap() {
    const host=$('[data-heatmap]'), base=allCampaignBase().filter(r=>!selectedFamily||r.family===selectedFamily); if(!base.length){host.innerHTML='No base rows.';return;}
    const ranks={}; heatMetricKeys.forEach(k=>{ranks[k]=new Map(base.map(r=>[r.__key,percentile(r,k,base)]));}); const sorted=base.slice().sort((a,b)=>(n(b.dev_sharpe_12)??-Infinity)-(n(a.dev_sharpe_12)??-Infinity));
    host.innerHTML=`<table class="qi-heatmap"><thead><tr><th>Strategy / family</th>${heatMetricKeys.map(k=>`<th>${esc(metricMap.get(k)?.label||human(k))}</th>`).join('')}</tr></thead><tbody>${sorted.map(r=>`<tr><td data-key="${esc(r.__key)}"><strong>${esc(r.id)}</strong><span>${esc(r.family||'—')} · ${esc(r.__decision?.decision_code||r.__decision?.decision||'no family verdict')}</span></td>${heatMetricKeys.map(k=>{const p=ranks[k].get(r.__key),opacity=p === null ? .02 : .04 + .34*(p/100);return `<td class="metric" style="--heat:${opacity.toFixed(3)}">${esc(formatMetric(k,r[k]))}</td>`;}).join('')}</tr>`).join('')}</tbody></table>`;
    $$('td[data-key]',host).forEach(el=>el.addEventListener('click',()=>{const r=rows.find(x=>x.__key===el.dataset.key);if(r)selectRow(r);}));
  }
  function renderInspector() {
    const r=selectedRow(), title=$('[data-inspect="title"]'),mode=$('[data-inspect="mode"]'),meta=$('[data-inspect="meta"]'),kpis=$('[data-inspect="kpis"]'),fp=$('[data-inspect="fingerprint"]'),decision=$('[data-inspect="decision"]');
    if(!r){title.textContent='Select a point';mode.textContent='—';meta.textContent='Click any point, robustness bar or heatmap row.';kpis.innerHTML='';fp.innerHTML='';decision.textContent='';return;}
    title.textContent=r.id;mode.textContent=String(r.mode||'row').toUpperCase(); meta.textContent=`${r.__campaign} · ${r.family||'no family'} · ${r.status||'status unknown'} · lane ${r.__lane}`;
    const items=[['Dev SR12',fmt(r.dev_sharpe_12)],['Research SR12',fmt(r.research_sharpe_12)],['Control margin',signFmt(r.__causalMargin)],['|Research→Dev|',fmt(r.__absDecay)],['Cost drag',fmt(r.__costDrag)],['Turnover',pct(r.mean_turnover_12)],['Worst DD',pct(r.worst_drawdown_12)],['Evidence',pct(r.evidence_completeness)]]; kpis.innerHTML=items.map(([a,b])=>`<div><span>${esc(a)}</span><b>${esc(b)}</b></div>`).join('');
    const base=allCampaignBase(); fp.innerHTML=`<h3>Within-context fingerprint</h3>${fingerprintKeys.map(([k,label])=>{const p=percentile(r,k,base);return `<div class="qi-fingerprint-row"><span>${esc(label)}</span><div class="qi-fingerprint-track"><i style="width:${p===null?0:clamp(p,1,100)}%"></i></div><b>${p===null?'—':Math.round(p)}</b></div>`;}).join('')}<div class="qi-fingerprint-foot">Percentiles compare desirable direction inside ${esc(selectedCampaign)} only. They are not averaged.</div>`;
    const d=r.__decision, challenger=r.__challenger; decision.innerHTML=d?`<strong>${esc(d.decision||'FAMILY DECISION')} / ${esc(d.decision_code||'')}</strong><br>${esc(d.reason||'Formal family adjudication is attached to this row.')} ${challenger?`<br><br>Strongest matched destructive challenger: <b>${esc(challenger.id)}</b> · Dev SR12 ${fmt(challenger.dev_sharpe_12)}.`:''}`:`No unique family adjudication is attached to this row; the workbench does not infer one.${challenger?` Strongest matched challenger: ${esc(challenger.id)}.`:''}`;
  }
  function sparkline(values) { const vs=values.filter(v=>isNum(v.value)); if(!vs.length)return ''; const w=260,h=70,p=8,min=Math.min(...vs.map(v=>Number(v.value))),max=Math.max(...vs.map(v=>Number(v.value))),x=i=>p+i/(Math.max(1,vs.length-1))*(w-2*p),y=v=>p+(max-Number(v))/(max-min||1)*(h-2*p); const pts=vs.map((v,i)=>`${x(i)},${y(v.value)}`).join(' ');return `<svg class="qi-spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><line class="base" x1="${p}" y1="${h-p}" x2="${w-p}" y2="${h-p}"></line><polyline class="line" points="${pts}"></polyline>${vs.map((v,i)=>`<circle class="dot" cx="${x(i)}" cy="${y(v.value)}" r="3"><title>${esc(v.campaign)}: ${fmt(v.value)}</title></circle>`).join('')}</svg>`; }
  function renderLearning() {
    const host=$('[data-trajectories]'), t=learning?.trajectories||{}, defs=[['best_robust_sharpe','Best robust Sharpe','num'],['control_support_rate','Control support','pct'],['median_central_control_margin','Median control margin','num'],['median_dev_minus_research_sharpe_12','Median Dev−Research SR12','num']];
    host.innerHTML=defs.map(([k,label,type])=>{const q=t[k],latest=q?.latest;return `<article class="qi-trajectory-card"><span>${esc(label)}</span><strong>${type==='pct'?pct(latest):fmt(latest)}</strong><small>${esc(q?.direction||'—')} · Δ first→latest ${type==='pct'?pct(q?.delta_first_to_latest):signFmt(q?.delta_first_to_latest)}</small>${sparkline(q?.values||[])}</article>`;}).join('');
    $('[data-learning-tags]').innerHTML=`<div class="qi-state-tags">${(learning?.state_tags||[]).map(s=>`<span>${esc(s)}</span>`).join('')}</div>`; const event=learning?.validation_calibration?.events?.[0], f=$('[data-forward-calibration]'); f.innerHTML=event?`<div class="qi-forward-card"><strong>${Math.round((event.retention_ratio||0)*100)}% forward retention</strong><p>${esc(event.candidate)}: development robust Sharpe ${fmt(event.development_robust_sharpe)} → forward SR12 ${fmt(event.forward_sharpe_12)}. One observed forward gate is calibration evidence, not a universal shrinkage estimate.</p></div>`:`<div class="qi-forward-card"><strong>No forward calibration event</strong><p>Forward evidence remains missing.</p></div>`;
  }
  function coverageState() {
    const bt=backtest||{}, a=attribution||{}, strategySeries=String(bt.status).toLowerCase()==='available' && Array.isArray(bt.series) && bt.series.length>0, strategies=a.strategies&&typeof a.strategies==='object'?Object.values(a.strategies):[], has=(field)=>strategies.some(s=>Array.isArray(s[field])&&s[field].length>0), cov=a.coverage||{};
    return [['Daily strategy returns',strategySeries||cov.daily_returns===true,strategySeries?'Committed backtest series':'No committed backtest time series'],['Coin weights',cov.coin_weights===true,cov.coin_weights===true?'Lagged holdings present':'No committed per-coin holdings'],['Coin P&L',has('coins')||cov.coin_contribution===true,has('coins')?'Per-coin contribution present':'Requires weights × coin returns'],['Factor exposures',has('factors')||cov.factor_exposure===true,has('factors')?'Measured factor packet present':'No committed factor exposure packet'],['Regime attribution',has('regimes')||cov.regime_attribution===true,has('regimes')?'Conditional returns present':'No causal regime-return packet'],['Provenance',Boolean(a.source||a.provenance),(a.source||a.provenance)?'Attribution source recorded':'No attribution chain of custody']];
  }
  function attrBarRows(items,labelKey,valueKey,formatter=fmt) { if(!Array.isArray(items)||!items.length)return '<div class="qi-empty-inline">No measured values.</div>'; const vals=items.map(x=>Math.abs(Number(x[valueKey])||0)),max=Math.max(...vals,1e-12); return items.slice().sort((a,b)=>Math.abs(Number(b[valueKey])||0)-Math.abs(Number(a[valueKey])||0)).slice(0,12).map(x=>`<div class="qi-attr-bar"><span>${esc(x[labelKey]||'—')}</span><div><i style="width:${Math.max(2,Math.abs(Number(x[valueKey])||0)/max*100)}%"></i></div><b>${esc(formatter(x[valueKey]))}</b></div>`).join(''); }
  function renderAttributionStrategy(key) { const s=attribution?.strategies?.[key]; if(!s)return; $('[data-attribution-coins]').innerHTML=attrBarRows(s.coins,'coin','contribution',v=>signFmt(v)); $('[data-attribution-factors]').innerHTML=attrBarRows(s.factors,'factor',s.factors?.some(x=>'beta'in x)?'beta':'correlation',v=>signFmt(v)); $('[data-attribution-regimes]').innerHTML=attrBarRows(s.regimes,'regime',s.regimes?.some(x=>'sharpe'in x)?'sharpe':'mean_return',v=>signFmt(v)); }
  function renderAttribution() {
    const cov=coverageState(), host=$('[data-coverage]');host.innerHTML=cov.map(([label,ok,note])=>`<div class="qi-coverage-card ${ok?'available':''}"><i></i><strong>${esc(label)}</strong><span>${esc(note)}</span></div>`).join(''); const strategies=attribution?.strategies&&typeof attribution.strategies==='object'?Object.keys(attribution.strategies):[], ready=strategies.some(k=>{const s=attribution.strategies[k];return (s.coins?.length||s.factors?.length||s.regimes?.length)}); $('[data-attribution-status]').textContent=ready?'MEASURED ATTRIBUTION AVAILABLE':'ATTRIBUTION EVIDENCE GAP'; $('[data-attribution-ready]').hidden=!ready; $('[data-attribution-gap]').hidden=ready;
    if(ready){const sel=$('[data-attribution-strategy]');sel.innerHTML=strategies.map(k=>`<option value="${esc(k)}">${esc(k)}</option>`).join('');sel.onchange=()=>renderAttributionStrategy(sel.value);renderAttributionStrategy(strategies[0]);} else {const src=backtest?.source?.note||'No committed strategy-level return stream is available.';$('[data-attribution-note]').textContent=`${src} Coin contribution, factor beta and regime-conditional return charts remain blank rather than inferred.`;}
  }
  function exportView() { const mx=metricMap.get(xKey),my=metricMap.get(yKey),fset=new Set(currentPareto.map(r=>r.__key)),header=['strategy','family','campaign','mode',xKey,yKey,'pareto_member','family_decision','control_margin','abs_research_dev_gap','cost_drag','turnover','worst_drawdown'],q=v=>`"${String(v??'').replace(/"/g,'""')}"`,lines=[header.join(',')].concat(currentRows.filter(r=>isNum(r[xKey])&&isNum(r[yKey])).map(r=>[r.id,r.family,r.__campaign,r.mode,r[xKey],r[yKey],fset.has(r.__key),r.__decision?.decision_code||r.__decision?.decision||'',r.__causalMargin,r.__absDecay,r.__costDrag,r.mean_turnover_12,r.worst_drawdown_12].map(q).join(','))); const blob=new Blob([lines.join('\n')],{type:'text/csv'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`q25-pareto-${selectedCampaign}-${mx?.key||xKey}-vs-${my?.key||yKey}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000); }
  function renderAll() { renderContext();renderPareto();renderInspector();renderIncidence();renderDominance();renderCausal();renderFragility();renderHeatmap();renderLearning();renderAttribution(); }
  function bind() {
    $('[data-control="campaign"]').addEventListener('change',e=>{selectedCampaign=e.target.value;selectedFamily='';updateFamilyOptions();selectedKey=null;renderAll();}); $('[data-control="x"]').addEventListener('change',e=>{xKey=e.target.value;renderAll();}); $('[data-control="y"]').addEventListener('change',e=>{yKey=e.target.value;renderAll();}); $('[data-control="family"]').addEventListener('change',e=>{selectedFamily=e.target.value;selectedKey=null;renderAll();}); $('[data-control="base-only"]').addEventListener('change',e=>{baseOnly=e.target.checked;selectedKey=null;renderAll();});
    $('[data-action="reset"]').addEventListener('click',()=>{selectedCampaign=defaultCampaign();selectedFamily='';xKey='mean_turnover_12';yKey='dev_sharpe_12';baseOnly=true;$('[data-control="campaign"]').value=selectedCampaign;metricOptions($('[data-control="x"]'),xKey);metricOptions($('[data-control="y"]'),yKey);$('[data-control="base-only"]').checked=true;updateFamilyOptions();selectedKey=null;renderAll();}); $('[data-action="export"]').addEventListener('click',exportView); window.addEventListener('resize',()=>{renderPareto();renderCausal();renderFragility();});
  }
  async function fetchJson(url, optional=false) { try { const r=await fetch(url,{cache:'no-store'}); if(!r.ok){if(optional)return null;throw new Error(`HTTP ${r.status}`);}return await r.json(); } catch(e){if(optional)return null;throw e;} }
  async function init() {
    try {
      const [matrix,control,learn,bt,attr]=await Promise.all([fetchJson(root.dataset.matrixSource),fetchJson(root.dataset.controlSource),fetchJson(root.dataset.learningSource),fetchJson(root.dataset.backtestSource,true),fetchJson(root.dataset.attributionSource,true)]); const x=extractMatrix(matrix);rows=x.rows;decisions=x.decisions;controlPlane=control||{};learning=learn||{};backtest=bt||{};attribution=attr;enrich();initControls();bind(); const initial=allCampaignBase().filter(r=>isNum(r.dev_sharpe_12)).sort((a,b)=>Number(b.dev_sharpe_12)-Number(a.dev_sharpe_12))[0];selectedKey=initial?.__key||null;renderAll(); $('[data-insight-state]').textContent='EVIDENCE ONLINE'; $('.qt-feed')?.classList.add('is-live');
    } catch(e) { $('[data-insight-state]').textContent='EVIDENCE LOAD FAILED'; $('[data-context-note]').textContent=`Unable to load committed evidence: ${e.message}`; console.error(e); }
  }
  init();
})();