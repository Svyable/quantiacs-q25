# Frontier-E: another three alpha hypotheses

**Decision: freeze all three families; promote zero.** All 18 objects (nine base variants, six ablations/falsifiers and three generic controls) completed exact Quantiacs evaluation. No base window reached the 1.0 worst-fold/cost development floor, and every central mechanism lost to at least one defining control.

The prior Frontier-D PR is merged and its GitHub benchmark succeeded. This campaign leaves those failed formulas frozen and tests different causal objects. It uses the same sponsor data hash for development comparability, without merging separate source contexts into one ranking.

## The hypotheses

- **Downside impact relief:** a fall in negative displacement per unit of relative dollar volume may indicate improved capacity to absorb selling. This is an OHLCV proxy, not observed order flow. It differs from the old candle-location absorption formula and from directed cross-asset volume diffusion. Removing volume tests whether ordinary downside return contraction explains the result.
- **Range acceptance escape:** an upside breakout after repeated acceptance inside earlier high-low ranges may sustain continuation. This develops an unimplemented Frontier-D idea under a new preregistration: ATR-scaled escape, five-day event persistence, direct confidence sizing and a common market gate. The old contract is preserved. Removing acceptance or using stale acceptance attacks the proposed timing relationship.
- **Upside response convexity:** sensitivity to large positive peer-market moves may exceed sensitivity to moderate moves, identifying assets with additional upside participation. Each peer market excludes the asset itself; bucket membership and fitted coefficients use past data. A linear-response ablation and sign-inverted convexity test whether the nonlinear term and its direction matter.

All three allocate at most five names, up to 20% each, with weight proportional to a bounded score. They do not normalize weak scores to full gross. Entries are on Monday, a 63-day positive market-return state gates scheduled allocation, and invalid-price/eligibility exits persist until the next Monday. No existing strategy has been silently restyled or retuned.

## Preregistration and provenance

24 ideas were scored before new returns; six were registered and three implemented. The remaining three are untested, not rejected. The hypothesis ledger, exact transforms, fixed constants and grids are in this directory.

GitHub preregistration freeze: `7fa091d5875434a78a67b9db25c5d32609b5c675`. GitHub implementation freeze: `656e004eac1b63c648058f612d06caecf6b6a2c7`. Both precede measurement. `implementation_freeze.json` records file hashes; [source.json](../../evidence/frontier_20260911e/source.json) records toolbox and dependency provenance. The public/default Quantiacs loader used the sponsor snapshot cached by the toolbox. No outside market dataset was substituted.

## Exact development results

Robust Sharpe is the minimum across 2016–2020 research and 2021–2022 development at 4%, 8% and 12% ATR-linked slippage. The full zero/4/8/12 cost ladder, CAGR, Sortino, Calmar, hit rate, turnover, runtime and cleaner diagnostics are preserved in individual evidence records. Figures below are observed local statistics, not official qualification or forecasts.

| Cell | Mode | Robust SR | Research SR, 12% | Dev SR, 12% | Worst DD, 12% |
|---|---|---:|---:|---:|---:|
| upside_response_convexity_falsifier | falsifier | 0.985 | 1.239 | 0.985 | -33.5% |
| upside_response_convexity_w42 | base | 0.827 | 1.325 | 0.827 | -23.9% |
| upside_response_convexity_w63 | base | 0.725 | 0.941 | 0.725 | -34.1% |
| persistent_low_vol | control | 0.641 | 1.495 | 0.641 | -93.3% |
| upside_response_convexity_w84 | base | 0.639 | 0.639 | 0.879 | -30.7% |
| downside_impact_relief_w42 | base | 0.296 | 1.767 | 0.296 | -54.8% |
| equal_liquid | control | 0.270 | 1.436 | 0.270 | -93.6% |
| upside_response_convexity_ablation | ablation | 0.224 | 1.530 | 0.224 | -56.5% |
| downside_impact_relief_ablation | ablation | 0.164 | 1.596 | 0.164 | -48.4% |
| range_acceptance_escape_w84 | base | 0.154 | 1.612 | 0.154 | -30.7% |
| range_acceptance_escape_ablation | ablation | 0.113 | 1.568 | 0.113 | -50.7% |
| range_acceptance_escape_w42 | base | 0.109 | 1.737 | 0.109 | -32.0% |
| range_acceptance_escape_falsifier | falsifier | 0.089 | 1.628 | 0.089 | -30.6% |
| range_acceptance_escape_w63 | base | 0.085 | 1.676 | 0.085 | -30.7% |
| inverse_vol_trend | control | 0.053 | 1.528 | 0.053 | -87.1% |
| downside_impact_relief_w84 | base | -0.032 | 1.706 | -0.032 | -70.9% |
| downside_impact_relief_w63 | base | -0.222 | 1.700 | -0.222 | -70.3% |
| downside_impact_relief_falsifier | falsifier | -0.289 | 1.861 | -0.289 | -62.8% |

## What survived scrutiny—and what did not

