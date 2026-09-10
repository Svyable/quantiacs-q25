# Frontier-D: serial dependence and ordinal leadership

**Decision: freeze both families; promote zero strategies.** All ten candidate/control cells and three generic controls earned valid exact Quantiacs return streams. Both families failed the frozen destructive-control comparison and all six base cells missed the 1.0 development floor. These results advance the research process, but do not demonstrate additional profitable alpha.

## Mechanisms and novelty

The campaign considered 24 scored hypotheses across serial dependence, ordinal leadership, range geometry and execution economics, then preregistered six. Two were implemented to keep the measurement budget finite. Four unimplemented hypotheses remain preregistered, not economically rejected.

- **Variance-ratio reversal:** estimate whether five-day variance is smaller than five times daily variance, using only observations through yesterday. Buy recent relative losers when that serial-dependence state predicts reversal and the market's 21-day return is positive. This tests serial dependence and conditional reversal, beyond the existing volatility-curve, signed-risk and generic mean-reversion mechanisms.
- **Rank transition:** measure improvement in five-day-return percentile over 21 days and discount it by historical rank-transition noise. This measures ordinal leadership and reliability, rather than return consistency or graph centrality. Its ablation asks whether the reliability term adds anything beyond rank migration.

Both use historical eligibility, five fixed 20% slots, cash, Monday entries and immediate exits on invalid prices or eligibility loss. An exit stays closed until Monday; recovering eligibility cannot revive a stale holding. Existing frozen strategies were not silently changed.

