# Q25 Strategy Atlas

This is the public-facing model-card layer for the frozen Q25 research roster. It answers four questions for every strategy: **what is the mechanism, what job does it do in a portfolio, what evidence do we have, and what can still invalidate it?**

> Historical metrics are frozen local research / execution-translation evidence through **2026-08-20**. They are not current official Quantiacs scores. Baseline research friction was `4% × ATR(14)` per unit change; stress results use the ATR fraction shown per strategy.

Machine-readable roster: [`configs/historical_top10.yaml`](../configs/historical_top10.yaml).

---

## 1 — V10 multi-factor ensemble · Pareto

**Mode:** `aqr_ensemble_pareto_v10`  
**Role:** primary high-capacity legacy core  
**Historical evidence:** SR **2.261** · max DD **-30.90%** · 12%-ATR stress SR **1.965**  
**Current status:** prepare / precheck; no current official clearance claimed

### Mechanism

V10 is a mature ensemble rather than a single indicator. The lineage combines a prior orthogonal core with factor-style cross-sectional scores, regime/state routing, defensive sleeves, residual and tail information, capped allocation, and explicit cash. The Pareto mode is preferred over max-Sharpe/max-return siblings because those siblings are alternative risk points in the **same family**, not independent discoveries.

### Why it earns a slot

It is the most powerful historical anchor in the roster and creates a demanding benchmark for every new idea: a challenger should either improve the anchor's risk/cost frontier or add genuinely residual return.

### What can kill it

- current official multipass or correlation failure;
- recent degradation that persists out of sample;
- discovering that a proposed “new” sleeve is merely V10 exposure in disguise;
- excess dependence on one market regime.

**Archived source provenance:** `q25_v10_aqr_ensemble_pareto_submission.py` / historical preparation wrapper.

---

## 2 — V11 new-only event ensemble · Balanced

**Mode:** `newonly_balanced_v11`  
**Role:** independent event / lifecycle core  
**Historical evidence:** SR **1.261** · max DD **-23.11%** · 12%-ATR stress SR **0.899**  
**Current status:** prepare / precheck

### Mechanism

V11 deliberately avoided incumbent factor reuse. Balanced mode combines four causal mechanisms:

| Sleeve | Frozen allocation | Idea |
|---|---:|---|
| Network seesaw | 10% | directed negative cross-crypto shock propagation |
| Motif | 30% | learned 7-day price/candle/volume state |
| Lifecycle | 50% | entry into / persistence within the dynamic liquid universe |
| Calendar | 10% | sparse asset-specific month recurrence |

The book is long-only, asset-agnostic, historical-`is_liquid` only, capped, and allowed to hold cash.

### Why it earns a slot

It is not another reskinned V10. Its matched historical correlations to the other three core members were only 0.288–0.414, making it valuable even with a lower standalone Sharpe.

### What can kill it

- unstable event frequencies or insufficient live activity;
- motif overfit from too many latent states;
- lifecycle edge disappearing after universe transition costs;
- external-correlation rejection on the current platform.

**Archived source provenance:** `q25_v11_newonly_orthogonal_submission.py`.

---

## 3 — C165 mobility / consensus risk

**Mode:** `C165__anchor_trend21__market_trend_h63__w10__geometric__hl0__f00`  
**Role:** risk-efficiency core  
**Historical evidence:** SR **1.230** · max DD **-21.45%** · 12%-ATR stress SR **0.934**  
**Current status:** prepare / precheck; standalone contest adapter required

### Mechanism

C165 combines a 21-day anchor with a small amount of 63-day market-trend probability through a geometric consensus blend. The point is not to manufacture a new alpha label; it is to improve **when and how much risk the book accepts**.

### Why it earns a slot

It improved the local risk/cost frontier of its immediate parent while retaining low matched correlation to V11 and V12. It is the conservative member of its refinement family.

### Important overlap warning

Historical C165–R002 correlation was approximately **0.998**. Those are alternatives inside one lineage. We do not count both as independent alpha.

### What can kill it

- recent factor drift;
- no incremental value after financing it against the anchor;
- current platform correlation identifying it as redundant.

**Archived source provenance:** `q25_consensus_risk_round19_research.py`.

---

## 4 — V12 signed volume diffusion · 50/50 bridge

**Mode:** `signed_bridge_six5`  
**Role:** structural volume/return network core  
**Historical evidence:** SR **1.035** · max DD **-33.86%** · 12%-ATR stress SR **0.750**  
**Current status:** prepare / precheck; official SR must remain **strictly > 1** without rounding

