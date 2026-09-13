(() => {
  'use strict';
  const L = window.Q25Lab;
  if (!L?.root) return;
  const { $, $$ } = L;

  L.renderCausal = () => {
    const host = $('[data-causal-board]');
    const summary = $('[data-causal-summary]');
    if (!host) return;
    const groups = L.filteredGroups()
      .filter((g) => g.bestBase && g.strongestControl && L.isNum(g.margin))
      .sort((a, b) => Number(b.margin) - Number(a.margin));
    const positive = groups.filter((g) => g.margin > 0).length;
    const negative = groups.filter((g) => g.margin <= 0).length;
    const conflicts = groups.filter((g) => {
      const code = String(g.decision?.decision || g.decision?.decision_code || '');
      return g.margin > 0 && /FREEZE|FALSIFIED|KILL|FAIL/i.test(code);
    }).length;
    if (summary) {
      summary.innerHTML = [
        ['MATCHED', groups.length],
        ['POSITIVE SR12 MARGIN', positive],
        ['NON-POSITIVE', negative],
        ['POSITIVE BUT FROZEN', conflicts]
      ].map(([label, value]) => `<div><span>${label}</span><strong>${value}</strong></div>`).join('');
    }
    if (!groups.length) {
      host.innerHTML = '<div class="qt-warning">No filtered family has both a measured base and a matched ablation/falsifier/control with development Sharpe.</div>';
      return;
    }
    const max = Math.max(...groups.map((g) => Math.abs(Number(g.margin))), 0.001);
    host.innerHTML = groups.map((g) => {
      const margin = Number(g.margin);
      const width = Math.min(50, Math.abs(margin) / max * 50);
      const code = g.decision ? (g.decision.decision_code || g.decision.decision) : 'NO FAMILY DECISION';
      const conflict = margin > 0 && /FREEZE|FALSIFIED|KILL|FAIL/i.test(String(code));
      const failed = Array.isArray(g.decision?.failed_controls) && g.decision.failed_controls.length
        ? ` · failed controls: ${g.decision.failed_controls.join(', ')}` : '';
      return `<div class="ql-causal-row" data-select-key="${L.esc(g.bestBase.__key)}">
        <div class="ql-causal-id"><strong>${L.esc(g.family)}${conflict ? ' · conflict' : ''}</strong><span>${L.esc(g.campaign)} · best Dev-SR12 base ${L.esc(g.bestBase.id)} · strongest matched ${L.esc(g.strongestControl.id)}</span></div>
        <div class="ql-causal-num">${L.fmt(g.bestBase.dev_sharpe_12)}</div>
        <div class="ql-causal-num">${L.fmt(g.strongestControl.dev_sharpe_12)}</div>
        <div class="ql-margin-track"><i class="${margin > 0 ? 'positive' : 'negative'}" style="width:${width}%"></i></div>
        <div class="ql-causal-decision ${L.decisionClass(code)}" title="${L.esc(code + failed)}">${margin > 0 ? '+' : ''}${L.fmt(margin)} · ${L.esc(code)}</div>
      </div>`;
    }).join('');
    $$('[data-select-key]', host).forEach((el) => el.addEventListener('click', () => L.selectRow(el.dataset.selectKey)));
  };

  const gateState = (v) => v === true ? 'pass' : v === false ? 'fail' : 'unknown';
  const gateMark = (v) => v === true ? '✓' : v === false ? '×' : '?';

  L.renderTriage = () => {
    const host = $('[data-triage]');
    if (!host) return;
    const bases = L.filtered.filter((row) => row.mode === 'base').map((row) => {
      const economic = L.isNum(row.dev_sharpe_12) ? Number(row.dev_sharpe_12) >= 1 : null;
      const control = row.__matchedControl && L.isNum(row.__causalMargin) ? Number(row.__causalMargin) > 0 : null;
      const complete = L.isNum(row.evidence_completeness) ? Number(row.evidence_completeness) >= 1 : null;
      const adjudicated = row.__decision ? /CONTINUE/i.test(String(row.__decision.decision || row.__decision.decision_code || '')) : null;
      const gates = [economic, control, complete, adjudicated];
      return { row, gates, score: gates.filter((x) => x === true).length, known: gates.filter((x) => x !== null).length };
    }).sort((a, b) => b.score - a.score || b.known - a.known || (Number(b.row.dev_sharpe_12) || -Infinity) - (Number(a.row.dev_sharpe_12) || -Infinity));
    if (!bases.length) {
      host.innerHTML = '<div class="qt-warning">No base cells match the current filters.</div>';
      return;
    }
    host.innerHTML = '<div class="ql-triage-head"><span>BASE CELL</span><span>SR≥1</span><span>SR CTRL</span><span>EVID</span><span>CONT</span><span>SCORE</span></div>' + bases.slice(0, 30).map(({ row, gates, score, known }) => `<div class="ql-triage-row" data-select-key="${L.esc(row.__key)}">
      <div class="ql-triage-name"><strong>${L.esc(row.id)}</strong><span>${L.esc(row.__campaign)} · ${L.esc(row.family || '—')}</span></div>
      ${gates.map((gate) => `<span class="ql-gate ${gateState(gate)}" title="${gate === null ? 'unknown in matrix' : gate ? 'passes this displayed field' : 'fails this displayed field'}">${gateMark(gate)}</span>`).join('')}
      <div class="ql-triage-score" title="${known} known fields">${score}/${known}</div>
    </div>`).join('');
    $$('[data-select-key]', host).forEach((el) => el.addEventListener('click', () => L.selectRow(el.dataset.selectKey)));
  };
})();
