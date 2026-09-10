---
title: Lab Control Plane
---

# Lab control plane

The repository now has a deterministic layer between **measured evidence** and **what an agent works on next**.

```bash
python -m research.lab status
python -m research.lab status path/to/matrix.json --json
python -m research.lab compare old/matrix.json new/matrix.json
python -m research.lab failures path/to/matrix.json
```

This is deliberately not another optimizer. It does not invent a composite alpha score or blend Sharpe, drawdown and turnover into one magic number.

## Triage vocabulary

| Action | Meaning |
|---|---|
| `REPAIR` | economics are unknown because the base implementation/evaluation failed; fix mechanics without retuning the hypothesis |
| `FORWARD_TEST` | valid base is on the development Pareto frontier and clears the predefined development Sharpe floor; seek untouched evidence |
| `KILL_WEAK_ALPHA` | valid base is below the predefined development floor; do not parameter-rescue it |
| `HOLD_DOMINATED` | valid base is dominated by another current base on robust Sharpe, drawdown and turnover |
| `HOLD` | evidence packet is incomplete |
| `CONTROL` | falsifier/ablation/control evidence; never promote as if it were an independent alpha |

## Pareto, not a beauty score

For valid development base strategies the Pareto screen uses three recorded quantities:

1. maximize the minimum Sharpe across research/dev × 4/8/12%-ATR cost cells;
2. prefer less severe worst 12%-ATR drawdown;
3. prefer lower mean 12%-ATR turnover.

A strategy is dominated only when another valid base is no worse on all three and strictly better on at least one. This preserves genuine trade-offs instead of hiding them in weights chosen after seeing the results.

## Campaign drift comparator

`research.lab compare` first checks evidence context. A score delta is called an **exact replay comparison** only when data, manifest, folds, costs and source hashes match. If the market panel/manifest/folds change, the tool labels the snapshots `NOT_DIRECTLY_COMPARABLE`. If the structural research context matches but evaluator/source hashes change, it labels the comparison `METHODOLOGY_OR_SOURCE_DELTA`.

That distinction matters whenever a bug fix suddenly “improves” a Sharpe. A methodological repair can reveal previously hidden economics, but it is not evidence that the alpha itself improved.

## Cleaner translation is evidence

The current Quantiacs toolbox cleaner can translate otherwise causal raw weights around data availability and liquidity handling. The benchmark therefore records cleaner impact rather than blindly requiring byte-for-byte parity.

The integrity rule remains strict: mutations explainable by the platform's missing-price/liquidity translation are measured and evaluated through the official cleaned path; mutations outside those masks remain a hard failure. The evidence packet records the number of changed cells/days, explained vs unexplained changes, and gross exposure before/after cleaning.

This makes failures reproducible and prevents a platform-adapter detail from masquerading as economic falsification.

[Research matrix](RESEARCH_MATRIX.md) · [Evidence model](EVIDENCE_MODEL.md) · [Testing pyramid](TESTING_PYRAMID.md)
