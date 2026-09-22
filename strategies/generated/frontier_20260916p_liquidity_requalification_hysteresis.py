"""Frontier-P liquidity requalification hysteresis — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260916p_liquidity_requalification_hysteresis
Preregistration SHA256: c9557848eb0b1de6b4f29c59a343e0f2e77179b8b22aa6f0284315c5e9354ccf

Mechanism: use historical is_liquid membership as a causal state process. Rank
currently eligible assets whose recent eligibility persistence has improved
relative to longer memory, after a short stable requalification period, and
pair that state with orderly positive market-residual price assimilation.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
EPS = 1e-12
SHORT_MEMORY = 14
MIN_STABLE_DAYS = 7
AGE_CAP = 28
CONFIRM_DAYS = 7
FAMILY = "liquidity_requalification_hysteresis"
PREREGISTRATION_SHA256 = "c9557848eb0b1de6b4f29c59a343e0f2e77179b8b22aa6f0284315c5e9354ccf"
PARAMS = {"window": 63, "top_k": 5}


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _run_age(liquid, cap=AGE_CAP):
    """Consecutive current eligible days, capped so replay state is bounded."""
    active = pd.DataFrame(True, index=liquid.index, columns=liquid.columns)
    age = pd.DataFrame(0.0, index=liquid.index, columns=liquid.columns)
    for lag in range(cap):
        active = active & liquid.shift(lag).fillna(False)
        age = age + active.astype(float)
    return age


def _eligibility_state(liquid, window):
    history = liquid.astype(float).shift(1)
    min_periods = max(21, window // 2)
    long_share = history.rolling(window, min_periods=min_periods).mean()
    short_share = history.rolling(SHORT_MEMORY, min_periods=MIN_STABLE_DAYS).mean()
    flips = (history - history.shift(1)).abs().rolling(
        window, min_periods=min_periods
    ).sum()

    requalification_gap = (short_share - long_share).clip(lower=0.0)
    memory_of_exclusion = (1.0 - long_share).clip(lower=0.0)
    stability = 1.0 / (1.0 + flips.clip(lower=0.0))
    age = _run_age(liquid)

    state = requalification_gap * memory_of_exclusion * stability
    state = state.where(age >= MIN_STABLE_DAYS, 0.0)
    return state.where(liquid, 0.0)


def _residual_confirmation(close, liquid):
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = returns.sub(market, axis=0)
    numerator = residual.rolling(CONFIRM_DAYS, min_periods=5).sum()
    denominator = residual.abs().rolling(CONFIRM_DAYS, min_periods=5).sum()
    efficiency = numerator / (denominator + EPS)
    return efficiency.clip(lower=0.0)


def _rotate_eligible(values, eligible):
    ordered = values.sort_index(axis=1)
    mask = eligible.reindex(columns=ordered.columns).fillna(False)
    out = ordered.copy()
    for i in range(len(out)):
        arr = out.iloc[i].to_numpy(dtype=float).copy()
        loc = np.flatnonzero(mask.iloc[i].to_numpy(dtype=bool) & np.isfinite(arr))
        if len(loc) > 1:
            arr[loc] = np.roll(arr[loc], 1)
            out.iloc[i] = arr
    return out.reindex(columns=values.columns)


def signals(data, window, mode="base"):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()

    state = _eligibility_state(liquid, window)
    confirmation = _residual_confirmation(close, liquid)

    if mode == "base":
        deployed_state = state
    elif mode == "ablation":
        deployed_state = pd.DataFrame(1.0, index=state.index, columns=state.columns)
    elif mode == "falsifier":
        deployed_state = _rotate_eligible(state, liquid)
    else:
        raise ValueError("unknown control mode")

    score = deployed_state * confirmation
    score = score.where(liquid & np.isfinite(score) & (score > 0), 0.0)
    return score.replace([np.inf, -np.inf], np.nan), liquid


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    selected = selected.reindex(columns=score.columns)
    target = selected.astype(float) * min(NAME_CAP, 1.0 / top_k)

    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)

    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": times, "asset": score.columns},
        name=COMPETITION_TYPE,
    )


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] not in {42, 63, 84} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-P grid")
    if p["window"] + AGE_CAP + CONFIRM_DAYS + 14 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown mode")

    score, liquid = signals(data, p["window"], mode)
    return _allocate(score, liquid, data.time, p["top_k"])


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


if __name__ == "__main__":
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt

    qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date="2016-01-01",
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )
