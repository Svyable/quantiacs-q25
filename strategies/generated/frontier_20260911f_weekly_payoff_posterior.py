"""frontier_20260911f_weekly_payoff_posterior — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911f_weekly_payoff_posterior
Preregistration SHA256: e99c5f26dd2d7d91c94c9f06b4fb0828c2ecc5d96c30abc39f430c4e22da8748
Classification: discovery_hypothesis
Mechanism: Past fully realized weekly gain probabilities and loss magnitudes conditioned on market state predict whether taking risk has positive utility.
Nearest incumbent: Frontier-A AR forecast surprise / V10 regime routing
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


def _weekly_labels(close, liquid, state):
    monday = pd.Series(close.index.dayofweek == 0, index=close.index)
    label = np.log(close / close.shift(7))
    label = label.where(liquid.shift(7, fill_value=False)).where(monday, axis=0)
    return label.where(state.shift(7).notna(), axis=0)


def _posterior(labels, condition, window):
    sample = labels.where(condition, axis=0)
    valid = sample.notna()
    n = valid.astype(float).rolling(window).sum()
    wins = (sample > 0).astype(float).rolling(window).sum()
    gains = sample.clip(lower=0).fillna(0).rolling(window).sum()
    losses = -sample.clip(upper=0).fillna(0).rolling(window).sum()
    probability = (wins+1)/(n+2)
    gain = (gains+.02)/(wins+1)
    loss = (losses+.02)/(n-wins+1)
    utility = probability*gain - 1.5*(1-probability)*loss
    return (utility/(gain+loss)).clip(0, 1), n


def signals(data, window, mode="base"):
    close, liquid, returns = _context(data)
    market_sum = _market(returns, liquid).rolling(21).sum()
    state = (market_sum > 0).where(market_sum.notna())
    label = _weekly_labels(close, liquid, state)
    if mode == "falsifier":
        label = _rotate_eligible(label, liquid.shift(7, fill_value=False) & label.notna())
    score = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    origin_state = state.shift(7)
    for value in (False, True):
        conditioned, n = _posterior(label, origin_state.eq(value), window)
        if mode == "ablation":
            conditioned, _ = _posterior(label, origin_state.notna(), window)
        conditioned = conditioned.where(n >= 4, 0.0)
        score = score.where(~state.eq(value), conditioned, axis=0)
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
