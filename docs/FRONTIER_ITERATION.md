# Frontier strategy campaign and iteration engine

The old factory renders ideas but does not run or extract backtests. This campaign
adds three executable families and a bounded development benchmark with resumable,
content-addressed results. The six preregistrations and 24-hypothesis slate are in
[`experiments/frontier_20260910`](../experiments/frontier_20260910).

## Families

| Family | Measured object | Nearest incumbent | Changed axes | Destructive control |
|---|---|---|---|---|
| Forecast surprise | Error from a rolling residual AR(1) forecast made before the outcome | V10 residual momentum | Transform; timing/state | Pair each asset with another asset's forecast |
| Flow absorption | Abnormal dollar volume × high close location × small candle body | V12 directed volume diffusion | Transform; timing/state | Destroy own-asset flow/price pairing |
| Volatility curve | Short/middle/long volatility shape, curvature, and recovery | C165/inverse-vol trend | Transform; timing/state | Invert curve-shape gate |

These are novelty hypotheses, not established independent alpha. Residual tests
against three executable controls are implemented. Historical V10/V11/V12 return
streams are absent, so comparisons with that historical core remain PENDING.
The frozen roster is unchanged. On-chain and benchmark-weight signals remain out
of this campaign because publication/revision/replay semantics are unverified.

Each standalone Python file in `strategies/generated/frontier_20260910_*.py`
contains its own signal and allocation code. It needs only numpy, pandas, xarray,
and the Quantiacs toolbox for execution, with no repository imports. Targets use
completed daily data; Quantiacs applies its next-execution shift. Finite rolling
state reconstructs within 365 daily bars. Weekly allocations have a 25% name cap,
unit gross limit, cash for empty slots, and daily historical-liquidity masking.

The Lattice attachment motivates a finite candidate space, explicit constraints,
and preserving eliminated candidates. It supplies no financial evidence, and
statistical falsification here is not claimed to be sound logical deduction.

## Run

Install the repository requirements plus pytest in a Python environment, then set
`API_KEY` through your environment or the gitignored `.env` file. Never put it in
code, a command-line argument, a result artifact, or a commit.

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q tests
python -m research.iteration --budget 18
```

The default campaign has **18 evaluations**: three coarse lookbacks for each of
three families, one matched canonical ablation and one canonical falsifier per
family, and three controls. Controls are equal-liquid, inverse-vol trend, and
persistent low volatility. The canonical tests examine mechanism interpretation;
noncanonical variants are plateau checks, not separately validated mechanisms.
Do not advance a noncanonical winner without its own matched falsifiers.

Use a smaller budget to split work into iterations:

```bash
python -m research.iteration --budget 6
python -m research.iteration --budget 6
python -m research.iteration --budget 6
```

Identical inputs resume the same directory. Completed and failed evaluations are
preserved and skipped. A new code/data/config identity creates a separate result
set; never overwrite a failed run. Exit code 2 means blocked or incomplete, not a
successful economic evaluation. Setup failures produce a dated blocked report
with null metrics and no ranks. There is no synthetic-performance fallback.

## Benchmark conventions

- Sponsor `cryptodaily` data from 2015 supplies warm-up; selection stops at the
  end of 2022. Validation, diagnostics and live data never enter mutation/ranking.
- Research: 2016–2020. Development: 2021–2022. Each fold starts a separate
  evaluation account using Quantiacs's first-row/cold-start convention.
- `qnt.stats.calc_stat` supplies exact local-toolbox metrics at ATR fractions
  0.00, 0.04, 0.08 and 0.12. These are **ATR multipliers, not basis points**;
  0.12 is a research stress beyond the supplied rule's stated 0.10 maximum.
- The dataset name must remain `cryptodaily`, because the toolbox uses it to
  choose arithmetic crypto Sharpe. Annualization is explicitly 365.
- Missing daily coverage, invalid weights, cleaner mutation, prefix mismatch or
  bounded-replay mismatch fail the evaluation. No cleaner-repaired strategy is
  silently substituted for the source strategy.
- Candidate score is minimum Sharpe over research/dev × 0.04/0.08/0.12. Ties use
  worst drawdown, then lower mean turnover, then stable candidate ID.
- Family stack rank uses the median of the three base scores, only after the
  entire grid and canonical destructive controls finish. Missing/failed/undefined
  evidence gets no performance rank. The zero-cost rung never selects winners.
- A canonical falsifier or ablation that equals or beats its parent freezes the
  family. Statistical failures are recorded, not repaired by blend tuning.
- Residual diagnostics fit exposures against the controls in 2016–2020 and apply
  them unchanged in 2021–2022. They are local research diagnostics, not official
  uniqueness clearance. No automatic portfolio combination or submission occurs.

Each run writes `context.json`, per-candidate metrics, daily return CSVs,
`attempts.jsonl`, the existing `RunRecord` registry format, `rankings.json`, a
readable `report.md`, residual diagnostics and a freeze ledger. Identity includes
strategy and engine hashes, data fingerprint, toolbox stats source and policies.
Code changes must be interpreted as additional research looks, even when a data
refresh produces a new directory. Budgets count candidates, not individual cost
rungs: an ordinary evaluation makes eight exact fold/cost calls.

## Boundaries and next iteration

The engine exhausts the declared coarse grid; it is not an unrestricted Sharpe
optimizer. New families require a new broad slate and preregistration. Parameter
changes outside the declared grid are rejected. Campaign creation fails if the
original campaign directory exists, protecting preregistrations from reruns.

After a family survives development, freeze an exact candidate and run validation
2023–2024, diagnostic regimes, full-IS eligibility, matched historical-core
comparisons, complete multipass, and hosted uniqueness/runtime checks. These are
**not implemented as automatic promotion** in this first engine. Existing numeric
policy gates remain unset. Neither a high development rank nor green software CI
qualifies a contest entry. Full-IS Sharpe strictly greater than 1 must be measured
on the official evaluation span; this engine does not claim that gate passed.

Sources: the supplied Q25 rules/example; the repository frontier and external
research leads; [official guide mechanics](https://quantiacs.com/documentation/en/examples/q24_crypto_guide.html)
and [official toolbox stats implementation](https://github.com/quantiacs/toolbox/blob/master/qnt/stats.py).
The linked guide is labeled Q24 and is used for API mechanics, not as a substitute
for current Q25 submission verification.
