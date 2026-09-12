"""PENDING RESEARCH STRATEGY — frontier_20260912i_partial_edge_entropy.
Experiment: frontier_20260912i_partial_edge_entropy
Preregistration SHA256: daf813f71630d44e58ff0e3b83cc1860778f472fb57b6ea5544351aacf51701f
Mechanism: concentration of direct conditional residual dependence.
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
SHRINK = 0.35


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).sort_index(axis=1).mean(axis=1)
    return close, liquid, returns.sub(market, axis=0)


def _corr_partial(frame):
    x = frame.dropna(how="any")
    if x.shape[0] < 16 or x.shape[1] < 3:
        return None, None
    cov = np.cov(x.to_numpy(dtype=float), rowvar=False, ddof=1)
    var = np.diag(cov)
    if np.any(~np.isfinite(cov)) or np.any(var <= 1e-12):
        return None, None
    corr = cov / np.outer(np.sqrt(var), np.sqrt(var))
    np.fill_diagonal(corr, 1.0)
    shrunk = (1.0 - SHRINK) * cov + SHRINK * np.diag(var) + np.eye(len(var)) * 1e-12
    precision = np.linalg.pinv(shrunk, hermitian=True)
    pdiag = np.diag(precision)
    if np.any(pdiag <= 1e-12) or not np.isfinite(precision).all():
        return None, None
    partial = -precision / np.sqrt(np.outer(pdiag, pdiag))
    np.fill_diagonal(partial, 1.0)
    return corr, partial


def _concentration(matrix, labels):
    a = np.abs(matrix).copy()
    np.fill_diagonal(a, 0.0)
    out = []
    for row in a:
        total = row.sum()
        if not np.isfinite(total) or total <= 1e-12:
            out.append(np.nan)
            continue
        p = row[row > 0] / total
        if len(p) <= 1:
            out.append(1.0)
            continue
        h = -float(np.sum(p * np.log(p))) / np.log(len(p))
        out.append(1.0 - h)
    return pd.Series(out, index=labels)


def _rotate(series):
    s = series.sort_index()
    if len(s) > 1:
        s = pd.Series(np.roll(s.to_numpy(dtype=float), 1), index=s.index)
    return s.reindex(series.index)


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
        usable = res.iloc[i-window+1:i+1][active].dropna(how="any")
        if len(usable) < minp:
            continue
        corr, partial = _corr_partial(usable)
        if corr is None:
            continue
        base = _concentration(partial, active)
        marginal = _concentration(corr, active)
        if mode == "base":
            node = base.rank(pct=True, method="average")
        elif mode == "ablation":
            node = marginal.rank(pct=True, method="average")
        elif mode == "falsifier":
            node = _rotate(base.rank(pct=True, method="average"))
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
