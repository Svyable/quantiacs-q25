"""frontier_20260911h_neighbor_identity_churn — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911h_neighbor_identity_churn
Preregistration SHA256: 386412f0049b53f9b488b873ec1a776db4c2170531659ff05b8145b426ab0c5c
Classification: discovery_hypothesis
Mechanism: Turnover in an asset's strongest residual-correlation neighbors, with positive residual trend, is cluster-membership change rather than static isolation.
Nearest incumbent: Frontier-B topology_migration / static low-correlation ranking
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
NEIGHBOR_COUNT = 3


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


def _neighbor_sets(correlation, labels, count=NEIGHBOR_COUNT):
    matrix = np.abs(np.asarray(correlation, float))
    np.fill_diagonal(matrix, np.nan)
    out = []
    for i in range(len(labels)):
        row = matrix[i]
        order = np.argsort(-np.nan_to_num(row, nan=-np.inf))
        chosen = []
        for j in order:
            if np.isfinite(row[j]):
                chosen.append(str(labels[j]))
            if len(chosen) >= count:
                break
        out.append(frozenset(chosen))
    return out


def _churn(current_sets, previous_sets):
    out = np.full(len(current_sets), np.nan)
    for i, (now, old) in enumerate(zip(current_sets, previous_sets)):
        union = now | old
        if not union:
            continue
        out[i] = 1.0 - (len(now & old) / len(union))
    return out


def _mean_abs_offdiag(correlation):
    matrix = np.abs(np.asarray(correlation, float))
    np.fill_diagonal(matrix, np.nan)
    out = np.full(len(matrix), np.nan)
    for i, row in enumerate(matrix):
        finite = row[np.isfinite(row)]
        if finite.size:
            out[i] = float(np.mean(finite))
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
        if len(names) < 4:
            continue
        current = residual.loc[:, names].iloc[i - window + 1:i + 1]
        previous = residual.loc[:, names].iloc[i - GRAPH_LAG - window + 1:i - GRAPH_LAG + 1]
        now_corr = current.corr(min_periods=min_obs).to_numpy(dtype=float)
        old_corr = previous.corr(min_periods=min_obs).to_numpy(dtype=float)
        if not (np.isfinite(now_corr).all() and np.isfinite(old_corr).all()):
            continue
        churn = _churn(_neighbor_sets(now_corr, names), _neighbor_sets(old_corr, names))
        isolation = 1.0 - _mean_abs_offdiag(now_corr)
        valid = np.isfinite(churn)
        if mode == "ablation":
            raw = np.clip(isolation, 0.0, 1.0)
            valid = np.isfinite(raw)
        else:
            if mode == "falsifier":
                churn = np.array(churn, float)
                churn[valid] = np.roll(churn[valid], 1)
            raw = np.clip(churn, 0.0, 1.0)
        gate = valid & (trend.loc[close.index[i], names].to_numpy() > 0)
        score.loc[close.index[i], names] = np.where(gate, raw, 0.0)
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
