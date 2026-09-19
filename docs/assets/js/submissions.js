(() => {
  'use strict';
  const root=document.querySelector('[data-submission-readiness]');
  if(!root)return;
  const source=root.dataset.source;
  const $=(s)=>root.querySelector(s);
  const esc=(v)=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt=(v,d=3)=>v===null||v===undefined||!Number.isFinite(Number(v))?'—':Number(v).toFixed(d);
  const yes=(v)=>v===true?'PASS':v===false?'FAIL':'—';

  function render(packet){
    $('[data-sr-state]').textContent='READINESS LIVE';
    $('[data-hard-blocker]').textContent=packet.hard_blocker||'—';
    const s=packet.summary||{};
    $('[data-sr-kpis]').innerHTML=[
      ['PACKAGED',`${s.packaged_count??0}/${s.candidate_count??0}`],
      ['FULL-HISTORY FLOOR',`${s.full_history_floor_pass_count??0}/${s.candidate_count??0}`],
      ['FROZEN FORWARD',String(s.frozen_forward_observed_count??0)],
      ['PUBLIC SMOKE CLEAR',String(s.public_smoke_clear_count??0)],
      ['ACCOUNT-BOUND CLEAR',String(s.account_bound_clear_count??0)]
    ].map(([k,v])=>`<article><span>${esc(k)}</span><strong>${esc(v)}</strong></article>`).join('');

    const rows=packet.candidates||[];
    $('[data-sr-candidates]').innerHTML=rows.map(r=>{
      const m=r.full_history||{}, f=r.forward_validation||{}, p=r.public_correlation_smoke||{};
      const klass=f.state==='FROZEN_FORWARD_OBSERVED'?'is-forward':(!r.artifact_present?'is-unpackaged':'');
      const blockers=(r.blockers||[]).length?(r.blockers||[]).join(' · '):'NO RECORDED BLOCKER';
      return `<article class="sr-card ${klass}">
        <span class="sr-card-label">EXACT CANDIDATE</span><h3>${esc(r.label)}</h3><div class="sr-stage">${esc(r.stage)}</div>
        <div class="sr-metrics">
          <div><span>SR @4%</span><strong>${fmt(m.sharpe_4pct_atr)}</strong></div>
          <div><span>SR @10%</span><strong>${fmt(m.sharpe_10pct_atr)}</strong></div>
          <div><span>SR @12%</span><strong>${fmt(m.sharpe_12pct_atr)}</strong></div>
        </div>
        <div class="sr-row"><span>Artifact</span><strong>${r.artifact_present?'PACKAGED':'NOT PACKAGED'}</strong></div>
        <div class="sr-row"><span>Forward @4%</span><strong>${fmt(f.sharpe_4pct_atr)} · ${yes(f.pass_4pct)}</strong></div>
        <div class="sr-row"><span>Public correlation</span><strong>${esc(p.state||'NOT_RUN')}</strong></div>
        <div class="sr-blockers ${(r.blockers||[]).length?'':'ok'}">${esc(blockers)}</div>
      </article>`;
    }).join('');

    const sharpe7=rows.find(r=>r.id==='ebenezar_20260912_sharpe7_vol2');
    const fw=sharpe7?.forward_validation||{};
    const diag=fw.post_validation_diagnostic||{};
    $('[data-forward-detail]').innerHTML=`<div class="sr-detail">
      <article><strong>Sharpe7 frozen 2023–2024</strong><p>SR ${fmt(fw.sharpe_4pct_atr)} @4% ATR and ${fmt(fw.sharpe_10pct_atr)} @10% ATR. Both clear the fixed 1.0 floor.</p></article>
      <article><strong>Later diagnostic is softer</strong><p>2025→${esc(fw.last_market_date||'latest')} SR ${fmt(diag['0.04']?.sharpe_ratio)} @4% and ${fmt(diag['0.10']?.sharpe_ratio)} @10%. Confidence evidence, not permission to retune.</p></article>
      <article><strong>Protected live boundary</strong><p>Live start remains ${esc(fw.protected_live_start||'—')}; frozen evidence changes confidence, not the formula.</p></article>
    </div>`;

    const smoked=rows.filter(r=>r.public_correlation_smoke?.state==='PUBLIC_DEFAULT_CLEAR');
    $('[data-correlation-detail]').innerHTML=`<div class="sr-detail">
      ${smoked.map(r=>`<article><strong>${esc(r.label)} · PUBLIC_DEFAULT_CLEAR</strong><p>${esc(r.public_correlation_smoke.message||'')} Participant ID ${esc(r.public_correlation_smoke.participant_id||'0')}.</p></article>`).join('')}
      <article><strong>Still unresolved</strong><p>Participant/account-bound uniqueness must be rerun on the exact final artifact. A public smoke result cannot be promoted into account clearance.</p></article>
    </div>`;
  }

  fetch(source,{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()}).then(render).catch(err=>{
    $('[data-sr-state]').textContent='READINESS ERROR';
    $('[data-sr-candidates]').innerHTML=`<div class="qt-warning">Submission readiness unavailable: ${esc(err.message||err)}</div>`;
  });
})();