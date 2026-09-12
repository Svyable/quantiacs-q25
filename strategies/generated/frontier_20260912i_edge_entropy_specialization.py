"""frontier_20260912i_edge_entropy_specialization — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260912i_edge_entropy_specialization
Preregistration SHA256: 846f2f052715604292ffa94495abb7c09faa366846090e775626608fb115ff12
Mechanism: change in normalized residual-edge dependence entropy during fragmentation
Nearest incumbent: topology_migration / Frontier-H static-isolation controls
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


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    r = np.log(close / close.shift(1))
    market = r.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = r.sub(market, axis=0)
    return close, liquid, residual


def _entropy_stats(frame, min_periods):
    corr = frame.corr(min_periods=min_periods).replace([np.inf, -np.inf], np.nan)
    arr = np.abs(corr.to_numpy(float))
    np.fill_diagonal(arr, np.nan)
    entropy = np.full(arr.shape[0], np.nan)
    for i, row in enumerate(arr):
        finite = row[np.isfinite(row) & (row > 0)]
        if len(finite) < 2:
            continue
        p = finite / finite.sum()
        entropy[i] = -float(np.sum(p * np.log(p))) / np.log(len(p))
    global_level = float(np.nanmean(arr)) if np.isfinite(arr).any() else np.nan
    return pd.Series(entropy, index=corr.index), global_level


def _rotate_eligible(series, eligible_row):
    out = series.copy()
    labels = sorted([c for c in series.index if bool(eligible_row.get(c, False)) and np.isfinite(series.get(c, np.nan))])
    if len(labels) > 1:
        out.loc[labels] = np.roll(series.reindex(labels).to_numpy(float), 1)
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
        cent, cg = _entropy_stats(cur, minp)
        pent, pg = _entropy_stats(prev, minp)
        if not np.isfinite(cg) or not np.isfinite(pg):
            continue
        fragmentation = max(pg - cg, 0.0)
        if fragmentation <= 0:
            continue
        if mode == "ablation":
            node = (1.0 - cent).clip(lower=0.0)
        else:
            node = pent - cent
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
