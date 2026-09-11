"""frontier_20260911f_adaptive_expert_cash — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911f_adaptive_expert_cash
Preregistration SHA256: b4ca0b64a63c4d18da2e573b7fc61ffae53d495b5a3f3efb613a46138b7fb0f4
Classification: allocator_experiment
Mechanism: A causal downside-penalized exponential policy over fixed trend, low-volatility and cash experts improves allocation versus a static mixture.
Nearest incumbent: V5 latency / V10 portfolio routing
Novelty axes: transform
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
PARAMS = {'top_k': 5, 'window': 126}
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


def _unit_slots(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    chosen = (ranked.rank(axis=1, ascending=False, method="first") <= top_k)
    target = chosen.reindex(columns=score.columns).astype(float)*min(NAME_CAP, 1/top_k)
    return _hold(target, liquid, times).to_pandas()


def _expert_probabilities(proxy, window, mode):
    utility = proxy - 3*proxy.clip(upper=0).pow(2)
    utility = utility.rolling(window).sum().shift(1)
    utility['cash'] = 0.0
    if mode == "falsifier":
        utility.loc[:, ['trend','defensive']] = utility[['defensive','trend']].to_numpy()
    if mode == "ablation":
        return pd.DataFrame(1/3, index=utility.index, columns=utility.columns)
    logits = (2*utility).clip(-40,40)
    exponential = np.exp(logits.sub(logits.max(axis=1), axis=0))
    return exponential.div(exponential.sum(axis=1), axis=0)


def signals(data, window, mode="base", top_k=5):
    close, liquid, returns = _context(data)
    trend = _unit_slots(returns.rolling(63).sum(), liquid, data.time, top_k)
    vol = returns.rolling(63).std().where(lambda x: x > 1e-12)
    defensive = _unit_slots(1/vol, liquid, data.time, top_k)
    simple = np.expm1(returns).replace([np.inf,-np.inf], np.nan)
    # Historical close-to-close teacher proxy only. Exact candidate performance
    # is computed separately by Quantiacs; no teacher P&L is reported as evidence.
    proxy = pd.DataFrame({
        'trend': (trend.shift(1)*simple).fillna(0).sort_index(axis=1).sum(axis=1),
        'defensive': (defensive.shift(1)*simple).fillna(0).sort_index(axis=1).sum(axis=1),
    })
    probability = _expert_probabilities(proxy, window, mode)
    target = trend.mul(probability.trend, axis=0)+defensive.mul(probability.defensive, axis=0)
    ready = pd.Series(np.arange(len(close)) >= window+70, index=close.index)
    return target.where(ready,0.0,axis=0), liquid


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
    score, liquid = signals(data, p["window"], mode, p["top_k"])
    return _hold(score, liquid, data.time)


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
