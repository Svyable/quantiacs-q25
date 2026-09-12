---
title: Q25 Backtest Studio
description: Interactive, evidence-aware Q25 backtest diagnostics for strategy equity, Crypto10 benchmark, relative score, drawdown, rolling risk, and monthly returns.
permalink: /backtest/
---

<link rel="stylesheet" href="{{ '/assets/css/backtest.css' | relative_url }}">

<div class="q25-shell bt-studio" data-backtest-studio data-data-url="{{ '/data/backtest_dashboard.json' | relative_url }}">
  <section class="bt-hero">
    <div>
      <div class="q25-eyebrow">Q25 / evidence-aware backtest studio</div>
      <h1>See the strategy the way a research desk should.</h1>
      <p>Interactive equity, Crypto10 benchmark, relative score, underwater drawdown, rolling risk, and monthly return diagnostics. Every displayed number is read from a committed backtest packet; missing evidence remains visibly missing.</p>
    </div>
    <div class="bt-hero-meta">
      <span class="bt-state" data-bind="status">loading</span>
      <span data-bind="period">period —</span>
      <span data-bind="generated">generated —</span>
    </div>
  </section>

  <nav class="bt-subnav" aria-label="Backtest studio navigation">
    <a href="{{ '/' | relative_url }}">Research lab</a>
    <a class="is-active" href="{{ '/backtest/' | relative_url }}">Backtest studio</a>
    <a href="{{ '/RESEARCH_MATRIX.html' | relative_url }}">Research matrix</a>
    <a href="https://github.com/Svyable/quantiacs-q25">Repository</a>
  </nav>

  <section class="bt-kpis" aria-label="Backtest key metrics">
    <article><span>Sharpe</span><strong data-metric="sharpe">—</strong><small>annualized</small></article>
    <article><span>Total return</span><strong data-metric="total_return">—</strong><small>test period</small></article>
    <article><span>Mean return</span><strong data-metric="mean_return">—</strong><small>annualized</small></article>
    <article><span>Volatility</span><strong data-metric="volatility">—</strong><small>annualized</small></article>
    <article><span>Max drawdown</span><strong data-metric="max_drawdown">—</strong><small>peak to trough</small></article>
    <article><span>Avg turnover</span><strong data-metric="avg_turnover">—</strong><small>daily</small></article>
  </section>

  <section class="bt-panel bt-main-panel">
    <header class="bt-panel-head">
      <div><span class="bt-kicker">Performance</span><h2 data-bind="chart-title">Strategy equity vs Crypto10</h2></div>
      <div class="bt-controls" role="group" aria-label="Chart view">
        <button type="button" class="is-active" data-view="equity">Equity</button>
        <button type="button" data-view="score">Relative score</button>
        <button type="button" data-view="drawdown">Drawdown</button>
        <button type="button" data-view="volatility">Rolling vol</button>
      </div>
    </header>
    <div class="bt-chart-shell">
      <svg class="bt-chart" data-chart="primary" role="img" aria-label="Interactive backtest chart"></svg>
      <div class="bt-tooltip" data-tooltip hidden></div>
      <div class="bt-empty" data-empty hidden>
        <strong>No committed time-series packet yet.</strong>
        <span>Run <code>python scripts/build_backtest_dashboard.py --input &lt;stats.csv&gt;</code> and commit the generated JSON. The page will populate without changing its markup.</span>
      </div>
    </div>
    <footer class="bt-chart-footer">
      <div class="bt-legend" data-legend><span><i class="strategy"></i>Strategy</span><span><i class="benchmark"></i>Crypto10</span></div>
      <div class="bt-ranges" role="group" aria-label="Chart range"><button type="button" data-range="1y">1Y</button><button type="button" data-range="3y">3Y</button><button type="button" class="is-active" data-range="all">All</button></div>
    </footer>
  </section>

  <section class="bt-grid-two">
    <article class="bt-panel">
      <header class="bt-panel-head"><div><span class="bt-kicker">Underwater</span><h2>Drawdown depth</h2></div><strong class="bt-inline-stat" data-bind="worst-dd">—</strong></header>
      <svg class="bt-mini-chart" data-chart="drawdown" role="img" aria-label="Strategy drawdown chart"></svg>
    </article>
    <article class="bt-panel bt-scorecard">
      <header class="bt-panel-head"><div><span class="bt-kicker">Q25 live model</span><h2>Volatility-normalized relative score</h2></div></header>
      <div class="bt-score-number" data-bind="relative-score">—</div>
      <p>Strategy equity divided by <code>max(Crypto10 equity, 1)</code> after applying the committed live-period scaling assumptions.</p>
      <dl>
        <div><dt>Strategy 10% vol scale</dt><dd data-bind="strategy-scale">—</dd></div>
        <div><dt>Crypto10 10% vol scale</dt><dd data-bind="benchmark-scale">—</dd></div>
        <div><dt>Latest strategy equity</dt><dd data-bind="strategy-equity">—</dd></div>
        <div><dt>Latest benchmark equity</dt><dd data-bind="benchmark-equity">—</dd></div>
      </dl>
    </article>
  </section>

  <section class="bt-panel">
    <header class="bt-panel-head"><div><span class="bt-kicker">Seasonality</span><h2>Monthly strategy returns</h2></div><span class="bt-muted">hover cells for exact return</span></header>
    <div class="bt-heatmap-wrap" data-heatmap></div>
  </section>

  <section class="bt-grid-two" style="margin-top:1.1rem">
    <article class="bt-panel">
      <header class="bt-panel-head"><div><span class="bt-kicker">Exposure</span><h2>Trading diagnostics</h2></div></header>
      <dl class="bt-diagnostics">
        <div><dt>Bias</dt><dd data-metric="bias">—</dd></div><div><dt>Avg instruments</dt><dd data-metric="instruments">—</dd></div><div><dt>Avg holding time</dt><dd data-metric="avg_holding_time">—</dd></div><div><dt>Observations</dt><dd data-bind="observations">—</dd></div>
      </dl>
    </article>
    <article class="bt-panel">
      <header class="bt-panel-head"><div><span class="bt-kicker">Evidence</span><h2>What this view actually proves</h2></div></header>
      <p class="bt-evidence-note" data-bind="evidence-note">Loading packet provenance…</p>
      <div class="bt-provenance"><span>source</span><code data-bind="source-path">—</code><span>commit</span><code data-bind="source-commit">—</code></div>
    </article>
  </section>

  <div class="bt-footnote">This is a visualization layer, not a second backtester. It renders committed strategy statistics and does not infer missing performance. Q25 eligibility, correlation, submission and live-period results remain separate evidence lanes.</div>
</div>

<script src="{{ '/assets/js/backtest.js' | relative_url }}" defer></script>
