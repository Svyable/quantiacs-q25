# HELIOS causal refinement

**Measured 2026-09-14 · development only · `FALSIFIED_DEVELOPMENT` · promote zero.**

The user supplied a 4,748-line VIPER–HELIOS v22 strategy. This work translates
its most useful engineering ideas into a self-contained implementation and tests
them with the repository's exact evaluator. It does **not** reproduce v22 or
inherit its reported Sharpe. The new candidate did not earn promotion.

[Standalone Python](../strategies/generated/q25_helios_causal.py) ·
[Frozen experiment](../experiments/helios_20260914/manifest.json) ·
[PM report](../experiments/helios_20260914/pm_report.md) ·
[Exact evidence](../evidence/helios_20260914/report.md)

## What was built

| Layer | Implementation | Test of its contribution |
|---|---|---|
| Factor construction | Volatility-normalized momentum, close-location/volume flow, path/downside quality, low risk; cross-sectional centering and residualization against momentum | Compare matched fixed-prior factor book |
| Delayed learning | Rank IC on completed 5- and 21-day outcomes, separately sampled without overlap; uncertainty/count shrinkage; 65% fixed-prior anchor | Freeze priors or rotate learned factor assignments |
| Portfolio risk | Finite EW covariance, 50% single-market-factor shrinkage, positive definite floor, conviction-weighted risk-budget solver | Remove off-diagonal covariance while preserving learning |
| Execution | ATR-aware admission, Monday target updates, exits that cannot reopen midweek, declining intraweek gross ceiling | Remove ATR admission while keeping exact evaluation costs |
| Exposure | Own-price trend filter, breadth and finite-window market drawdown, 40% annualized target at allocation, 25% name cap, cash | Audit raw weights and replay; no leverage or forced gross floor |

These are refinements of V10/factor-balance architecture. They are not new
independent raw-information mechanisms. The previously failed Frontier-F
expert/cash policy and state-conditioned posterior were not retuned.

Every dependency in `strategy(data)` is NumPy, pandas or xarray. Quantiacs is
imported only by the executable runner, after local access is configured.
The function returns a complete `time × asset` path in the caller's coordinate
order. It neither fetches data nor reads a model/cache from disk.

## Timing and replay

The target dated `t` uses the completed daily bar at `t`. The official evaluator
applies the execution lag; the strategy does not shift the whole target again.
For a training observation completed on day `u`, factor values from `u-h` are
paired with the fully realized return from `u-h` to `u`. Coefficients are then
lagged one more day, so a decision on `t` learns only from outcomes ending by
`t-1`.

The membership mask comes from the original forecast date, not from the
survivors on the label's ending date. Prices must be complete across the label
interval. Unavailable labels are censored rather than replaced by zero returns.
The 5- and 21-day streams can overlap each other; nonoverlap applies **within**
each stream. Shrinkage is deliberately conservative, not a calibrated posterior.

The largest declared memory window is 189 days. Adding feature history,
outcome maturity, the embargo and the weekly holding interval requires at most
343 daily rows. This fits the repository's fixed 365-day replay check. No
all-history EWM, expanding neural fit, previous Python invocation or shifted
training schedule is needed to reconstruct the latest target.

Monday updates hold **target weights**, not fixed quantities. Price drift can
still create daily trading under Quantiacs accounting. The ATR hurdle compares
volatility-scaled conviction with a round-trip cost proxy; it is not an estimate
of expected profit. Risk targeting is performed on each desired allocation;
the intraweek gross ceiling is conservative but is not a guarantee that actual
realized volatility stays below 40%. The name cap is an internal constraint.

## Exact results

All ten objects completed: three base windows, four matched controls and three
repository baselines. The score is the **minimum Sharpe across 2016–2020 and
2021–2022 at 4%, 8% and 12% ATR costs**. It is a research policy score, not the
official full-history eligibility calculation or a contest-period result.

| Object | Robust development Sharpe | Interpretation |
|---|---:|---|
| Existing persistent-low-vol control | 0.641 | Baseline; also below the policy floor |
| HELIOS, 189-day learning | 0.320 | Best base; no promotion |
| Misassigned learned factor weights | 0.302 | Beats the central parent; fails the skill-assignment test |
| No ATR admission hurdle | 0.294 | Beats the central parent; proposed hurdle does not earn its place |
| HELIOS, 126-day learning | 0.271 | Preregistered central parent |
| Existing equal-liquid control | 0.270 | Baseline |
| Diagonal risk model | 0.263 | Slightly worse than central parent |
| HELIOS, 63-day learning | 0.210 | Short-memory base |
| Static factor weights | 0.175 | Learning improves on this ablation, but fails the destructive control |
| Existing inverse-vol trend control | 0.053 | Baseline |

The central parent's fold breakdown shows why an attractive headline can be
misleading:

| Fold | Zero cost | 4% ATR | 8% ATR | 12% ATR |
|---|---:|---:|---:|---:|
| 2016–2020 | 2.622 | 2.497 | 2.371 | 2.245 |
| 2021–2022 | 0.662 | 0.532 | 0.402 | 0.271 |

At 12% ATR, central-parent maximum drawdown was **−17.88%** in research and
**−35.38%** in development. Its downside was materially smaller than the
persistent-low-vol control's, but it failed the preregistered Sharpe and
mechanism tests. The 189-day best result is a boundary point, not a demonstrated
parameter plateau. Do not extend the window grid to rescue it.

