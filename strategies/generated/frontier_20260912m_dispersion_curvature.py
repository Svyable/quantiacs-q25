"""Frontier-M dispersion curvature — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260912m_dispersion_curvature
Preregistration SHA256: 1dd3b968f077dad63644fc5b9aa49abef5b046f17c49ba5faf464a84e31b5657

Mechanism: long residual-return laggards only while cross-sectional convergence
is accelerating. The ablation uses first-difference convergence; the falsifier
inverts curvature. Pre-existing Frontier-L reserve, activated before M returns.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "dispersion_curvature"
PARAMS = {"window": 42, "top_k": 5}

def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)

def _curvature_state(dispersion, lag):
    recent = dispersion.shift(lag) - dispersion
    prior = dispersion.shift(2 * lag) - dispersion.shift(lag)
    return recent, recent - prior

def signals(data, window, mode="base"):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    r = np.log(close / close.shift(1))
    market = r.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = r.sub(market, axis=0).where(liquid)
    minp = max(10, window // 2)
    cumulative = residual.rolling(window, min_periods=minp).sum()
    dispersion = cumulative.where(liquid).std(axis=1)
    lag = max(7, window // 3)
    convergence, curvature = _curvature_state(dispersion, lag)
    laggard = (-cumulative).clip(lower=0.0)

    if mode == "base":
        state = curvature.clip(lower=0.0)
    elif mode == "ablation":
        state = convergence.clip(lower=0.0)
    elif mode == "falsifier":
        state = (-curvature).clip(lower=0.0)
    else:
        raise ValueError("unknown mode")

    score = laggard.mul(state, axis=0).where(liquid, 0.0).fillna(0.0)
    return score, liquid


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    selected = selected.reindex(columns=score.columns)
    target = selected.astype(float) * min(NAME_CAP, 1.0 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": times, "asset": score.columns},
        name=COMPETITION_TYPE,
    )


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] not in {21, 42, 63} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-M grid")
    lag = max(7, p["window"] // 3)
    if p["window"] + 2 * lag + 14 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown mode")
    score, liquid = signals(data, p["window"], mode)
    return _allocate(score, liquid, data.time, p["top_k"])

def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)

if __name__ == "__main__":
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt
    qnbt.backtest(competition_type=COMPETITION_TYPE, load_data=load_data,
                   lookback_period=LOOKBACK_DAYS, start_date="2016-01-01",
                   strategy=strategy, analyze=True, check_correlation=True)
