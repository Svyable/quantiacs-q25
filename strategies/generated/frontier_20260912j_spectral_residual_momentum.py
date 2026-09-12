"""PENDING RESEARCH STRATEGY — frontier_20260912j_spectral_residual_momentum.
Experiment: frontier_20260912j_spectral_residual_momentum
Preregistration SHA256: 37c2ab1b51207f65f37c94e56200d22b8cdd29ecd04f66609905c7a6d7fb1879
Mechanism: momentum after projecting out the leading residual-correlation principal component.
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
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = returns.sub(market, axis=0).where(liquid)
    return close, liquid, residual

def _spectral_score(frame, mode):
    x = frame.dropna(how="any")
    if x.shape[0] < max(16, TREND_DAYS) or x.shape[1] < 3:
        return None
    mu = x.mean(axis=0)
    sigma = x.std(axis=0, ddof=1).replace(0.0, np.nan)
    z = x.sub(mu, axis=1).div(sigma, axis=1)
    if not np.isfinite(z.to_numpy(dtype=float)).all():
        return None
    corr = np.corrcoef(z.to_numpy(dtype=float), rowvar=False)
    if not np.isfinite(corr).all():
        return None
    _, vecs = np.linalg.eigh((corr + corr.T) / 2.0)
    v = vecs[:, -1]
    tail = z.iloc[-TREND_DAYS:].to_numpy(dtype=float)
    if mode == "ablation":
        projected = tail
    else:
        use_v = np.roll(v, 1) if mode == "falsifier" else v
        projected = tail - np.outer(tail @ use_v, use_v)
    score = projected.sum(axis=0)
    return pd.Series(score, index=x.columns)

def signals(data, window, mode="base"):
    close, liquid, residual = _context(data)
    ordered = sorted(close.columns)
    res = residual.reindex(columns=ordered)
    liq = liquid.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=close.index, columns=ordered)
    for i, dt in enumerate(pd.DatetimeIndex(close.index)):
        if dt.dayofweek != 0 or i < window:
            continue
        active = [c for c in ordered if bool(liq.iloc[i][c])]
        if len(active) < 3:
            continue
        frame = res.iloc[i-window+1:i+1][active]
        node = _spectral_score(frame, mode)
        if node is None:
            continue
        node = node.replace([np.inf, -np.inf], np.nan).clip(lower=0.0)
        out.loc[dt, active] = node.fillna(0.0).to_numpy(dtype=float)
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
    qnbt.backtest(competition_type=COMPETITION_TYPE, load_data=load_data,
                   lookback_period=LOOKBACK_DAYS, start_date="2016-01-01",
                   strategy=strategy, analyze=True, check_correlation=True)
