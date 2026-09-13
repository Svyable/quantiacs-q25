"""Frontier-L relative-value convergence — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260912l_relative_value_convergence
Preregistration SHA256: df0820cac4a7624f388aac15f3f64ea360b8fe3f5f3d9c09ebb20a62c08b1b65

Mechanism: select eligible cross-sectional laggards only while the dispersion of
window returns is contracting. This is a regime-conditioned convergence signal,
not unconditional mean reversion or shock recovery.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "relative_value_convergence"
PARAMS = {"window": 42, "top_k": 5}
STATE_LAG = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def signals(data, window, mode="base"):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    window_return = np.log(close / close.shift(window)).where(liquid)
    center = window_return.sort_index(axis=1).median(axis=1, skipna=True)
    relative = window_return.sub(center, axis=0)
    laggard = (-relative).clip(lower=0.0)
    dispersion = relative.where(liquid).sort_index(axis=1).std(axis=1, skipna=True)
    contraction = (dispersion.shift(STATE_LAG) - dispersion).clip(lower=0.0)
    expansion = (dispersion - dispersion.shift(STATE_LAG)).clip(lower=0.0)
    if mode == "base":
        score = laggard.mul(contraction, axis=0)
    elif mode == "ablation":
        score = laggard
    elif mode == "falsifier":
        score = laggard.mul(expansion, axis=0)
    else:
        raise ValueError("unknown control mode")
    return score.where(liquid, 0.0).replace([np.inf, -np.inf], np.nan), liquid


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    selected = selected.reindex(columns=score.columns)
    target = selected.astype(float) * min(NAME_CAP, 1.0 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(dtype=float), dims=("time", "asset"),
                        coords={"time": times, "asset": score.columns}, name=COMPETITION_TYPE)


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] not in {21, 42, 63} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-L grid")
    if p["window"] + STATE_LAG + 14 >= LOOKBACK_DAYS:
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
