# Q25 deadline submission shortlist — 2026-09-18

These are **current measured candidates**, not historical claims. All metrics use Quantiacs crypto-daily data from 2016-01-01 onward and the contest ATR-linked slippage model. Account-bound correlation/uniqueness remains unresolved until the exact files are run under the participant account.

| Candidate | Production mode | Sharpe @ 4% ATR | Sharpe @ 8% | Sharpe @ 12% | Max DD @ 4% | Avg turnover @ 4% | Vol @ 4% | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| lattice_consensus | multipass, 365d | 1.4599 | 1.2584 | 1.0564 | -76.07% | 0.1372 | 62.19% | qualified; account correlation pending |
| q25_sota_meta_ensemble_v1 | multipass, 900d | 1.3474 | 1.2086 | 1.0695 | -74.23% | 0.0700 | 47.44% | qualified; account correlation pending |
| hit126_consistency | single pass, parity-proven | 1.2070 | 1.1340 | 1.0609 | -75.02% | 0.0542 | 61.68% | qualified; account correlation pending |

## Current deployment order

1. **Lattice multipass** for highest measured contest-cost Sharpe. Do not substitute its single-pass history panel: recent single/multipass weights diverged by as much as 0.25.
2. **SOTA meta multipass** as the lower-volatility, lower-turnover diversified alternative. Its 12%-ATR stress Sharpe is slightly stronger than lattice's despite lower 4%-ATR Sharpe.
3. **Hit126 single pass** as the simplest hardened fallback. Real-data parity is effectively exact and the mechanism survives destructive controls.

## Submission discipline

- Do not retune these candidates after the measurements above.
- Do not attach historical Top-10 metrics to these current source files.
- Run the exact packaged file through the participant/account-bound correlation filter before treating it as prize-eligible.
- If a candidate fails uniqueness, move to the next frozen candidate rather than modifying the failed file to chase the filter.
- Preserve multipass for lattice and SOTA; use single pass for hit126 only because parity was explicitly demonstrated.