The strongest base cell was 42-day upside response convexity: robust Sharpe 0.827 and worst stressed drawdown -23.9%. Its central cell had development residual Sharpe 0.295 against three generic controls. These are interesting measurements, but the inverted-convexity control scored 0.985 versus 0.725 for its matched central parent. The proposed direction failed. Do not rename the inverted control a winner or round 0.985 up to 1.0.

Downside impact relief had a 0.296 best base robust score, with the central cell at -0.222. The volume-free ablation scored 0.164: the proposed volume conditioning did not improve this central implementation. Range acceptance scored 0.154 at best; central 0.085 lagged both the 0.113 acceptance-free control and the 0.089 stale-acceptance control.

All three also miss the preregistered progression screen of at least two base windows at robust SR >=1. Consequently no extra-delay or 2023–2024 diagnostic test was triggered. No later window was inspected to rescue a failure.

Unlike Frontier-D ordinal reliability, these interactions materially change portfolios. The table reports target-path changes relative to the central parent over all 2,922 input days, including warm-up, and paired 2021–2022 net return uncertainty at 4% ATR cost. Intervals use 2,000 fixed-seed circular 21-day block samples; they are annualized arithmetic percentage-point differences, not CAGR or selection-adjusted significance.

| Parent | Control | Changed target days | Annualized return difference | 95% block interval |
|---|---|---:|---:|---|
| downside_impact_relief_w63 | downside_impact_relief_ablation | 43.8% | -13.99 pp | [-52.58, 31.82] pp |
| downside_impact_relief_w63 | downside_impact_relief_falsifier | 43.1% | 4.10 pp | [-22.83, 42.11] pp |
| range_acceptance_escape_w63 | range_acceptance_escape_ablation | 33.6% | -7.96 pp | [-35.26, 15.22] pp |
| range_acceptance_escape_w63 | range_acceptance_escape_falsifier | 32.4% | -0.00 pp | [-1.84, 1.79] pp |
| upside_response_convexity_w63 | upside_response_convexity_ablation | 48.2% | -1.38 pp | [-36.49, 32.34] pp |
| upside_response_convexity_w63 | upside_response_convexity_falsifier | 48.2% | -10.37 pp | [-35.25, 14.91] pp |

## Originality and implementation health

| Central family | Dev residual SR | Correlation to equal-liquid | Correlation to inverse-vol trend |
|---|---:|---:|---:|
| downside_impact_relief | -1.623 | 0.596 | 0.741 |
| range_acceptance_escape | -1.417 | 0.581 | 0.691 |
| upside_response_convexity | 0.295 | 0.471 | 0.539 |

Historical V10/V11/V12 matched return streams and authenticated platform uniqueness remain PENDING. The generic-control regression is research-trained and evaluated on development; positive residual Sharpe alone is not admission.

| Layer | Evidence |
|---|---|
| L0/L1 | PASS: finite long-only weights, historical eligibility, cap/gross, order invariance, score-to-capital sensitivity and persistent exits |
| L2 | PASS: all 18 measured objects at seven prefix checkpoints; 365-day bounded replay |
| L3/L4 | OBSERVED_LOCAL: exact toolbox metrics at all four costs |
| L5/L6 | Research/development only; reused periods, no fresh-holdout claim |
| L7 | Three matched generic controls; historical-core and hosted checks PENDING |
| L8 | 24 scored ideas, six hashed registrations, three implementations, 18 measured objects |
| L9 | All three families FALSIFIED_DEVELOPMENT under frozen rules; no parameter rescue |
| Software | 147 tests passed; 42 premeasurement mechanism tests plus captured-evidence verification |

The central impact strategy was unchanged by the official cleaner. Central range and convexity targets each had one changed cell on a missing-price/nonfinite-liquidity date; the existing evaluator classified each as PLATFORM_DATA_TRANSLATION. Raw and platform-cleaned behavior are recorded separately, rather than presenting this as strict zero mutation. Full candidate evidence preserves each cell, including raw records and matched return streams.

## Next frontier

Freeze these formulas and directions. Do not expand their windows, flip their signs into new winners, or add optimized trend gates after inspecting the results. The next campaign should change its information object: conditional downside saturation or topology-based opportunity may warrant separately specified tests, but cannot inherit these scores. Range acceptance and a relative-volume impact proxy did not earn a fresh chronological look here.

The methodological gain is a stronger pre-return implementation contract: economically defining transforms demonstrably alter capital, peer markets exclude self-inclusion, volume falsifiers preserve eligible marginals, and every frozen cell earns measured evidence. The economic conclusion remains no qualifying new alpha in this campaign.

## Reproduce

Use dependencies and toolbox commit in `evidence/frontier_20260911e/source.json`. The dedicated `frontier-e-alpha-benchmark` workflow runs the same evaluation and paired diagnostics.

```bash
API_KEY=default python -m research.iteration \
  --manifest experiments/frontier_20260911e/manifest.json \
  --output results/frontier_20260911e --budget 18
python -m pytest -q tests
python scripts/build_research_dashboard.py --check
```

A revised sponsor snapshot gets a new data hash; preserve this evidence rather than overwriting it. The 2026-10-01 live window and all account submission actions remain untouched.