Matched development correlation was 0.791 versus inverse-vol trend, 0.624 versus
persistent low vol and 0.591 versus equal liquid. The regression fitted on the
research fold produced a negative development residual-Sharpe diagnostic.
Historical V10/V11/V12 matched streams were unavailable in this harness; no
historical-core diversification or sponsor uniqueness clearance is claimed.

The paired bootstrap is descriptive on reused development data. Its intervals
are not adjusted for selection and cannot override the frozen decision rule.
All four ablations/falsifiers change actual allocations; they are not score
changes discarded by the allocator. See the
[mechanism diagnostics](../evidence/helios_20260914/mechanism_diagnostics.json).

## Audit of the supplied v22 reference

Source identity is recorded by SHA-256 in the preregistrations. These findings
come from inspection of the supplied text; v22 itself was not benchmarked.

| Reference area | Why it needs scrutiny | Handling here |
|---|---|---|
| `compute_portfolio_returns` / `summarize_metrics` | Multiply target weights by same-date close returns; some allocation overlays use that same completed close. These diagnostics are not proof of executable P&L or parity with official stats. Same-bar conditioning can inflate the report. | Only official `qnt.stats.calc_stat` metrics are reported |
| Custom cost subtraction | Uses changes in target weights and its own ATR estimate; does not establish equivalence to execution, drift, missing-data and cost conventions in the toolbox | Exact cleaner and full official cost ladder |
| Neural warm-up / expanding fit | `TORCH_MIN_TRAIN_DAYS=756` means a 365-day input cannot activate the learned head; positional retraining and expanding histories need an explicit replay contract | Finite, calendar-anchored learning and 365-day replay tests |
| Broad exception fallbacks | `strategy` returns cash on any exception; the runner catches cleaning/writing/reporting errors. Software failures can resemble valid flat output or successful diagnostics | Missing observations have explicit rules; unexpected programming errors propagate |
| On-chain loaders | Separate sponsor datasets need current contest availability, publication timing and revision/replay checks | OHLCV and historical liquidity only |
| Trial-Sharpe list and numerous revisions | Hard-coded trial results and tuned versions are not evidence for a new implementation | Parameters and falsifiers frozen before measured returns |

The reference's delayed-label idea is useful. The issue is establishing its
decision-time and execution semantics, not treating every forward-label array
as automatically noncausal. Likewise, a neural architecture is not evidence
of superior forecasting.

Official context: the [Quantiacs crypto guide](https://quantiacs.com/documentation/en/examples/q24_crypto_guide.html)
documents automatic liquid selection, sponsor data and single/multipass
comparison. It is a Q24 guide, not fresh Q25-specific clearance for optional
datasets. Current toolbox source is frozen at
[`9e5274c`](https://github.com/quantiacs/toolbox/tree/9e5274c5ce102a66debc799fd2a2300969fb90f6).

## Reproduce

```bash
python -m pytest -q tests/test_helios.py
API_KEY=default python strategies/generated/q25_helios_causal.py
API_KEY=default python -m research.iteration \
  --manifest experiments/helios_20260914/manifest.json \
  --output results/helios_20260914 --budget 10
```

The standalone CLI defaults to 2016–2022 development reporting. `--write`
writes those research weights. The explicit `--platform-output` switch can
generate the frozen central strategy's latest weights for platform evaluation;
it does not calculate later-period metrics, submit or claim qualification.
It was **not run** in this campaign. In a notebook, call `strategy(data)` then
the normal Quantiacs cleaner/writer. Uploading this failed research candidate
is not recommended.

For allocator and paired-return diagnostics, load the same sponsor panel,
save it as NetCDF and run:

```bash
python scripts/analyze_mechanism_controls.py \
  --manifest experiments/helios_20260914/manifest.json \
  --run results/helios_20260914/<context-hash> \
  --data /absolute/path/to/sponsor_data.nc \
  --plan experiments/helios_20260914/diagnostics_plan.json
```

The data hash must be
`bc932fc6f016c2bc0fbf3f51bf6f59b48d895cd1ac7ed27602d63ecbfdc8bc58`.
The diagnostic plan is a schema adapter of the original frozen settings,
using 21-day blocks, 500 bootstrap draws and seed 7.

## Evidence boundary and next work

Prefix and bounded replay passed at seven real-data checkpoints per object;
sampled parity is not a complete hosted multipass run. The central candidate's
entire evaluation, including repeated replay and the cost ladder, took about
12 seconds locally. This is not a hosted runtime certification.

Raw targets obey strict liquidity and cap rules. The official cleaner changed
one central-candidate cell on missing-price/nonfinite-liquidity data; the
existing evaluator classified that as `PLATFORM_DATA_TRANSLATION`, with **zero
unexplained changed cells**. Cleaner output was not literally identical to raw
targets; the exact translation is preserved in the packet.

No 2023–2024 validation, 2025+ diagnostic, current full-IS eligibility,
authenticated correlation, hosted multipass or submission was performed. The
live contest period remains untouched. Preserve these formulas and failed
controls. Reusing the tested numerical components requires a separately
specified hypothesis; adding more overlays or tuning the frozen windows does
not repair this result.
