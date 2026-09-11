"""frontier_20260911e_downside_impact_relief — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911e_downside_impact_relief
Preregistration SHA256: 34f860a577c0f84fe5f1ba985be5e2d513f968c8df1d2a549f1f1ea435171354
Mechanism: Declining downside displacement per unit relative dollar volume marks recovering absorption capacity.
Nearest incumbent: Frontier-A flow absorption / V12 volume diffusion
Novelty axes: information primitive, transform, timing/state.
No performance or submission claim. Exact evidence is recorded separately.
Completed daily sponsor data; evaluator applies next-bar execution. Confidence
sets absolute fixed-slot size, never renormalized. 365-day bounded replay.
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


def _finish(score, liquid, returns):
    gate = _market(returns, liquid).rolling(MARKET_DAYS).sum() > 0
    return score.clip(0, 1).where(gate, 0.0, axis=0), liquid


def signals(data, window, mode="base"):
    close, liquid, returns = _context(data)
    volume = _field(data, "vol").where(lambda x: np.isfinite(x) & (x > 0))
    dollar = close * volume
    relative = (dollar / dollar.rolling(window).median().shift(1)).clip(.1, 10)
    valid = relative.notna() & np.isfinite(returns)
    if mode == "ablation":
        relative = relative.where(~valid, 1.0)
    elif mode == "falsifier":
        relative = _rotate_eligible(relative, liquid & valid)
    impact = (-returns).clip(lower=0).div(relative).where(valid)
    long = impact.rolling(window).mean().shift(1).where(lambda x: x > 1e-12)
    short = impact.rolling(SHORT_DAYS).mean().shift(1).where(lambda x: x > 1e-12)
    score = np.log(long / short).clip(lower=0)
    score = score.where(returns.rolling(STATE_DAYS).sum() > 0, 0.0)
    return _finish(score, liquid, returns)


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if 2 * p["window"] + SHORT_DAYS + MARKET_DAYS + 16 >= LOOKBACK_DAYS:
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
