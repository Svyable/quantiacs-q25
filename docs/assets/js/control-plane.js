(() => {
  'use strict';
  const root = document.querySelector('[data-control-plane]');
  if (!root) return;
  const $ = (s, scope = root) => scope.querySelector(s);
  const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num = (v) => v !== null && v !== '' && Number.isFinite(Number(v));
  const fmt = (v, d = 3) => num(v) ? Number(v).toFixed(d) : '—';
  const pct = (v, d = 1) => num(v) ? `${(Number(v) * 100).toFixed(d)}%` : '—';
  const shortHash = (v, n = 13) => v ? `${String(v).slice(0, n)}…` : '—';
  const cls = (v) => num(v) ? (Number(v) >= 0 ? 'pos' : 'neg') : '';
  const human = (v) => String(v || '').replace(/_/g, ' ');
  const set = (sel, text) => { const el = $(sel); if (el) el.textContent = text; };

  function renderKpis(data) {
    const latest = data.canonical_latest || {};
    const queue = data.measurement_queue || [];
    const receipts = data.measurement_receipts || [];
    const fwd = data.failed_forward_stack || [];
    const hist = data.frozen_historical_stack || [];
    const debt = data.surface_debt || {};
    const repro = data.reproducibility || {};
    set('[data-kpi="latest"]', latest.campaign || '—');
    set('[data-kpi-detail="latest"]', `${latest.decision || '—'} · ${latest.kind || '—'}`);
    set('[data-kpi="queue"]', String(queue.length));
    set('[data-kpi="receipts"]', String(receipts.length));
    set('[data-kpi="forward"]', String(fwd.length));
    set('[data-kpi="historical"]', String(hist.length));
    set('[data-kpi="debt"]', String(debt.measured_campaigns_since_full_matrix ?? '—'));
    set('[data-kpi-detail="debt"]', debt.latest_full_matrix_campaign ? `latest full: ${debt.latest_full_matrix_campaign}` : 'campaigns since full matrix');
    set('[data-kpi="repro"]', repro.status ? human(repro.status) : '—');
    set('[data-kpi-detail="repro"]', repro.campaign ? `${repro.campaign} · ${repro.decision_stable_count ?? '—'}/${repro.families_compared ?? '—'} stable` : 'latest reproducibility packet');
  }

  function renderFlow(data) {
    const host = $('[data-flow]'); if (!host) return;
    const queue = data.measurement_queue || [];
    const receipts = data.measurement_receipts || [];
    const latest = data.canonical_latest || {};
    const forward = data.failed_forward_stack || [];
    const historical = data.frozen_historical_stack || [];
    const stages = [
      {k:'queue', label:'FROZEN QUEUE', value:queue.length, body:queue.length ? `${queue.reduce((s,x)=>s+(x.candidate_count||0),0)} candidate cells await measurement or receipt.` : 'No frozen unmeasured campaign is currently queued.'},
      {k:'receipt', label:'MEASUREMENT RECEIPTS', value:receipts.length, body:receipts.length ? 'Receipts anchor measured output to artifact, data, manifest and workflow provenance.' : 'No committed measurement receipt.'},
      {k:'canonical', label:'CANONICAL LATEST', value:latest.campaign || '—', body:`${latest.decision || 'No decision'} · ${latest.family_stack?.length || 0} family summaries · ${latest.kind || 'unknown depth'}.`},
      {k:'forward', label:'FAILED FORWARD GATES', value:forward.length, body:forward.length ? 'Forward evidence is kept separate and can invalidate a development story.' : 'No failed forward packet recorded.'},
      {k:'historical', label:'FROZEN HISTORICAL', value:historical.length, body:'Dated roster preserved for precheck work; never cross-ranked against modern development packets.'}
    ];
    host.innerHTML = stages.map((s) => `<article class="cp-flow-card ${esc(s.k)}"><span>${esc(s.label)}</span><strong>${esc(s.value)}</strong><p>${esc(s.body)}</p></article>`).join('');
  }

  function renderLatest(data) {
    const latest = data.canonical_latest || {};
    set('[data-latest-title]', `${latest.frontier_label || 'Latest'} · ${latest.campaign || '—'}`);
    set('[data-latest-kind]', latest.kind || '—');
    const host = $('[data-family-stack]'); if (!host) return;
    const rows = latest.family_stack || [];
    host.innerHTML = rows.length ? rows.map((f) => `<div class="cp-family-row"><strong>#${esc(f.campaign_rank ?? '—')} ${esc(f.family)}</strong><span title="best base">${esc(f.best_base_id || '—')}</span><span>SR ${fmt(f.best_robust_sharpe)}</span><span class="${cls(f.floor_margin)}">floor ${fmt(f.floor_margin)}</span><span class="${cls(f.central_control_margin)}">ctrl ${fmt(f.central_control_margin)}</span><em title="${esc(f.decision_code || '')}">${esc(f.decision_code || '—')}</em></div>`).join('') : '<div class="qt-warning">No canonical family summaries are exposed.</div>';
  }

  function renderActions(data) {
    const host = $('[data-actions]'); if (!host) return;
    const actions = [...(data.dogfood?.next_actions || [])].sort((a,b) => (a.priority ?? 999) - (b.priority ?? 999));
    host.innerHTML = actions.length ? actions.map((a) => `<article class="cp-action"><div class="cp-action-head"><span>P${esc(a.priority ?? '—')} · ${esc(a.action || 'ACTION')}</span><span>${esc(a.campaign || 'GLOBAL')}</span></div><p>${esc(a.why || '')}</p></article>`).join('') : '<div class="qt-warning">No next actions recorded.</div>';
  }

  function renderQueue(data) {
    const host = $('[data-queue]'); if (!host) return;
    const rows = data.measurement_queue || [];
    host.innerHTML = rows.length ? rows.map((q) => `<article class="cp-queue-card"><div class="cp-queue-head"><strong>${esc(q.campaign)} · ${esc(q.frontier_label || '')}</strong><span class="cp-state">${esc(q.measurement_state || 'QUEUED')}</span></div><div class="cp-chip-row">${(q.families || []).map((f) => `<span>${esc(f)}</span>`).join('')}</div><p>${esc(q.classification_note || '')}</p><div class="cp-chip-row"><span>${esc(q.candidate_count ?? '—')} cells</span><span>${esc(q.family_count ?? '—')} families</span><span>${esc((q.selection_folds || []).join(' + ') || 'no folds')}</span><span>automatic promotion: ${esc(q.automatic_promotion)}</span></div></article>`).join('') : '<div class="qt-warning">Measurement queue is empty.</div>';
  }

  function renderForwardAndRepro(data) {
    const host = $('[data-forward]');
    const rows = data.failed_forward_stack || [];
    if (host) host.innerHTML = rows.length ? rows.map((r) => `<div class="cp-forward-card"><div class="cp-forward-metric dev"><span>DEVELOPMENT ROBUST SR</span><strong>${fmt(r.development_robust_sharpe)}</strong></div><div class="cp-forward-arrow">→</div><div class="cp-forward-metric fwd"><span>FORWARD SR12</span><strong>${fmt(r.forward_sharpe_12)}</strong></div><small>${esc(r.id)} · ${esc(r.decision || r.state || '')}</small></div>`).join('') : '<div class="qt-warning">No failed forward evidence recorded.</div>';
    const repro = data.reproducibility || {};
    const rh = $('[data-repro]'); if (!rh) return;
    rh.innerHTML = `<div class="cp-mini-grid"><div><span>REPLAY STATUS</span><strong>${esc(human(repro.status || '—'))}</strong></div><div><span>DECISIONS STABLE</span><strong>${esc(repro.decision_stable_count ?? '—')} / ${esc(repro.families_compared ?? '—')}</strong></div><div><span>MAX METRIC Δ</span><strong>${num(repro.max_abs_summary_metric_delta) ? Number(repro.max_abs_summary_metric_delta).toExponential(2) : '—'}</strong></div></div>`;
  }

  function renderReceipts(data) {
    const host = $('[data-receipts]'); if (!host) return;
    const rows = data.measurement_receipts || [];
    host.innerHTML = rows.length ? rows.map((r) => { const s = r.source || {}; return `<article class="cp-receipt"><div class="cp-receipt-head"><strong>${esc(r.campaign)} · ${esc(r.frontier_label || '')}</strong><span class="cp-state">${esc(r.status || 'RECEIPT')}</span></div><div class="cp-chip-row"><span>${esc(r.decision || '—')}</span><span>${esc((r.families || []).length)} families</span></div><div class="cp-receipt-grid"><div><span>ARTIFACT DIGEST</span><code title="${esc(s.artifact_digest || '')}">${esc(shortHash(s.artifact_digest,18))}</code></div><div><span>DATA SHA256</span><code title="${esc(s.data_sha256 || '')}">${esc(shortHash(s.data_sha256))}</code></div><div><span>MANIFEST SHA256</span><code title="${esc(s.manifest_sha256 || '')}">${esc(shortHash(s.manifest_sha256))}</code></div><div><span>MEASURED HEAD</span><code title="${esc(s.measured_head_sha || '')}">${esc(shortHash(s.measured_head_sha))}</code></div><div><span>WORKFLOW RUN</span><code>${esc(s.workflow_run_id ?? '—')}</code></div><div><span>ARTIFACT ID</span><code>${esc(s.artifact_id ?? '—')}</code></div></div></article>`; }).join('') : '<div class="qt-warning">No committed receipts.</div>';
  }

  function renderDebtAndCollisions(data) {
    const debt = data.surface_debt || {};
    const host = $('[data-debt]');
    if (host) host.innerHTML = `<div class="cp-mini-grid"><div><span>LATEST FULL MATRIX</span><strong>${esc(debt.latest_full_matrix_campaign || '—')}</strong></div><div><span>MEASURED SINCE FULL MATRIX</span><strong>${esc(debt.measured_campaigns_since_full_matrix ?? '—')}</strong></div><div><span>LATEST IS SUMMARY-ONLY</span><strong>${esc(debt.summary_only_latest ?? '—')}</strong></div></div><div class="qt-warning">Latest campaign mentioned by matrix: ${esc(debt.research_matrix_mentions_latest ?? '—')}. Surface debt is a documentation/evidence-depth issue, not an economic score.</div>`;
    const collisions = data.dogfood?.frontier_label_collisions || [];
    const ch = $('[data-collisions]'); if (!ch) return;
    ch.innerHTML = collisions.length ? collisions.map((c) => `<div class="cp-collision"><strong>${esc(c.severity || 'WARN')} · ${esc(c.frontier_label || 'label collision')}</strong><br>${esc((c.campaigns || []).join(' ↔ '))}<br>Display the full campaign UID; preserve historical IDs.</div>`).join('') : '<div class="cp-collision">No human-label collision recorded.</div>';
  }

  function renderHistory(data) {
    const host = $('[data-history]'); if (!host) return;
    const rows = data.frozen_historical_stack || [];
    host.innerHTML = rows.length ? rows.map((r) => `<tr><td>${esc(r.rank ?? '—')}</td><td><strong>${esc(r.name || r.id)}</strong><br><span>${esc(r.id)}</span></td><td>${esc(r.role || '—')}</td><td>${fmt(r.full_sharpe)}</td><td>${fmt(r.stress_sharpe)} @ ${pct(r.stress_atr_fraction,0)} ATR</td><td>${pct(r.max_drawdown,1)}</td><td>${esc(r.status || '—')}</td></tr>`).join('') : '<tr><td colspan="7">No frozen historical roster.</td></tr>';
  }

  function renderPolicy(data) {
    const p = data.policy || {};
    set('[data-policy-note]', p.lane_order_is_not_quality_order ? 'lane order is not quality order' : 'see policy');
    const host = $('[data-policy-rules]'); if (!host) return;
    host.innerHTML = `Cross-campaign scalar rank: <strong>${esc(p.cross_campaign_scalar_rank || '—')}</strong> · Weighted mega-score: <strong>${esc(p.weighted_mega_score)}</strong> · Missing metrics: <strong>${esc(p.missing_metrics || '—')}</strong><br>${esc(p.display_rule || '')}`;
  }

  const src = root.dataset.source || 'data/research_control_plane.json';
  fetch(src, {cache:'no-store'})
    .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then((data) => {
      renderKpis(data); renderFlow(data); renderLatest(data); renderActions(data); renderQueue(data); renderForwardAndRepro(data); renderReceipts(data); renderDebtAndCollisions(data); renderHistory(data); renderPolicy(data);
      root.querySelector('.qt-feed')?.classList.add('is-live');
      set('[data-cp-state]', 'CONTROL PLANE ONLINE');
    })
    .catch((err) => { set('[data-cp-state]', 'CONTROL PLANE ERROR'); console.error('Q25 control plane failed', err); });
})();
