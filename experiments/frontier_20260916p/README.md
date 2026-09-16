# Frontier-P — liquidity requalification hysteresis

Status: **IMPLEMENTED / UNMEASURED**. This campaign is preregistered development research, not a promoted Q25 strategy.

## Question

Does historical Crypto10 eligibility carry cross-sectional information beyond current `is_liquid` membership and ordinary short residual price efficiency?

The canonical signal treats membership as a state process rather than a one-day lifecycle event. For each currently eligible asset it compares recent 14-day eligibility persistence with a longer 42/63/84-day memory, multiplies the improvement by prior exclusion memory, penalizes repeated eligibility churn, and requires at least seven consecutive eligible days. That eligibility-memory state is paired with positive seven-day market-residual path efficiency.

This is deliberately separated from V11's simple new-asset / positive-entry lifecycle sleeve: two assets can have identical current entry age but different Frontier-P state because their longer eligibility histories differ.

## Frozen cells

Three base windows (42, 63, 84), central 63; one ablation that removes all historical membership state; one falsifier that rotates the complete eligibility-memory state across currently eligible asset identities. Allocation is top-five fixed slots on Mondays with immediate liquidity exits and unused gross left in cash.

The exact repository controls and 0/4/8/12% ATR-linked cost ladder apply. Selection uses only the reused research/dev folds. The 2023-2024 forward period is spent and excluded; 2025+ and live cannot drive mutation.

Preregistration SHA256: `c9557848eb0b1de6b4f29c59a343e0f2e77179b8b22aa6f0284315c5e9354ccf`.

No Frontier-P return metric was observed before the implementation freeze.
