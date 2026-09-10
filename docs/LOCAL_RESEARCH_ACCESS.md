# Local Quantiacs research access

## The short version

**Do not stop local Q25 research because you do not have a personal Quantiacs API key.**

The current open-source Quantiacs toolbox explicitly special-cases:

```text
API_KEY=default
```

for local/public data access. Its own test suite also sets `API_KEY="default"` before importing `qnt` modules.

This repository therefore treats access as two separate layers:

| Layer | Credential | What it is for |
|---|---|---|
| Local/public research | `API_KEY=default` | Quantiacs public market data, local strategy evaluation, local stats, causal/prefix checks, cost ladders and development benchmarks |
| Account-bound platform services | real participant API key / hosted session | participant-specific correlation/precheck, account identity, submission and other authenticated platform actions |

A real participant key can be supplied privately, but it is **not a prerequisite for doing measured local research**.

## Current source evidence

This behavior is grounded in the open-source toolbox rather than inferred from a README.

At toolbox commit `9e5274c5ce102a66debc799fd2a2300969fb90f6`, `qnt/data/common.py` does the following:

- reads `API_KEY` during module import;
- exits when it is blank;
- skips the account-authentication branch when the value is exactly `default`.

Source:

- https://github.com/quantiacs/toolbox/blob/9e5274c5ce102a66debc799fd2a2300969fb90f6/qnt/data/common.py

The same repository's tests explicitly set `API_KEY="default"`, including:

- https://github.com/quantiacs/toolbox/blob/9e5274c5ce102a66debc799fd2a2300969fb90f6/qnt/tests/test_strategy.py
- https://github.com/quantiacs/toolbox/blob/9e5274c5ce102a66debc799fd2a2300969fb90f6/qnt/tests/test_data_init.py
- https://github.com/quantiacs/toolbox/blob/9e5274c5ce102a66debc799fd2a2300969fb90f6/qnt/tests/test_statistic.py

Quantiacs' user-facing local-development documentation still recommends a personal profile key. Treat `default` as a **source-supported public/local path**, not a promise that every account-bound endpoint will work anonymously forever.

## Import-order rule

This matters because the toolbox reads `API_KEY` at import time.

Correct:

```python
import os
os.environ.setdefault("API_KEY", "default")

import qnt.data as qndata
import qnt.stats as qnstats
```

The repository runner does this automatically through `factory.runner.ensure_local_data_access()`.

Do **not** import `qnt` first and try to set the variable afterward.

## Commands

No personal credential:

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q tests
python scripts/run_strategy.py strategies/robust_weekly_waterfill.py
python -m research.iteration --budget 18
```

Explicit public/default mode if calling a standalone script outside the harness:

```bash
API_KEY=default python path/to/strategy.py
```

Optional authenticated mode:

```bash
export API_KEY='<participant-key>'
python -m research.iteration --budget 18
```

Never commit, log, print, place in CLI arguments, or write a real participant key into result artifacts.

## Agent rule: dogfood the research stack

A missing personal credential is **not** a valid reason to leave local strategy performance `PENDING`.

For every executable candidate, the agent should attempt the public/default path and, when the data endpoint and toolbox are reachable, produce measured local evidence such as:

- full/development/validation Sharpe according to the campaign's allowed selection policy;
- mean/CAGR-style return fields when correctly derived from Quantiacs stats;
- volatility;
- maximum drawdown;
- turnover / holding diagnostics;
- cost-ladder Sharpe;
- temporal folds/regimes;
- prefix-causality and bounded-replay parity;
- liquidity, long-only, gross and cleaner-mutation checks;
- matched return correlations / residual diagnostics where incumbent streams are available.

Only call a local metric `PENDING` when the run genuinely did not execute or the toolbox/data environment actually failed.

## Evidence boundary

Metrics produced through `API_KEY=default` are **real local Quantiacs-toolbox measurements**. They are not automatically:

- an official leaderboard score;
- participant-specific uniqueness clearance;
- a remote correlation/precheck result;
- a submitted strategy;
- evidence from the unseen live window.

Label those layers separately.

A useful report should say, for example:

```text
Local Quantiacs toolbox metrics: OBSERVED
Access mode: public_default
Hosted/account correlation precheck: PENDING
Submission: PENDING
```

## If `default` stops working

Do not reinterpret an infrastructure failure as an alpha failure.

Record:

- toolbox commit/version;
- access mode (`public_default`);
- loader attempted;
- exception type only if the message may contain sensitive request details;
- date/time;
- whether cached data were available.

Then classify the run as `BLOCKED_INFRA`, not `FAILED_ALPHA`.

If an authenticated key is later available, rerun the **same frozen candidate** rather than changing strategy parameters at the same time.

## Account-bound boundary

Use `factory.runner.require_authenticated_api_key()` only for code that truly requires participant identity. Do not put that guard in local research/backtest paths.

The operating principle is simple:

> **Measure everything we can locally with `default`; reserve credentials for the parts that are actually account-bound.**
