---
title: Q25 Contest Cookbook
description: A contest-specific research and implementation guide for Quantiacs Q25 Crypto Top-10 Long.
---

<link rel="stylesheet" href="{{ '/assets/css/terminal.css' | relative_url }}">
<link rel="stylesheet" href="{{ '/assets/css/cookbook.css' | relative_url }}">

<div class="qt-shell">
  <header class="qt-topbar">
    <a class="qt-brand" href="{{ '/' | relative_url }}" aria-label="Q25 terminal home"><span class="qt-brand-mark">Q25</span><span>RESEARCH TERMINAL</span></a>
    <nav class="qt-nav" aria-label="Research surfaces">
      <a href="{{ '/explorer.html' | relative_url }}">Explorer</a>
      <a href="{{ '/backtest/' | relative_url }}">Backtest</a>
      <a href="{{ '/cookbook.html' | relative_url }}" aria-current="page">Cookbook</a>
      <a href="{{ '/RESEARCH_MATRIX.html' | relative_url }}">Matrix</a>
      <a href="https://github.com/Svyable/quantiacs-q25">GitHub ↗</a>
    </nav>
    <div class="qt-feed"><span class="qt-feed-dot"></span><span>Q25 CONTRACT</span></div>
  </header>
</div>

<div class="qc-shell">
  <section class="qc-hero">
    <div class="qc-hero-copy">
      <div class="qc-eyebrow">Q25 CRYPTO TOP-10 · CONTEST-SPECIFIC FIELD GUIDE</div>
      <h1>Build alpha for the rules<br><span>that actually score.</span></h1>
      <p>This page distills the Quant Kitchen, mathematical foundations, factor construction, portfolio assembly, risk, performance analysis, deployment, factor encyclopedia and advanced-math notes into one Q25 workflow. The uploaded material began as a Q24 cookbook; the reusable research ideas are retained here only after being reframed around the Q25 contract.</p>
      <div class="qc-actions">
        <a href="#workflow">Start with the workflow</a>
        <a href="{{ '/backtest/' | relative_url }}">Open backtest surface</a>
        <a href="{{ '/SUBMISSION_CHECKLIST.html' | relative_url }}">Submission checklist</a>
      </div>
    </div>
    <aside class="qc-contract" aria-label="Q25 hard contract">
      <div><span>Direction</span><strong>Long only</strong></div>
      <div><span>Universe</span><strong>Monthly Crypto Top-10 via <code>is_liquid</code></strong></div>
      <div><span>Data</span><strong>Quantiacs-provided only</strong></div>
      <div><span>IS gate</span><strong>Sharpe &gt; 1 since 2016-01-01</strong></div>
      <div><span>Ranking</span><strong>Contest-period OOS Sharpe</strong></div>
      <div><span>Position-change cost</span><strong>4% × ATR(14)</strong></div>
      <div><span>Runtime</span><strong>≤ 5 min / point in time</strong></div>
    </aside>
  </section>

  <section class="qc-note">
    <strong>Two objectives, do not confuse them.</strong> Contest placement is determined by out-of-sample Sharpe among eligible submissions. The post-contest payout model is different: strategy and Crypto10 benchmark positions are scaled using fixed coefficients derived from 10% annualized volatility at the end of the contest, then live equity is judged relative to the benchmark. Negative absolute strategy performance is not rewarded.
  </section>

  <section id="workflow" class="qt-section">
    <div class="qt-section-heading"><div><span class="qt-kicker">RESEARCH PIPELINE</span><h2>From raw data to a defensible Q25 submission</h2></div></div>
    <div class="qc-step"><b>01</b><div><h3>Start with the contract, not the factor</h3><p>Mask every allocation by <code>is_liquid</code>, stay non-negative, never hand-pick symbols, use one quantitative rule set through the evaluation period, and keep contest code inside the sponsor data boundary.</p></div></div>
    <div class="qc-step"><b>02</b><div><h3>Construct causal trailing features</h3><p>Prices are non-stationary; work with returns, relative prices, trailing volatility, rolling residuals and other transformations whose timestamps are unambiguous. No centered windows, future-filled labels or global-statistic leakage.</p></div></div>
    <div class="qc-step"><b>03</b><div><h3>Turn factor hypotheses into a score</h3><p>Momentum, residual momentum, downside-risk, reversal, liquidity and behavioral transforms are hypothesis families—not guaranteed alpha. Normalize cross-sectionally, combine only mechanisms you can explain, and lag any outcome-dependent weighting.</p></div></div>
    <div class="qc-step"><b>04</b><div><h3>Portfolio construction is part of the signal</h3><p>Map scores to long-only weights, control concentration, preserve liquidity exits, and decide how cash behaves when no candidate qualifies. A factor that vanishes after portfolio construction did not create useful portfolio information.</p></div></div>
    <div class="qc-step"><b>05</b><div><h3>Price turnover before admiring Sharpe</h3><p>Q25 charges an ATR-linked cost on every position-size change. Slow signals, hysteresis, scheduled rebalancing and target smoothing can improve net economics, but each is a mechanism choice that must be tested rather than assumed.</p></div></div>
    <div class="qc-step"><b>06</b><div><h3>Try to destroy the thesis</h3><p>Compare single-pass and multi-pass behavior, run prefix/replay checks, remove the defining transform, add execution delay, test nearby chronological folds and check whether a simpler control preserves the edge.</p></div></div>
    <div class="qc-step"><b>07</b><div><h3>Promote evidence, not a pretty line</h3><p>Keep development, validation, diagnostics and authenticated submission evidence separate. The repository matrix is the ledger; this public site should never manufacture missing metrics.</p></div></div>
  </section>

  <section class="qt-section">
    <div class="qt-section-heading"><div><span class="qt-kicker">FACTOR PALETTE</span><h2>Useful ingredients, with their Q25 failure modes</h2></div></div>
    <div class="qc-grid">
      <article class="qc-card"><span class="qc-pill">Momentum</span><h3>Trend / residual trend</h3><p>Trailing multi-horizon price momentum and market-residual momentum are natural crypto hypotheses.</p><ul><li>Failure: market beta disguised as alpha</li><li>Q25 pressure: whipsaw turnover</li><li>Control: remove residualization or trend gate</li></ul></article>
      <article class="qc-card"><span class="qc-pill">Defensive</span><h3>Downside / idiosyncratic risk</h3><p>Inverse volatility, downside volatility and residual-risk scores can change which liquid assets receive capital.</p><ul><li>Failure: simply hiding in the least volatile coin</li><li>Q25 pressure: concentration and regime reversal</li><li>Control: raw inverse-vol baseline</li></ul></article>
      <article class="qc-card"><span class="qc-pill">Reversal</span><h3>Short-horizon mean reversion</h3><p>Z-score deviation, short-term reversal and range position can target overshoot rather than persistent trend.</p><ul><li>Failure: catching a falling knife</li><li>Q25 pressure: frequent position changes</li><li>Control: delayed entry / trend-conditioned variant</li></ul></article>
      <article class="qc-card"><span class="qc-pill">Liquidity</span><h3>Participation / volume state</h3><p>Volume, range and liquidity state can be used as conditioning information when it is available inside Quantiacs data.</p><ul><li>Failure: accidental proxy for future eligibility</li><li>Q25 pressure: monthly universe migration</li><li>Control: replace with plain <code>is_liquid</code></li></ul></article>
      <article class="qc-card"><span class="qc-pill">Behavioral</span><h3>Attention / anchoring</h3><p>Price-volume attention, anchoring and disposition-style transforms can be framed as falsifiable behavioral mechanisms.</p><ul><li>Failure: narrative without incremental returns</li><li>Q25 pressure: unstable thresholds</li><li>Control: permute price-volume pairing</li></ul></article>
      <article class="qc-card"><span class="qc-pill">Portfolio</span><h3>Risk-aware score mapping</h3><p>Equal-weight ranks, inverse-risk scaling, caps and cash gates can be more robust than fitting factor weights to full-history information coefficients.</p><ul><li>Failure: optimizer manufactures backtest fit</li><li>Q25 pressure: cost and uniqueness filters</li><li>Control: equal-weight factor combination</li></ul></article>
    </div>
  </section>

  <section class="qt-section">
    <div class="qt-section-heading"><div><span class="qt-kicker">CONTEST-LEGAL SCAFFOLD</span><h2>A minimal causal shape—not a promoted strategy</h2></div></div>
    <p class="qt-panel-note">This deliberately simple example shows the mechanics the cookbook expects: trailing data, automatic liquid-universe selection, long-only normalization and no hand-picked assets. It has no claimed Sharpe and must be evaluated by the exact repository harness before any promotion.</p>
    <div class="qc-code">
      <div class="qc-code-head"><span>Python</span><span>Q25 scaffold</span></div>
