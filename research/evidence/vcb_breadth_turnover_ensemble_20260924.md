# VCB × breadth 2% turnover-band evidence — 2026-09-24

Status: **FALSIFIED / DO NOT PROMOTE**
Evidence label: `ADAPTIVE_REUSE`
Experiment: `vcb_breadth_turnover_ensemble_20260924`
Measurement head: `6cda06db776a58a3e2847f4d8ea36bc9f9d15b51`
Workflow run: `35995495837` (`q25-turnover-ensemble` #3, success)
Artifact digest: `sha256:988934873ef5ec2860cb3ff179d376d2159068f308afb358c3daa27502e3c366`
Latest Sponsor date: 2026-09-23
Completed 90-day origins: 39

## Frozen hypothesis adjudication

The preregistered 2%-absolute asset-level no-trade band **fails its advancement gate**. It reduced current-IS target turnover from 0.0642693573 to 0.0598942013, a reduction of **6.8075%**, below the frozen requirement of at least **10%**. No threshold rescue or post-result band search is permitted; preserve this result so the 2% band is not recycled as an advancement candidate.

Other gates were economically strong but do not override the failed turnover gate. Current-IS band Sharpe was **1.760177** at 4% ATR, **1.577372** at 8%, and **1.393322** at 12%. Completed-history stitched 4%-ATR Sharpe was **1.788072**, annualized return **44.8398%**, annualized volatility **25.0772%**, max drawdown **-9.3560%**, and 10%-volatility-normalized return **17.8807%**. The static 50/50 comparator on the same stitched windows had Sharpe **1.761477**, annualized return **43.7967%**, volatility **24.8636%**, max drawdown **-9.2768%**, and normalized return **17.6148%**.

Origin stability: mean origin Sharpe **0.938254**, positive-origin fraction **64.1026%**, 730-day recency-weighted origin Sharpe **0.386214**. Correlation was **0.933130** to breadth and **0.752851** to VCB. The frozen extra-day-lag destructive control had stitched Sharpe **1.359957**, materially below the causal band result.

## Interpretation

The band marginally improved stitched Sharpe versus static 50/50 (+0.02660) and passed the stressed 12%-ATR Sharpe >1 hard gate, but its intended mechanism was turnover reduction and it did not achieve the preregistered minimum. Treat the 2% band as falsified for advancement. The static 50/50 VCB × breadth ensemble remains the incumbent reference rather than promoting this execution overlay.

No parameters were changed after observing these results.