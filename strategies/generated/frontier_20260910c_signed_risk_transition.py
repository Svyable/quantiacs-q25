"""frontier_20260910c_signed_risk_transition — PENDING RESEARCH STRATEGY; no performance or submission claim.
Experiment: frontier_20260910c_signed_risk_transition
Preregistration SHA256: 8ebd7630e3a92021efe90513c2a8e601c0709f88459a61b4e7f3a1f59e7bff80
Mechanism: Falling downside semivariance relative to upside semivariance, while residual trend stays positive, marks improving risk quality rather than low volatility level.
Nearest incumbent: CoCrash126 / V13 / vol_curve
Novelty axes: information_primitive, transform, timing_or_state_condition

Completed daily Quantiacs OHLCV + historical is_liquid only. The evaluator applies
the execution lag. State transitions compare trailing estimates with a fixed
21-day-prior estimate and fit inside the 365-day replay horizon.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "signed_risk_transition"
PARAMS = {"window": 63, "top_k": 5}
STATE_LAG = 21
TREND_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _rotate_by_label(frame):
    ordered = sorted(frame.columns)
    sorted_frame = frame.reindex(columns=ordered)
    rotated = pd.DataFrame(
        np.roll(sorted_frame.to_numpy(dtype=float), 1, axis=1),
        index=sorted_frame.index,
        columns=ordered,
    )
    return rotated.reindex(columns=frame.columns)


def signals(data, window, mode="base"):
    c = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & c.notna()
    r = np.log(c / c.shift(1))
    market = r.where(liquid).mean(axis=1)
    residual = r.sub(market, axis=0)

    minp = max(16, window // 2)
    downside = residual.clip(upper=0.0).pow(2).rolling(window, min_periods=minp).mean()
    upside = residual.clip(lower=0.0).pow(2).rolling(window, min_periods=minp).mean()
    balance = np.log((downside + 1e-10) / (upside + 1e-10))
    transition = balance.shift(STATE_LAG) - balance
    trend = residual.rolling(TREND_DAYS, min_periods=max(8, TREND_DAYS // 2)).sum()
    if mode == "base":
        state = transition
    elif mode == "ablation":
        state = -balance
    elif mode == "falsifier":
        state = _rotate_by_label(transition)
    else:
        raise ValueError("unknown control mode")
    score = state.clip(lower=0.0, upper=4.0) * trend.clip(lower=0.0)

    score = score.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return score.reindex(columns=c.columns), liquid


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"}:
        raise ValueError("expected exactly window, top_k")
    if any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("parameters must be positive integers")
    if p["window"] + STATE_LAG + TREND_DAYS + 16 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown control mode")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing:
        raise ValueError("times must be unique and increasing")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("assets must be unique")
    score, liquid = signals(data, p["window"], mode)
    return _allocate(score, liquid, data.time, p["top_k"])


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    selected = selected.reindex(columns=score.columns)
    raw = selected.astype(float) * min(NAME_CAP, 1 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=raw.index)
    weights = raw.where(monday, axis=0).ffill(limit=6).fillna(0.0)
    weights = weights.where(liquid, 0.0)
    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": times, "asset": score.columns},
        name=COMPETITION_TYPE,
    )


def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


if __name__ == "__main__":
    import qnt.backtester as qnbt
    qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date="2016-01-01",
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )
