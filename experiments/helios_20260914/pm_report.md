# HELIOS — 2026-09-14 PM report

**Decision: `FREEZE / FALSIFIED_DEVELOPMENT`. Promote zero.**

This is a focused user-directed translation of the supplied VIPER–HELIOS v22,
classified as a factor-family refinement. The source audit and implementation
are useful engineering work; the economic hypothesis did not survive its
predeclared tests. No parameter was changed after viewing measured returns.

## Evidence and decision

Seven strategy cells and three repository controls completed the exact public
Quantiacs evaluator on reused 2016–2022 development data. No cell was invalid.
The central 126-day variant scored 0.271; the best base, 189 days, scored 0.320.
The score is worst research/dev Sharpe at 4/8/12% ATR. The internal development
floor is 1.0; it is distinct from the official full-IS eligibility calculation.

| Central comparison | Comparator score | Central score | Frozen test |
|---|---:|---:|---|
| Static factor priors | 0.175 | 0.271 | Parent wins |
| Rotate learned factor assignments | 0.302 | 0.271 | **Parent loses** |
| Diagonal covariance | 0.263 | 0.271 | Parent wins narrowly |
| Remove ATR admission hurdle | 0.294 | 0.271 | **Parent loses** |

The generic persistent-low-vol control scored 0.641, with materially worse
drawdowns. Neither its better score nor the parent's better drawdown overrides
the predeclared tests. No control is selected as a replacement winner.

The central parent's 12%-ATR research Sharpe was 2.245 and dev Sharpe 0.271.
Research/dev CAGR at that cost was 82.52% / 3.47%; maximum drawdown was
−17.88% / −35.38%. This is a clear deterioration across the two allowed folds.
The full fold/cost results, Sortino, Calmar, turnover and net return streams
are in the [evidence packet](../../evidence/helios_20260914/report.md).

## Mechanism and portfolio role

Four cross-sectional momentum, flow, quality and low-risk factors feed a
bounded, matured-label IC learner. Coefficients retain a 65% uniform-prior
anchor. A finite structured covariance estimator allocates conviction-weighted
risk budgets. Trend/breadth/drawdown gates, cash, 25% caps, weekly target updates
and an ATR admission proxy control exposure and trading.

Nearest incumbents: V10, slow factor balance, VIPER–HELIOS engineering library.
Changed axes are transform and portfolio construction, with the **same raw
information lineage**. This is not independent-alpha discovery. Frontier-F's
failed state-posterior and adaptive expert/cash formulas remain unchanged.

## Testing pyramid

| Level | Result | Scope |
|---|---|---|
| L0 admissibility | PASS | Raw targets finite, long-only, strict historical liquidity, gross ≤1, cap ≤25%; OHLCV only |
| L1 mechanics | PASS | 17 focused synthetic tests, including coefficients, solver and exit persistence |
| L2 causality/replay | PASS, sampled | Seven real-data checkpoints per object; prefix maximum difference zero; 365-day latest-target parity |
| L3 exact stats | OBSERVED | Official cleaner and `qnt.stats.calc_stat`; access `public_default` |
| L4 costs | OBSERVED | 0/4/8/12% ATR on both folds; no custom P&L substituted |
| L5 temporal robustness | WEAK | Large deterioration from 2016–2020 to 2021–2022 |
| L6 chronology | DEVELOPMENT ONLY | No fresh validation claim; 2023–2024 remains spent and excluded |
| L7 originality/residual | LOCAL DIAGNOSTIC | Three generic controls; negative development residual diagnostic; historical core streams unavailable |
| L8 preregistration | PASS | Three base windows and four matched controls frozen before returns; seven formulas accounted for |
| L9 falsification | FAIL | Misassigned skill and no-ATR controls beat central parent |

The official cleaner translated one central-candidate cell where both price
and liquidity were missing. There were zero unexplained changed cells. This is
not literal raw/cleaner identity; the existing harness's platform-translation
classification is retained. Full replay details and source/data hashes are
attached to each candidate packet.

The 21-day paired bootstrap used 500 draws and seed 7, frozen before returns.
All four 95% intervals for central-minus-control annualized mean returns span
zero. These are descriptive reused-development diagnostics, not proof of
significance or selection-adjusted inference. The operational falsification
decision follows the predeclared score rule. All controls change deployed
target paths, so the comparison is not an allocator-identifiability failure.

## Provenance and limits

- Preregistration: `factor_learning/preregistration.json`, SHA-256
  `2750dba67cce799732131b39ae606e42ef6d5d8e3a8a373b45a85832805e8cdf`.
- Exact implementation and manifest hashes: `implementation_freeze.json`.
- Data SHA-256:
  `bc932fc6f016c2bc0fbf3f51bf6f59b48d895cd1ac7ed27602d63ecbfdc8bc58`.
- Toolbox: `9e5274c5ce102a66debc799fd2a2300969fb90f6`; Python 3.12,
  NumPy 2.2.6, pandas 2.2.3, xarray 2025.12.0, Numba 0.61.2.
- The seven cells are one refinement campaign, not seven independent findings.
  The reference itself contains many prior revisions and unverified trial
  Sharpes; its selection history is not known and no metrics are transferred.
- Latest-data platform output, current full-IS eligibility, hosted multipass,
  participant-bound uniqueness/correlation and submission: **NOT RUN**.
- 2023–2024, 2025+ and the future live window were not loaded for evaluation.

## Next-frontier read-through

Freeze this formulation. Longer IC memory and an extra layer of risk/cost
logic did not establish a stronger robust strategy. The numerical building
blocks can be reused under a new independently specified hypothesis, but a
new window, gate threshold or blend weight would be rescue tuning.

The supplied strategy's custom contemporaneous P&L, expanding learned head,
optional external datasets and broad exception fallbacks deserve separate
execution/replay validation before its own report is trusted. See the
[reference audit and usage guide](../../docs/HELIOS_REFINEMENT.md).