### Mechanism

V12 treats the market as a directed information network:

1. residualize each liquid asset return against a rolling 126-day equal-weight crypto market factor;
2. standardize abnormal log dollar-volume against its 63-day history;
3. on a fixed schedule, estimate causal links from leader abnormal volume at `t` to follower residual return at `t+1` using trailing history only;
4. retain stronger signed links;
5. diffuse current shocks through the directed network;
6. activate only when the cross-sectional opportunity exceeds a lagged threshold;
7. blend sparse five-name and six-name books 50/50.

### Why it earns a slot

Its information set is structurally different from trend/quality cores. The matched historical V12 correlations to V10/V11/C165 were 0.398 / 0.414 / 0.281.

### What can kill it

- exact official Sharpe slipping to 1.0 or below;
- network instability when the liquid universe changes;
- turnover/cost concentration on high-ATR names;
- recent information-flow structure becoming too similar to incumbents.

**Archived source provenance:** `q25_v12_signed_volume_diffusion_submission.py`.

---

## 5 — Co-crash shelter · base 126D

**Mode:** `cocrash_shelter / cocrash_base_r1`  
**Role:** defensive crash-comovement sleeve  
**Historical evidence:** SR **1.772** · max DD **-14.38%** · 12%-ATR stress SR **1.627**  
**Current status:** prepare / precheck; contest adapter required

### Mechanism

Measure which eligible names tend to fail together with the basket during stressed observations and prefer the names with lower common-crash sensitivity. It is a **downside dependence** strategy rather than a conventional low-volatility sort.

### Why it earns a slot

The historical combination of strong Sharpe, low drawdown and stressed-cost resilience made it one of the cleanest defensive sleeves recovered from the archive.

### What can kill it

- too few crash observations for stable estimation;
- crash correlation being merely a low-beta proxy;
- structural regime changes that reverse the historical shelter relationship.

---

## 6 — Residual dispersion switch

**Mode:** `hrt_dispersion_switch`  
**Role:** sparse dispersion-conditioned residual sleeve  
**Historical evidence:** SR **1.536** · max DD **-12.00%** · 8%-ATR stress SR **1.410**  
**Current status:** prepare / precheck

### Mechanism

Neutralize common market behavior, estimate cross-sectional residual dispersion, and deploy the idiosyncratic sleeve only when the dispersion state indicates enough asset-specific information to justify concentration. Cash is a valid state.

### Why it earns a slot

It pairs unusually low historical drawdown with a mechanism that is economically different from broad risk-on trend exposure.

### What can kill it

- dispersion as a contemporaneous risk measure with no forward information;
- sparse deployment causing fragile inference;
- overlap with other static residual/quality ensembles.

**Archived source provenance:** `q25_hrt_dispersion_switch.py`.

---

## 7 — Breadth Thrust Switch

**Mode:** `breadth_thrust_switch`  
**Role:** market breadth acceleration timing  
**Historical evidence:** SR **1.185** · max DD **-21.49%** · 8%-ATR stress SR **1.075**  
**Current status:** prepare / precheck

### Mechanism

Track how many eligible assets participate in trend and, critically, whether that participation is **accelerating**. Breadth acts as a market-level gate on gross risk rather than as a hand-picked asset signal.

### Why it earns a slot

It adds a universe-level state variable and can veto attractive individual scores when participation collapses.

### What can kill it

- breadth being a delayed proxy for the same market trend already inside V10;
- unstable behavior around `is_liquid` membership changes;
- insufficient stressed-cost evidence beyond the recovered 8%-ATR run.

---

## 8 — Slow defensive factor balance

**Mode:** `aqr_factor_balance`  
**Role:** diversified defensive factor sleeve  
**Historical evidence:** SR **1.526** · max DD **-24.72%** · 8%-ATR stress SR **1.445**  
**Current status:** prepare / precheck, conditional on portfolio-level overlap

### Mechanism

Blend slower information—trend persistence, quality/path efficiency, beta/residual-beta and risk normalization—so no single lookback or factor dominates the book.

### Why it earns a slot

It is a strong historical control for whether complexity actually adds value beyond a clean multi-factor baseline.

### What can kill it

- high correlation with generic trend/factor incumbents;
- insufficient incremental residual Sharpe;
- slower signals reacting too late to crypto regime breaks.

