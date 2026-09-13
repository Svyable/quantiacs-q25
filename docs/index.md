---
title: Q25 Quantitative Research Lab
description: Evidence-aware crypto alpha research for Quantiacs Q25 — real strategy results, interactive analysis, causal controls, forward validation and auditable research artifacts.
---

<link rel="stylesheet" href="{{ '/assets/css/explorer.css' | relative_url }}">

<div class="q25-shell" data-q25-dashboard>
  <section class="q25-hero q25-hero-v2">
    <div class="q25-hero-grid">
      <div>
        <div class="q25-eyebrow">Q25 / quantitative research lab</div>
        <h1>See the whole strategy universe.<br><span>Then try to break it.</span></h1>
        <p class="q25-lede">A public, evidence-aware research system for the Quantiacs Crypto Top-10 Long contest. Every committed strategy cell, control, failure, development metric and validation result stays inspectable. The lab optimizes for information gained—not for a permanently rising backtest headline.</p>
        <div class="q25-actions">
          <a class="q25-button q25-button-primary" href="{{ '/explorer.html' | relative_url }}">Explore every strategy</a>
          <a class="q25-button" href="{{ '/backtest/' | relative_url }}">Portfolio backtest studio</a>
          <a class="q25-button" href="{{ '/METHODOLOGY_HEALTH.html' | relative_url }}">Methodology health</a>
          <a class="q25-button" href="https://github.com/Svyable/quantiacs-q25">Repository ↗</a>
        </div>
      </div>
      <aside class="q25-live-panel" aria-label="live evidence pulse">
        <div class="q25-live-head"><span class="q25-live-dot"></span> committed evidence</div>
        <div class="q25-live-campaign" data-bind="latest-campaign">loading…</div>
        <div class="q25-live-decision" data-bind="latest-decision">reading methodology health</div>
        <div class="q25-live-rule"></div>
        <div class="q25-live-row"><span>validation</span><strong data-bind="validation-state">loading…</strong></div>
        <div class="q25-live-row"><span>queue</span><strong data-bind="queue-state">loading…</strong></div>
        <div class="q25-live-row"><span>optimization</span><strong>vector, never mega-score</strong></div>
      </aside>
    </div>
    <div class="q25-status-row" aria-label="research status">
      <span class="q25-pill" data-bind="evidence-tier">evidence: loading…</span>
      <span class="q25-pill" data-bind="validation-state">validation: loading…</span>
      <span class="q25-pill" data-bind="queue-state">queue: loading…</span>
    </div>
  </section>

  <section class="qx-home-explorer" data-strategy-overview data-source="{{ '/data/strategy_matrix.json' | relative_url }}">
    <div class="qx-home-explorer-grid">
      <div>
        <div class="q25-kicker">Live strategy matrix</div>
        <h2>Stop browsing filenames. Analyze the evidence.</h2>
        <p>The repository already contains a machine-readable matrix of measured strategies, research/dev metrics, controls, campaign context and evidence state. The new explorer turns that data into a searchable, sortable, cross-metric research surface.</p>
        <div class="q25-actions">
          <a class="q25-button q25-button-primary" href="{{ '/explorer.html' | relative_url }}">Open strategy explorer</a>
          <a class="q25-button" href="{{ '/data/strategy_matrix.json' | relative_url }}">Raw matrix JSON</a>
        </div>
        <div class="qx-home-top" data-home-top>Loading strongest measured base cells…</div>
      </div>
      <div class="qx-home-stats" aria-label="strategy matrix summary">
        <article><span>Measured rows</span><strong data-home-kpi="rows">—</strong></article>
        <article><span>Families</span><strong data-home-kpi="families">—</strong></article>
        <article><span>Campaigns / contexts</span><strong data-home-kpi="campaigns">—</strong></article>
        <article><span>Complete rows</span><strong data-home-kpi="complete">—</strong></article>
        <article><span>Best dev SR12</span><strong data-home-kpi="best">—</strong></article>
        <article><span>Rows ≥ 1.0</span><strong data-home-kpi="above">—</strong></article>
      </div>
    </div>
  </section>

  <section class="q25-section q25-section-tight">
    <div class="q25-section-head">
      <div><div class="q25-kicker">Two analysis modes</div><h2>Cross-strategy discovery + portfolio-level truth</h2></div>
      <p>Use the matrix explorer to compare strategy cells. Use the backtest studio to inspect a promoted portfolio packet through time. One is cross-sectional; the other is path-dependent.</p>
    </div>
    <div class="q25-two-col">
      <article class="q25-card q25-feature-card q25-card-accent">
        <span class="q25-card-label">Strategy Explorer</span>
        <h3>Compare every measured result</h3>
        <p>Filter by campaign, family, mode, status and evidence lane. Change X/Y metrics, inspect individual rows, rank campaign contexts, review family decisions and export the filtered evidence to CSV.</p>
        <div class="q25-chip-row"><span>interactive scatter</span><span>sortable ledger</span><span>family decisions</span><span>CSV export</span></div>
        <div class="q25-actions"><a class="q25-button q25-button-primary" href="{{ '/explorer.html' | relative_url }}">Launch explorer</a></div>
      </article>
      <article class="q25-card q25-feature-card">
        <span class="q25-card-label">Backtest Studio</span>
        <h3>Interrogate the full return path</h3>
        <p>Inspect strategy equity versus Crypto10, relative score, drawdown, rolling volatility, Sharpe path, mean return, daily snapshots and monthly seasonality from a committed backtest evidence packet.</p>
        <div class="q25-chip-row"><span>equity</span><span>Crypto10</span><span>drawdown</span><span>score</span><span>seasonality</span></div>
        <div class="q25-actions"><a class="q25-button" href="{{ '/backtest/' | relative_url }}">Open backtest studio</a></div>
      </article>
    </div>
  </section>

  <section class="q25-section">
    <div class="q25-section-head">
      <div><div class="q25-kicker">Five feedback channels, zero mega-score</div><h2>The frontier is allowed to say “nothing survives.”</h2></div>
      <p>Falsification, causal support, economics, promotion readiness and decision resolution are separate from validation depth and implementation health. A strategy can be causally interesting and still be economically dead.</p>
    </div>
    <div class="q25-metric-grid">
      <article class="q25-card q25-metric-card q25-metric-card-featured"><span class="q25-metric-label">Latest measured</span><strong class="q25-metric-value" data-bind="latest-campaign">—</strong><small data-bind="latest-decision">loading committed evidence</small></article>
      <article class="q25-card q25-metric-card"><span class="q25-metric-label">Falsification coverage</span><strong class="q25-metric-value" data-bind="falsification-ratio">—</strong><div class="q25-progress"><span data-bar="falsification"></span></div><small>central + ablation + destructive falsifier</small></article>
      <article class="q25-card q25-metric-card"><span class="q25-metric-label">Causal support</span><strong class="q25-metric-value" data-bind="causal-ratio">—</strong><div class="q25-progress"><span data-bar="causal"></span></div><small>central parent beats matched controls</small></article>
      <article class="q25-card q25-metric-card"><span class="q25-metric-label">Economic survival</span><strong class="q25-metric-value" data-bind="economic-ratio">—</strong><div class="q25-progress"><span data-bar="economic"></span></div><small>best base clears predefined floor</small></article>
      <article class="q25-card q25-metric-card"><span class="q25-metric-label">Promotion-ready</span><strong class="q25-metric-value" data-bind="promotion-ratio">—</strong><div class="q25-progress"><span data-bar="promotion"></span></div><small>economics ∩ causal support; still pre-validation</small></article>
      <article class="q25-card q25-metric-card"><span class="q25-metric-label">Evidence depth debt</span><strong class="q25-metric-value" data-bind="matrix-lag">—</strong><small data-bind="matrix-lag-detail">campaigns since full matrix</small></article>
    </div>
  </section>

  <section class="q25-section q25-snapshot-section">
    <div class="q25-section-head">
      <div><div class="q25-kicker">Current measured read</div><h2>The site shows failed ideas on purpose</h2></div>
      <p>These are frozen development or forward-validation reads already committed by the lab. “Supported” means a mechanism beat matched controls; it does not mean it passed the economic or contest gates.</p>
    </div>
    <div class="q25-snapshot-grid">
      <article class="q25-snapshot-card q25-snapshot-lead"><div class="q25-snapshot-top"><span>Frontier-K</span><strong>0.782</strong></div><h3>Nearest-peer detachment</h3><p>63-day parent beat both destructive controls but missed the fixed development floor.</p><div class="q25-verdict q25-verdict-warn">KILL_WEAK_ALPHA</div><small>Causal direction: yes · robust floor: no</small></article>
      <article class="q25-snapshot-card"><div class="q25-snapshot-top"><span>Frontier-L</span><strong>0.614</strong></div><h3>Dollar-volume share migration</h3><p>The strongest recent non-graph family beat both controls and still lacked enough economics.</p><div class="q25-verdict q25-verdict-warn">KILL_WEAK_ALPHA</div><small>Causal support: yes · economics: insufficient</small></article>
      <article class="q25-snapshot-card"><div class="q25-snapshot-top"><span>Frontier-F</span><strong>0.944</strong></div><h3>Conditional payoff posterior</h3><p>The best base cell was not the preregistered central mechanism; its pooled-state ablation was stronger.</p><div class="q25-verdict q25-verdict-bad">FALSIFIED</div><small>Strong-looking cell ≠ supported thesis</small></article>
      <article class="q25-snapshot-card q25-snapshot-dark"><div class="q25-snapshot-top"><span>Forward gate</span><strong>0.314</strong></div><h3>Topology migration</h3><p>The former development leader failed its frozen 2023–2024 forward test at 12% ATR-linked cost.</p><div class="q25-verdict q25-verdict-bad">FAIL_FORWARD_GATE</div><small>Spent fold. No rescue tuning.</small></article>
    </div>
  </section>

  <section class="q25-section">
    <div class="q25-section-head">
      <div><div class="q25-kicker">Contest contract</div><h2>The research UI keeps the Q25 rules visible</h2></div>
      <p>Eligibility and payout rules shape what “good” means. They are not retrofitted after a strategy looks attractive.</p>
    </div>
    <div class="q25-three-col">
      <article class="q25-card"><h3>Universe + direction</h3><p>Long-only allocations to the liquid Crypto Top 10. Manual asset selection is not the research model.</p></article>
      <article class="q25-card"><h3>Eligibility + costs</h3><p>Submission-time in-sample Sharpe must exceed 1.0, and position changes are evaluated with the contest’s ATR-linked transaction cost model.</p></article>
      <article class="q25-card"><h3>Winning metric</h3><p>Eligible strategies are ranked on out-of-sample contest-period Sharpe. Live payouts then use the volatility-normalized relative-performance model against Crypto10.</p></article>
    </div>
  </section>

  <section class="q25-section">
    <div class="q25-section-head">
      <div><div class="q25-kicker">Recursive research loop</div><h2>Increase information per look, not looks per idea</h2></div>
      <p>Every campaign is expected to produce traceable evidence even when zero strategies survive.</p>
    </div>
    <div class="q25-loop">
      <div><span>01</span><strong>Map</strong><small>nearest incumbent + novelty axes</small></div>
      <div><span>02</span><strong>Preregister</strong><small>freeze mechanism, grid, controls</small></div>
      <div><span>03</span><strong>Audit</strong><small>causality, liquidity, cleaner, replay</small></div>
      <div><span>04</span><strong>Measure</strong><small>same folds + same cost ladder</small></div>
      <div><span>05</span><strong>Destroy</strong><small>ablation + mechanism falsifier</small></div>
      <div><span>06</span><strong>Validate</strong><small>frozen chronology, no rescue tuning</small></div>
      <div><span>07</span><strong>Rewrite</strong><small>new evidence supersedes old narrative</small></div>
    </div>
  </section>

  <section class="q25-section q25-section-muted">
    <div class="q25-section-head"><div><div class="q25-kicker">Evidence lanes</div><h2>Keep incompatible evidence separate</h2></div></div>
    <div class="q25-three-col">
      <article class="q25-card"><h3>Development</h3><p>Research/dev folds, cost ladder, controls and implementation integrity. Useful for selection pressure; never a production claim.</p></article>
      <article class="q25-card"><h3>Forward validation</h3><p>Frozen candidate, frozen chronological fold, no parameter switching after observation. Later validation may invalidate the development story.</p></article>
      <article class="q25-card"><h3>Authenticated preclear</h3><p>Participant-bound correlation and submission checks stay separate from public research evidence and are never inferred from local diagnostics.</p></article>
    </div>
  </section>

  <section class="q25-section q25-links-section">
    <div class="q25-section-head"><div><div class="q25-kicker">Source of truth</div><h2>Drill into evidence, not decoration</h2></div></div>
    <div class="q25-link-grid">
      <a href="{{ '/explorer.html' | relative_url }}"><strong>Strategy Explorer</strong><span>all measured rows, interactive cross-metric charting, filters and export</span></a>
      <a href="{{ '/backtest/' | relative_url }}"><strong>Backtest Studio</strong><span>equity, Crypto10, drawdown, risk, score and seasonality</span></a>
      <a href="{{ '/METHODOLOGY_HEALTH.html' | relative_url }}"><strong>Methodology Health</strong><span>recursive telemetry + validation reconciliation</span></a>
      <a href="{{ '/REPRODUCIBILITY_HEALTH.html' | relative_url }}"><strong>Reproducibility Health</strong><span>replay decision stability + context drift</span></a>
      <a href="{{ '/RESEARCH_MATRIX.html' | relative_url }}"><strong>Research Matrix</strong><span>comparable evidence lanes and campaign packets</span></a>
      <a href="{{ '/EVIDENCE_MODEL.html' | relative_url }}"><strong>Evidence Model</strong><span>strategy quality ≠ evidence quality ≠ implementation health</span></a>
      <a href="{{ '/STRATEGY_ATLAS.html' | relative_url }}"><strong>Strategy Atlas</strong><span>mechanism map, incumbents, controls and originality context</span></a>
      <a href="{{ '/RESEARCH_METHOD.html' | relative_url }}"><strong>Research Method</strong><span>chronology, costs, controls and promotion boundaries</span></a>
      <a href="https://github.com/Svyable/quantiacs-q25"><strong>Repository ↗</strong><span>strategies, evidence packets, experiments, workflows and generated data</span></a>
    </div>
  </section>

  <div class="q25-footnote"><strong>Machine-readable:</strong> <a href="{{ '/data/methodology_health.json' | relative_url }}">methodology_health.json</a> · <a href="{{ '/data/reproducibility_health.json' | relative_url }}">reproducibility_health.json</a> · <a href="{{ '/data/strategy_matrix.json' | relative_url }}">strategy_matrix.json</a> · <a href="{{ '/data/backtest_dashboard.json' | relative_url }}">backtest_dashboard.json</a>. Missing evidence stays missing.</div>
</div>

<script src="{{ '/assets/js/dashboard.js' | relative_url }}" defer></script>
<script src="{{ '/assets/js/matrix-explorer.js' | relative_url }}" defer></script>
