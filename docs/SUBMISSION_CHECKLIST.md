# Submission Checklist — Hosted `strategy.ipynb`

Hosted Quantiacs boundary (Layer 3). Mark each item **DONE** / **PENDING** / **N/A**.

## Pre-flight (local)

- [ ] Experiment preregistered (`experiments/<id>/preregistration.json` + SHA256)
- [ ] L0–L9 policy reviewed (`docs/TESTING_PYRAMID.md`)
- [ ] Contest-hard gates understood: IS Sharpe **> 1.0**, long-only, `is_liquid`, uniqueness
- [ ] No fabricated metrics in docs or registry
- [ ] Strategy uses only Quantiacs cryptodaily fields
- [ ] No hand-picked asset list
- [ ] `competition_type = crypto_daily_long`
- [ ] Promotion decision recorded (promote / kill / hold)

## Notebook skeleton

Use `templates/strategy.ipynb` or equivalent:

1. Markdown: contest id, experiment id, track, mechanism, falsifier (no metrics claims)
2. Code: imports + `API_KEY` / host session assumptions
3. Code: `load_data` / data load (`cryptodaily_load_data`)
4. Code: `strategy(data)` — long-only × `is_liquid`
5. **Path A — single-pass style:** clean → check → write  
   - [ ] `qnout.clean` (or current host equivalent)  
   - [ ] `qnout.check` / stats print  
   - [ ] `qnout.write`  
6. **Path B — multipass:** `qnbt.backtest(..., load_data=..., competition_type="crypto_daily_long", ...)`  
   - [ ] `lookback_period` / `start_date="2016-01-01"`  
   - [ ] `analyze=True`, `check_correlation=True` as appropriate  
7. Markdown: results section labeled **OBSERVED** (paste from run) or **PENDING**

## Hosted run

- [ ] Notebook executed on Quantiacs host (or marked **PENDING**)
- [ ] Correlation / uniqueness filter reviewed
- [ ] IS Sharpe from host stats recorded only if observed
- [ ] Submission slot within contest limits (max running / participate — see rules snapshot)
- [ ] Deadline awareness: **2026-09-30**; live **2026-10-01 → 2027-01-31**

## Post-submit

- [ ] Registry / experiment ledger updated with host run id (if any)
- [ ] PM report section “Submission readiness” filled
- [ ] Do not retune on live contest prints during the live window for “research”

## Honesty

If the hosted notebook was **not** run, write **PENDING** clearly. Do not invent host Sharpe or correlation outcomes.
