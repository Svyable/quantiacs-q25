(() => {
  'use strict';
  const L = window.Q25Lab;
  if (!L?.root) return;
  const { $, $$ } = L;

  L.renderStability = () => {
    const host = $('[data-stability]');
    if (!host) return;
    const groups = L.filteredGroups()
      .map((g) => ({ ...g, bases: g.bases.filter((row) => L.isNum(row[L.stabilityMetric])) }))
      .filter((g) => g.bases.length >= 2);
    if (!groups.length) {
      host.innerHTML = '<div class="qt-warning">No filtered family exposes two or more measured base cells for this metric.</div>';
      return;
    }
    const all = groups.flatMap((g) => g.bases.map((row) => Number(row[L.stabilityMetric])));
    const min = Math.min(...all);
    const max = Math.max(...all);
    const span = max - min || 1;
    groups.sort((a, b) => Math.max(...b.bases.map((r) => Number(r[L.stabilityMetric]))) - Math.max(...a.bases.map((r) => Number(r[L.stabilityMetric]))));
    host.innerHTML = groups.map((g) => {
      const vals = g.bases.map((row) => Number(row[L.stabilityMetric]));
      const med = L.median(vals);
      const spread = Math.max(...vals) - Math.min(...vals);
      const floorHits = /sharpe/i.test(L.stabilityMetric) ? vals.filter((v) => v >= 1).length : null;
      const sorted = [...g.bases].sort((a, b) => {
        const ma = String(a.id).match(/(?:w|window|lookback)[_-]?(\d+)/i);
        const mb = String(b.id).match(/(?:w|window|lookback)[_-]?(\d+)/i);
        if (ma && mb) return Number(ma[1]) - Number(mb[1]);
        return String(a.id).localeCompare(String(b.id));
      });
      const cells = sorted.map((row) => {
        const value = Number(row[L.stabilityMetric]);
        const heat = (value - min) / span;
        const alpha = 0.08 + heat * 0.68;
        return `<div class="ql-heat-cell" data-select-key="${L.esc(row.__key)}" title="${L.esc(row.id)} · ${L.esc(L.human(L.stabilityMetric))} ${L.esc(L.metricFmt(L.stabilityMetric, value))}" style="background:rgba(106,184,255,${alpha.toFixed(3)})"><span>${L.esc(L.paramLabel(row.id, g.family))}</span><strong>${L.esc(L.metricFmt(L.stabilityMetric, value))}</strong></div>`;
      }).join('');
      return `<div class="ql-stability-row">
        <div class="ql-stability-family"><strong>${L.esc(g.family)}</strong><span>${L.esc(g.campaign)} · ${sorted.length} base cells</span></div>
        <div class="ql-stability-cells">${cells}</div>
        <div class="ql-stability-stat"><div><span>MEDIAN</span><strong>${L.metricFmt(L.stabilityMetric, med)}</strong></div><div><span>SPREAD</span><strong>${L.metricFmt(L.stabilityMetric, spread)}</strong></div><div><span>${floorHits === null ? 'CELLS' : 'SR≥1'}</span><strong>${floorHits === null ? sorted.length : floorHits}</strong></div></div>
      </div>`;
    }).join('');
    $$('[data-select-key]', host).forEach((el) => el.addEventListener('click', () => L.selectRow(el.dataset.selectKey)));
  };
})();
