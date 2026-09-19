(() => {
  'use strict';

  const source = window.Q25_LEARNING_ROUTER_URL || 'data/learning_router.json';
  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
  const human = (value) => String(value || '').replace(/_/g, ' ');

  function routeCard(row) {
    return `<article class="lr-belief">
      <span>${esc(human(row.id))}</span>
      <strong>${esc(human(row.state))}</strong>
      <p>${esc(row.evidence)}</p>
      <small>${esc(row.uncertainty)}</small>
    </article>`;
  }

  function queueRows(rows, label) {
    if (!rows?.length) return `<div class="lr-empty">${esc(label)}: none</div>`;
    return rows.map((row) => `<div class="lr-queue-row">
      <span>${esc(row.campaign)}</span>
      <strong>${esc(row.family_count ?? '—')} ${Number(row.family_count) === 1 ? 'family' : 'families'}</strong>
    </div>`).join('');
  }

  function render(packet, section) {
    const pipeline = packet.pipeline || {};
    const router = packet.router || {};
    const bottleneck = pipeline.bottleneck || {};
    const next = router.next_action || {};
    const budget = router.new_hypothesis_budget || {};
    const pending = pipeline.pending_canonical_ingest || [];
    const unmeasured = pipeline.frozen_unmeasured || [];

    section.innerHTML = `
      <div class="lr-head">
        <div>
          <span class="qt-kicker">RESEARCH BUDGET ROUTER</span>
          <h2>Do the next evidence-changing thing.</h2>
          <p>The router joins process diagnostics with evidence-stage state. It does not score strategies; it prevents new hypothesis generation from jumping ahead of measured evidence, frozen experiments, or canonical ingestion.</p>
        </div>
        <div class="lr-bottleneck">
          <span>CURRENT BOTTLENECK</span>
          <strong>${esc(human(bottleneck.stage || 'unknown'))}</strong>
          <small>${esc(bottleneck.reason || 'No bottleneck encoded.')}</small>
        </div>
      </div>

      <div class="lr-route">
        <div class="lr-next">
          <span>NEXT JUSTIFIED ACTION</span>
          <strong>${esc(human(next.action || 'none encoded'))}</strong>
          <code>${esc(next.campaign || pipeline.canonical_latest?.campaign || '—')}</code>
          <p>${esc(next.why || 'No deterministic pipeline action is currently encoded.')}</p>
        </div>
        <div class="lr-budget ${budget.state === 'NEW_OBJECT_CLASS_JUSTIFIED' ? 'is-open' : 'is-blocked'}">
          <span>NEW-HYPOTHESIS BUDGET</span>
          <strong>${esc(human(budget.state || 'unknown'))}</strong>
          <p>${esc(budget.why || '')}</p>
        </div>
      </div>

      <div class="lr-grid">
        <article class="lr-panel">
          <div class="lr-panel-head"><span>MEASURED → CANONICAL</span><strong>${pending.length}</strong></div>
          ${queueRows(pending, 'Pending ingest')}
        </article>
        <article class="lr-panel">
          <div class="lr-panel-head"><span>FROZEN → MEASURED</span><strong>${unmeasured.length}</strong></div>
          ${queueRows(unmeasured, 'Frozen unmeasured')}
        </article>
        <article class="lr-panel">
          <div class="lr-panel-head"><span>CANONICAL → FULL MATRIX</span><strong>${esc(pipeline.surface_debt?.measured_campaigns_since_full_matrix ?? 0)}</strong></div>
          <p>Latest full matrix: <code>${esc(pipeline.surface_debt?.latest_full_matrix_campaign || '—')}</code></p>
        </article>
        <article class="lr-panel">
          <div class="lr-panel-head"><span>DEVELOPMENT → FORWARD</span><strong>${esc(pipeline.failed_forward_count ?? 0)} failed</strong></div>
          <p>Forward failures stay calibration evidence; they do not become a universal shrinkage constant.</p>
        </article>
      </div>

      <div class="lr-beliefs">${(packet.belief_updates || []).map(routeCard).join('')}</div>

      <div class="lr-guardrail">
        <span>MUTATION GUARDRAIL</span>
        <strong>${esc(router.mutation_guardrail || '—')}</strong>
      </div>

      <div class="rl-links">
        <a href="LEARNING_ROUTER.html">Generated learning-router report</a>
        <a href="data/learning_router.json">Raw router JSON</a>
        <a href="control-plane.html">Research control plane</a>
      </div>
    `;
  }

  function mount() {
    const terminal = document.querySelector('[data-q25-terminal]');
    const control = document.querySelector('[data-control-plane]');
    if (!terminal && !control) return;
    if (document.querySelector('[data-learning-router]')) return;

    const section = document.createElement('section');
    section.className = 'qt-section lr-console';
    section.setAttribute('data-learning-router', '');
    section.innerHTML = '<div class="lr-loading">Routing research budget…</div>';

    const host = terminal || control;
    const recursive = host.querySelector('[data-recursive-learning]');
    const anchor = recursive || host.querySelector('.qt-rulebar') || host.querySelector('.cp-kpis') || host.querySelector('.qt-hero') || host.querySelector('.cp-hero');
    if (anchor) anchor.insertAdjacentElement('afterend', section);
    else host.prepend(section);

    fetch(source, {cache: 'no-store'})
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then((packet) => render(packet, section))
      .catch((error) => {
        section.innerHTML = `<div class="lr-error"><strong>Learning router unavailable</strong><span>${esc(error.message || error)}</span></div>`;
      });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once: true});
  else mount();
})();