The official [Quantiacs crypto guide](https://quantiacs.com/documentation/en/examples/q24_crypto_guide.html) supplies OHLCV and backtesting conventions, not evidence for these economic hypotheses. No additional dataset permission is assumed from the earlier contest guide.

## Frozen contract and provenance

Preregistration commit: `7811b04`. Implementation and analysis-plan freeze: `7bbb7b2`. Exact preregistration SHA256 values are in each hypothesis directory and its generated strategy docstring. Manifest and data hashes, source hashes, toolbox version, dependency versions, candidate packets and matched returns are preserved in [the evidence directory](../../evidence/frontier_20260910d/).

The local public/default endpoint supplied 2015–2022 data, with 2015 reserved for warm-up. No old cached research dataset was substituted. An initial numerical-library SIGBUS prevented importing the statistics engine; fresh numerical-library binaries resolved it without strategy changes. See `source.json` for that infrastructure history.

## Observed economics

The robust score is minimum Sharpe across research (2016–2020) and development (2021–2022) at 4%, 8% and 12% ATR-linked slippage. All four configured costs, including zero cost, are preserved in each raw candidate JSON.

| Cell | Robust Sharpe | Research SR, 12% | Dev SR, 12% | Worst DD, 12% |
|---|---:|---:|---:|---:|
| Reversal, W42 | -0.140 | 1.416 | -0.140 | -80.2% |
| Reversal, W63 | -0.284 | 1.676 | -0.284 | -75.2% |
| Reversal, W84 | -0.176 | 1.709 | -0.176 | -76.3% |
| Reversal, remove variance-ratio condition | 0.158 | 1.274 | 0.158 | -81.8% |
| Reversal, invert condition | 0.478 | 0.478 | 0.926 | -59.1% |
| Rank transition, W42 | 0.110 | 1.650 | 0.110 | -75.8% |
| Rank transition, W63 | 0.057 | 1.592 | 0.057 | -75.7% |
| Rank transition, W84 | 0.144 | 1.459 | 0.144 | -78.7% |
| Rank, remove reliability | 0.057 | 1.590 | 0.057 | -75.7% |
| Rank, permute reliability | 0.057 | 1.589 | 0.057 | -76.4% |

The persistent-low-volatility control scores 0.641 under this same run. The reversal falsifier is an experimental control, not a newly selected winner. Its positive residual diagnostic does not override its weak robust score or qualify it for promotion.

## What the methodology revealed

The rank reliability term changes targets on only 14 of 2,922 warm-up/research/development dates relative to its ablation, and produces **identical 2021–2022 net returns**. The fixed-slot allocator usually selects all positive migration candidates, so reweighting their scores rarely changes holdings. Signal complexity was mostly discarded by portfolio construction. This is an implementation-to-economics limitation, not a software exception.

The reversal conditioning term does change the portfolio, but in the wrong direction under the frozen decision rule. Relative to its ablation, the central candidate's annualized arithmetic development return difference is -38.0 percentage points. A paired 21-day circular block bootstrap gives a wide 95% interval of [-85.1, +6.0] points. Against its inverted-condition control, the difference is -44.8 points with interval [-111.0, +19.6]. These are uncertainty diagnostics on reused development history, not CAGR, selection-adjusted significance or proof of a population effect. They cannot rescue the failed gates.

The permutation falsifier now rotates only through currently eligible finite observations, preserving that cross-section's marginal distribution. Adding a future-listed or permanently ineligible column cannot change the tested portfolio. This prevents an apparently destructive control from succeeding merely by moving a valid signal into an ineligible asset.

## Originality and evidence boundaries

Research-trained regression against equal-liquid, inverse-volatility trend and persistent-low-volatility controls yields central development residual Sharpe of -1.394 for reversal and -1.238 for rank transition. The central rank candidate's correlations to those controls are 0.736, 0.765 and 0.712. Neither supports an independent-alpha claim. Exact historical V10/V11/V12 matched streams remain unavailable; no historical score is transplanted.

| Testing layer | Result |
|---|---|
| L0 admissibility | PASS: finite, long-only, historical liquidity, gross <=1 and name cap |
| L1 deterministic mechanics | PASS: complete grid, asset ordering, inactive-column invariance, exit/reentry and direct serial-order test |
| L2 prefix and bounded replay | PASS for all 13 measured objects at seven checkpoints; 365-day replay |
| L3 exact Quantiacs stats | OBSERVED_LOCAL, public_default; all 13 cells complete |
| L4 costs | OBSERVED at 0%, 4%, 8%, 12% ATR-linked slippage |
| L5/L6 time robustness | Research and development observed; validation, later diagnostics and live untouched by this campaign |
| L7 originality | Local controls observed; historical-core and authenticated uniqueness PENDING |
| L8 research accounting | 24 sketches, six hashed preregistrations, two implementations, six base variants, four destructive/ablation cells, three generic controls |
| L9 falsification | Both families FALSIFIED_DEVELOPMENT under the predeclared rule |
| Hosted/account-bound checks | PENDING; no submission or account selection |

The cleaner's exact translation diagnostics are retained in every raw record and self-contained candidate packet. Observed platform translation is not silently described as unchanged raw weights. CAGR, Sortino, Calmar, hit rate, turnover and runtime are likewise in the packets/records, not inferred from a neighboring strategy.

## Next frontier

1. Require material **portfolio-level** separation from the ablation before calling an interaction useful. A changed score is insufficient if allocation erases it.
2. Freeze serial-dependence reversal as tested. The inverted condition is a lead for an independently preregistered continuation study, not permission to reverse the trade after seeing these returns.
3. Retain the four other preregistrations as untested options. A future campaign should favor a different information object, such as range acceptance or an explicit execution hurdle, rather than tuning these two failed families.
4. Bring promising prior topology cells through the current integrity harness as a distinct repair/forward-evidence task. This campaign does not rewrite their historical evidence.

No validation or live window was used to repair these candidates. Positive research-period Sharpe alone would have given a misleading answer.

## Reproduce

Use the toolbox commit and versions in `evidence/frontier_20260910d/source.json`; the dedicated GitHub workflow installs the principal pinned dependencies.

```bash
API_KEY=default python -m research.iteration \
  --manifest experiments/frontier_20260910d/manifest.json \
  --output results/frontier_20260910d --budget 13
python -m pytest -q tests
python scripts/build_research_dashboard.py --check
```

The dedicated workflow also downloads the same sponsor panel, verifies its hash against the run, and runs `scripts/analyze_mechanism_controls.py` using the frozen analysis plan. It preserves evidence even if a later run fails. A future sponsor-data revision gets a different data hash and must not overwrite this captured evidence.
