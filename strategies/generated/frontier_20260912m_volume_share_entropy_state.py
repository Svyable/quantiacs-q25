"""Frontier-M volume-share entropy state — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260912m_volume_share_entropy_state
Preregistration SHA256: a7cf0bfb6b118e5791780d91d59cf64376bb26487a02ba580c7f5f7767188a41

Mechanism: positive migration in eligible-universe dollar-volume share is active
only while cross-sectional activity-share entropy is falling. This is a
pre-existing Frontier-L reserve activated before any Frontier-M market look.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "volume_share_entropy_state"
PARAMS = {"window": 42, "top_k": 5}
TREND_DAYS = 21

def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)

def _share_entropy(shares):
    s = pd.Series(shares, dtype=float).replace([np.inf, -np.inf], np.nan).dropna()
    s = s[s > 0]
    if len(s) < 2 or float(s.sum()) <= 0:
        return np.nan
    p = s / s.sum()
    return float(-(p * np.log(p)).sum() / np.log(len(p)))

def signals(data, window, mode="base"):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    vol = _field(data, "vol").where(lambda x: np.isfinite(x) & (x >= 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    r = np.log(close / close.shift(1))
    market = r.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = r.sub(market, axis=0).where(liquid)
    dollar = (close * vol).where(liquid)
    total = dollar.sort_index(axis=1).sum(axis=1, min_count=1).replace(0, np.nan)
    share = dollar.div(total, axis=0)
    entropy = share.apply(_share_entropy, axis=1)
    lag = max(7, window // 2)
    migration = np.log(share.clip(lower=1e-16)) - np.log(share.shift(lag).clip(lower=1e-16))
    trend = residual.rolling(TREND_DAYS, min_periods=max(5, TREND_DAYS // 2)).sum()

    if mode == "base":
        state = (entropy.shift(lag) - entropy).clip(lower=0.0)
    elif mode == "ablation":
        state = pd.Series(1.0, index=share.index)
    elif mode == "falsifier":
        state = (entropy - entropy.shift(lag)).clip(lower=0.0)
    else:
        raise ValueError("unknown mode")

    score = migration.clip(lower=0.0).mul(state, axis=0)
    score = score.where(liquid & (trend > 0), 0.0).fillna(0.0)
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
    if p["window"] + max(7, p["window"] // 2) + TREND_DAYS + 14 >= LOOKBACK_DAYS:
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
