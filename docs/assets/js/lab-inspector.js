(() => {
  'use strict';
  const L = window.Q25Lab;
  if (!L?.root) return;
  const { $ } = L;

  L.selectRow = (key) => {
    L.selectedKey = key;
    L.renderScatter();
    L.renderLedger();
    L.renderInspector();
  };

  L.renderInspector = () => {
    const title = $('[data-inspect="title"]');
    const body = $('[data-inspect="body"]');
    const row = L.rows.find((item) => item.__key === L.selectedKey) || null;
    if (!title || !body) return;
    if (!row) { title.textContent = 'Select a point or ledger row'; return; }
    title.textContent = row.id;
    const control = row.__matchedControl;
    const decision = row.__decision;
    const metrics = [
      ['Dev SR12', row.dev_sharpe_12], ['Research SR12', row.research_sharpe_12], ['Dev decay', row.__devDecay],
      ['Dev-SR12 control margin', row.__causalMargin], ['Dev SR0', row.dev_sharpe_0], ['Cost drag', row.__costDrag],
      ['Dev CAGR12', row.dev_cagr_12], ['Dev Sortino12', row.dev_sortino_12], ['Dev Calmar12', row.dev_calmar_12],
      ['Hit rate12', row.dev_hit_rate_12], ['Turnover12', row.mean_turnover_12], ['Worst DD12', row.worst_drawdown_12],
      ['Selection score', row.selection_score], ['Evidence completeness', row.evidence_completeness]
    ];
    const metricCards = metrics.map(([label, value]) => {
      const rendered = /cagr|hit rate|turnover|worst dd|completeness/i.test(label) ? L.pct(value) : L.fmt(value);
      return `<div><span>${L.esc(label)}</span><strong>${rendered}</strong></div>`;
    }).join('');
    const controlCard = control ? `<div class="ql-match-card"><h3>STRONGEST MATCHED DEV-SR12 CHALLENGER</h3><div class="ql-match-pair"><div><span>SELECTED BASE</span><strong>${L.esc(row.id)} · ${L.fmt(row.dev_sharpe_12)}</strong></div><span class="ql-match-vs">VS</span><div><span>${L.esc(String(control.mode||'control').toUpperCase())}</span><strong>${L.esc(control.id)} · ${L.fmt(control.dev_sharpe_12)}</strong></div></div><p style="margin-top:8px">Descriptive Dev-SR12 comparison only; it does not replace the preregistered family adjudication.</p></div>`
      : '<div class="ql-match-card"><h3>MATCHED CONTROL</h3><p>No same-family ablation/falsifier/control with a measured dev_sharpe_12 is attached in this matrix context. No control margin is inferred.</p></div>';
    const failed = Array.isArray(decision?.failed_controls) && decision.failed_controls.length ? `<br>Failed controls: ${L.esc(decision.failed_controls.join(', '))}` : '';
    const decisionCard = decision ? `<div class="ql-decision-card"><h3>FAMILY ADJUDICATION · AUTHORITATIVE</h3><p><strong>${L.esc(decision.decision_code||decision.decision)}</strong><br>${L.esc(decision.reason||'No reason recorded.')}${failed}</p></div>`
      : '<div class="ql-decision-card"><h3>FAMILY ADJUDICATION</h3><p>No family decision object is attached in this matrix context.</p></div>';
    body.className = '';
    body.innerHTML = `<div class="ql-inspect-meta"><span>${L.esc(row.__campaign)}</span><span>${L.esc(row.family||'no family')}</span><span>${L.esc(row.mode||'no mode')}</span><span>${L.esc(row.status||'no status')}</span><span>${L.esc(row.__lane)}</span></div><div class="ql-inspect-grid">${metricCards}</div>${controlCard}${decisionCard}`;
  };
})();