<pre><code>import numpy as np
import xarray as xr
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats

IS_START = "2016-01-01"


def strategy(data):
    close = data.sel(field="close")
    liquid = data.sel(field="is_liquid")

    ret = close / close.shift(time=1) - 1.0
    mom = close / close.shift(time=84) - 1.0
    downside = xr.where(ret &lt; 0, ret, 0.0)
    down_vol = np.sqrt((downside ** 2).rolling(time=30, min_periods=20).mean())

    # Long-only score; no manual symbols.
    score = xr.where(mom &gt; 0, mom / (down_vol + 1e-8), 0.0) * liquid
    score = score.fillna(0.0)

    gross = score.sum("asset")
    weights = xr.where(gross &gt; 0, score / gross, 0.0)
    return weights.fillna(0.0)


if __name__ == "__main__":
    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    weights = qnout.clean(strategy(data), data, "crypto_daily_long")
    stats = qnstats.calc_stat(
        data,
        weights.sel(time=slice(IS_START, None)),
    ).sel(time=slice(IS_START, None))
    print(stats.to_pandas().tail())</code></pre>
    </div>
    <div class="qc-two">
      <div class="qc-note"><strong>Then verify multi-pass.</strong><br>Single-pass is useful for research speed. A day-by-day multi-pass backtest is the stronger deployment check. Matching statistics are evidence against ordinary lookahead mistakes, not permission to use global mutable state or future-dependent transforms.</div>
      <div class="qc-note"><strong>Then inspect cost sensitivity.</strong><br>The official contest cost is 4% × ATR(14) per position-size change, and the rules reserve discretion to use instrument-specific ATR impact up to 10% × ATR(14). High-turnover alpha should be treated as fragile until it survives the repository cost ladder.</div>
    </div>
  </section>

  <section class="qt-section">
    <div class="qt-section-heading"><div><span class="qt-kicker">MEASUREMENT</span><h2>What to measure before the leaderboard matters</h2></div></div>
    <table class="qc-table">
      <thead><tr><th>Question</th><th>Measure</th><th>Why it matters in Q25</th></tr></thead>
      <tbody>
        <tr><td>Does it clear the submission gate?</td><td>IS Sharpe since 2016-01-01</td><td>Must be greater than 1.0 at submission.</td></tr>
        <tr><td>Is the return path tolerable?</td><td>Max drawdown, Sortino, Calmar</td><td>Sharpe alone can hide tail concentration and ugly path dependence.</td></tr>
        <tr><td>Is the edge tradeable after contest costs?</td><td>Turnover + cost ladder</td><td>Every target change can incur ATR-linked friction.</td></tr>
        <tr><td>Did research survive chronology?</td><td>Research → development → forward folds</td><td>Separates discovery from later evidence and reduces overfitting pressure.</td></tr>
        <tr><td>Is the mechanism doing anything?</td><td>Ablation / destructive control</td><td>If removing the claimed mechanism leaves the edge intact, the story is wrong or incomplete.</td></tr>
        <tr><td>Can it be submitted safely?</td><td>Causality, cleaner parity, replay, runtime</td><td>Economic performance does not excuse an invalid implementation.</td></tr>
      </tbody>
    </table>
  </section>

  <section class="qt-section">
    <div class="qt-section-heading"><div><span class="qt-kicker">BENCHMARK & PAYOUT</span><h2>Crypto10 is not just a chart decoration</h2></div></div>
    <div class="qc-two">
      <article class="qc-card"><h3>Contest ranking</h3><p>Eligible submissions are ranked by out-of-sample Sharpe during the contest period. Positive contest-period performance is required. This is the optimization target for winning placement.</p></article>
      <article class="qc-card"><h3>Live payout economics</h3><p>At contest end, strategy and Crypto10 benchmark volatility are normalized to 10% using fixed multipliers for the live period. Payout depends on positive relative equity versus the scaled benchmark, subject to the negative-absolute-performance floor.</p></article>
    </div>
    <div class="qc-code"><div class="qc-code-head"><span>Python</span><span>Official benchmark data path</span></div><pre><code>benchmark = qndata.index_load_weights(
    index_name="CRYPTO10",
    min_date="2016-01-01",
)</code></pre></div>
  </section>

  <section class="qt-section">
    <div class="qt-section-heading"><div><span class="qt-kicker">CONSTRAINT-FIRST RESEARCH</span><h2>A useful idea from lattice deduction</h2></div></div>
    <div class="qc-source">
      <p>The Lattice Deduction Transformer paper is relevant here as a <em>research-process analogy</em>, not as evidence of trading alpha. Its central idea is to represent partial information explicitly and repeatedly eliminate candidates while preserving sound constraints. Applied to this lab: begin with a broad hypothesis set; prune anything that violates the Q25 contract, causality, runtime, cleaner parity or preregistered evidence gates; branch only on surviving uncertainties; and allow the portfolio to abstain into cash when no candidate earns allocation.</p>
      <p>That is a discipline for search. It does <strong>not</strong> imply that a transformer, lattice representation or Sudoku result predicts cryptocurrency returns.</p>
    </div>
  </section>

  <section class="qt-section">
    <div class="qt-section-heading"><div><span class="qt-kicker">SOURCE MAP</span><h2>How the nine cookbook chapters are used here</h2></div></div>
    <table class="qc-table">
      <thead><tr><th>Source chapter</th><th>Retained for Q25</th><th>Reframed / discarded</th></tr></thead>
      <tbody>
        <tr><td>01 · Quant Kitchen</td><td><code>xarray</code>, Quantiacs stack, infrastructure discipline</td><td>Q24 labeling and generic production assumptions</td></tr>
        <tr><td>02 · Mathematical Foundations</td><td>Returns, stationarity intuition, covariance, robust statistics</td><td>Tests used mechanically without a trading hypothesis</td></tr>
        <tr><td>03 · Factor Construction</td><td>Momentum, defensive, behavioral, reversal families</td><td>Any factor treated as proven before Q25 evidence</td></tr>
        <tr><td>04 · Strategy Assembly</td><td>Factor → score → weight → risk pipeline</td><td>Forward-return weighting without strict lag discipline</td></tr>
        <tr><td>05 · Risk Management</td><td>Position limits, downside risk, volatility awareness</td><td>Leverage ideas that conflict with contest mechanics</td></tr>
        <tr><td>06 · Performance Analysis</td><td>Sharpe, drawdown, geometric returns, uncertainty</td><td>Headline Sharpe without chronology or costs</td></tr>
        <tr><td>07 · Production Deployment</td><td>Validation, reproducibility, failure handling</td><td>Broker infrastructure irrelevant to Quantiacs submission</td></tr>
        <tr><td>08 · Factor Encyclopedia</td><td>Hypothesis vocabulary and implementation prompts</td><td>Unverified “expected IC” numbers as evidence</td></tr>
        <tr><td>09 · Advanced Mathematics</td><td>Ideas only when they generate falsifiable causal tests</td><td>Complexity for novelty’s sake</td></tr>
      </tbody>
    </table>
  </section>

  <footer class="qt-footer">
    <div><strong>Q25 Contest Cookbook</strong><span>Rules first. Causality second. Evidence before promotion.</span></div>
    <div class="qt-footer-links"><a href="{{ '/' | relative_url }}">Terminal</a><a href="{{ '/RESEARCH_METHOD.html' | relative_url }}">Method</a><a href="{{ '/TESTING_PYRAMID.html' | relative_url }}">Testing</a><a href="{{ '/STRATEGY_ATLAS.html' | relative_url }}">Strategy Atlas</a></div>
  </footer>
</div>
