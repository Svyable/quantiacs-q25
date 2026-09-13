(() => {
  'use strict';

  const fmt = (v, d = 3) => Number.isFinite(Number(v)) ? Number(v).toFixed(d) : '—';
  const pct = (v, d = 1) => Number.isFinite(Number(v)) ? `${(Number(v) * 100).toFixed(d)}%` : '—';
  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const isNum = (v) => v !== null && v !== '' && Number.isFinite(Number(v));
  const human = (key) => String(key || '').replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase());
  const metricPct = /(?:cagr|drawdown|turnover|hit_rate|mean_return|volatility|return)/i;
  const formatMetric = (key, value) => metricPct.test(key) ? pct(value, Math.abs(Number(value)) < .01 ? 2 : 1) : fmt(value, 3);
  const modeClass = (mode) => ['base','control','ablation','falsifier'].includes(String(mode || '').toLowerCase()) ? String(mode).toLowerCase() : 'other';
  const svgEl = (name, attrs = {}) => { const el = document.createElementNS('http://www.w3.org/2000/svg', name); Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k, v)); return el; };

  function pathContext(path, row) {
    let campaign = row.campaign || row.campaign_id || row.experiment || '';
    let lane = row.lane || '';
    if (!lane && path.length) lane = String(path[0]);
    if (!campaign && path[0] === 'additional_campaigns' && path[1]) campaign = String(path[1]);
    if (!campaign) {
      const hit = path.find((p) => typeof p === 'string' && /^(?:frontier|ebenezar|campaign|topology|historical)/i.test(p));
      if (hit) campaign = String(hit);
    }
    return {campaign: campaign || lane || 'unscoped', lane: lane || 'unscoped'};
  }

  function looksLikeResult(obj) {
    if (!obj || Array.isArray(obj) || typeof obj !== 'object' || typeof obj.id !== 'string') return false;
    const keys = Object.keys(obj);
    const hasMetric = keys.some((k) => /(sharpe|score|cagr|sortino|calmar|drawdown|turnover|hit_rate|volatility|return)/i.test(k) && (isNum(obj[k]) || obj[k] === null));
    return hasMetric || typeof obj.status === 'string' || typeof obj.failure_type === 'string';
  }

  function extractMatrix(data) {
    const rows = [];
    const familyDecisions = [];
    const seenRows = new Set();
    const seenFamilies = new Set();
    function walk(node, path = []) {
      if (Array.isArray(node)) { node.forEach((item, i) => walk(item, path.concat(i))); return; }
      if (!node || typeof node !== 'object') return;
      if (looksLikeResult(node)) {
        const ctx = pathContext(path, node);
        const row = {...node, __campaign: ctx.campaign, __lane: ctx.lane, __path: path.join('.')};
        row.__key = [ctx.campaign, ctx.lane, row.id, row.mode || '', row.__path].join('|');
        if (!seenRows.has(row.__key)) { seenRows.add(row.__key); rows.push(row); }
      } else if (typeof node.family === 'string' && typeof node.decision === 'string' && ('best_score' in node || 'decision_code' in node)) {
        const ctx = pathContext(path, node);
        const key = [ctx.campaign, node.family, node.decision_code || node.decision].join('|');
        if (!seenFamilies.has(key)) {
          seenFamilies.add(key);
          familyDecisions.push({...node, __campaign: ctx.campaign, __lane: ctx.lane});
        }
      }
      Object.entries(node).forEach(([key, value]) => walk(value, path.concat(key)));
    }
    walk(data, []);
    return {rows, familyDecisions};
  }

  function numericKeys(rows) {
    const counts = new Map();
    rows.forEach((row) => Object.entries(row).forEach(([k,v]) => {
      if (!k.startsWith('__') && isNum(v)) counts.set(k, (counts.get(k) || 0) + 1);
    }));
    const preferred = ['dev_sharpe_12','research_sharpe_12','selection_score','dev_sharpe_0','research_sharpe_0','dev_cagr_12','research_cagr_12','dev_sortino_12','research_sortino_12','dev_calmar_12','research_calmar_12','worst_drawdown_12','mean_turnover_12','dev_hit_rate_12','research_hit_rate_12'];
    return [...counts.keys()].sort((a,b) => {
      const ia = preferred.indexOf(a), ib = preferred.indexOf(b);
      if (ia >= 0 || ib >= 0) return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib);
      return (counts.get(b) - counts.get(a)) || a.localeCompare(b);
    });
  }

  function setHomeOverview(packet, root) {
    const {rows} = extractMatrix(packet);
    const complete = rows.filter((r) => String(r.status).toUpperCase() === 'COMPLETE');
    const best = rows.filter((r) => isNum(r.dev_sharpe_12)).sort((a,b) => Number(b.dev_sharpe_12) - Number(a.dev_sharpe_12))[0];
    const families = new Set(rows.map((r) => r.family).filter(Boolean));
    const campaigns = new Set(rows.map((r) => r.__campaign).filter(Boolean));
    const above = rows.filter((r) => isNum(r.dev_sharpe_12) && Number(r.dev_sharpe_12) >= 1).length;
    const bind = (name, value) => root.querySelectorAll(`[data-home-kpi="${name}"]`).forEach((el) => { el.textContent = value; });
    bind('rows', rows.length.toLocaleString());
    bind('families', families.size.toLocaleString());
    bind('campaigns', campaigns.size.toLocaleString());
    bind('complete', rows.length ? `${Math.round(complete.length / rows.length * 100)}%` : '—');
    bind('best', best ? fmt(best.dev_sharpe_12, 3) : '—');
    bind('above', above.toLocaleString());
    const top = root.querySelector('[data-home-top]');
    if (top) {
      const leaders = rows.filter((r) => r.mode === 'base' && isNum(r.dev_sharpe_12)).sort((a,b) => Number(b.dev_sharpe_12) - Number(a.dev_sharpe_12)).slice(0,3);
      top.innerHTML = leaders.length ? leaders.map((r, i) => `<div><b>${i+1}. ${esc(r.id)}</b><span>${esc(r.__campaign)} · dev SR12 ${fmt(r.dev_sharpe_12,3)}</span></div>`).join('') : 'No base-strategy development rows found.';
    }
  }

  const homeRoot = document.querySelector('[data-strategy-overview]');
  if (homeRoot) {
    const src = homeRoot.dataset.source || 'data/strategy_matrix.json';
    fetch(src, {cache:'no-store'}).then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }).then((data) => setHomeOverview(data, homeRoot)).catch((err) => {
      const top = homeRoot.querySelector('[data-home-top]'); if (top) top.textContent = `Matrix unavailable: ${err.message}`;
    });
  }

  const root = document.querySelector('[data-matrix-explorer]');
  if (!root) return;
  const $ = (sel, scope = root) => scope.querySelector(sel);
  const $$ = (sel, scope = root) => Array.from(scope.querySelectorAll(sel));
  let allRows = [], filteredRows = [], familyDecisions = [], metrics = [];
  let xMetric = 'mean_turnover_12', yMetric = 'dev_sharpe_12', selectedKey = null;
  let sortKey = 'dev_sharpe_12', sortDir = -1, page = 1;
  const pageSize = 75;

  function fillSelect(select, values, allLabel = 'All') {
    if (!select) return;
    const current = select.value;
    select.innerHTML = `<option value="">${esc(allLabel)}</option>` + values.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
    if (values.includes(current)) select.value = current;
  }

  function initControls() {
    fillSelect($('[data-filter="campaign"]'), [...new Set(allRows.map((r) => r.__campaign).filter(Boolean))].sort());
    fillSelect($('[data-filter="family"]'), [...new Set(allRows.map((r) => r.family).filter(Boolean))].sort());
    fillSelect($('[data-filter="mode"]'), [...new Set(allRows.map((r) => r.mode).filter(Boolean))].sort());
    fillSelect($('[data-filter="status"]'), [...new Set(allRows.map((r) => r.status).filter(Boolean))].sort());
    fillSelect($('[data-filter="lane"]'), [...new Set(allRows.map((r) => r.__lane).filter(Boolean))].sort());
    metrics = numericKeys(allRows);
    const x = $('[data-axis="x"]'), y = $('[data-axis="y"]');
    [x,y].forEach((select) => { select.innerHTML = metrics.map((m) => `<option value="${esc(m)}">${esc(human(m))}</option>`).join(''); });
    if (!metrics.includes(xMetric)) xMetric = metrics.find((m) => /turnover/i.test(m)) || metrics[0];
    if (!metrics.includes(yMetric)) yMetric = metrics.find((m) => /dev_sharpe_12/i.test(m)) || metrics.find((m) => /sharpe/i.test(m)) || metrics[1] || metrics[0];
    if (x) x.value = xMetric; if (y) y.value = yMetric;
  }

  function filters() {
    return {
      search: ($('[data-filter="search"]')?.value || '').trim().toLowerCase(),
      campaign: $('[data-filter="campaign"]')?.value || '',
      family: $('[data-filter="family"]')?.value || '',
      mode: $('[data-filter="mode"]')?.value || '',
      status: $('[data-filter="status"]')?.value || '',
      lane: $('[data-filter="lane"]')?.value || '',
      baseOnly: Boolean($('[data-filter="base-only"]')?.checked)
    };
  }

  function applyFilters() {
    const f = filters();
    filteredRows = allRows.filter((r) => {
      if (f.campaign && r.__campaign !== f.campaign) return false;
      if (f.family && r.family !== f.family) return false;
      if (f.mode && r.mode !== f.mode) return false;
      if (f.status && r.status !== f.status) return false;
      if (f.lane && r.__lane !== f.lane) return false;
      if (f.baseOnly && r.mode !== 'base') return false;
      if (f.search) {
        const hay = [r.id,r.family,r.mode,r.status,r.__campaign,r.__lane,r.decision,r.decision_code].filter(Boolean).join(' ').toLowerCase();
        if (!hay.includes(f.search)) return false;
      }
      return true;
    });
    page = 1;
    renderAll();
  }

  function renderKpis() {
    const set = (name, value, detail) => {
      const el = $(`[data-kpi="${name}"]`), d = $(`[data-kpi-detail="${name}"]`);
      if (el) el.textContent = value; if (d && detail) d.textContent = detail;
    };
    const complete = filteredRows.filter((r) => String(r.status).toUpperCase() === 'COMPLETE').length;
    const vals = filteredRows.filter((r) => isNum(r.dev_sharpe_12)).map((r) => Number(r.dev_sharpe_12));
    const above = vals.filter((v) => v >= 1).length;
    set('rows', filteredRows.length.toLocaleString(), `${allRows.length.toLocaleString()} total extracted rows`);
    set('families', new Set(filteredRows.map((r) => r.family).filter(Boolean)).size.toLocaleString(), 'unique family labels in current view');
    set('complete', filteredRows.length ? `${Math.round(complete / filteredRows.length * 100)}%` : '—', `${complete.toLocaleString()} COMPLETE rows`);
    set('best-dev', vals.length ? fmt(Math.max(...vals),3) : '—', `${vals.length.toLocaleString()} rows expose dev_sharpe_12`);
    set('above-floor', above.toLocaleString(), `${vals.length ? Math.round(above/vals.length*100) : 0}% of rows with dev_sharpe_12`);
    set('campaigns', new Set(filteredRows.map((r) => r.__campaign).filter(Boolean)).size.toLocaleString(), 'distinct campaign/context labels');
    const count = $('[data-filter-count]'); if (count) count.textContent = `${filteredRows.length.toLocaleString()} / ${allRows.length.toLocaleString()} rows`;
  }

  function niceTicks(min,max,count=5) {
    if (!Number.isFinite(min) || !Number.isFinite(max)) return [];
    if (min === max) return [min];
    const raw = (max-min)/Math.max(1,count-1), pow = Math.pow(10, Math.floor(Math.log10(Math.abs(raw) || 1))), frac = raw/pow;
    const nice = (frac <= 1 ? 1 : frac <= 2 ? 2 : frac <= 5 ? 5 : 10) * pow;
    const start = Math.ceil(min/nice)*nice, out=[]; for (let v=start; v<=max+nice*.25; v+=nice) out.push(v); return out;
  }

  function renderScatter() {
    const svg = $('[data-chart="scatter"]'), shell = svg?.parentElement, empty = $('[data-chart-empty]');
    if (!svg || !shell) return;
    const points = filteredRows.filter((r) => isNum(r[xMetric]) && isNum(r[yMetric]));
    svg.replaceChildren();
    if (empty) empty.hidden = points.length > 0;
    if (!points.length) return;
    const width = Math.max(360, shell.clientWidth || 900), height = 430, m = {t:22,r:24,b:54,l:70}, pw=width-m.l-m.r, ph=height-m.t-m.b;
    svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
    const xs=points.map((r)=>Number(r[xMetric])), ys=points.map((r)=>Number(r[yMetric]));
    let xmin=Math.min(...xs), xmax=Math.max(...xs), ymin=Math.min(...ys), ymax=Math.max(...ys);
    const xpad=Math.max((xmax-xmin)*.08,Math.abs(xmax||1)*.015,.0001), ypad=Math.max((ymax-ymin)*.08,Math.abs(ymax||1)*.015,.0001);
    xmin-=xpad;xmax+=xpad;ymin-=ypad;ymax+=ypad;
    if (/sharpe/i.test(yMetric)) { ymin=Math.min(ymin,0); ymax=Math.max(ymax,1); }
    const x=(v)=>m.l+(Number(v)-xmin)/(xmax-xmin||1)*pw, y=(v)=>m.t+(ymax-Number(v))/(ymax-ymin||1)*ph;
    niceTicks(xmin,xmax,6).forEach((tick)=>{const xx=x(tick);svg.append(svgEl('line',{x1:xx,y1:m.t,x2:xx,y2:height-m.b,class:'grid'}));const t=svgEl('text',{x:xx,y:height-27,'text-anchor':'middle'});t.textContent=formatMetric(xMetric,tick);svg.append(t);});
    niceTicks(ymin,ymax,6).forEach((tick)=>{const yy=y(tick);svg.append(svgEl('line',{x1:m.l,y1:yy,x2:width-m.r,y2:yy,class:'grid'}));const t=svgEl('text',{x:m.l-10,y:yy+3,'text-anchor':'end'});t.textContent=formatMetric(yMetric,tick);svg.append(t);});
    svg.append(svgEl('line',{x1:m.l,y1:height-m.b,x2:width-m.r,y2:height-m.b,class:'axis'}));
    svg.append(svgEl('line',{x1:m.l,y1:m.t,x2:m.l,y2:height-m.b,class:'axis'}));
    if (/sharpe/i.test(yMetric) && ymin <= 1 && ymax >= 1) svg.append(svgEl('line',{x1:m.l,y1:y(1),x2:width-m.r,y2:y(1),class:'floor'}));
    const xl=svgEl('text',{x:m.l+pw/2,y:height-6,'text-anchor':'middle'});xl.textContent=human(xMetric);svg.append(xl);
    const yl=svgEl('text',{x:15,y:m.t+ph/2,'text-anchor':'middle',transform:`rotate(-90 15 ${m.t+ph/2})`});yl.textContent=human(yMetric);svg.append(yl);
    const tip=$('[data-tooltip]');
    points.forEach((row) => {
      const circle=svgEl('circle',{cx:x(row[xMetric]),cy:y(row[yMetric]),r:row.__key===selectedKey?6.5:5,class:`point ${modeClass(row.mode)}${row.__key===selectedKey?' is-selected':''}`,'data-key':row.__key});
      circle.addEventListener('pointermove',(e)=>{if(!tip)return;tip.innerHTML=`<strong>${esc(row.id)}</strong><span>${esc(human(xMetric))}<b>${esc(formatMetric(xMetric,row[xMetric]))}</b></span><span>${esc(human(yMetric))}<b>${esc(formatMetric(yMetric,row[yMetric]))}</b></span><span>context<b>${esc(row.__campaign)}</b></span><span>mode<b>${esc(row.mode||'—')}</b></span>`;tip.hidden=false;const sr=shell.getBoundingClientRect();tip.style.left=`${clamp(e.clientX-sr.left+12,8,sr.width-275)}px`;tip.style.top=`${clamp(e.clientY-sr.top-85,8,sr.height-135)}px`;});
      circle.addEventListener('pointerleave',()=>{if(tip)tip.hidden=true;});
      circle.addEventListener('click',()=>selectRow(row.__key));
      svg.append(circle);
    });
  }

  function renderCampaignBars() {
    const host=$('[data-chart="campaign-bars"]'); if(!host)return;
    const metric = filteredRows.some((r)=>isNum(r.dev_sharpe_12)) ? 'dev_sharpe_12' : yMetric;
    const label=$('[data-campaign-metric-label]'); if(label)label.textContent=metric;
    const groups=new Map();
    filteredRows.forEach((r)=>{if(!isNum(r[metric]))return;const k=r.__campaign||r.__lane||'unscoped';const v=Number(r[metric]);const prev=groups.get(k);if(!prev||v>prev.value)groups.set(k,{value:v,row:r});});
    const arr=[...groups.entries()].sort((a,b)=>b[1].value-a[1].value).slice(0,14);
    if(!arr.length){host.innerHTML='<div class="qx-subtle">No campaign rollup is available for the current metric/filter.</div>';return;}
    const min=Math.min(0,...arr.map(([,v])=>v.value)),max=Math.max(...arr.map(([,v])=>v.value),1e-9),span=max-min||1;
    host.innerHTML=`<div class="qx-bar-note">Best ${esc(metric)} per current campaign/context filter. Bars are descriptive, not promotion scores.</div>`+arr.map(([name,item])=>{const width=Math.max(1,(item.value-min)/span*100);return `<div class="qx-bar-row" title="${esc(item.row.id)}"><div class="qx-bar-label">${esc(name)}</div><div class="qx-bar-track"><span style="width:${width.toFixed(2)}%"></span></div><div class="qx-bar-value">${esc(formatMetric(metric,item.value))}</div></div>`;}).join('');
  }

  function renderFamilyBoard() {
    const host=$('[data-family-board]'); if(!host)return;
    const activeCampaigns=new Set(filteredRows.map((r)=>r.__campaign));
    let rows=familyDecisions.filter((d)=>!activeCampaigns.size||activeCampaigns.has(d.__campaign));
    if(!rows.length) rows=familyDecisions;
    rows=rows.sort((a,b)=>(Number(b.best_score)||-Infinity)-(Number(a.best_score)||-Infinity)).slice(0,16);
    if(!rows.length){host.innerHTML='<div class="qx-subtle">Family-decision summaries are not present in this matrix packet.</div>';return;}
    host.innerHTML=rows.map((d)=>`<div class="qx-family-row" data-decision="${esc(d.decision_code||d.decision)}"><strong title="${esc(d.__campaign)}">${esc(d.family)}</strong><span>${isNum(d.best_score)?fmt(d.best_score,3):'—'}</span><em>${esc(d.decision_code||d.decision)}</em></div>`).join('');
  }

  function comparable(a,b,key) {
    const av=a[key],bv=b[key],an=isNum(av),bn=isNum(bv); if(an&&bn)return(Number(av)-Number(bv))*sortDir; if(an)return-1;if(bn)return 1;return String(av??'').localeCompare(String(bv??''))*sortDir;
  }

  function sortedRows() { return [...filteredRows].sort((a,b)=>comparable(a,b,sortKey)); }
  function tableValue(row,key) {
    if(key==='campaign')return row.__campaign||'—';
    if(key==='id'||key==='family'||key==='mode'||key==='status')return row[key]||'—';
    return isNum(row[key])?formatMetric(key,row[key]):'—';
  }

  function renderTable() {
    const body=$('[data-table-body]'); if(!body)return;
    const rows=sortedRows(), pages=Math.max(1,Math.ceil(rows.length/pageSize)); page=clamp(page,1,pages);
    const slice=rows.slice((page-1)*pageSize,page*pageSize);
    const cols=['id','campaign','family','mode','status','dev_sharpe_12','research_sharpe_12','dev_cagr_12','dev_sortino_12','worst_drawdown_12','mean_turnover_12','selection_score'];
    body.innerHTML=slice.length?slice.map((r)=>`<tr data-row-key="${esc(r.__key)}" class="${r.__key===selectedKey?'is-selected':''}">${cols.map((c)=>{const num=!['id','campaign','family','mode','status'].includes(c);const st=c==='status'?(String(r.status).toUpperCase()==='COMPLETE'?'status-good':(r.status?'status-bad':'')):'';return `<td class="${num?'num ':''}${st}">${esc(tableValue(r,c))}</td>`;}).join('')}</tr>`).join(''):`<tr><td colspan="12">No rows match the current filters.</td></tr>`;
    $$('[data-row-key]',body).forEach((tr)=>tr.addEventListener('click',()=>selectRow(tr.dataset.rowKey)));
    const summary=$('[data-table-summary]');if(summary)summary.textContent=`${rows.length.toLocaleString()} rows · sorted by ${sortKey} ${sortDir<0?'descending':'ascending'}`;
    const label=$('[data-page-label]');if(label)label.textContent=`Page ${page} / ${pages}`;
    const prev=$('[data-page="prev"]'),next=$('[data-page="next"]');if(prev)prev.disabled=page<=1;if(next)next.disabled=page>=pages;
  }

  function renderInspector(row) {
    const id=$('[data-inspect="id"]'),meta=$('[data-inspect="meta"]'),grid=$('[data-inspect="metrics"]'),extra=$('[data-inspect="extra"]');
    if(!row){if(id)id.textContent='Click a point or row';if(meta)meta.textContent='The inspector preserves the row’s exact evidence lane and metric names.';if(grid)grid.innerHTML='';if(extra)extra.innerHTML='';return;}
    if(id)id.textContent=row.id;
    if(meta)meta.innerHTML=`<b>${esc(row.family||'unclassified')}</b> · ${esc(row.mode||'mode —')} · ${esc(row.status||'status —')}<br>${esc(row.__campaign)} · lane ${esc(row.__lane)}`;
    const nums=Object.keys(row).filter((k)=>!k.startsWith('__')&&isNum(row[k]));
    const preferred=metrics.filter((m)=>nums.includes(m));
    const ordered=[...preferred,...nums.filter((k)=>!preferred.includes(k)).sort()];
    if(grid)grid.innerHTML=ordered.map((k)=>`<div><span>${esc(human(k))}</span><strong>${esc(formatMetric(k,row[k]))}</strong></div>`).join('')||'<div><span>Metrics</span><strong>none</strong></div>';
    const textFields=Object.entries(row).filter(([k,v])=>!k.startsWith('__')&&typeof v==='string'&&!['id','family','mode','status'].includes(k));
    if(extra)extra.innerHTML=`<div><b>Evidence path</b><br><code>${esc(row.__path)}</code></div>`+(textFields.length?`<div style="margin-top:.55rem">${textFields.map(([k,v])=>`<b>${esc(human(k))}</b>: ${esc(v)}`).join('<br>')}</div>`:'');
  }

  function selectRow(key) {
    selectedKey=key; const row=allRows.find((r)=>r.__key===key); renderInspector(row); renderScatter(); renderTable();
  }

  function exportCsv() {
    if(!filteredRows.length)return;
    const base=['id','__campaign','__lane','family','mode','status'];
    const keys=[...base,...new Set(filteredRows.flatMap((r)=>Object.keys(r).filter((k)=>!k.startsWith('__'))))].filter((v,i,a)=>a.indexOf(v)===i);
    const cell=(v)=>{if(v===null||v===undefined)return'';const s=typeof v==='object'?JSON.stringify(v):String(v);return/[",\n]/.test(s)?`"${s.replace(/"/g,'""')}"`:s;};
    const csv=[keys.join(','),...filteredRows.map((r)=>keys.map((k)=>cell(k==='__campaign'?r.__campaign:k==='__lane'?r.__lane:r[k])).join(','))].join('\n');
    const blob=new Blob([csv],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='q25-filtered-strategy-matrix.csv';document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url);
  }

  function renderAll() { renderKpis(); renderScatter(); renderCampaignBars(); renderFamilyBoard(); renderTable(); }

  $$('[data-filter]').forEach((el)=>el.addEventListener(el.tagName==='INPUT'?'input':'change',applyFilters));
  $('[data-reset]')?.addEventListener('click',()=>{ $$('[data-filter]').forEach((el)=>{ if(el.type==='checkbox')el.checked=false;else el.value=''; }); applyFilters(); });
  $('[data-export]')?.addEventListener('click',exportCsv);
  $('[data-axis="x"]')?.addEventListener('change',(e)=>{xMetric=e.target.value;renderScatter();});
  $('[data-axis="y"]')?.addEventListener('change',(e)=>{yMetric=e.target.value;renderScatter();renderCampaignBars();});
  $$('[data-sort]').forEach((th)=>th.addEventListener('click',()=>{const key=th.dataset.sort;if(sortKey===key)sortDir*=-1;else{sortKey=key;sortDir=['id','campaign','family','mode','status'].includes(key)?1:-1;}page=1;renderTable();}));
  $('[data-page="prev"]')?.addEventListener('click',()=>{page--;renderTable();});
  $('[data-page="next"]')?.addEventListener('click',()=>{page++;renderTable();});
  let resizeTimer; window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(renderScatter,120);});

  const source=root.dataset.source||'data/strategy_matrix.json';
  fetch(source,{cache:'no-store'}).then((r)=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();}).then((packet)=>{
    const extracted=extractMatrix(packet);allRows=extracted.rows;familyDecisions=extracted.familyDecisions;filteredRows=[...allRows];
    initControls();renderAll();if(filteredRows.length){const first=filteredRows.find((r)=>r.mode==='base'&&isNum(r.dev_sharpe_12))||filteredRows[0];selectRow(first.__key);}
  }).catch((err)=>{
    const body=$('[data-table-body]');if(body)body.innerHTML=`<tr><td colspan="12">Could not load strategy matrix: ${esc(err.message)}</td></tr>`;
    const count=$('[data-filter-count]');if(count)count.textContent='matrix unavailable';
  });
})();
