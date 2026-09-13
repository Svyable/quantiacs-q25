(() => {
  'use strict';

  const root = document.querySelector('[data-q25-terminal]');
  if (!root) return;

  const $ = (s, scope = root) => scope.querySelector(s);
  const $$ = (s, scope = root) => Array.from(scope.querySelectorAll(s));
  const num = (v) => v !== null && v !== '' && Number.isFinite(Number(v));
  const n = (v) => num(v) ? Number(v) : null;
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = (v, d = 3) => num(v) ? Number(v).toFixed(d) : '—';
  const pct = (v, d = 1) => num(v) ? `${(Number(v) * 100).toFixed(d)}%` : '—';
  const shortPct = (v) => num(v) ? `${(Number(v) * 100).toFixed(Math.abs(Number(v)) < .01 ? 2 : 1)}%` : '—';
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const statusUpper = (v) => String(v || '').toUpperCase();
  const metricPct = /(?:cagr|drawdown|turnover|hit_rate|return|volatility)/i;
  const metricFmt = (key, v) => metricPct.test(key) ? shortPct(v) : fmt(v, 3);
  const human = (s) => String(s || '').replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase());
  const svgEl = (name, attrs = {}) => {
    const el = document.createElementNS('http://www.w3.org/2000/svg', name);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    return el;
  };

  let packet = null;
  let rows = [];
  let decisions = [];
  let filtered = [];
  let selectedKey = null;
  let sortKey = 'dev_sharpe_12';
  let visibleRows = 35;

  function pathContext(path, row) {
    let campaign = row.campaign || row.campaign_id || row.experiment || '';
    let lane = row.lane || (path.length ? String(path[0]) : '');
    if (!campaign && path[0] === 'additional_campaigns' && path[1]) campaign = String(path[1]);
    if (!campaign) {
      const hit = path.find((p) => typeof p === 'string' && /^(?:frontier|ebenezar|campaign|topology|historical)/i.test(p));
      if (hit) campaign = String(hit);
    }
    return {campaign: campaign || lane || 'unscoped', lane: lane || 'unscoped'};
  }

  function looksLikeRow(obj) {
    if (!obj || Array.isArray(obj) || typeof obj !== 'object' || typeof obj.id !== 'string') return false;
    return Object.keys(obj).some((k) => /(sharpe|score|cagr|sortino|calmar|drawdown|turnover|hit_rate|return|volatility)/i.test(k) && (num(obj[k]) || obj[k] === null)) || typeof obj.status === 'string';
  }

  function extract(data) {
    const out = [], familyOut = [], seen = new Set(), seenFamilies = new Set();
    function walk(node, path = []) {
      if (Array.isArray(node)) { node.forEach((x, i) => walk(x, path.concat(i))); return; }
      if (!node || typeof node !== 'object') return;
      if (looksLikeRow(node)) {
        const ctx = pathContext(path, node);
        const row = {...node, __campaign: ctx.campaign, __lane: ctx.lane, __path: path.join('.')};
        row.__key = [row.__campaign, row.__lane, row.id, row.mode || '', row.__path].join('|');
        if (!seen.has(row.__key)) { seen.add(row.__key); out.push(row); }
      } else if (typeof node.family === 'string' && typeof node.decision === 'string' && ('best_score' in node || 'decision_code' in node)) {
        const ctx = pathContext(path, node);
        const key = [ctx.campaign, node.family, node.decision_code || node.decision].join('|');
        if (!seenFamilies.has(key)) {
          seenFamilies.add(key);
          familyOut.push({...node, __campaign: ctx.campaign, __lane: ctx.lane});
        }
      }
      Object.entries(node).forEach(([k, v]) => walk(v, path.concat(k)));
    }
    walk(data);
    return {rows: out, decisions: familyOut};
  }

  function decisionFor(row) {
    if (!row.family) return null;
    const exact = decisions.find((d) => d.__campaign === row.__campaign && d.family === row.family);
    if (exact) return exact;
    const matches = decisions.filter((d) => d.family === row.family);
    return matches.length === 1 ? matches[0] : null;
  }

  function enrich(row) {
    const d = decisionFor(row);
    const research = n(row.research_sharpe_12), dev = n(row.dev_sharpe_12), sr0 = n(row.dev_sharpe_0);
    return {
      ...row,
      __decision: d,
      __decisionCode: d ? (d.decision_code || d.decision) : '',
      __delta: research !== null && dev !== null ? dev - research : null,
      __stability: research !== null && dev !== null ? Math.abs(dev - research) : null,
      __costDrag: sr0 !== null && dev !== null ? sr0 - dev : null
    };
  }

  function fillSelect(sel, values) {
    const el = $(sel); if (!el) return;
    el.innerHTML = '<option value="">All</option>' + values.filter(Boolean).map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
  }

  function initFilters() {
    fillSelect('[data-filter="campaign"]', [...new Set(rows.map((r) => r.__campaign))].sort());
    fillSelect('[data-filter="family"]', [...new Set(rows.map((r) => r.family).filter(Boolean))].sort());
    fillSelect('[data-filter="mode"]', [...new Set(rows.map((r) => r.mode).filter(Boolean))].sort());
    fillSelect('[data-filter="status"]', [...new Set(rows.map((r) => r.status).filter(Boolean))].sort());
  }

  function currentFilters() {
    return {
      q: ($('[data-filter="search"]')?.value || '').trim().toLowerCase(),
      campaign: $('[data-filter="campaign"]')?.value || '',
      family: $('[data-filter="family"]')?.value || '',
      mode: $('[data-filter="mode"]')?.value || '',
      status: $('[data-filter="status"]')?.value || ''
    };
  }

  function applyFilters() {
    const f = currentFilters();
    filtered = rows.filter((r) => {
      if (f.campaign && r.__campaign !== f.campaign) return false;
      if (f.family && r.family !== f.family) return false;
      if (f.mode && r.mode !== f.mode) return false;
      if (f.status && r.status !== f.status) return false;
      if (f.q) {
        const hay = [r.id, r.family, r.mode, r.status, r.__campaign, r.__lane, r.__decisionCode].filter(Boolean).join(' ').toLowerCase();
        if (!hay.includes(f.q)) return false;
      }
      return true;
    });
    visibleRows = 35;
    renderAll();
  }

  function renderKpis() {
    const bases = rows.filter((r) => r.mode === 'base');
    const floor = bases.filter((r) => num(r.dev_sharpe_12) && Number(r.dev_sharpe_12) >= 1);
    const complete = rows.filter((r) => statusUpper(r.status) === 'COMPLETE');
    const survivors = decisions.filter((d) => /^CONTINUE\b/i.test(String(d.decision || '')) || /^CONTINUE\b/i.test(String(d.decision_code || '')));
    const campaigns = new Set(rows.map((r) => r.__campaign).filter(Boolean));
    const best = bases.filter((r) => num(r.dev_sharpe_12)).sort((a, b) => Number(b.dev_sharpe_12) - Number(a.dev_sharpe_12))[0];
    const set = (k, v) => $$(`[data-kpi="${k}"]`).forEach((el) => { el.textContent = v; });
    set('rows', rows.length.toLocaleString());
    set('bases', bases.length.toLocaleString());
    set('floor', floor.length.toLocaleString());
    set('survivors', new Set(survivors.map((d) => `${d.__campaign}|${d.family}`)).size.toLocaleString());
    set('complete', rows.length ? `${Math.round(complete.length / rows.length * 100)}%` : '—');
    set('campaigns', campaigns.size.toLocaleString());
    set('best', best ? fmt(best.dev_sharpe_12) : '—');
    const detail = $('[data-kpi-detail="best"]');
    if (detail) detail.textContent = best ? `${best.id} · ${best.__campaign}${best.__decisionCode ? ` · ${best.__decisionCode}` : ' · no family adjudication attached'}` : 'No measured base cell';
    const asof = $('[data-asof]');
    if (asof) asof.textContent = packet?.frontier_source?.git_commit ? `source ${String(packet.frontier_source.git_commit).slice(0,7)}` : `schema v${packet?.schema_version ?? '—'}`;
  }

  function niceTicks(min, max, count = 5) {
    if (!Number.isFinite(min) || !Number.isFinite(max)) return [];
    if (min === max) return [min];
    const raw = (max - min) / Math.max(1, count - 1);
    const p = Math.pow(10, Math.floor(Math.log10(Math.abs(raw) || 1)));
    const f = raw / p;
    const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p;
    const start = Math.ceil(min / step) * step;
    const out = [];
    for (let v = start; v <= max + step * .25; v += step) out.push(v);
    return out;
  }

  function chartFrame(svg, shell, points, xKey, yKey, opts = {}) {
    svg.replaceChildren();
    if (!points.length) return null;
    const width = Math.max(360, shell.clientWidth || 820), height = opts.height || 390;
    const m = {t: 18, r: 20, b: 45, l: 58}, pw = width - m.l - m.r, ph = height - m.t - m.b;
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    let xs = points.map((r) => Number(r[xKey])), ys = points.map((r) => Number(r[yKey]));
    let xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(...ys), ymax = Math.max(...ys);
    const xpad = Math.max((xmax - xmin) * .08, .0001), ypad = Math.max((ymax - ymin) * .08, .0001);
    xmin -= xpad; xmax += xpad; ymin -= ypad; ymax += ypad;
    if (opts.includeOne) { xmin = Math.min(xmin, 0, 1); xmax = Math.max(xmax, 1); ymin = Math.min(ymin, 0, 1); ymax = Math.max(ymax, 1); }
    if (opts.xZero) xmin = Math.min(0, xmin);
    const x = (v) => m.l + (Number(v) - xmin) / (xmax - xmin || 1) * pw;
    const y = (v) => m.t + (ymax - Number(v)) / (ymax - ymin || 1) * ph;
    niceTicks(xmin, xmax, 6).forEach((tick) => {
      const xx = x(tick); svg.append(svgEl('line', {x1:xx,y1:m.t,x2:xx,y2:height-m.b,class:'grid'}));
      const t = svgEl('text', {x:xx,y:height-18,'text-anchor':'middle'}); t.textContent = metricFmt(xKey, tick); svg.append(t);
    });
    niceTicks(ymin, ymax, 6).forEach((tick) => {
      const yy = y(tick); svg.append(svgEl('line', {x1:m.l,y1:yy,x2:width-m.r,y2:yy,class:'grid'}));
      const t = svgEl('text', {x:m.l-8,y:yy+3,'text-anchor':'end'}); t.textContent = metricFmt(yKey, tick); svg.append(t);
    });
    svg.append(svgEl('line', {x1:m.l,y1:height-m.b,x2:width-m.r,y2:height-m.b,class:'axis'}));
    svg.append(svgEl('line', {x1:m.l,y1:m.t,x2:m.l,y2:height-m.b,class:'axis'}));
    if (opts.includeOne && ymin <= 1 && ymax >= 1) svg.append(svgEl('line', {x1:m.l,y1:y(1),x2:width-m.r,y2:y(1),class:'floor'}));
    if (opts.includeOne && xmin <= 1 && xmax >= 1) svg.append(svgEl('line', {x1:x(1),y1:m.t,x2:x(1),y2:height-m.b,class:'floor'}));
    const xl = svgEl('text', {x:m.l+pw/2,y:height-3,'text-anchor':'middle'}); xl.textContent = opts.xLabel || human(xKey); svg.append(xl);
    const yl = svgEl('text', {x:12,y:m.t+ph/2,'text-anchor':'middle',transform:`rotate(-90 12 ${m.t+ph/2})`}); yl.textContent = opts.yLabel || human(yKey); svg.append(yl);
    return {x,y,m,pw,ph,width,height,xmin,xmax,ymin,ymax};
  }

  function pointClass(row) {
    const mode = String(row.mode || '').toLowerCase();
    return ['base','control','ablation','falsifier'].includes(mode) ? mode : 'other';
  }

  function attachTooltip(circle, row, shell, lines) {
    const tip = $('[data-tooltip]');
    circle.addEventListener('pointermove', (e) => {
      if (!tip) return;
      tip.innerHTML = `<strong>${esc(row.id)}</strong>` + lines.map(([k,v]) => `<span>${esc(k)}<b>${esc(v)}</b></span>`).join('') + `<span>campaign<b>${esc(row.__campaign)}</b></span>`;
      tip.hidden = false;
      const r = shell.getBoundingClientRect();
      tip.style.left = `${clamp(e.clientX-r.left+12, 6, r.width-300)}px`;
      tip.style.top = `${clamp(e.clientY-r.top-70, 6, r.height-130)}px`;
    });
    circle.addEventListener('pointerleave', () => { if (tip) tip.hidden = true; });
    circle.addEventListener('click', () => selectRow(row.__key));
  }

  function renderStability() {
    const svg = $('[data-chart="stability"]'), shell = svg?.parentElement;
    if (!svg || !shell) return;
    const points = filtered.filter((r) => num(r.research_sharpe_12) && num(r.dev_sharpe_12));
    const f = chartFrame(svg, shell, points, 'research_sharpe_12', 'dev_sharpe_12', {includeOne:true,xLabel:'Research SR @ 12%',yLabel:'Development SR @ 12%'});
    if (!f) return;
    const lo = Math.max(f.xmin, f.ymin), hi = Math.min(f.xmax, f.ymax);
    if (lo < hi) svg.append(svgEl('line', {x1:f.x(lo),y1:f.y(lo),x2:f.x(hi),y2:f.y(hi),class:'diag'}));
    points.forEach((row) => {
      const c = svgEl('circle', {cx:f.x(row.research_sharpe_12),cy:f.y(row.dev_sharpe_12),r:row.__key===selectedKey?6.5:4.7,class:`point ${pointClass(row)}${row.__key===selectedKey?' selected':''}`});
      attachTooltip(c,row,shell,[['research SR12',fmt(row.research_sharpe_12)],['dev SR12',fmt(row.dev_sharpe_12)],['Δ',fmt(row.__delta)]]);
      svg.append(c);
    });
  }

  function renderFunnel() {
    const host = $('[data-funnel]'), note = $('[data-funnel-note]'); if (!host) return;
    const bases = filtered.filter((r) => r.mode === 'base' && num(r.dev_sharpe_12));
    const floor = bases.filter((r) => Number(r.dev_sharpe_12) >= 1);
    const adjudicated = bases.filter((r) => r.__decision);
    const survivors = bases.filter((r) => r.__decision && (/^CONTINUE\b/i.test(String(r.__decision.decision || '')) || /^CONTINUE\b/i.test(String(r.__decision.decision_code || ''))));
    const stages = [
      ['Measured base cells', bases.length],
      ['Dev SR12 ≥ 1.0', floor.length],
      ['Family adjudication attached', adjudicated.length],
      ['Family decision survives', survivors.length]
    ];
    const max = Math.max(...stages.map(([,v]) => v),1);
    host.innerHTML = stages.map(([label,value]) => `<div class="qt-funnel-row"><div class="qt-funnel-label">${esc(label)}</div><div class="qt-funnel-track"><span style="width:${(value/max*100).toFixed(2)}%"></span></div><div class="qt-funnel-value">${value}</div></div>`).join('');
    if (note) note.textContent = survivors.length ? `${survivors.length} filtered base row(s) belong to families currently marked CONTINUE. This still does not assert forward validation or authenticated preclear.` : 'No filtered base row currently belongs to a family marked CONTINUE. A development Sharpe above 1.0 can still be dead because controls or later evidence invalidate the mechanism.';
  }

  function renderCostDrag() {
    const host = $('[data-chart="cost-drag"]'); if (!host) return;
    const vals = filtered.filter((r) => num(r.__costDrag)).sort((a,b) => Number(b.__costDrag) - Number(a.__costDrag)).slice(0,10);
    if (!vals.length) { host.innerHTML = '<div class="qt-warning">No rows in the current filter expose both dev_sharpe_0 and dev_sharpe_12.</div>'; return; }
    const max = Math.max(...vals.map((r) => Math.max(0, Number(r.__costDrag))), .001);
    host.innerHTML = vals.map((r) => `<div class="qt-bar-row" title="${esc(r.__campaign)}"><div class="qt-bar-label">${esc(r.id)}</div><div class="qt-bar-track"><span style="width:${(Math.max(0,Number(r.__costDrag))/max*100).toFixed(2)}%"></span></div><div class="qt-bar-value">${fmt(r.__costDrag)}</div></div>`).join('');
  }

  function paretoRows(points) {
    const sorted = [...points].sort((a,b) => Number(a.mean_turnover_12) - Number(b.mean_turnover_12) || Number(b.dev_sharpe_12) - Number(a.dev_sharpe_12));
    let best = -Infinity; const frontier = [];
    sorted.forEach((r) => { if (Number(r.dev_sharpe_12) > best) { frontier.push(r); best = Number(r.dev_sharpe_12); } });
    return frontier;
  }

  function renderPareto() {
    const svg = $('[data-chart="pareto"]'), shell = svg?.parentElement; if (!svg || !shell) return;
    const points = filtered.filter((r) => r.mode === 'base' && num(r.mean_turnover_12) && num(r.dev_sharpe_12));
    const f = chartFrame(svg, shell, points, 'mean_turnover_12', 'dev_sharpe_12', {height:320,includeOne:true,xZero:true,xLabel:'Mean turnover @ 12%',yLabel:'Development SR @ 12%'});
    if (!f) return;
    const frontier = paretoRows(points);
    if (frontier.length > 1) {
      const poly = svgEl('polyline', {class:'pareto-line',points:frontier.map((r) => `${f.x(r.mean_turnover_12)},${f.y(r.dev_sharpe_12)}`).join(' ')}); svg.append(poly);
    }
    const frontKeys = new Set(frontier.map((r) => r.__key));
    points.forEach((row) => {
      const c = svgEl('circle', {cx:f.x(row.mean_turnover_12),cy:f.y(row.dev_sharpe_12),r:frontKeys.has(row.__key)?6:4.5,class:`point base${row.__key===selectedKey?' selected':''}`,opacity:frontKeys.has(row.__key)?1:.65});
      attachTooltip(c,row,shell,[['turnover',shortPct(row.mean_turnover_12)],['dev SR12',fmt(row.dev_sharpe_12)],['Pareto',frontKeys.has(row.__key)?'yes':'no']]);
      svg.append(c);
    });
  }

  function sortedRows() {
    const list = [...filtered];
    const desc = (a,b,key) => (num(b[key])?Number(b[key]):-Infinity) - (num(a[key])?Number(a[key]):-Infinity);
    const asc = (a,b,key) => (num(a[key])?Number(a[key]):Infinity) - (num(b[key])?Number(b[key]):Infinity);
    list.sort((a,b) => {
      if (sortKey === 'stability') return asc(a,b,'__stability');
      if (sortKey === 'cost_drag') return asc(a,b,'__costDrag');
      if (sortKey === 'mean_turnover_12') return asc(a,b,'mean_turnover_12');
      if (sortKey === 'worst_drawdown_12') return desc(a,b,'worst_drawdown_12');
      return desc(a,b,sortKey);
    });
    return list;
  }

  function decisionClass(code) {
    if (/CONTINUE/i.test(code)) return 'continue';
    if (/FREEZE|FALSIFIED|KILL|FAIL/i.test(code)) return 'freeze';
    return '';
  }

  function renderLedger() {
    const body = $('[data-ledger-body]'), caption = $('[data-ledger-caption]'), more = $('[data-action="show-more"]'); if (!body) return;
    const ordered = sortedRows(), shown = ordered.slice(0, visibleRows);
    body.innerHTML = shown.length ? shown.map((r,i) => {
      const code = r.__decisionCode || '—';
      const evidence = num(r.evidence_completeness) ? pct(r.evidence_completeness,0) : (statusUpper(r.status)==='COMPLETE' ? 'COMPLETE' : (r.status || '—'));
      const srClass = num(r.dev_sharpe_12) ? (Number(r.dev_sharpe_12)>=1?'good':Number(r.dev_sharpe_12)<0?'bad':'') : '';
      const deltaClass = num(r.__delta) ? (Number(r.__delta) < -.5 ? 'bad' : Math.abs(Number(r.__delta)) < .15 ? 'good' : '') : '';
      return `<tr data-row-key="${esc(r.__key)}" class="${r.__key===selectedKey?'selected':''}"><td>${i+1}</td><td><strong>${esc(r.id)}</strong><br><span>${esc(r.family||'—')}</span></td><td>${esc(r.__campaign)}</td><td><span class="qt-mode ${esc(String(r.mode||'other').toLowerCase())}">${esc(r.mode||'—')}</span></td><td><span class="qt-decision ${decisionClass(code)}" title="${esc(code)}">${esc(code)}</span></td><td class="${srClass}">${fmt(r.dev_sharpe_12)}</td><td>${fmt(r.research_sharpe_12)}</td><td class="${deltaClass}">${fmt(r.__delta)}</td><td>${fmt(r.__costDrag)}</td><td>${shortPct(r.mean_turnover_12)}</td><td>${shortPct(r.worst_drawdown_12)}</td><td>${esc(evidence)}</td></tr>`;
    }).join('') : '<tr><td colspan="12">No rows match the current filters.</td></tr>';
    $$('[data-row-key]', body).forEach((tr) => tr.addEventListener('click', () => selectRow(tr.dataset.rowKey)));
    if (caption) caption.textContent = `Showing ${Math.min(visibleRows, ordered.length).toLocaleString()} of ${ordered.length.toLocaleString()} filtered rows`;
    if (more) more.hidden = visibleRows >= ordered.length;
  }

  function filteredDecisions() {
    const f = currentFilters();
    return decisions.filter((d) => (!f.campaign || d.__campaign === f.campaign) && (!f.family || d.family === f.family));
  }

  function renderFamilyBoard() {
    const host = $('[data-family-board]'), summary = $('[data-decision-summary]'); if (!host) return;
    const ds = filteredDecisions().sort((a,b) => (Number(b.best_score)||-Infinity)-(Number(a.best_score)||-Infinity));
    const freeze = ds.filter((d) => /FREEZE/i.test(String(d.decision))).length;
    const cont = ds.filter((d) => /CONTINUE/i.test(String(d.decision))).length;
    if (summary) summary.innerHTML = `<div><span>FAMILIES</span><strong>${ds.length}</strong></div><div><span>CONTINUE</span><strong>${cont}</strong></div><div><span>FREEZE</span><strong>${freeze}</strong></div>`;
    host.innerHTML = ds.length ? ds.map((d) => `<div class="qt-family-row ${/CONTINUE/i.test(String(d.decision))?'continue':''}"><strong>${esc(d.family)}</strong><span>${fmt(d.best_score)}</span><span>${esc(d.__campaign)}</span><em title="${esc(d.reason||'')}">${esc(d.decision_code||d.decision)}</em></div>`).join('') : '<div class="qt-warning">No family decision summaries match the current campaign/family filter.</div>';
  }

  function campaignDate(name) {
    const m = String(name).match(/(20\d{6})/); return m ? Number(m[1]) : 0;
  }

  function renderCampaignTape() {
    const host = $('[data-campaign-tape]'); if (!host) return;
    const map = new Map();
    filtered.filter((r) => r.mode === 'base' && num(r.dev_sharpe_12)).forEach((r) => {
      const prev = map.get(r.__campaign); if (!prev || Number(r.dev_sharpe_12) > Number(prev.dev_sharpe_12)) map.set(r.__campaign, r);
    });
    const arr = [...map.values()].sort((a,b) => campaignDate(b.__campaign)-campaignDate(a.__campaign) || a.__campaign.localeCompare(b.__campaign));
    if (!arr.length) { host.innerHTML = '<div class="qt-warning">No measured base cells match the current filters.</div>'; return; }
    const vals = arr.map((r) => Number(r.dev_sharpe_12)), min = Math.min(0,...vals), max = Math.max(1,...vals), span = max-min || 1;
    host.innerHTML = arr.map((r) => `<div class="qt-campaign-row"><div class="qt-campaign-name" title="${esc(r.id)}">${esc(r.__campaign)}</div><div class="qt-campaign-track"><span style="width:${((Number(r.dev_sharpe_12)-min)/span*100).toFixed(2)}%"></span><i title="SR 1.0 floor" style="left:${((1-min)/span*100).toFixed(2)}%"></i></div><div class="qt-campaign-value">${fmt(r.dev_sharpe_12)}</div></div>`).join('');
  }

  function selectRow(key) {
    selectedKey = key;
    renderLedger(); renderStability(); renderPareto(); renderInspector();
    const inspector = $('[data-inspector]'); if (inspector) inspector.scrollIntoView({behavior:'smooth',block:'nearest'});
  }

  function renderInspector() {
    const host = $('[data-inspector]'); if (!host) return;
    const r = rows.find((x) => x.__key === selectedKey);
    if (!r) return;
    const d = r.__decision;
    const metrics = [
      ['Dev SR12', r.dev_sharpe_12], ['Research SR12', r.research_sharpe_12], ['Dev SR0', r.dev_sharpe_0], ['Cost drag', r.__costDrag],
      ['Dev CAGR12', r.dev_cagr_12], ['Dev Sortino12', r.dev_sortino_12], ['Dev Calmar12', r.dev_calmar_12], ['Dev hit rate12', r.dev_hit_rate_12],
      ['Turnover12', r.mean_turnover_12], ['Worst DD12', r.worst_drawdown_12], ['Selection score', r.selection_score], ['Evidence completeness', r.evidence_completeness]
    ];
    host.innerHTML = `<div class="qt-inspector-grid"><div class="qt-inspector-title"><span class="qt-kicker">ROW INSPECTOR</span><h2>${esc(r.id)}</h2><p>${esc(r.__campaign)} · ${esc(r.family||'no family')} · ${esc(r.mode||'no mode')} · ${esc(r.status||'no status')}</p><div class="qt-inspector-meta"><span>lane: ${esc(r.__lane)}</span><span>rank: ${esc(r.rank ?? '—')}</span><span>rankable: ${esc(r.rankable ?? '—')}</span><span>path: ${esc(r.__path)}</span></div></div><div class="qt-metric-cards">${metrics.map(([label,v]) => `<div class="qt-metric-card"><span>${esc(label)}</span><strong>${/cagr|hit rate|turnover|drawdown|completeness/i.test(label)?shortPct(v):fmt(v)}</strong></div>`).join('')}</div>${d ? `<div class="qt-inspector-reason"><strong>${esc(d.decision_code||d.decision)}</strong> · ${esc(d.reason||'No reason recorded.')} ${Array.isArray(d.failed_controls)&&d.failed_controls.length?`Failed controls: ${esc(d.failed_controls.join(', '))}.`:''}</div>` : `<div class="qt-inspector-reason">No family adjudication object is attached to this row in the current matrix packet. That absence is left visible rather than inferred.</div>`}</div>`;
  }

  function exportCsv() {
    const ordered = sortedRows();
    const cols = ['id','campaign','lane','family','mode','status','family_decision','dev_sharpe_12','research_sharpe_12','dev_minus_research','dev_sharpe_0','cost_drag','dev_cagr_12','dev_sortino_12','dev_calmar_12','dev_hit_rate_12','mean_turnover_12','worst_drawdown_12','selection_score','evidence_completeness'];
    const quote = (v) => `"${String(v ?? '').replace(/"/g,'""')}"`;
    const lines = [cols.map(quote).join(',')].concat(ordered.map((r) => [r.id,r.__campaign,r.__lane,r.family,r.mode,r.status,r.__decisionCode,r.dev_sharpe_12,r.research_sharpe_12,r.__delta,r.dev_sharpe_0,r.__costDrag,r.dev_cagr_12,r.dev_sortino_12,r.dev_calmar_12,r.dev_hit_rate_12,r.mean_turnover_12,r.worst_drawdown_12,r.selection_score,r.evidence_completeness].map(quote).join(',')));
    const blob = new Blob([lines.join('\n')], {type:'text/csv;charset=utf-8'}), url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = 'q25-terminal-filtered.csv'; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 500);
  }

  function renderAll() {
    const count = $('[data-filter-count]'); if (count) count.textContent = `${filtered.length.toLocaleString()} / ${rows.length.toLocaleString()} rows`;
    renderStability(); renderFunnel(); renderCostDrag(); renderPareto(); renderLedger(); renderFamilyBoard(); renderCampaignTape();
  }

  function wire() {
    $$('[data-filter]').forEach((el) => el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', applyFilters));
    $('[data-action="reset"]')?.addEventListener('click', () => { $$('[data-filter]').forEach((el) => { el.value = ''; }); applyFilters(); });
    $('[data-sort-select]')?.addEventListener('change', (e) => { sortKey = e.target.value; renderLedger(); });
    $('[data-action="show-more"]')?.addEventListener('click', () => { visibleRows += 50; renderLedger(); });
    $('[data-action="export"]')?.addEventListener('click', exportCsv);
    window.addEventListener('resize', () => { renderStability(); renderPareto(); });
  }

  const source = root.dataset.matrixSource || 'data/strategy_matrix.json';
  fetch(source, {cache:'no-store'})
    .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then((data) => {
      packet = data;
      const extracted = extract(data);
      decisions = extracted.decisions;
      rows = extracted.rows.map(enrich);
      filtered = [...rows];
      initFilters(); wire(); renderKpis(); renderAll();
      const feed = $('.qt-feed'); if (feed) feed.classList.add('is-live');
      const state = $('[data-terminal-state]'); if (state) state.textContent = 'MATRIX ONLINE';
    })
    .catch((err) => {
      const state = $('[data-terminal-state]'); if (state) state.textContent = 'MATRIX ERROR';
      const body = $('[data-ledger-body]'); if (body) body.innerHTML = `<tr><td colspan="12">Matrix unavailable: ${esc(err.message)}</td></tr>`;
      console.error('Q25 terminal failed to load matrix', err);
    });
})();
