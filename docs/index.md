---
title: Q25 Research Terminal
description: Evidence-aware quantitative research terminal for the Quantiacs Q25 Crypto Top-10 contest.
---

<link rel="stylesheet" href="{{ '/assets/css/terminal.css' | relative_url }}">

<div class="qt-shell" data-q25-terminal data-matrix-source="{{ '/data/strategy_matrix.json' | relative_url }}" data-method-source="{{ '/data/methodology_health.json' | relative_url }}">
  <header class="qt-topbar">
    <a class="qt-brand" href="{{ '/' | relative_url }}" aria-label="Q25 terminal home"><span class="qt-brand-mark">Q25</span><span>RESEARCH TERMINAL</span></a>
    <nav class="qt-nav" aria-label="Research surfaces">
      <a href="{{ '/explorer.html' | relative_url }}">Explorer</a>
      <a href="{{ '/backtest/' | relative_url }}">Backtest</a>
      <a href="{{ '/RESEARCH_MATRIX.html' | relative_url }}">Matrix</a>
      <a href="{{ '/METHODOLOGY_HEALTH.html' | relative_url }}">Methodology</a>
      <a href="https://github.com/Svyable/quantiacs-q25">GitHub ↗</a>
    </nav>
    <div class="qt-feed"><span class="qt-feed-dot"></span><span data-terminal-state>LOADING MATRIX</span></div>
  </header>

  <section class="qt-hero">
    <div class="qt-hero-copy">
      <div class="qt-overline">CRYPTO TOP-10 · LONG ONLY · EVIDENCE BEFORE NARRATIVE</div>
      <h1>Find what survives.<br><span>Expose what only looked good.</span></h1>
      <p>One terminal for the committed Q25 research record: development economics, research-to-dev decay, transaction-cost fragility, destructive controls, family adjudication, evidence completeness and frozen failures. Missing evidence stays missing.</p>
      <div class="qt-hero-actions">
        <a class="qt-primary" href="#leaderboard">Open live leaderboard</a>
        <a href="{{ '/explorer.html' | relative_url }}">Deep matrix explorer</a>
        <a href="{{ '/EVIDENCE_MODEL.html' | relative_url }}">Evidence contract</a>
      </div>
    </div>
    <div class="qt-hero-terminal" aria-label="live terminal summary">
      <div class="qt-terminal-head"><span>MARKET / RESEARCH PULSE</span><span data-asof>matrix commit</span></div>
      <div class="qt-terminal-grid">
        <div><span>ROWS</span><strong data-kpi="rows">—</strong></div>
        <div><span>BASE CELLS</span><strong data-kpi="bases">—</strong></div>
        <div><span>DEV SR12 ≥ 1</span><strong data-kpi="floor">—</strong></div>
        <div><span>SURVIVING FAMILIES</span><strong data-kpi="survivors">—</strong></div>
        <div><span>COMPLETE EVIDENCE</span><strong data-kpi="complete">—</strong></div>
        <div><span>CAMPAIGNS</span><strong data-kpi="campaigns">—</strong></div>
      </div>
      <div class="qt-terminal-callout">
        <span>BEST MEASURED DEV SR12</span>
        <strong data-kpi="best">—</strong>
        <small data-kpi-detail="best">No row selected yet</small>
      </div>
    </div>
  </section>

  <section class="qt-rulebar" aria-label="contest contract">
    <div><span>UNIVERSE</span><strong>Crypto Top 10</strong></div>
    <div><span>DIRECTION</span><strong>Long only</strong></div>
    <div><span>SUBMISSION FLOOR</span><strong>IS Sharpe &gt; 1.0</strong></div>
    <div><span>RANKING</span><strong>Contest OOS Sharpe</strong></div>
    <div><span>RESEARCH RULE</span><strong>Controls can kill a pretty backtest</strong></div>
  </section>

  <section class="qt-section qt-command" aria-label="matrix filters">
    <div class="qt-section-heading">
      <div><span class="qt-kicker">CONTROL SURFACE</span><h2>Interrogate the matrix</h2></div>
      <div class="qt-result-count" data-filter-count>— rows</div>
    </div>
    <div class="qt-controls">
      <label class="qt-search"><span>SEARCH</span><input data-filter="search" type="search" placeholder="strategy, family, campaign…" autocomplete="off"></label>
      <label><span>CAMPAIGN</span><select data-filter="campaign"><option value="">All</option></select></label>
      <label><span>FAMILY</span><select data-filter="family"><option value="">All</option></select></label>
      <label><span>MODE</span><select data-filter="mode"><option value="">All</option></select></label>
      <label><span>STATUS</span><select data-filter="status"><option value="">All</option></select></label>
      <button type="button" class="qt-reset" data-action="reset">RESET</button>
    </div>
  </section>

  <section class="qt-section qt-grid-2 qt-analysis-row">
    <article class="qt-panel qt-panel-chart">
      <div class="qt-panel-head">
        <div><span class="qt-kicker">EVIDENCE STABILITY</span><h2>Research → development</h2></div>
        <div class="qt-legend"><span><i class="base"></i>base</span><span><i class="control"></i>control</span><span><i class="other"></i>other</span></div>
      </div>
      <p class="qt-panel-note">Each point compares the same row’s research SR@12% with development SR@12%. The diagonal is stability—not a promotion threshold.</p>
      <div class="qt-chart-shell"><svg class="qt-chart" data-chart="stability" role="img" aria-label="Research versus development Sharpe scatter"></svg><div class="qt-tooltip" data-tooltip hidden></div></div>
    </article>

    <article class="qt-panel qt-screening">
      <div class="qt-panel-head"><div><span class="qt-kicker">SCREENING FUNNEL</span><h2>Where candidates disappear</h2></div></div>
      <p class="qt-panel-note">This is a descriptive screen, not a submission claim. Family adjudication remains separate from strategy economics and evidence depth.</p>
      <div class="qt-funnel" data-funnel></div>
      <div class="qt-warning" data-funnel-note>Loading family decisions…</div>
    </article>
  </section>

  <section class="qt-section qt-grid-2 qt-analysis-row">
    <article class="qt-panel">
      <div class="qt-panel-head">
        <div><span class="qt-kicker">COST FRAGILITY</span><h2>Sharpe lost at the 12% cost rung</h2></div>
        <span class="qt-badge">DEV SR0 − DEV SR12</span>
      </div>
      <p class="qt-panel-note">Largest measured cost drag among the current filtered rows. Missing cost pairs are excluded rather than imputed.</p>
      <div class="qt-bars" data-chart="cost-drag"></div>
    </article>

    <article class="qt-panel">
      <div class="qt-panel-head"><div><span class="qt-kicker">ECONOMIC EFFICIENCY</span><h2>Sharpe vs turnover Pareto frontier</h2></div><span class="qt-badge">BASE CELLS</span></div>
      <p class="qt-panel-note">Descriptive Pareto set: higher development SR@12% and lower turnover. It does not override controls, validation, or implementation health.</p>
      <div class="qt-chart-shell qt-chart-short"><svg class="qt-chart" data-chart="pareto" role="img" aria-label="Sharpe versus turnover Pareto chart"></svg></div>
    </article>
  </section>

  <section class="qt-section" id="leaderboard">
    <div class="qt-section-heading">
      <div><span class="qt-kicker">LIVE STRATEGY LEDGER</span><h2>Every measured row, with the failure modes beside the headline</h2></div>
      <div class="qt-ledger-tools">
        <label><span>SORT</span><select data-sort-select>
          <option value="dev_sharpe_12">Dev SR12</option>
          <option value="research_sharpe_12">Research SR12</option>
          <option value="stability">Research→Dev stability</option>
          <option value="cost_drag">Lowest cost drag</option>
          <option value="mean_turnover_12">Lowest turnover</option>
          <option value="worst_drawdown_12">Best drawdown</option>
          <option value="selection_score">Selection score</option>
        </select></label>
        <button type="button" data-action="export">EXPORT CSV</button>
      </div>
    </div>
    <div class="qt-ledger-wrap">
      <table class="qt-ledger">
        <thead><tr><th>#</th><th>Strategy</th><th>Campaign</th><th>Mode</th><th>Family decision</th><th>Dev SR12</th><th>Research SR12</th><th>Δ Dev−Research</th><th>Cost drag</th><th>Turnover</th><th>Worst DD</th><th>Evidence</th></tr></thead>
        <tbody data-ledger-body><tr><td colspan="12">Loading matrix…</td></tr></tbody>
      </table>
    </div>
    <div class="qt-ledger-footer"><span data-ledger-caption>—</span><button type="button" data-action="show-more">SHOW MORE</button></div>
  </section>

  <section class="qt-section qt-grid-2 qt-analysis-row">
    <article class="qt-panel">
      <div class="qt-panel-head"><div><span class="qt-kicker">FAMILY ADJUDICATION</span><h2>Mechanisms, not filenames</h2></div></div>
      <div class="qt-decision-summary" data-decision-summary></div>
      <div class="qt-family-board" data-family-board></div>
    </article>
    <article class="qt-panel">
      <div class="qt-panel-head"><div><span class="qt-kicker">CAMPAIGN TAPE</span><h2>Best measured base cell by campaign</h2></div></div>
      <p class="qt-panel-note">Campaign bars show economics only. A high bar can still belong to a falsified family.</p>
      <div class="qt-campaign-tape" data-campaign-tape></div>
    </article>
  </section>

  <section class="qt-section qt-inspector" data-inspector>
    <div class="qt-inspector-empty"><span class="qt-kicker">ROW INSPECTOR</span><h2>Click a ledger row or chart point.</h2><p>The inspector keeps economics, evidence provenance and family adjudication visible together without collapsing them into one score.</p></div>
  </section>

  <section class="qt-section qt-principles">
    <div><span class="qt-kicker">THREE AXES</span><h2>What this terminal refuses to collapse</h2></div>
    <div class="qt-principle-grid">
      <article><strong>01</strong><h3>Strategy quality</h3><p>Sharpe, CAGR, Sortino, Calmar, drawdown, turnover, cost sensitivity and residual contribution where measured.</p></article>
      <article><strong>02</strong><h3>Evidence quality</h3><p>Development, validation, diagnostic and authenticated evidence are distinct. A good dev result is not validation.</p></article>
      <article><strong>03</strong><h3>Implementation health</h3><p>Causality, liquid-only constraints, cleaner parity, bounded replay and runtime stay separate from economic outcomes.</p></article>
    </div>
  </section>

  <footer class="qt-footer">
    <div><strong>Q25 Research Terminal</strong><span>Public evidence surface for Svyable/quantiacs-q25.</span></div>
    <div class="qt-footer-links"><a href="{{ '/explorer.html' | relative_url }}">Explorer</a><a href="{{ '/RESEARCH_MATRIX.html' | relative_url }}">Research Matrix</a><a href="{{ '/STRATEGY_ATLAS.html' | relative_url }}">Strategy Atlas</a><a href="{{ '/REPRODUCIBILITY_HEALTH.html' | relative_url }}">Reproducibility</a></div>
  </footer>
</div>

<script src="{{ '/assets/js/terminal.js' | relative_url }}" defer></script>
