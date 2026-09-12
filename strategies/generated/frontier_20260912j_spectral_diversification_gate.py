"""PENDING RESEARCH STRATEGY — frontier_20260912j_spectral_diversification_gate.
Experiment: frontier_20260912j_spectral_diversification_gate
Preregistration SHA256: 41669128c118b8ac827fca2bcdd0493960a9c2531f943a2df35c169a182b483c
Mechanism: falling leading-eigenvalue concentration as a residual opportunity state.
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
STATE_LAG = 21
TREND_DAYS = 21

def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)

def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = returns.sub(market, axis=0).where(liquid)
    return close, liquid, residual

def _leading_share(corr):
    m = np.asarray(corr, dtype=float)
    if m.ndim != 2 or m.shape[0] < 2 or not np.isfinite(m).all():
        return np.nan
    eig = np.linalg.eigvalsh((m + m.T) / 2.0)
    eig = np.clip(eig, 0.0, None)
    total = eig.sum()
    return float(eig[-1] / total) if total > 1e-12 else np.nan

def signals(data, window, mode="base"):
    close, liquid, residual = _context(data)
    ordered = sorted(close.columns)
    res = residual.reindex(columns=ordered)
    liq = liquid.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=close.index, columns=ordered)
    minp = max(16, window // 2)
    trend = res.rolling(TREND_DAYS, min_periods=max(5, TREND_DAYS // 2)).sum()
    for i, dt in enumerate(pd.DatetimeIndex(close.index)):
        if dt.dayofweek != 0 or i < window + STATE_LAG:
            continue
        active = [c for c in ordered if bool(liq.iloc[i][c]) and bool(liq.iloc[i-STATE_LAG][c])]
        if len(active) < 3:
            continue
        cur = res.iloc[i-window+1:i+1][active].corr(min_periods=minp).to_numpy(dtype=float)
        old = res.iloc[i-STATE_LAG-window+1:i-STATE_LAG+1][active].corr(min_periods=minp).to_numpy(dtype=float)
        if not (np.isfinite(cur).all() and np.isfinite(old).all()):
            continue
        cur_share, old_share = _leading_share(cur), _leading_share(old)
        if not (np.isfinite(cur_share) and np.isfinite(old_share)):
            continue
        diversification = max(old_share - cur_share, 0.0)
        concentration = max(cur_share - old_share, 0.0)
        trend_now = trend.loc[dt, active].replace([np.inf, -np.inf], np.nan)
        positive = trend_now.where(trend_now > 0)
        rank = positive.rank(pct=True, method="average").fillna(0.0)
        if mode == "base":
            raw = rank * diversification
        elif mode == "ablation":
            raw = rank
        elif mode == "falsifier":
            raw = rank * concentration
        else:
            raise ValueError("unknown mode")
        out.loc[dt, active] = raw.to_numpy(dtype=float)
    return out.reindex(columns=close.columns), liquid

def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    target = selected.reindex(columns=score.columns).astype(float) * min(NAME_CAP, 1 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(dtype=float), dims=("time", "asset"),
                        coords={"time": pd.DatetimeIndex(times), "asset": score.columns},
                        name=COMPETITION_TYPE)

def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] + STATE_LAG + TREND_DAYS + 40 >= LOOKBACK_DAYS:
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
    qnbt.backtest(competition_type=COMPETITION_TYPE, load_data=load_data,
                   lookback_period=LOOKBACK_DAYS, start_date="2016-01-01",
                   strategy=strategy, analyze=True, check_correlation=True)
