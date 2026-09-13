(() => {
  'use strict';
  const L = window.Q25Lab;
  if (!L?.root) return;
  const { $, $$ } = L;

  L.renderKpis = () => {
    const bases = L.filtered.filter((row) => row.mode === 'base');
    const groups = L.filteredGroups();
    const matched = groups.filter((g) => g.bestBase && g.strongestControl);
    const positive = matched.filter((g) => L.isNum(g.margin) && g.margin > 0);
    const floor = bases.filter((row) => L.isNum(row.dev_sharpe_12) && Number(row.dev_sharpe_12) >= 1);
    const continuing = new Set(
      groups
        .filter((g) => /CONTINUE/i.test(String(g.decision?.decision || g.decision?.decision_code || '')))
        .map((g) => g.key)
    );
    const decay = L.median(bases.map((row) => L.n(row.__devDecay)).filter(Number.isFinite));
    const set = (name, value) => $$(`[data-kpi="${name}"]`).forEach((el) => { el.textContent = value; });
    set('rows', L.filtered.length.toLocaleString());
    set('bases', bases.length.toLocaleString());
    set('matched', matched.length.toLocaleString());
    set('positive', positive.length.toLocaleString());
    set('floor', floor.length.toLocaleString());
    set('continue', continuing.size.toLocaleString());
    set('decay', decay === null ? '—' : L.fmt(decay));
    const count = $('[data-filter-count]');
    if (count) count.textContent = `${L.filtered.length.toLocaleString()} / ${L.rows.length.toLocaleString()} rows`;
  };
})();
