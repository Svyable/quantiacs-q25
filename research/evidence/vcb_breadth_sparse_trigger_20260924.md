# VCB × breadth 5% sparse-trigger evidence — 2026-09-29

Status: **FALSIFIED / DO NOT PROMOTE**
Evidence label: `ADAPTIVE_REUSE`
Experiment: `vcb_breadth_sparse_trigger_20260924`
Preregistration: `research/preregistrations/vcb_breadth_sparse_trigger_20260924.md`
Measurement head: `ce32f03b6cffcf5423582ad0af69b70f3e60c659` (merged in PR #152)
Workflow run: `36510096981` (`q25-sparse-trigger` #2, success)
Artifact: `sparse-trigger-evidence` id `11009206326`, digest `sha256:d90dc41916c155322b6351c0135caa1e08dce76cb47271c15be8647e494cc803`
Latest Sponsor date: 2026-09-27
Completed 90-day origins: 39 (all scored)

## Frozen hypothesis adjudication

The preregistered 5% portfolio-level sparse trigger **fails its advancement gate**. It reduced current-IS target turnover from 0.0642972343 to 0.0611580455, a reduction of **4.8823%**. The frozen requirement was at least **10%**. That is weaker than the already-falsified 2% per-asset band (6.8075%). No threshold rescue or post-result trigger grid is permitted.

All other gates passed at the official 4%-ATR cost unless stated:

| Gate | Result | Threshold |
|---|---:|---:|
| current-IS Sharpe | 1.746591 | > 1.0 |
| turnover reduction vs static | **4.8823%** | ≥ 10% ✗ |
| stitched completed-origin Sharpe | 1.756087 | ≥ 1.65748 |
| 10%-vol-normalized stitched return | 17.5609% | ≥ 16.57% |
| stitched max drawdown | -9.3657% | ≥ -12.27% |
| current-IS Sharpe @ 12% ATR | 1.368714 | > 1.0 |
| integrity (weights + native prefix) | PASS | — |
| extra-day-lag control not better | 1.329655 < 1.756087 | — |

The static 50/50 comparator on the same stitched windows had Sharpe **1.761477**, annualized return **43.7967%**, volatility **24.8636%**, max drawdown **-9.2768%**. The trigger returned **-0.0054** Sharpe relative to it, and its correlation to it was 0.99867. Origin stability: mean origin Sharpe 0.930295, positive-origin fraction 66.67%, 730-day recency-weighted origin Sharpe 0.364628. Correlation was 0.934 to breadth and 0.752 to VCB. Bounded 365-day replay matched at all 7 checkpoints.

## Interpretation

Two execution overlays (2% band, 5% trigger) have now failed to cut turnover by 10% without giving up economics. The ensemble's turnover is not made of small, spread-out adjustments that a threshold can suppress. It comes from genuine target moves, mostly in the breadth sleeve (ρ 0.93). Further execution-threshold studies on this blend are low-value. Keep the **static 50/50** as the incumbent.

## Measurement defect found and repaired (before economics were observed)

Run `36509822132` failed the adapter prefix-causality check at row 1442 (diff 0.209). Sponsor data contains **3 non-positive close cells**. A zero close makes `c / c.shift(1)` infinite, and bottleneck's running-sum rolling kernels then diverge from native xarray for hundreds of days. For the frozen static blend, the two backends disagree on **210 days** (max |Δw| 0.209). The frozen members' weights therefore depend on which backend is installed. This is an infrastructure defect, not lookahead. Economics above use the default backend for comparability with all earlier measurements.

## Production adapter `q25_vcb_breadth_static_ensemble_v2`

`submissions/q25_vcb_breadth_ensemble_singlepass.py` treats non-positive closes as missing before forming returns. It passes prefix causality/bounded replay on Sponsor data (max diff 6.2e-12). It differs from the default-backend research blend on 257 days (max 0.209), and all of those differences come from the zero-close defect.

| Current IS (2016-01-01 → 2026-09-27) | 4% ATR | 8% ATR | 12% ATR |
|---|---:|---:|---:|
| Sharpe | **1.716182** | 1.528050 | 1.338624 |
| CAGR | 71.14% | 60.19% | 49.92% |
| Max drawdown | -33.68% | -36.19% | -38.83% |
| Avg turnover | 0.07013 | 0.07015 | 0.07018 |

The contest gate (IS Sharpe > 1.0) holds with margin at every cost level. The frozen default-backend blend measured 1.761221 at 4% on the same panel. The 0.045 gap is the price of backend-invariant behaviour, not an economic change to the mechanism. Stitched origin economics were not re-measured for v2.

No parameters were changed after observing these results.
