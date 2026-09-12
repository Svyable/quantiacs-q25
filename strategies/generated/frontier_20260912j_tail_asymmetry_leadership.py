"""PENDING RESEARCH STRATEGY — frontier_20260912j_tail_asymmetry_leadership.
Experiment: frontier_20260912j_tail_asymmetry_leadership
Preregistration SHA256: 2e007d15a822c4139a098035d8080ae13d13295d528360455d1d79daa6e77d1c
Mechanism: upside-vs-downside residual tail participation asymmetry.
No performance or submission claim.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
PARAMS = {"window": 63, "top_k": 5}
TREND_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    r = np.log(close / close.shift(1))
    market = r.where(liquid).sort_index(axis=1).mean(axis=1)
    return close, liquid, r.sub(market, axis=0)


def _coex(frame, side):
    x = frame.dropna(how="any")
    n = x.shape[1]
    if len(x) < 16 or n < 3:
        return None
    q = x.quantile(.25 if side == "down" else .75)
    e = x.le(q, axis=1) if side == "down" else x.ge(q, axis=1)
    a = e.to_numpy(dtype=float)
    p = a.mean(axis=0)
    joint = (a.T @ a) / len(a)
    denom = np.sqrt(np.outer(p, p))
    m = np.divide(joint, denom, out=np.zeros_like(joint), where=denom > 1e-12)
    np.fill_diagonal(m, np.nan)
    return pd.Series(np.nanmean(m, axis=1), index=x.columns)


def signals(data, window, mode="base"):
    close, liquid, residual = _context(data)
    ordered = sorted(close.columns)
    res = residual.reindex(columns=ordered)
    liq = liquid.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=close.index, columns=ordered)
    minp = max(16, window // 2)
    for i, dt in enumerate(pd.DatetimeIndex(close.index)):
        if dt.dayofweek != 0 or i < window + TREND_DAYS:
            continue
        active = [c for c in ordered if bool(liq.iloc[i][c])]
        if len(active) < 3:
            continue
        frame = res.iloc[i-window+1:i+1][active].dropna(how="any")
        if len(frame) < minp:
            continue
        down = _coex(frame, "down")
        up = _coex(frame, "up")
        if down is None or up is None:
            continue
        if mode == "base":
            raw = up - down
            node = raw.rank(pct=True, method="average")
        elif mode == "ablation":
            raw = -(up + down) / 2.0
            node = raw.rank(pct=True, method="average")
        elif mode == "falsifier":
            raw = down - up
            node = raw.rank(pct=True, method="average")
        else:
            raise ValueError("unknown mode")
        trend = res.iloc[max(0, i-TREND_DAYS+1):i+1][active].sum(min_count=max(5, TREND_DAYS//2))
        node = node.where(trend > 0, 0.0)
        out.loc[dt, active] = node.fillna(0.0).to_numpy()
    return out.reindex(columns=close.columns), liquid


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    target = selected.reindex(columns=score.columns).astype(float) * min(NAME_CAP, 1 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(dtype=float), dims=("time", "asset"), coords={"time": pd.DatetimeIndex(times), "asset": score.columns}, name=COMPETITION_TYPE)


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] + TREND_DAYS + 40 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed bounded replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown mode")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing or len(times) == 0:
        raise ValueError("nonempty increasing unique dates required")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("unique asset coordinates required")
    score, liquid = signals(data, p["window"], mode)
    return _allocate(score, liquid, data.time, p["top_k"])


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


if __name__ == "__main__":
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt
    qnbt.backtest(competition_type=COMPETITION_TYPE, load_data=load_data, lookback_period=LOOKBACK_DAYS, start_date="2016-01-01", strategy=strategy, analyze=True, check_correlation=True)
