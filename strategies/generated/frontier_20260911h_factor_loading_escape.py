"""frontier_20260911h_factor_loading_escape — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911h_factor_loading_escape
Preregistration SHA256: 698163d3b74ec0063e712b2e221498ca29002d22b42b2879b2970da6632d0f71
Classification: discovery_hypothesis
Mechanism: Declining absolute loading on the leading residual-correlation eigenvector during spectral-gap compression identifies leaving the common residual factor.
Nearest incumbent: Frontier-B topology_migration / C165 residual-dispersion timing
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


def _leading_factor(correlation):
    """Absolute leading-eigenvector loadings and (l1-l2)/sum(|l|) gap share."""
    matrix = np.asarray(correlation, float)
    if matrix.ndim != 2 or matrix.shape[0] < 4 or matrix.shape[0] != matrix.shape[1]:
        n = 0 if matrix.ndim != 2 else matrix.shape[0]
        return np.full(n, np.nan), np.nan
    if not np.isfinite(matrix).all():
        return np.full(matrix.shape[0], np.nan), np.nan
    symmetric = 0.5 * (matrix + matrix.T)
    values, vectors = np.linalg.eigh(symmetric)
    order = np.argsort(values)
    leading = vectors[:, order[-1]]
    loadings = np.abs(leading)
    if values.size < 2:
        return loadings, np.nan
    total = float(np.sum(np.abs(values)))
    if total <= 1e-12:
        return loadings, np.nan
    gap = float(values[order[-1]] - values[order[-2]]) / total
    return loadings, gap


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
        now, now_gap = _leading_factor(now_corr)
        old, old_gap = _leading_factor(old_corr)
        if not (np.isfinite(now_gap) and np.isfinite(old_gap)):
            continue
        compression = max(old_gap - now_gap, 0.0)
        valid = np.isfinite(now) & np.isfinite(old)
        escape = old - now
        if mode == "ablation":
            raw = np.clip(1.0 - now, 0.0, 1.0)
        else:
            if mode == "falsifier":
                escape = np.array(escape, float)
                escape[valid] = np.roll(escape[valid], 1)
            raw = np.clip(escape, 0.0, 1.0)
        gate = valid & (trend.loc[close.index[i], names].to_numpy() > 0) & (compression > 0)
        score.loc[close.index[i], names] = np.where(gate, raw * min(compression, 1.0), 0.0)
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
