"""frontier_20260911g_forecast_agreement — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911g_forecast_agreement
Preregistration SHA256: 34803e473e8eae5a03519e1e0a0007b4291b247eed3c2c1ed015e7b6256c7180
Classification: discovery_hypothesis
Mechanism: Agreement between a slow residual-mean forecast and a fully realized one-week residual forecast identifies usable positive leadership.
Nearest incumbent: Frontier-A AR forecast surprise / Frontier-F weekly payoff posterior
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
PARAMS = {"top_k": 5, "window": 42}
FAST_DAYS = 7


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


def _rank(frame, eligible):
    ordered = frame.where(eligible).sort_index(axis=1)
    return ordered.rank(axis=1, ascending=False, method="first")


def signals(data, window, mode="base"):
    close, liquid, returns = _context(data)
    residual = returns.sub(_market(returns, liquid), axis=0).where(liquid)
    slow = residual.rolling(window).mean()
    fast = residual.rolling(FAST_DAYS).mean()
    eligible = liquid & slow.notna() & fast.notna()
    if mode == "ablation":
        positive = slow.where(eligible & (slow > 0))
        peak = positive.max(axis=1)
        score = positive.div(peak.replace(0, np.nan), axis=0).clip(0, 1).fillna(0.0)
        return score.reindex(columns=close.columns).fillna(0.0), liquid
    n = eligible.sum(axis=1)
    disagreement = (_rank(slow, eligible) - _rank(fast, eligible)).abs().div((n - 1).clip(lower=1), axis=0)
    agreement = (1.0 - disagreement).where(n > 1)
    both_positive = eligible & (slow > 0) & (fast > 0)
    if mode == "falsifier":
        score = disagreement.where(both_positive, 0.0)
    else:
        score = agreement.where(both_positive, 0.0)
    return score.reindex(columns=close.columns).clip(0, 1).fillna(0.0), liquid


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
