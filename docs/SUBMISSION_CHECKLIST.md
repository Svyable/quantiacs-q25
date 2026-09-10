# Submission Checklist — Hosted / Account-Bound Boundary

Layer 3 begins **after measured local research**. Mark each item **DONE** / **PENDING** / **N/A**.

A personal Quantiacs credential is **not required for local/public-data research**. The repo harness uses `API_KEY=default` for that layer. A real participant key or authenticated hosted session may be required for participant-specific correlation/precheck, account identity and submission.

See [`LOCAL_RESEARCH_ACCESS.md`](LOCAL_RESEARCH_ACCESS.md).

## Pre-flight — measured local evidence first

- [ ] Experiment preregistered (`experiments/<id>/preregistration.json` + SHA256)
- [ ] L0–L9 policy reviewed (`docs/TESTING_PYRAMID.md`)
- [ ] Contest-hard gates understood: IS Sharpe **> 1.0**, long-only, `is_liquid`, uniqueness
- [ ] No fabricated metrics in docs or registry
- [ ] Strategy uses only currently permitted Quantiacs contest data
- [ ] No hand-picked asset list
- [ ] `competition_type = crypto_daily_long`
- [ ] Local/public Quantiacs metrics attempted with the frozen candidate; missing personal credentials were **not** treated as a blocker
- [ ] Local access provenance recorded as `public_default` or `authenticated`, never the key
- [ ] Prefix, liquidity, cleaner/missed-date, gross/long-only and cost checks recorded where applicable
- [ ] Promotion decision recorded (promote / kill / hold)

## Notebook skeleton

Use `templates/strategy.ipynb` or equivalent:

1. Markdown: contest id, experiment id, track, mechanism, falsifier and exact frozen candidate identity
2. Code: imports + explicit access/session assumptions  
   - local/off-host reproduction: initialize `API_KEY=default` before importing `qnt` when no participant key exists  
   - hosted/authenticated environment: use the platform session; never paste/commit a credential
3. Code: `load_data` / data load (`cryptodaily_load_data`)
4. Code: `strategy(data)` — long-only × historical `is_liquid`
5. **Path A — single-pass style:** clean → check → write  
   - [ ] `qnout.clean` (or current host equivalent)  
   - [ ] `qnout.check` / stats print  
   - [ ] `qnout.write`  
6. **Path B — multipass:** `qnbt.backtest(..., load_data=..., competition_type="crypto_daily_long", ...)`  
   - [ ] `lookback_period` / `start_date="2016-01-01"`  
   - [ ] `analyze=True`  
   - [ ] `check_correlation=True` only when the environment can perform the intended participant/account-bound check
7. Markdown: split results into **OBSERVED LOCAL**, **OBSERVED HOSTED/ACCOUNT**, and **PENDING** rather than collapsing all layers into one status

## Hosted / account-bound run

- [ ] Exact locally frozen candidate executed on Quantiacs host when required (or marked **PENDING**)
- [ ] Participant-specific correlation / uniqueness filter reviewed when authenticated access is available
- [ ] Official/host IS Sharpe recorded only if actually observed
- [ ] Runtime / missed-date / liquidity behavior confirmed in the target environment
- [ ] Submission slot within contest limits (see current rules snapshot/platform)
- [ ] Deadline awareness: **2026-09-30**; live **2026-10-01 → 2027-01-31**

## Evidence labels

Use labels that say what actually happened:

```text
Local Quantiacs toolbox metrics: OBSERVED
Local access mode: public_default
Hosted/account correlation precheck: PENDING
Submission: PENDING
```

A local measurement made with `API_KEY=default` is real toolbox evidence. It is not automatically an official leaderboard score or participant-specific uniqueness result.

## Post-submit

- [ ] Registry / experiment ledger updated with host/submission run id (if any)
- [ ] PM report section “Submission readiness” filled
- [ ] Local and hosted/account-bound values kept in separate fields
- [ ] Do not retune on live contest prints during the live window for “research”

## Honesty

If a hosted/account-bound check was not run, write **PENDING** clearly. Do not invent host Sharpe or correlation outcomes.

But **do not use “no personal API key” as a reason to leave local toolbox research PENDING**. Attempt `API_KEY=default` first. If that path genuinely fails, record `BLOCKED_INFRA` and preserve the same frozen strategy for a later infrastructure-only rerun.
