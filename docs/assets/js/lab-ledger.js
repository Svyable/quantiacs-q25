(() => {
  'use strict';
  const L = window.Q25Lab;
  if (!L?.root) return;
  const { $, $$ } = L;

  L.sortedRows = () => {
    const list = [...L.filtered];
    const ascending = new Set(['mean_turnover_12']);
    list.sort((a, b) => {
      const av = L.n(a[L.sortKey]);
      const bv = L.n(b[L.sortKey]);
      if (av === null && bv === null) return 0;
      if (av === null) return 1;
      if (bv === null) return -1;
      return ascending.has(L.sortKey) ? av - bv : bv - av;
    });
    return list;
  };

  L.renderLedger = () => {
    const body = $('[data-ledger-body]');
    const caption = $('[data-ledger-caption]');
    const more = $('[data-action="show-more"]');
    if (!body) return;
    const ordered = L.sortedRows();
    const shown = ordered.slice(0, L.visibleRows);
    const signedClass = (value) => L.isNum(value) ? Number(value) > 0 ? 'positive' : Number(value) < 0 ? 'negative' : '' : '';
    body.innerHTML = shown.length ? shown.map((row, index) => {
      const code = row.__decisionCode || '—';
      const evidence = L.isNum(row.evidence_completeness) ? L.pct(row.evidence_completeness, 0) : (row.status || '—');
      return `<tr data-select-key="${L.esc(row.__key)}" class="${row.__key===L.selectedKey?'selected':''}">
        <td>${index+1}</td><td><strong>${L.esc(row.id)}</strong><br><span>${L.esc(row.family||'—')}</span></td><td>${L.esc(row.__campaign)}</td>
        <td><span class="qt-mode ${L.esc(String(row.mode||'other').toLowerCase())}">${L.esc(row.mode||'—')}</span></td>
        <td><span class="qt-decision ${L.decisionClass(code)}" title="${L.esc(code)}">${L.esc(code)}</span></td>
        <td>${L.fmt(row.dev_sharpe_12)}</td><td>${L.fmt(row.research_sharpe_12)}</td><td class="${signedClass(row.__devDecay)}">${L.fmt(row.__devDecay)}</td>
        <td class="${signedClass(row.__causalMargin)}">${L.fmt(row.__causalMargin)}</td><td>${L.fmt(row.__costDrag)}</td><td>${L.pct(row.mean_turnover_12)}</td><td>${L.pct(row.worst_drawdown_12)}</td><td>${L.esc(evidence)}</td>
      </tr>`;
    }).join('') : '<tr><td colspan="13">No rows match the current filters.</td></tr>';
    $$('[data-select-key]', body).forEach((el) => el.addEventListener('click', () => L.selectRow(el.dataset.selectKey)));
    if (caption) caption.textContent = `Showing ${Math.min(L.visibleRows,ordered.length).toLocaleString()} of ${ordered.length.toLocaleString()} filtered rows`;
    if (more) more.hidden = L.visibleRows >= ordered.length;
  };

  L.exportCsv = () => {
    const columns = ['id','campaign','lane','family','mode','status','family_decision','dev_sharpe_12','research_sharpe_12','dev_decay','dev_sr12_control_margin','matched_control_id','matched_control_mode','matched_control_dev_sharpe_12','dev_sharpe_0','cost_drag','dev_cagr_12','dev_sortino_12','dev_calmar_12','dev_hit_rate_12','mean_turnover_12','worst_drawdown_12','selection_score','evidence_completeness'];
    const quote = (value) => `"${String(value??'').replace(/"/g,'""')}"`;
    const lines = [columns.map(quote).join(',')];
    L.sortedRows().forEach((row) => lines.push([
      row.id,row.__campaign,row.__lane,row.family,row.mode,row.status,row.__decisionCode,row.dev_sharpe_12,row.research_sharpe_12,row.__devDecay,row.__causalMargin,
      row.__matchedControl?.id,row.__matchedControl?.mode,row.__matchedControl?.dev_sharpe_12,row.dev_sharpe_0,row.__costDrag,row.dev_cagr_12,row.dev_sortino_12,row.dev_calmar_12,
      row.dev_hit_rate_12,row.mean_turnover_12,row.worst_drawdown_12,row.selection_score,row.evidence_completeness
    ].map(quote).join(',')));
    const blob = new Blob([lines.join('\n')], {type:'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url; anchor.download = 'q25-causal-lab-filtered.csv'; document.body.appendChild(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 500);
  };
})();
