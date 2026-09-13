---
title: Q25 Strategy Explorer
description: Interactive, evidence-aware analysis of every measured Q25 strategy cell, campaign, family, control and validation result committed to the research matrix.
---

<link rel="stylesheet" href="{{ '/assets/css/explorer.css' | relative_url }}">

<div class="qx-shell" data-matrix-explorer data-source="{{ '/data/strategy_matrix.json' | relative_url }}">
  <section class="qx-hero">
    <div>
      <div class="qx-eyebrow">Q25 / evidence matrix explorer</div>
      <h1>Every measured strategy.<br><span>Every metric. No cherry-picking.</span></h1>
      <p>Explore the committed Q25 research matrix across campaigns, mechanism families, base strategies, ablations, falsifiers and controls. The charts below are generated in your browser from the repository’s machine-readable evidence—not from hand-entered headline numbers.</p>
      <div class="qx-actions">
        <a class="qx-button qx-button-primary" href="{{ '/' | relative_url }}">Research lab</a>
        <a class="qx-button" href="{{ '/backtest/' | relative_url }}">Backtest studio</a>
        <a class="qx-button" href="{{ '/data/strategy_matrix.json' | relative_url }}">Raw matrix JSON</a>
        <a class="qx-button" href="https://github.com/Svyable/quantiacs-q25">Repository ↗</a>
      </div>
    </div>
    <aside class="qx-rule-card">
      <strong>Read the lanes correctly</strong>
      <p>Development evidence, forward validation, historical-core evidence and implementation health stay separate. A high development Sharpe is not a contest result, and an implementation failure is not a zero-return strategy.</p>
      <div class="qx-rule-row"><span>Q25 eligibility floor</span><b>IS Sharpe &gt; 1.0</b></div>
      <div class="qx-rule-row"><span>Portfolio</span><b>long-only / liquid top 10</b></div>
      <div class="qx-rule-row"><span>Contest rank</span><b>out-of-sample Sharpe</b></div>
    </aside>
  </section>

  <section class="qx-kpis" aria-label="filtered strategy metrics">
    <article><span>Rows in view</span><strong data-kpi="rows">—</strong><small data-kpi-detail="rows">loading matrix</small></article>
    <article><span>Families</span><strong data-kpi="families">—</strong><small data-kpi-detail="families">unique mechanism labels</small></article>
    <article><span>Complete evidence</span><strong data-kpi="complete">—</strong><small data-kpi-detail="complete">status = COMPLETE</small></article>
    <article><span>Best dev SR @ cost</span><strong data-kpi="best-dev">—</strong><small data-kpi-detail="best-dev">best observed dev_sharpe_12</small></article>
    <article><span>Above 1.0 floor</span><strong data-kpi="above-floor">—</strong><small data-kpi-detail="above-floor">development cells only</small></article>
    <article><span>Campaigns / lanes</span><strong data-kpi="campaigns">—</strong><small data-kpi-detail="campaigns">distinct evidence contexts</small></article>
  </section>

  <section class="qx-panel qx-controls-panel">
    <div class="qx-panel-head">
      <div><span class="qx-kicker">Slice the evidence</span><h2>Filter before you rank</h2></div>
      <div class="qx-filter-count" data-filter-count>Loading…</div>
    </div>
    <div class="qx-controls">
      <label class="qx-search"><span>Search</span><input type="search" data-filter="search" placeholder="strategy, family, campaign…" autocomplete="off"></label>
      <label><span>Campaign / lane</span><select data-filter="campaign"><option value="">All</option></select></label>
      <label><span>Family</span><select data-filter="family"><option value="">All</option></select></label>
      <label><span>Mode</span><select data-filter="mode"><option value="">All</option></select></label>
      <label><span>Status</span><select data-filter="status"><option value="">All</option></select></label>
      <label><span>Evidence lane</span><select data-filter="lane"><option value="">All</option></select></label>
      <label class="qx-check"><input type="checkbox" data-filter="base-only"><span>Base strategies only</span></label>
      <button class="qx-button qx-button-small" type="button" data-reset>Reset</button>
      <button class="qx-button qx-button-small" type="button" data-export>Export filtered CSV</button>
    </div>
  </section>

  <section class="qx-grid qx-grid-main">
    <article class="qx-panel qx-chart-panel">
      <div class="qx-panel-head qx-panel-head-wrap">
        <div><span class="qx-kicker">Cross-metric map</span><h2>What are you paying for the Sharpe?</h2></div>
        <div class="qx-metric-selectors">
          <label><span>X</span><select data-axis="x"></select></label>
          <label><span>Y</span><select data-axis="y"></select></label>
        </div>
      </div>
      <p class="qx-subtle">Each point is a committed strategy/result row. Hover for exact values; click a point to inspect all available metrics and evidence metadata.</p>
      <div class="qx-chart-shell">
        <svg data-chart="scatter" role="img" aria-label="interactive strategy metric scatter plot"></svg>
        <div class="qx-tooltip" data-tooltip hidden></div>
        <div class="qx-chart-empty" data-chart-empty hidden>No rows in the current filter have both selected metrics.</div>
      </div>
      <div class="qx-legend"><span class="base">base</span><span class="control">control</span><span class="ablation">ablation</span><span class="falsifier">falsifier</span><span class="other">other</span></div>
    </article>

    <aside class="qx-panel qx-inspector" data-inspector>
      <div class="qx-panel-head"><div><span class="qx-kicker">Selected row</span><h2 data-inspect="id">Click a point or row</h2></div></div>
      <div class="qx-inspector-meta" data-inspect="meta">The inspector preserves the row’s exact evidence lane and metric names.</div>
      <div class="qx-inspector-grid" data-inspect="metrics"></div>
      <div class="qx-inspector-extra" data-inspect="extra"></div>
    </aside>
  </section>

  <section class="qx-grid qx-grid-secondary">
    <article class="qx-panel">
      <div class="qx-panel-head"><div><span class="qx-kicker">Campaign frontier</span><h2>Best observed metric by context</h2></div><span class="qx-badge" data-campaign-metric-label>dev_sharpe_12</span></div>
      <div class="qx-bar-chart" data-chart="campaign-bars"></div>
    </article>
    <article class="qx-panel">
      <div class="qx-panel-head"><div><span class="qx-kicker">Decision ledger</span><h2>Family adjudication</h2></div></div>
      <div class="qx-family-board" data-family-board></div>
    </article>
  </section>

  <section class="qx-panel qx-table-panel">
    <div class="qx-panel-head qx-panel-head-wrap">
      <div><span class="qx-kicker">Strategy ledger</span><h2>Sortable committed results</h2></div>
      <p class="qx-subtle">Click any column header to sort. Click a row to inspect every available metric. Nulls stay null.</p>
    </div>
    <div class="qx-table-wrap">
      <table class="qx-table">
        <thead>
          <tr>
            <th data-sort="id">Strategy</th>
            <th data-sort="campaign">Campaign / context</th>
            <th data-sort="family">Family</th>
            <th data-sort="mode">Mode</th>
            <th data-sort="status">Status</th>
            <th data-sort="dev_sharpe_12">Dev SR 12</th>
            <th data-sort="research_sharpe_12">Research SR 12</th>
            <th data-sort="dev_cagr_12">Dev CAGR 12</th>
            <th data-sort="dev_sortino_12">Dev Sortino</th>
            <th data-sort="worst_drawdown_12">Worst DD</th>
            <th data-sort="mean_turnover_12">Turnover</th>
            <th data-sort="selection_score">Selection</th>
          </tr>
        </thead>
        <tbody data-table-body><tr><td colspan="12">Loading committed evidence…</td></tr></tbody>
      </table>
    </div>
    <div class="qx-table-footer"><span data-table-summary>—</span><div><button type="button" class="qx-button qx-button-small" data-page="prev">Previous</button><span data-page-label>—</span><button type="button" class="qx-button qx-button-small" data-page="next">Next</button></div></div>
  </section>

  <section class="qx-panel qx-method-note">
    <div><span class="qx-kicker">Evidence discipline</span><h2>Metrics are not interchangeable evidence.</h2></div>
    <p>This explorer intentionally exposes research/dev metrics, failure states, controls and campaign context together while keeping their labels intact. It does not recast development results as forward validation, does not turn missing values into zeroes, and does not promote strategies merely because a chart point looks attractive.</p>
    <div class="qx-actions">
      <a class="qx-button" href="{{ '/EVIDENCE_MODEL.html' | relative_url }}">Evidence model</a>
      <a class="qx-button" href="{{ '/RESEARCH_MATRIX.html' | relative_url }}">Research matrix</a>
      <a class="qx-button" href="{{ '/RESEARCH_METHOD.html' | relative_url }}">Research method</a>
      <a class="qx-button" href="{{ '/METHODOLOGY_HEALTH.html' | relative_url }}">Methodology health</a>
    </div>
  </section>

  <div class="qx-footnote">Source: <code>docs/data/strategy_matrix.json</code>. The browser computes every view from committed repository data at page load.</div>
</div>

<script src="{{ '/assets/js/matrix-explorer.js' | relative_url }}" defer></script>
