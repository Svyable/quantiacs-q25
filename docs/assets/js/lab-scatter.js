(() => {
  'use strict';
  const L = window.Q25Lab;
  if (!L?.root) return;
  const { $ } = L;

  const niceTicks = (min, max, count = 5) => {
    if (!Number.isFinite(min) || !Number.isFinite(max)) return [];
    if (min === max) return [min];
    const raw = (max - min) / Math.max(1, count - 1);
    const power = Math.pow(10, Math.floor(Math.log10(Math.abs(raw) || 1)));
    const fraction = raw / power;
    const step = (fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10) * power;
    const start = Math.ceil(min / step) * step;
    const out = [];
    for (let value = start; value <= max + step * 0.25; value += step) out.push(value);
    return out;
  };

  L.renderScatter = () => {
    const svg = $('[data-chart="scatter"]');
    const shell = svg?.parentElement;
    const empty = $('[data-chart-empty]');
    if (!svg || !shell) return;
    const points = L.filtered.filter((row) => L.isNum(row[L.xMetric]) && L.isNum(row[L.yMetric]));
    svg.replaceChildren();
    if (empty) empty.hidden = points.length > 0;
    if (!points.length) return;

    const width = Math.max(420, shell.clientWidth || 820);
    const height = 430;
    const margin = { t:20, r:22, b:52, l:66 };
    const plotW = width - margin.l - margin.r;
    const plotH = height - margin.t - margin.b;
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    const xs = points.map((row) => Number(row[L.xMetric]));
    const ys = points.map((row) => Number(row[L.yMetric]));
    let xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(...ys), ymax = Math.max(...ys);
    const xpad = Math.max((xmax - xmin) * 0.08, 0.001);
    const ypad = Math.max((ymax - ymin) * 0.08, 0.001);
    xmin -= xpad; xmax += xpad; ymin -= ypad; ymax += ypad;
    if (/sharpe/i.test(L.yMetric)) { ymin = Math.min(ymin, 0); ymax = Math.max(ymax, 1); }
    if (L.xMetric === '__causalMargin') { xmin = Math.min(xmin, 0); xmax = Math.max(xmax, 0); }
    const x = (v) => margin.l + (Number(v) - xmin) / (xmax - xmin || 1) * plotW;
    const y = (v) => margin.t + (ymax - Number(v)) / (ymax - ymin || 1) * plotH;

    niceTicks(xmin, xmax, 6).forEach((tick) => {
      const xx = x(tick);
      svg.append(L.svgEl('line', { x1:xx, y1:margin.t, x2:xx, y2:height-margin.b, class:'grid' }));
      const label = L.svgEl('text', { x:xx, y:height-26, 'text-anchor':'middle' });
      label.textContent = L.metricFmt(L.xMetric, tick); svg.append(label);
    });
    niceTicks(ymin, ymax, 6).forEach((tick) => {
      const yy = y(tick);
      svg.append(L.svgEl('line', { x1:margin.l, y1:yy, x2:width-margin.r, y2:yy, class:'grid' }));
      const label = L.svgEl('text', { x:margin.l-8, y:yy+3, 'text-anchor':'end' });
      label.textContent = L.metricFmt(L.yMetric, tick); svg.append(label);
    });
    svg.append(L.svgEl('line', { x1:margin.l, y1:height-margin.b, x2:width-margin.r, y2:height-margin.b, class:'axis' }));
    svg.append(L.svgEl('line', { x1:margin.l, y1:margin.t, x2:margin.l, y2:height-margin.b, class:'axis' }));
    if (xmin <= 0 && xmax >= 0) svg.append(L.svgEl('line', { x1:x(0), y1:margin.t, x2:x(0), y2:height-margin.b, class:'diag' }));
    if (/sharpe/i.test(L.yMetric) && ymin <= 1 && ymax >= 1) svg.append(L.svgEl('line', { x1:margin.l, y1:y(1), x2:width-margin.r, y2:y(1), class:'floor' }));
    const xLabel = L.svgEl('text', { x:margin.l+plotW/2, y:height-4, 'text-anchor':'middle' });
    xLabel.textContent = L.human(L.xMetric); svg.append(xLabel);
    const yLabel = L.svgEl('text', { x:12, y:margin.t+plotH/2, 'text-anchor':'middle', transform:`rotate(-90 12 ${margin.t+plotH/2})` });
    yLabel.textContent = L.human(L.yMetric); svg.append(yLabel);

    const tip = $('[data-tooltip]');
    points.forEach((row) => {
      const mode = String(row.mode || 'other').toLowerCase();
      const cls = ['base','control','ablation','falsifier'].includes(mode) ? mode : 'other';
      const dot = L.svgEl('circle', { cx:x(row[L.xMetric]), cy:y(row[L.yMetric]), r:row.__key===L.selectedKey?6.3:4.7, class:`point ${cls}${row.__key===L.selectedKey?' selected':''}` });
      dot.addEventListener('pointermove', (event) => {
        if (!tip) return;
        tip.innerHTML = `<strong>${L.esc(row.id)}</strong><span>${L.esc(L.human(L.xMetric))}<b>${L.esc(L.metricFmt(L.xMetric,row[L.xMetric]))}</b></span><span>${L.esc(L.human(L.yMetric))}<b>${L.esc(L.metricFmt(L.yMetric,row[L.yMetric]))}</b></span><span>family<b>${L.esc(row.family||'—')}</b></span>`;
        tip.hidden = false;
        const box = shell.getBoundingClientRect();
        tip.style.left = `${L.clamp(event.clientX-box.left+12,6,box.width-285)}px`;
        tip.style.top = `${L.clamp(event.clientY-box.top-70,6,box.height-120)}px`;
      });
      dot.addEventListener('pointerleave', () => { if (tip) tip.hidden = true; });
      dot.addEventListener('click', () => L.selectRow(row.__key));
      svg.append(dot);
    });
  };
})();
