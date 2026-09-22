# ONSET — imported research record

**Do not advance.** The primary on-chain model measured full historical Sharpe 1.1739, later (2023+) Sharpe 0.7148 and recent (2025+) Sharpe -0.6242 through 2026-09-15. Full drawdown was -54.62%. These are local official-toolbox measurements with 0.04 ATR slippage, not contest estimates.

The source at `strategies/generated/q25_onset.py` is byte-for-byte the previously delivered single-file strategy. Six current sponsor blockchain series feed four weekly rolling ridge models, trained only on matured 7/21-day outcomes. A risk-managed historical-liquid basket receives the model's exposure. An unforecasted basket outperformed it; recent primary Sharpe remains negative even at zero slippage (-0.4533).

## Evidence boundaries

- Original design and source audit: `experiments/onset_20260916/`.
- Complete imported trial metrics and daily returns: `evidence/onset_20260916/imported/`.
- Human-readable original report: [report.html](report.html).
- Original 2016–2022 combined development scoring differs from the repository's minimum research/dev × cost score. Do not silently cross-rank these metrics.
- Later history was already exposed: diagnostics, not fresh validation.
- Three prefix and three 1,825-day bounded-replay checkpoints matched exactly. This is not exhaustive multipass.
- On-chain release/revision vintages and current Q25 eligibility remain unverified; hosted correlation was not run.
- Snapshot hashes are preserved; raw sponsor data and virtual environments are excluded from Git.

## Reproduce the candidate

Install `experiments/onset_20260916/requirements.txt` in Python 3.12. With sponsor data access:

```bash
API_KEY=default python strategies/generated/q25_onset.py --end 2026-09-15 --out results/onset_replay
```

To match the original snapshots exactly, supply `--crypto /path/to/crypto_data.nc --chain-dir /path/to/fresh_alpha`. Current provider data may contain revisions. Do not modify the frozen source to improve these results.

## Next refinement

First deepen the record using the repository's exact evaluator and fold/cost policy. Then separately preregister an OHLCV-only allocator experiment against the unforecasted basket. The new work must keep ONSET's failed prediction hypothesis frozen and use matched-gross controls to distinguish asset allocation from cash exposure. Any such test is an allocator refinement, not an independent-alpha claim.
