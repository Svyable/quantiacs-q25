(() => {
  'use strict';

  const source = window.Q25_RECURSIVE_LEARNING_URL || 'data/recursive_learning.json';
  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
  const num = (value) => value !== null && value !== '' && Number.isFinite(Number(value));
  const fmt = (value, digits = 3) => num(value) ? Number(value).toFixed(digits) : '—';
  const signed = (value, digits = 3) => {
    if (!num(value)) return '—';
    const n = Number(value);
    return `${n > 0 ? '+' : ''}${n.toFixed(digits)}`;
  };
  const pct = (value, digits = 1) => num(value) ? `${(Number(value) * 100).toFixed(digits)}%` : '—';
  const ratio = (metric) => metric && num(metric.count) && num(metric.total)
    ? `${metric.count}/${metric.total}`
    : '—';
  const longRatio = (metric) => metric && num(metric.count) && num(metric.total)
    ? `${metric.count}/${metric.total} · ${pct(metric.rate)}`
    : '—';

  function metricCard(label, value, detail, tone = '') {
    return `<article class="rl-metric ${tone}"><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(detail)}</small></article>`;
  }

  function campaignRows(packet) {
    return (packet.campaigns || []).map((row) => {
      const support = row.control_support || {};
      const gap = row.research_to_dev || {};
      const supportTone = support.count > 0 ? 'rl-good' : 'rl-bad';
      const economicTone = Number(row.best_robust_sharpe) >= 1 ? 'rl-good' : 'rl-warn';
      return `<div class="rl-campaign-row">
        <div class="rl-campaign-id"><span>${esc(row.campaign)}</span><small>${esc(row.decision || '—')}</small></div>
        <div class="rl-campaign-cell"><span>BEST ROBUST SR</span><strong class="${economicTone}">${fmt(row.best_robust_sharpe)}</strong></div>
        <div class="rl-campaign-cell"><span>CONTROL SUPPORT</span><strong class="${supportTone}">${esc(longRatio(support))}</strong></div>
        <div class="rl-campaign-cell"><span>MEDIAN CAUSAL MARGIN</span><strong class="${Number(row.median_central_control_margin) > 0 ? 'rl-good' : 'rl-bad'}">${signed(row.median_central_control_margin)}</strong></div>
        <div class="rl-campaign-cell"><span>MEDIAN DEV−RESEARCH</span><strong class="${Number(gap.median_dev_minus_research_sharpe_12) >= 0 ? 'rl-good' : 'rl-warn'}">${signed(gap.median_dev_minus_research_sharpe_12)}</strong></div>
      </div>`;
    }).join('');
  }

  function miniBars(packet) {
    const trajectory = packet.trajectories?.best_robust_sharpe?.values || [];
    const finite = trajectory.map((row) => Number(row.value)).filter(Number.isFinite);
    const max = finite.length ? Math.max(...finite, 1) : 1;
    return trajectory.map((row) => {
      const v = Number(row.value);
      const width = Number.isFinite(v) ? Math.max(2, Math.min(100, v / max * 100)) : 0;
      const campaign = String(row.campaign || '').replace(/^frontier_\d{8}/, '');
      return `<div class="rl-bar-row"><span>${esc(campaign || row.campaign)}</span><div><i style="width:${width.toFixed(1)}%"></i></div><strong>${fmt(row.value)}</strong></div>`;
    }).join('');
  }

  function actionRows(packet) {
    return (packet.next_actions || []).map((row) => `<div class="rl-action">
      <span>P${esc(row.priority)}</span>
      <div><strong>${esc(String(row.action || '').replace(/_/g, ' '))}</strong><p>${esc(row.why)}</p></div>
    </div>`).join('');
  }

  function stateTags(packet) {
    return (packet.state_tags || []).map((tag) => `<span>${esc(String(tag).replace(/_/g, ' '))}</span>`).join('');
  }

  function story(packet) {
    const best = packet.trajectories?.best_robust_sharpe || {};
    const support = packet.trajectories?.control_support_rate || {};
    const recent = packet.recent_window || {};
    const gap = recent.research_to_dev || {};
    const validation = packet.validation_calibration || {};
    const debt = packet.evidence_debt || {};
    return `<div class="rl-story-grid">
      <div><span>ECONOMICS</span><strong>${fmt(best.first)} → ${fmt(best.latest)}</strong><p>Best robust development Sharpe across the recent window, Δ ${signed(best.delta_first_to_latest)}.</p></div>
      <div><span>CAUSAL SUPPORT</span><strong>${pct(support.first)} → ${pct(support.latest)}</strong><p>Share of families whose central parent beat both destructive controls.</p></div>
      <div><span>SELECTION OPTIMISM</span><strong>${signed(gap.pooled_median_dev_minus_research_sharpe_12)}</strong><p>Pooled median Dev−Research SR@12 across ${esc(gap.base_cells_compared ?? '—')} comparable base cells.</p></div>
      <div><span>FORWARD TRANSLATION</span><strong>${pct(validation.median_forward_to_development_retention)}</strong><p>${esc(validation.failed_gate_count ?? 0)} failed frozen gate(s); forward−development Δ ${signed(validation.median_forward_minus_development_sharpe)}.</p></div>
      <div><span>EVIDENCE DEBT</span><strong>${esc(debt.measured_campaigns_since_full_matrix ?? 0)} since matrix</strong><p>Latest full matrix ${esc(debt.latest_full_matrix_campaign || '—')}; queue ${esc(debt.measurement_queue_count ?? 0)}.</p></div>
    </div>`;
  }

  function render(packet, section) {
    const recent = packet.recent_window || {};
    const validation = packet.validation_calibration || {};
    const gap = recent.research_to_dev || {};
    const debt = packet.evidence_debt || {};
    const policy = packet.policy || {};

    section.innerHTML = `
      <div class="rl-heading">
        <div>
          <span class="qt-kicker">DOGFOOD / RECURSIVE LEARNING</span>
          <h2>Is the research loop actually learning?</h2>
          <p>Temporal diagnostics across the latest canonical campaigns. Falsification, economics, selection optimism, validation transfer and evidence debt stay separate—there is deliberately no research mega-score.</p>
        </div>
        <div class="rl-policy"><span>POLICY</span><strong>${esc(policy.aggregate_score || 'FORBIDDEN')}</strong><small>aggregate score · cross-campaign rank ${esc(policy.cross_campaign_scalar_rank || 'FORBIDDEN')}</small></div>
      </div>

      <div class="rl-tags" aria-label="recursive learning state">${stateTags(packet)}</div>

      <div class="rl-metrics">
        ${metricCard('Falsification coverage', ratio(recent.falsification_coverage), `${pct(recent.falsification_coverage?.rate)} of recent families`, 'good')}
        ${metricCard('Control-supported', ratio(recent.control_support), `${pct(recent.control_support?.rate)} causal-support rate`, recent.control_support?.count ? 'mixed' : 'bad')}
        ${metricCard('Economic survivors', ratio(recent.economic_survival), 'robust SR ≥ 1.0', recent.economic_survival?.count ? 'good' : 'bad')}
        ${metricCard('Promotion-ready', ratio(recent.promotion_ready), 'control support ∩ economics', recent.promotion_ready?.count ? 'good' : 'bad')}
        ${metricCard('Median Dev−Research', signed(gap.pooled_median_dev_minus_research_sharpe_12), `${esc(gap.nonnegative_gap_count ?? 0)}/${esc(gap.base_cells_compared ?? 0)} cells held or improved`, Number(gap.pooled_median_dev_minus_research_sharpe_12) >= 0 ? 'good' : 'warn')}
        ${metricCard('Forward retention', pct(validation.median_forward_to_development_retention), `${esc(validation.failed_gate_count ?? 0)}/${esc(validation.observed_gate_count ?? 0)} observed gates failed`, Number(validation.median_forward_to_development_retention) >= 1 ? 'good' : 'warn')}
      </div>

      <div class="rl-grid">
        <article class="rl-panel rl-trajectory">
          <div class="rl-panel-head"><div><span>RECENT WINDOW</span><h3>Campaign trajectory</h3></div><small>${esc((packet.window_campaigns || []).join(' → '))}</small></div>
          <div class="rl-mini-bars">${miniBars(packet)}</div>
          <div class="rl-campaigns">${campaignRows(packet)}</div>
        </article>

        <article class="rl-panel rl-next">
          <div class="rl-panel-head"><div><span>RECURSIVE CONTROL</span><h3>Derived next actions</h3></div><small>state-derived, not discretionary rescue</small></div>
          <div class="rl-actions">${actionRows(packet)}</div>
        </article>
      </div>

      <article class="rl-panel rl-story">
        <div class="rl-panel-head"><div><span>WHAT CHANGED</span><h3>Learning vector</h3></div><small>diagnostic channels remain incomparable</small></div>
        ${story(packet)}
        <div class="rl-footnote">Exact family-name novelty is only a lexical breadth proxy. Missing metrics remain missing. Frozen campaigns and spent validation folds are not rewritten by these diagnostics. Next queued campaign: <strong>${esc(debt.next_queued_campaign || '—')}</strong>.</div>
      </article>

      <div class="rl-links"><a href="RECURSIVE_LEARNING.html">Generated recursive-learning report</a><a href="data/recursive_learning.json">Raw telemetry JSON</a><a href="control-plane.html">Research control plane</a></div>
    `;
  }

  function createSection() {
    const section = document.createElement('section');
    section.className = 'qt-section rl-console';
    section.id = 'recursive-learning';
    section.setAttribute('data-recursive-learning', '');
    section.innerHTML = '<div class="rl-loading"><span></span> Loading recursive-learning telemetry…</div>';
    return section;
  }

  function mount() {
    const terminal = document.querySelector('[data-q25-terminal]');
    const controlPlane = document.querySelector('[data-control-plane]');
    if (!terminal && !controlPlane) return;
    if (document.querySelector('[data-recursive-learning]')) return;

    const section = createSection();
    if (terminal) {
      const anchor = terminal.querySelector('.qt-rulebar') || terminal.querySelector('.qt-hero');
      if (anchor) anchor.insertAdjacentElement('afterend', section);
      else terminal.prepend(section);
    } else {
      const anchor = controlPlane.querySelector('.cp-kpis') || controlPlane.querySelector('.cp-hero');
      if (anchor) anchor.insertAdjacentElement('afterend', section);
      else controlPlane.prepend(section);
    }

    fetch(source, {cache: 'no-store'})
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((packet) => render(packet, section))
      .catch((error) => {
        section.innerHTML = `<div class="rl-error"><strong>Recursive telemetry unavailable</strong><span>${esc(error.message || error)}</span></div>`;
      });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once: true});
  else mount();
})();
