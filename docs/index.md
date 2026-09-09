---
title: Q25 Quantitative Research Lab
description: Causal crypto alpha research, orthogonality, regime-aware risk, and cost-aware portfolio construction for Quantiacs Q25.
---

# Q25 Quantitative Research Lab

> **Build mechanisms, not backtest screenshots.**
>
> This repository is our public research surface for the Quantiacs Q25 Crypto Top-10 Long problem: causal signals, dynamic `is_liquid` eligibility, long-only allocation, explicit cash, cost-aware execution, and a heavy bias toward **new residual alpha rather than cosmetic variants of the same trend trade**.

**Contest window:** entry deadline **September 30, 2026** · live evaluation **October 1, 2026 – January 31, 2027**.  
**Research rule:** historical numbers below are frozen local research evidence through **August 20, 2026**. They are **not current official Quantiacs scores, forecasts, or promises of live performance**.

[Strategy Atlas](STRATEGY_ATLAS.md) · [Research Method](RESEARCH_METHOD.md) · [Testing Pyramid](TESTING_PYRAMID.md) · [Submission Checklist](SUBMISSION_CHECKLIST.md) · [Top-10 data](../configs/historical_top10.yaml)

---

## The thesis

Most crypto strategy repositories optimize a single score. We treat Q25 as a **portfolio of falsifiable mechanisms**.

The research stack asks five questions in order:

1. **What information is the signal claiming to extract?** Trend persistence, cross-asset diffusion, abnormal volume, crash comovement, higher moments, breadth, lifecycle, or something else?
2. **Is it causal?** No future leakage, centered windows, hidden negative shifts, hand-picked symbols, or data unavailable at the decision time.
3. **Is it actually different?** A new name for a 0.95-correlated return stream is not new alpha.
4. **Does it survive realistic friction and hostile windows?** Cost ladders, chronological folds, drawdowns, turnover, sparse-activity checks, and prefix invariance matter more than a single full-period Sharpe.
5. **Can it be packaged safely for the platform?** Long-only, liquid-only, bounded gross, current cleaner/checker, multipass parity, runtime, and external-correlation checks.

That order is deliberate. Optimization comes **after** mechanism and integrity.

---

## Historical top ten

Frozen research-preparation roster, full history beginning 2016-01-01. Baseline research friction was `4% × ATR(14)` per unit position change; the stress column states the larger ATR fraction used for that row.

| # | Strategy | Mechanism / role | Full SR | Max DD | Stress SR | Stress |
|---:|---|---|---:|---:|---:|---:|
| 1 | **V10 multi-factor ensemble — Pareto** | legacy multi-factor core | **2.261** | -30.90% | **1.965** | 12% ATR |
| 2 | **V11 new-only event ensemble — Balanced** | shock network + motif + lifecycle + calendar | 1.261 | -23.11% | 0.899 | 12% ATR |
| 3 | **C165 mobility / consensus risk** | short/medium consensus-risk blend | 1.230 | -21.45% | 0.934 | 12% ATR |
| 4 | **V12 signed volume diffusion** | abnormal-volume → residual-return network | 1.035 | -33.86% | 0.750 | 12% ATR |
| 5 | **Co-crash shelter — 126D** | defensive crash-comovement selection | 1.772 | -14.38% | 1.627 | 12% ATR |
| 6 | **Residual dispersion switch** | sparse dispersion-conditioned residual alpha | 1.536 | -12.00% | 1.410 | 8% ATR |
| 7 | **Breadth Thrust Switch** | market breadth acceleration timing | 1.185 | -21.49% | 1.075 | 8% ATR |
| 8 | **Slow defensive factor balance** | diversified defensive factor mix | 1.526 | -24.72% | 1.445 | 8% ATR |
| 9 | **126D positive-return consistency** | persistent-trend reserve | 1.700 | -24.84% | 1.538 | 12% ATR |
| 10 | **V5 latency ensemble** | low-risk alternate within V10 family | 2.105 | **-10.30%** | 1.830 | 12% ATR |

