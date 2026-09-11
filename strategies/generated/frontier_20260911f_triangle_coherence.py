"""frontier_20260911f_triangle_coherence — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911f_triangle_coherence
Preregistration SHA256: 21319da5235308bb87745b343ceda9a27310f11d1d5bb839fb491335b1d2cd31
Classification: discovery_hypothesis
Mechanism: Increasing consistency of signed residual-correlation triangles identifies coherent emerging opportunity.
Nearest incumbent: Frontier-B unsigned centrality migration
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
PARAMS = {'top_k': 5, 'window': 63}
SHORT_DAYS = 7
STATE_DAYS = 21
MARKET_DAYS = 63


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    return close, liquid, returns


def _rotate_eligible(frame, eligible):
    """Preserve each day's eligible finite marginal, independent of column order.

    Never rotate through future-listed or ineligible names. A singleton cannot
    be permuted, so it is left intact; no diagnostic power is claimed there.
    """
    ordered = frame.sort_index(axis=1)
    mask = eligible.reindex(columns=ordered.columns) & np.isfinite(ordered)
    out = ordered.copy()
    for i in range(len(out)):
        locations = np.flatnonzero(mask.iloc[i].to_numpy())
        if len(locations) > 1:
            out.iloc[i, locations] = np.roll(ordered.iloc[i, locations].to_numpy(), 1)
    return out.reindex(columns=frame.columns)


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = (ranked.rank(axis=1, ascending=False, method="first") <= top_k)
    target = (selected.reindex(columns=score.columns).astype(float)
              * score.clip(0, 1).fillna(0) * min(NAME_CAP, 1 / top_k))
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=score.index)
    # An exit is an explicit zero event, so eligibility recovery cannot revive
    # a stale target. Six-bar carry limit bounds state even on incomplete input.
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(), dims=("time", "asset"),
                        coords={"time": times, "asset": score.columns},
                        name=COMPETITION_TYPE)


def _market(returns, liquid):
    # Stable arithmetic order; no inactive/future-listed asset can enter peers.
    observed = returns.where(liquid).sort_index(axis=1)
    return observed.mean(axis=1)


def _hold(target, liquid, times):
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(), dims=("time", "asset"),
                        coords={"time": times, "asset": target.columns},
                        name=COMPETITION_TYPE)


def _balance(correlation):
    matrix = np.asarray(correlation, float).copy()
    matrix[~np.isfinite(matrix)] = 0.0
    np.fill_diagonal(matrix, 0.0)
    absolute = np.abs(matrix)
    numerator = np.diag(matrix @ matrix @ matrix)
    denominator = np.diag(absolute @ absolute @ absolute)
    return np.divide(numerator, denominator, out=np.full(len(matrix), np.nan),
                     where=denominator > 1e-12)


def signals(data, window, mode="base"):
    close, liquid, returns = _context(data)
    residual = returns.sub(_market(returns, liquid), axis=0).where(liquid)
    score = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    prior_liquid = liquid.shift(21, fill_value=False)
    trend = residual.rolling(21).sum()
    for i in range(window + 21, len(close)):
        if close.index[i].dayofweek != 0:
            continue
        names = sorted(liquid.columns[(liquid.iloc[i] & prior_liquid.iloc[i]).to_numpy()])
        if len(names) < 3:
            continue
        current = residual.loc[:, names].iloc[i-window+1:i+1]
        previous = residual.loc[:, names].iloc[i-21-window+1:i-21+1]
        now = _balance(current.corr(min_periods=max(16, window//2)))
        old = _balance(previous.corr(min_periods=max(16, window//2)))
        valid = np.isfinite(now) & np.isfinite(old)
        change = now-old
        if mode == "ablation":
            raw = (now+1)/2
        else:
            if mode == "falsifier":
                change[valid] = np.roll(change[valid], 1)
            raw = change/2
        raw = np.where(valid & (trend.loc[close.index[i], names].to_numpy() > 0),
                       np.clip(raw, 0, 1), 0.0)
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
