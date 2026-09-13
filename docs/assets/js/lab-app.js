(() => {
  'use strict';
  const L = window.Q25Lab;
  if (!L?.root) return;
  const { $, $$ } = L;

  const fillSelect = (selector, values, allLabel = 'All') => {
    const el = $(selector);
    if (!el) return;
    const current = el.value;
    el.innerHTML = `<option value="">${L.esc(allLabel)}</option>` + values.filter(Boolean).map((v) => `<option value="${L.esc(v)}">${L.esc(v)}</option>`).join('');
    if (values.includes(current)) el.value = current;
  };

  const numericKeys = () => {
    const counts = new Map();
    L.rows.forEach((row) => Object.entries(row).forEach(([key, value]) => {
      if (L.isNum(value) && (!key.startsWith('__') || ['__causalMargin','__devDecay','__costDrag'].includes(key))) counts.set(key, (counts.get(key) || 0) + 1);
    }));
    const preferred = ['__causalMargin','dev_sharpe_12','research_sharpe_12','__devDecay','__costDrag','selection_score','dev_sharpe_0','dev_cagr_12','dev_sortino_12','dev_calmar_12','mean_turnover_12','worst_drawdown_12','dev_hit_rate_12','research_cagr_12','research_sortino_12'];
    return [...counts.keys()].sort((a, b) => {
      const ia = preferred.indexOf(a), ib = preferred.indexOf(b);
      if (ia >= 0 || ib >= 0) return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib);
      return (counts.get(b) - counts.get(a)) || a.localeCompare(b);
    });
  };

  const initControls = () => {
    fillSelect('[data-filter="campaign"]', [...new Set(L.rows.map((row) => row.__campaign))].sort());
    fillSelect('[data-filter="family"]', [...new Set(L.rows.map((row) => row.family).filter(Boolean))].sort());
    fillSelect('[data-filter="mode"]', [...new Set(L.rows.map((row) => row.mode).filter(Boolean))].sort());
    fillSelect('[data-filter="status"]', [...new Set(L.rows.map((row) => row.status).filter(Boolean))].sort());
    const metrics = numericKeys();
    const options = metrics.map((m) => `<option value="${L.esc(m)}">${L.esc(L.human(m))}</option>`).join('');
    const x = $('[data-axis="x"]'), y = $('[data-axis="y"]'), stability = $('[data-stability-metric]');
    if (x) { x.innerHTML = options; if (!metrics.includes(L.xMetric)) L.xMetric = metrics[0]; x.value = L.xMetric; }
    if (y) { y.innerHTML = options; if (!metrics.includes(L.yMetric)) L.yMetric = metrics.find((m) => m === 'dev_sharpe_12') || metrics[0]; y.value = L.yMetric; }
    const stableMetrics = metrics.filter((m) => !m.startsWith('__') && !/rank|schema/i.test(m));
    if (stability) {
      stability.innerHTML = stableMetrics.map((m) => `<option value="${L.esc(m)}">${L.esc(L.human(m))}</option>`).join('');
      if (!stableMetrics.includes(L.stabilityMetric)) L.stabilityMetric = stableMetrics[0];
      stability.value = L.stabilityMetric;
    }
  };

  const filterState = () => ({
    q: ($('[data-filter="search"]')?.value || '').trim().toLowerCase(),
    campaign: $('[data-filter="campaign"]')?.value || '',
    family: $('[data-filter="family"]')?.value || '',
    mode: $('[data-filter="mode"]')?.value || '',
    status: $('[data-filter="status"]')?.value || '',
    baseOnly: Boolean($('[data-filter="base-only"]')?.checked),
    matchedOnly: Boolean($('[data-filter="matched-only"]')?.checked)
  });

  L.applyFilters = () => {
    const f = filterState();
    L.filtered = L.rows.filter((row) => {
      if (f.campaign && row.__campaign !== f.campaign) return false;
      if (f.family && row.family !== f.family) return false;
      if (f.mode && row.mode !== f.mode) return false;
      if (f.status && row.status !== f.status) return false;
      if (f.baseOnly && row.mode !== 'base') return false;
      if (f.matchedOnly && !row.__matchedControl) return false;
      if (f.q) {
        const haystack = [row.id,row.family,row.mode,row.status,row.__campaign,row.__lane,row.__decisionCode].filter(Boolean).join(' ').toLowerCase();
        if (!haystack.includes(f.q)) return false;
      }
      return true;
    });
    L.visibleRows = 40;
    L.renderAll();
  };

  L.renderAll = () => {
    L.renderKpis(); L.renderCausal(); L.renderTriage(); L.renderStability();
    L.renderScatter(); L.renderLedger(); L.renderInspector();
  };

  const wire = () => {
    $$('[data-filter]').forEach((el) => el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', L.applyFilters));
    $('[data-action="reset"]')?.addEventListener('click', () => { $$('[data-filter]').forEach((el) => { if (el.type === 'checkbox') el.checked = false; else el.value = ''; }); L.applyFilters(); });
    $('[data-action="export"]')?.addEventListener('click', L.exportCsv);
    $('[data-action="show-more"]')?.addEventListener('click', () => { L.visibleRows += 60; L.renderLedger(); });
    $('[data-sort-select]')?.addEventListener('change', (e) => { L.sortKey = e.target.value; L.renderLedger(); });
    $('[data-stability-metric]')?.addEventListener('change', (e) => { L.stabilityMetric = e.target.value; L.renderStability(); });
    $('[data-axis="x"]')?.addEventListener('change', (e) => { L.xMetric = e.target.value; L.renderScatter(); });
    $('[data-axis="y"]')?.addEventListener('change', (e) => { L.yMetric = e.target.value; L.renderScatter(); });
    window.addEventListener('resize', () => L.renderScatter());
  };

  const source = L.root.dataset.source || 'data/strategy_matrix.json';
  fetch(source, { cache:'no-store' })
    .then((response) => { if (!response.ok) throw new Error(`HTTP ${response.status}`); return response.json(); })
    .then((data) => {
      L.packet = data;
      const extracted = L.extract(data);
      L.rows = extracted.rows; L.decisions = extracted.decisions; L.enrichAll(); L.filtered = [...L.rows];
      initControls(); wire(); L.renderAll();
      $('.qt-feed')?.classList.add('is-live');
      const state = $('[data-lab-state]'); if (state) state.textContent = 'MATRIX ONLINE';
    })
    .catch((err) => {
      const state = $('[data-lab-state]'); if (state) state.textContent = 'MATRIX ERROR';
      const body = $('[data-ledger-body]'); if (body) body.innerHTML = `<tr><td colspan="13">Matrix unavailable: ${L.esc(err.message)}</td></tr>`;
      console.error('Q25 causal lab failed', err);
    });
})();