These are not ten independent bets. V5, for example, is a lower-risk relative of the V10 lineage. We keep the overlap visible rather than inflating the apparent number of discoveries.

---

## The four-core research graph

The strongest frozen core is **V10 + V11 + C165 + V12** because their matched historical daily streams were meaningfully less correlated with one another than many of the high-scoring reserves.

| | V10 | V11 | C165 | V12 |
|---|---:|---:|---:|---:|
| **V10** | 1.000 | 0.288 | 0.329 | 0.398 |
| **V11** | 0.288 | 1.000 | 0.334 | 0.414 |
| **C165** | 0.329 | 0.334 | 1.000 | 0.281 |
| **V12** | 0.398 | 0.414 | 0.281 | 1.000 |

Those correlations cover the matched 2022-01-01 through 2026-08-20 local streams. They are historical diagnostics, not platform uniqueness approvals.

### V10 — adaptive multi-factor core

V10 is the mature lineage: a Pareto blend of the earlier orthogonal core with factor-state routing, defensive sleeves, residual/tail features, capped allocation and cash. Its purpose is not “maximum return at any price”; it is the **high-capacity anchor** against which new mechanisms have to prove incremental value.

### V11 — event alpha without incumbent reuse

V11 was built from a clean slate. Its balanced mode combines:

- directed negative cross-crypto shock propagation (“seesaw” behavior),
- a learned seven-day shock/candle/volume motif,
- positive-entry liquidity-lifecycle events, and
- sparse asset-specific calendar recurrence.

The balanced frozen allocation was 10% / 30% / 50% / 10%. No V9/V10 return stream or factor score is fed into the signal.

### C165 — consensus risk rather than more raw momentum

C165 is a risk-efficiency refinement: a 21-day anchor combined geometrically with a small 63-day market-trend probability. It improved historical drawdown and stressed-cost efficiency versus its immediate parent while remaining intentionally close to that family. That closeness is why it gets **one slot, not several aliases**.

### V12 — signed volume-to-return diffusion

V12 is the most structurally different member of the core. It:

1. residualizes each asset's return against a rolling crypto-market factor;
2. standardizes abnormal dollar-volume;
3. estimates a causal directed network from leader volume shocks to follower next-day residual returns;
4. retains statistically stronger signed links;
5. diffuses the current shock vector through the frozen-at-decision network; and
6. activates sparse long-only books only when the opportunity score clears a causal threshold.

That is the kind of new alpha we want: **information flow**, not another moving-average parameter sweep.

---

## Defensive and conditional sleeves

### Co-crash shelter

Instead of asking which asset went up the most, co-crash research asks which liquid names are least likely to fail *with* the basket during stressed states. The sleeve's role is convexity-by-selection: reduce common crash exposure while preserving upside participation.

### Residual dispersion switch

Dispersion can create opportunity when asset-specific information dominates the common market factor. The switch deploys sparse residual alpha only when cross-sectional conditions justify it, otherwise allowing cash.

### Breadth thrust

Breadth is a market-state variable, not an asset picker. We track the fraction of eligible names participating in trend and the acceleration of that participation. A broadening market can justify more gross; collapsing breadth can veto otherwise attractive individual scores.

### Factor balance

The defensive factor sleeve spreads risk across slower trend, quality, beta/residual-beta, and risk-normalized cross-sectional information rather than trusting a single lookback.

### Trend consistency and latency ensemble

These are useful controls and reserves. They remain in the top ten because their frozen historical efficiency was strong, but the lab explicitly marks their overlap with the dominant trend/factor lineage. High Sharpe does not magically create orthogonality.

---

## Frontier lab: interesting does not mean admitted

### V13 low residual-skew

The V13 satellite found a real higher-moment seam: estimate rolling market beta, form residual returns, prefer the lowest 252-day residual skewness, and activate only above a lagged opportunity threshold. Frozen local research showed Sharpe 1.446 and 12%-ATR stress Sharpe 1.303, but also a **-62.38% maximum drawdown**. Under the newer internal drawdown discipline it stays outside the current top-ten roster.

That is a feature of the process, not a failure: a spectacular equity curve does not overrule unacceptable path risk.