**Archived source provenance:** `q25_aqr_factor_balance.py`.

---

## 9 — 126D positive-return consistency · five names

**Mode:** `trend_hit126__concentrated5`  
**Role:** persistent-trend reserve  
**Historical evidence:** SR **1.700** · max DD **-24.84%** · 12%-ATR stress SR **1.538**  
**Current status:** conditional reserve; adapter required

### Mechanism

Rank liquid assets by the consistency of positive daily returns over a 126-day horizon, concentrate in the strongest five, and control risk rather than continuously changing the lookback.

### Why it is only a reserve

The standalone metrics were strong, but historical residual tests versus the dominant V9/V10 lineage were weak. This is a good example of why “high Sharpe” and “new alpha” are different claims.

### What can kill it

- no positive residual Sharpe after controlling for the anchor;
- correlation failure;
- concentration cost during abrupt leadership reversals.

---

## 10 — V5 latency ensemble

**Mode:** `latency_ensemble_v4`  
**Role:** low-risk alternative within the V10 family  
**Historical evidence:** SR **2.105** · max DD **-10.30%** · 12%-ATR stress SR **1.830**  
**Current status:** conditional reserve / family alternative

### Mechanism

Blend multiple trailing-performance routers with different response speeds around a protective core. The objective is to make risk allocation robust to **decision latency** rather than optimize one perfect horizon.

### Why it is only a reserve

Its historical risk profile was excellent, but matched recent correlation to V10 was about **0.916**. V5 is therefore a potential replacement / lower-risk alternative, not evidence of a second independent alpha source.

### What can kill it

- no incremental portfolio diversification versus V10;
- stale router performance estimates;
- hidden regime selection through latency windows.

---

# Frontier mechanisms not promoted into the top ten

## V13 — low residual skewness

V13 estimates rolling beta to the equal-weight market, forms residual returns, ranks the **lowest 252-day residual skewness**, and deploys a sparse top-three book only when a lagged opportunity threshold is crossed. Frozen research was interesting—SR 1.446 and 12%-ATR stress SR 1.303—but maximum drawdown reached **-62.38%**. Under the newer risk discipline it remains a satellite research seam, not a core admission.

## Market-assimilation delay acceleration

A later family estimated how much of each asset's response to market moves arrived at lags 0–3 and searched for abrupt contraction in delayed response. Several sparse candidates passed many performance and cost gates but breached the frozen recent-correlation ceiling. The seam remains worth studying; the failed gate remains binding.

## Frontier-G — edge uncertainty, forecast agreement, cost-relative persistence

Campaign `frontier_20260911g` implemented three new objects after Frontier-F froze signed triangles, weekly posteriors and expert routing:

| Family | Object | Development result |
|---|---|---|
| Forecast agreement | slow vs 7-day residual rank agreement | `KILL_WEAK_ALPHA` — best robust SR **0.458**, beat ablation and falsifier, missed the 1.0 floor |
| Edge-uncertainty change | rising variance of residual-correlation edges | `FALSIFIED_DEVELOPMENT` — level ablation beat every change window |
| Cost-relative persistence | persistent residual / own relative ATR | `FALSIFIED_DEVELOPMENT` — no-ATR ablation beat the central parent |

These are frozen research seams, not contest entries. Details: [campaign note](FRONTIER_CAMPAIGN_G.md), [PM report](https://github.com/Svyable/quantiacs-q25/blob/main/experiments/frontier_20260911g/pm_report.md).

## VIPER–HELIOS engineering library

The VIPER–HELIOS line contributed reusable architecture: causal IC-weighting, covariance shrinkage, equal-risk contribution, multi-horizon momentum, ATR-aware no-trade bands, absolute trend gates and crash overlays. These are **engineering primitives**, not licenses to transfer old metrics onto a new strategy.

---

# Portfolio-level rules

A strategy enters the active slate only when it adds something the slate does not already have. The current research standard is:

- compare matched daily return streams, not strategy names;
- residualize challengers against incumbent cores;
- run chronological folds and cost ladders;
- preserve cash when opportunity or risk capacity is weak;
- cap positions and enforce historical `is_liquid`;
- treat 2025 and earlier Q25-preview diagnostics as already observed, not pristine holdouts;
- demand a current Quantiacs cleaner/checker/multipass/correlation pass before any live-entry decision.

The leaderboard is therefore a **research map**, not a command to submit ten strategies.