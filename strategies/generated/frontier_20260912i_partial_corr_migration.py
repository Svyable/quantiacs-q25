"""frontier_20260912i_partial_corr_migration — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260912i_partial_corr_migration
Preregistration SHA256: b991d46f21421e29c93c42509c7aea1b2206337864184e7d9c7788f11d656f5e
Mechanism: conditional-dependence migration using ridge-regularized partial correlations
Nearest incumbent: topology_migration
No performance or submission claim. Completed daily Quantiacs OHLCV + historical
is_liquid only. The evaluator owns the execution lag. Weekly targets, persistent
eligibility exits, cash, and <=365-day replay.
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
GRAPH_LAG = 21
TREND_DAYS = 21
RIDGE = 0.10


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = returns.sub(market, axis=0)
    return close, liquid, residual


def _corr(frame, min_periods):
    corr = frame.corr(min_periods=min_periods).astype(float)
    corr = corr.replace([np.inf, -np.inf], np.nan)
    np.fill_diagonal(corr.values, 1.0)
    return corr


def _ordinary_stats(frame, min_periods):
    corr = _corr(frame, min_periods)
    arr = corr.to_numpy(float).copy()
    np.fill_diagonal(arr, np.nan)
    central = np.nanmean(np.abs(arr), axis=1)
    global_level = float(np.nanmean(np.abs(arr))) if np.isfinite(arr).any() else np.nan
    return pd.Series(central, index=corr.index), global_level


def _partial_stats(frame, min_periods):
    corr = _corr(frame, min_periods)
    arr = corr.to_numpy(float)
    finite = np.isfinite(arr)
    arr = np.where(finite, arr, 0.0)
    arr = (arr + arr.T) / 2.0
    np.fill_diagonal(arr, 1.0)
    precision = np.linalg.pinv(arr + RIDGE * np.eye(arr.shape[0]), hermitian=True)
    diag = np.diag(precision)
    denom = np.sqrt(np.outer(np.clip(diag, 1e-12, None), np.clip(diag, 1e-12, None)))
    partial = -precision / denom
    np.fill_diagonal(partial, np.nan)
    central = np.nanmean(np.abs(partial), axis=1)
    global_level = float(np.nanmean(np.abs(partial))) if np.isfinite(partial).any() else np.nan
    return pd.Series(central, index=corr.index), global_level


def _rotate_eligible(series, eligible_row):
    out = series.copy()
    labels = sorted([c for c in series.index if bool(eligible_row.get(c, False)) and np.isfinite(series.get(c, np.nan))])
    if len(labels) > 1:
        vals = series.reindex(labels).to_numpy(float)
        out.loc[labels] = np.roll(vals, 1)
    return out


def signals(data, window, mode="base"):
    close, liquid, residual = _context(data)
    ordered = sorted(close.columns)
    rs = residual.reindex(columns=ordered)
    liq = liquid.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=close.index, columns=ordered)
    times = pd.DatetimeIndex(close.index)
    minp = max(16, window // 2)
    first = window + GRAPH_LAG + 2
    for i in range(first, len(times)):
        if times[i].dayofweek != 0:
            continue
        cur = rs.iloc[i - window + 1:i + 1]
        prev_end = i - GRAPH_LAG
        prev = rs.iloc[prev_end - window + 1:prev_end + 1]
        cur_p, cur_g = _partial_stats(cur, minp)
        prev_p, prev_g = _partial_stats(prev, minp)
        if not np.isfinite(cur_g) or not np.isfinite(prev_g):
            continue
        fragmentation = max(prev_g - cur_g, 0.0)
        if fragmentation <= 0:
            continue
        if mode == "ablation":
            cur_c, _ = _ordinary_stats(cur, minp)
            prev_c, _ = _ordinary_stats(prev, minp)
            node = prev_c - cur_c
        else:
            node = prev_p - cur_p
            if mode == "falsifier":
                node = _rotate_eligible(node, liq.iloc[i])
            elif mode != "base":
                raise ValueError("unknown mode")
        trend = rs.iloc[max(0, i - TREND_DAYS + 1):i + 1].sum(min_count=max(5, TREND_DAYS // 2))
        raw = node.clip(lower=0.0) * fragmentation
        raw = raw.where((trend > 0) & liq.iloc[i], 0.0)
        out.iloc[i] = raw.reindex(ordered).fillna(0.0).to_numpy(float)
    return out.reindex(columns=close.columns), liquid


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    target = selected.reindex(columns=score.columns).astype(float) * min(NAME_CAP, 1 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(float), dims=("time", "asset"),
                        coords={"time": times, "asset": score.columns}, name=COMPETITION_TYPE)


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if 2 * p["window"] + GRAPH_LAG + TREND_DAYS + 14 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed bounded replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown mode")
    times = pd.DatetimeIndex(data.time.values)
    if len(times) == 0 or not times.is_unique or not times.is_monotonic_increasing:
        raise ValueError("nonempty increasing unique dates required")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("unique assets required")
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
