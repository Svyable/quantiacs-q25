"""Q25 SUBMISSION CANDIDATE: 126-day positive-return consistency.

Fresh contest adapter for the archived Trend_hit126 mechanism. Historical
metrics are provenance only and are NOT attributed to this implementation.

Mechanism:
- Among historically liquid names, estimate the fraction of positive daily
  log returns over the trailing 126 days.
- Require positive 126-day displacement so consistency is continuation rather
  than high-frequency noise.
- Select the five strongest consistency scores on a weekly schedule.
- Inverse-volatility size with a 25% name cap; unused capacity stays cash.
- Long-only, no asset identifiers, sponsor data only.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import xarray as xr

STRATEGY_ID = "q25_deadline_hit126_consistency_v1"
COMPETITION_TYPE = "crypto_daily_long"
IN_SAMPLE_START = "2016-01-01"
LOOKBACK_DAYS = 320

HIT_WINDOW = 126
HIT_MIN = 84
RISK_WINDOW = 63
RISK_MIN = 42
TOP_K = 5
NAME_CAP = 0.25
EPS = 1e-12


def _frame(data: xr.DataArray, field: str) -> pd.DataFrame:
    out = data.sel(field=field).transpose("time", "asset").to_pandas().astype(float)
    out.index = pd.DatetimeIndex(out.index)
    return out


def _waterfill(raw: pd.Series, cap: float = NAME_CAP) -> pd.Series:
    raw = pd.to_numeric(raw, errors="coerce").replace([np.inf, -np.inf], np.nan)
    raw = raw.fillna(0.0).clip(lower=0.0)
    w = pd.Series(0.0, index=raw.index, dtype=float)
    for _ in range(12):
        rem = 1.0 - float(w.sum())
        if rem <= 1e-12:
            break
        room = (cap - w).clip(lower=0.0)
        eligible = (raw > 0.0) & (room > 1e-12)
        if not bool(eligible.any()):
            break
        score = raw.where(eligible, 0.0)
        denom = float(score.sum())
        if denom <= EPS:
            break
        add = rem * score / denom
        add = pd.concat([add, room], axis=1).min(axis=1)
        w = (w + add.where(eligible, 0.0)).clip(lower=0.0, upper=cap)
    if float(w.sum()) > 1.0 + 1e-12:
        w /= float(w.sum())
    return w


def _signals(data: xr.DataArray):
    close = _frame(data, "close")
    liquid = _frame(data, "is_liquid").fillna(0.0) > 0.0
    tradable = liquid & close.notna() & (close > 0.0)

    log_close = np.log(close.where(close > 0.0))
    ret = log_close.diff()
    positive = (ret > 0.0).astype(float).where(ret.notna())

    hit = positive.rolling(HIT_WINDOW, min_periods=HIT_MIN).mean()
    displacement = log_close - log_close.shift(HIT_WINDOW)
    risk = ret.rolling(RISK_WINDOW, min_periods=RISK_MIN).std(ddof=1)

    # Consistency is the information primitive. Displacement is only a sign
    # confirmation so a high hit rate with a few catastrophic losses is not
    # treated as persistent positive trend.
    score = (hit - 0.50).where(displacement > 0.0)
    return tradable, score, risk


def compute_weights(data: xr.DataArray) -> xr.DataArray:
    tradable, score, risk = _signals(data)
    dates = pd.DatetimeIndex(score.index)
    rebalance = pd.Series(dates.dayofweek == 0, index=dates)
    target = pd.DataFrame(np.nan, index=dates, columns=score.columns, dtype=float)

    for dt in dates[rebalance.to_numpy()]:
        s = score.loc[dt].replace([np.inf, -np.inf], np.nan)
        valid = tradable.loc[dt].fillna(False) & s.notna() & (s > 0.0)
        # hit-rate scores are discrete and ties are common. Canonicalize the
        # coordinate order before method="first" so a caller's asset ordering
        # cannot change the portfolio. This is an implementation-integrity fix,
        # not an economic ranking input or a hand-picked asset rule.
        canonical = sorted(s.index.astype(str))
        s_c = s.reindex(canonical)
        valid_c = valid.reindex(canonical)
        rank_c = s_c.where(valid_c).rank(ascending=False, method="first")
        rank = rank_c.reindex(s.index)
        selected = valid & (rank <= TOP_K)
        if not bool(selected.any()):
            target.loc[dt] = 0.0
            continue
        # Keep consistency relevant to sizing without letting tiny hit-rate
        # differences dominate the inverse-risk budget.
        conviction = (0.5 + s.clip(lower=0.0) / 0.15).clip(0.5, 1.5)
        raw = (conviction / (risk.loc[dt] + EPS)).where(selected, 0.0)
        target.loc[dt] = _waterfill(raw)

    weights = target.ffill().fillna(0.0).where(tradable, 0.0)

    held = pd.Series(False, index=weights.columns)
    active = pd.DataFrame(False, index=dates, columns=weights.columns)
    for i, dt in enumerate(dates):
        if bool(rebalance.iloc[i]):
            held = weights.loc[dt] > 0.0
        held = held & tradable.loc[dt].fillna(False)
        active.loc[dt] = held
    weights = weights.where(active, 0.0).clip(lower=0.0, upper=NAME_CAP)

    gross = weights.sum(axis=1)
    over = gross > 1.0 + 1e-12
    if bool(over.any()):
        weights.loc[over] = weights.loc[over].div(gross.loc[over], axis=0)

    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": weights.index.to_numpy(), "asset": weights.columns.to_numpy()},
        name=STRATEGY_ID,
    ).fillna(0.0)


def strategy(data: xr.DataArray) -> xr.DataArray:
    return compute_weights(data).isel(time=-1, drop=True)


def load_data(period: int):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


def run_single_pass(write_output: bool = False):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    import qnt.output as qnout
    import qnt.stats as qnstats

    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    weights = compute_weights(data)
    cleaned = qnout.clean(weights, data, COMPETITION_TYPE)
    in_sample = cleaned.sel(time=slice(IN_SAMPLE_START, None))

    report = {"strategy_id": STRATEGY_ID, "cost_ladder": {}}
    for cost in (0.00, 0.04, 0.08, 0.12):
        stats = qnstats.calc_stat(
            data, in_sample, slippage_factor=cost, points_per_year=365
        ).sel(time=slice(IN_SAMPLE_START, None))
        last = stats.isel(time=-1)
        values = {}
        for field in ("sharpe_ratio", "equity", "max_drawdown", "avg_turnover", "volatility"):
            if field in last.field.values:
                values[field] = float(last.sel(field=field).item())
        report["cost_ladder"][f"{cost:.2f}"] = values

    print(json.dumps(report, indent=2, sort_keys=True))
    if write_output:
        # Hosted/account-bound check includes the contest correlation screen.
        qnout.check(cleaned, data, COMPETITION_TYPE, check_correlation=True)
        qnout.write(cleaned)
    return cleaned, report


def run_multipass():
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt
    return qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date=IN_SAMPLE_START,
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )


if __name__ == "__main__":
    # Parity against Quantiacs multipass was validated on current real data.
    # Single pass is therefore the production path: faster, same weights.
    run_single_pass(write_output=True)
