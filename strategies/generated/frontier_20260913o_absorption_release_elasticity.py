"""Frontier-O price-volume absorption/release elasticity — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260913o_absorption_release_elasticity
Preregistration SHA256: 51a2fede98155a65235f790baf1bb22b702dbe7a9d4a6de2cb119626863ce847

Mechanism: rank liquid assets that previously absorbed abnormal same-asset dollar
volume with little market-residual displacement, then show a positive efficient
release. This is a same-asset price-volume elasticity object, not cross-asset
abnormal-volume diffusion.
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
ABSORB_DAYS = 5
MIN_ABSORB_DAYS = 3
RELEASE_DAYS = 3
FAMILY = "absorption_release_elasticity"
PREREGISTRATION_SHA256 = "51a2fede98155a65235f790baf1bb22b702dbe7a9d4a6de2cb119626863ce847"
PARAMS = {"window": 63, "top_k": 5}


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _base(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    vol = _field(data, "vol").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna() & vol.notna()
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = returns.sub(market, axis=0)
    dollar = (close * vol).where(liquid)
    return liquid, residual, dollar


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


def _pressure_and_displacement(residual, dollar, window):
    min_periods = max(20, window // 2)
    baseline_dollar = dollar.shift(1).rolling(window, min_periods=min_periods).mean()
    pressure = np.log((dollar + EPS) / (baseline_dollar + EPS)).clip(lower=0.0)

    abs_resid = residual.abs()
    baseline_move = abs_resid.shift(1).rolling(window, min_periods=min_periods).mean()
    displacement = (abs_resid / (baseline_move + EPS)).clip(lower=0.0)
    return pressure, displacement


def _score_from_components(pressure, displacement, residual, liquid, mode):
    if mode == "base":
        paired_pressure = pressure
    elif mode == "ablation":
        paired_pressure = pd.DataFrame(1.0, index=pressure.index, columns=pressure.columns)
    elif mode == "falsifier":
        paired_pressure = _rotate_eligible(pressure, liquid)
    else:
        raise ValueError("unknown control mode")

    absorption = (paired_pressure / (1.0 + displacement)).where(liquid)
    absorb_days = absorption.gt(0.0).rolling(ABSORB_DAYS, min_periods=ABSORB_DAYS).sum()
    stored = absorption.rolling(ABSORB_DAYS, min_periods=ABSORB_DAYS).sum()
    stored = stored.where(absorb_days >= MIN_ABSORB_DAYS).shift(1)

    release_move = residual.clip(lower=0.0).rolling(RELEASE_DAYS, min_periods=RELEASE_DAYS).sum()
    release_flow = pressure.rolling(RELEASE_DAYS, min_periods=RELEASE_DAYS).mean()
    release_efficiency = release_move / (1.0 + release_flow)

    score = (stored.clip(lower=0.0) * release_efficiency.clip(lower=0.0)).where(liquid, 0.0)
    return score.replace([np.inf, -np.inf], np.nan)


def signals(data, window, mode="base"):
    liquid, residual, dollar = _base(data)
    pressure, displacement = _pressure_and_displacement(residual, dollar, window)
    score = _score_from_components(pressure, displacement, residual, liquid, mode)
    return score, liquid


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
        raise ValueError("outside preregistered Frontier-O grid")
    if p["window"] + ABSORB_DAYS + RELEASE_DAYS + 14 >= LOOKBACK_DAYS:
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
