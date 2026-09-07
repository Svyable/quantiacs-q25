# experiments/ — append-only research ledger

Each experiment lives in `experiments/<id>/` and is **append-only**:

- Do **not** delete failed experiments to “clean up.”
- Do **not** rewrite preregistration after peeking at holdout.
- Record kills and passes in `formula_ledger.csv` (header from `templates/`).

## Create

```bash
python scripts/new_experiment.py \
  --track robustness \
  --mechanism momentum \
  --thesis "Weekly SMA trend + capped water-fill survives mid cost ladder" \
  --falsifier "Sign-flipped trend or daily uncapped equal-weight matches cost-stressed Sharpe"
```

This writes:

- `preregistration.json` + `preregistration.sha256`
- `formula_ledger.csv` (header)
- `pm_report.md` stub

## Status vocabulary

| Status | Meaning |
|--------|---------|
| `preregistered` | Hypothesis locked; no holdout peek |
| `running` | Local pyramid in progress |
| `failed` / `killed` | Falsified or gates failed — **keep** |
| `passed_local` | Local gates OK; hosted still PENDING |
| `submitted` | Hosted boundary executed / submitted |
| `PENDING` | Metric or layer not yet run — never invent numbers |

## Dual-track note

Prefer linking discovery and robustness experiment ids when they test the **same mechanism**. Convergence is stronger evidence.
