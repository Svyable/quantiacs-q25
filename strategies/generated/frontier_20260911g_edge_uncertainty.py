"""frontier_20260911g_edge_uncertainty — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911g_edge_uncertainty
Preregistration SHA256: 7b1432c558ea68754f3e12c1f64105dd1c53bc69530b0c11e58e820a1d759fc1
Classification: discovery_hypothesis
Mechanism: Rising variance of residual-correlation edges plus a positive own residual identifies idiosyncratic leadership during graph fragmentation.
Nearest incumbent: Frontier-B topology migration / Frontier-F signed-triangle change
Novelty axes: information_primitive, transform, timing_or_state_condition
No performance or submission claim. Fully realized data only; toolbox owns the
candidate execution lag. Weekly entries, persistent eligibility exits, cash,
explicit risk caps, and <=365-day replay. Evidence is recorded separately.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
PARAMS = {"top_k": 5, "window": 63}
GRAPH_LAG = 21
TREND_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    return close, liquid, returns


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    target = (selected.reindex(columns=score.columns).astype(float)
              * score.clip(0, 1).fillna(0) * min(NAME_CAP, 1 / top_k))
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=score.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(), dims=("time", "asset"),
                        coords={"time": times, "asset": score.columns},
                        name=COMPETITION_TYPE)


def _market(returns, liquid):
    observed = returns.where(liquid).sort_index(axis=1)
    return observed.mean(axis=1)


def _edge_uncertainty(correlation):
    matrix = np.asarray(correlation, float).copy()
    matrix[~np.isfinite(matrix)] = np.nan
    np.fill_diagonal(matrix, np.nan)
    out = np.full(len(matrix), np.nan)
    for i, row in enumerate(matrix):
        finite = row[np.isfinite(row)]
        if finite.size >= 2:
            out[i] = float(np.std(finite))
    return out


def signals(data, window, mode="base"):
    close, liquid, returns = _context(data)
    residual = returns.sub(_market(returns, liquid), axis=0).where(liquid)
    score = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    prior_liquid = liquid.shift(GRAPH_LAG, fill_value=False)
    trend = residual.rolling(TREND_DAYS).sum()
    min_obs = max(16, window // 2)
    for i in range(window + GRAPH_LAG, len(close)):
        if close.index[i].dayofweek != 0:
            continue
        names = sorted(liquid.columns[(liquid.iloc[i] & prior_liquid.iloc[i]).to_numpy()])
        if len(names) < 3:
            continue
        current = residual.loc[:, names].iloc[i - window + 1:i + 1]
        previous = residual.loc[:, names].iloc[i - GRAPH_LAG - window + 1:i - GRAPH_LAG + 1]
        now = _edge_uncertainty(current.corr(min_periods=min_obs))
        old = _edge_uncertainty(previous.corr(min_periods=min_obs))
        valid = np.isfinite(now) & np.isfinite(old)
        change = now - old
        if mode == "ablation":
            raw = np.clip(now, 0, 1)
        else:
            if mode == "falsifier":
                change = np.array(change, float)
                change[valid] = np.roll(change[valid], 1)
            raw = np.clip(change / 2.0, 0, 1)
        raw = np.where(valid & (trend.loc[close.index[i], names].to_numpy() > 0), raw, 0.0)
        score.loc[close.index[i], names] = raw
    return score, liquid


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] + 100 >= LOOKBACK_DAYS:
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