### Market-assimilation delay

Later research found a sparse “assimilation delay acceleration” seam based on how quickly individual assets absorb equal-weight market moves. Some candidates cleared performance, cost, fold and activity gates but failed the frozen recent-correlation ceiling. They remain research leads—not admissions.

### VIPER–HELIOS architecture

A parallel engineering line explored causal IC-weighted factor blends, covariance shrinkage toward a single crypto-market factor, equal-risk contribution, multi-horizon momentum, ATR-aware no-trade regions, absolute-trend filters and crash overlays. We treat that work as an **architecture library**: useful components can migrate into new hypotheses, but old headline metrics are never pasted onto a materially different implementation.

---

## The SOTA research loop

```text
mechanism hypothesis
      ↓
causal implementation + static audit
      ↓
prefix invariance / no-lookahead checks
      ↓
chronological discovery → validation folds
      ↓
cost ladder + turnover + liquidity checks
      ↓
return-stream residualization vs incumbents
      ↓
multiple-testing / PBO / deflated-Sharpe diagnostics
      ↓
Pareto promotion: return × drawdown × costs × originality
      ↓
current Quantiacs cleaner + multipass + external correlation
      ↓
only then: candidate for live entry
```

### What we optimize

- **Residual Sharpe**, not just total Sharpe.
- **Drawdown geometry**, not just terminal equity.
- **Cost resilience**, especially with ATR-linked friction.
- **Sparse opportunity quality**, not forced 100% gross.
- **Cross-strategy diversity**, not strategy-count theater.
- **Causal stability**, including prefix replay and warning-as-error runs.

### What we refuse to optimize around

- the already observed 2025/Q25-preview segments as if they were pristine holdouts;
- single-symbol exceptions or manual coin selection;
- hidden future data, negative shifts, centered rolling features;
- rounded eligibility thresholds;
- dozens of cosmetically different versions of one return stream.

---

## A new synthesis in this repo

`strategies/q25_sota_meta_ensemble.py` is a **new PENDING research strategy** that combines the best *mechanism classes* without claiming historical champion parity:

- residual momentum,
- causal abnormal-volume response,
- co-crash safety,
- low residual skewness,
- path-efficient trend,
- breadth / trend / volatility regime gating,
- inverse-risk allocation with cash and a 25% internal name cap.

It is intentionally labeled **PENDING** until it passes the repository's full testing pyramid. The historical top-ten numbers do not attach to it.

---

## Research foundations

We use academic work as **hypothesis inspiration**, never as a source of fitted coefficients or external contest data.

- Fousekis & Tzaferi, *Returns and volume: Frequency connectedness in cryptocurrency markets*, Economic Modelling (2021), DOI: [10.1016/j.econmod.2020.11.013](https://doi.org/10.1016/j.econmod.2020.11.013)
- Jia, Wu, Yan & Liu, *A seesaw effect in the cryptocurrency market: Understanding the return cross predictability of cryptocurrencies*, Journal of Empirical Finance (2023), DOI: [10.1016/j.jempfin.2023.101428](https://doi.org/10.1016/j.jempfin.2023.101428)
- Jia, Liu & Yan, *Higher moments, extreme returns, and cross-section of cryptocurrency returns*, Finance Research Letters (2021), DOI: [10.1016/j.frl.2020.101536](https://doi.org/10.1016/j.frl.2020.101536)
- Quantiacs Q25 schedule and platform: [quantiacs.com](https://quantiacs.com/)

The papers motivate families such as return/volume diffusion, cross-asset lead-lag, and higher-moment signals. Every contest strategy still uses only permitted Quantiacs-provided fields.

---

## Status legend

**Historical research** — frozen evidence from a dated prior campaign; useful for comparison, not a current platform score.  
**Prepare / precheck** — worthy of current official validation before entry.  
**Conditional reserve** — strong historical result with overlap, packaging, or evidence limitations.  
**PENDING** — new implementation with no attached performance claim.

The target is not to tell a beautiful backtest story. The target is to enter the live window with a small set of **causal, distinct, cost-aware mechanisms that have survived attempts to kill them**.