# Frontier-P — liquidity requalification hysteresis

Status: **MEASURED / FROZEN / FALSIFIED_DEVELOPMENT**. This campaign is development research, not a promoted Q25 strategy.

## Question

Does historical Crypto10 eligibility carry cross-sectional information beyond current `is_liquid` membership and ordinary short residual price efficiency?

The canonical signal treats membership as a state process rather than a one-day lifecycle event. For each currently eligible asset it compares recent 14-day eligibility persistence with a longer 42/63/84-day memory, multiplies the improvement by prior exclusion memory, penalizes repeated eligibility churn, and requires at least seven consecutive eligible days. That eligibility-memory state is paired with positive seven-day market-residual path efficiency.

This is deliberately separated from V11's simple new-asset / positive-entry lifecycle sleeve: two assets can have identical current entry age but different Frontier-P state because their longer eligibility histories differ.

## Frozen cells

Three base windows (42, 63, 84), central 63; one ablation that removes all historical membership state; one falsifier that rotates the complete eligibility-memory state across currently eligible asset identities. Allocation is top-five fixed slots on Mondays with immediate liquidity exits and unused gross left in cash.

The exact repository controls and 0/4/8/12% ATR-linked cost ladder apply. Selection uses only the reused research/dev folds. The 2023-2024 forward period is spent and excluded; 2025+ and live cannot drive mutation.

Preregistration SHA256: `c9557848eb0b1de6b4f29c59a343e0f2e77179b8b22aa6f0284315c5e9354ccf`.

## Observed development result

The first exact Quantiacs measurement completed successfully under the frozen source and preregistration.

- best base: `w84` robust Sharpe **-1.354**
- central `w63`: robust Sharpe **-1.432**
- `w42`: robust Sharpe **-1.719**
- no-history ablation: robust Sharpe **-0.175**
- rotated-state falsifier: robust Sharpe **-0.998**
- family decision: **FALSIFIED_DEVELOPMENT / FREEZE**

Both destructive controls beat the central parent, and every base misses the fixed 1.0 development floor. Preserve the negative result; do not invert, retune or grid-rescue the family.

Canonical measurement receipt: `evidence/measurement_receipts/frontier_20260916p.json`.
