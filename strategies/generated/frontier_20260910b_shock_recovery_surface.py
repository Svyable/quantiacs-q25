"""frontier_20260910b_shock_recovery_surface — PENDING RESEARCH STRATEGY; no performance or submission claim.
Experiment: frontier_20260910b_shock_recovery_surface
Preregistration SHA256: 75e750fe7672dcb2aeaa9d2b312f81ae72e6974eb38646bd89d0856d114e6d69
Mechanism: standardized idiosyncratic shock depth × recovery slope × age × failed recovery
Nearest incumbent: CoCrash126 and V10 residual momentum
Novelty axes: information_primitive, transform, timing_or_state_condition

Completed daily Quantiacs close + historical is_liquid only. The evaluator applies
the execution lag. Event state is bounded by the candidate recovery window.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "shock_recovery_surface"
PARAMS = {"window": 42, "top_k": 5}
VOL_WINDOW = 42
SHOCK_DAYS = 3
SHOCK_Z = 2.0


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def signals(data, window, mode="base"):
    c = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & c.notna()
    r = np.log(c / c.shift(1))
    market = r.where(liquid).mean(axis=1)
    residual = r.sub(market, axis=0)

    ordered = sorted(c.columns)
    resid = residual.reindex(columns=ordered)
    liq = liquid.reindex(columns=ordered)
    scale = resid.rolling(VOL_WINDOW, min_periods=VOL_WINDOW // 2).std(ddof=1).shift(1).clip(lower=1e-6)
    z3 = resid.rolling(SHOCK_DAYS, min_periods=SHOCK_DAYS).sum() / (scale * np.sqrt(SHOCK_DAYS))
    shock = z3 <= -SHOCK_Z
    depth_raw = (-z3).where(shock, 0.0).clip(lower=0.0, upper=8.0)

    if mode == "falsifier":
        shock_vals = np.roll(shock.to_numpy(dtype=bool), 1, axis=1)
        depth_vals = np.roll(depth_raw.to_numpy(dtype=float), 1, axis=1)
        shock = pd.DataFrame(shock_vals, index=shock.index, columns=shock.columns)
        depth_raw = pd.DataFrame(depth_vals, index=depth_raw.index, columns=depth_raw.columns)
    elif mode not in {"base", "ablation"}:
        raise ValueError("unknown control mode")

    rv = resid.fillna(0.0).to_numpy(dtype=float)
    lv = liq.to_numpy(dtype=bool)
    sv = shock.fillna(False).to_numpy(dtype=bool)
    dv = depth_raw.fillna(0.0).to_numpy(dtype=float)
    n, m = rv.shape
    since = np.full((n, m), window + 1, dtype=float)
    recovery = np.zeros((n, m), dtype=float)
    failures = np.zeros((n, m), dtype=float)
    depth = np.zeros((n, m), dtype=float)

    for i in range(n):
        for j in range(m):
            if not lv[i, j]:
                continue
            if sv[i, j]:
                since[i, j] = 0.0
                depth[i, j] = dv[i, j]
                continue
            if i > 0 and lv[i - 1, j] and since[i - 1, j] <= window:
                since[i, j] = min(since[i - 1, j] + 1.0, window + 1.0)
                recovery[i, j] = recovery[i - 1, j] + rv[i, j]
                failures[i, j] = failures[i - 1, j] + float(rv[i, j] < 0.0)
                depth[i, j] = depth[i - 1, j]

    active = (since >= 1.0) & (since <= float(window)) & (recovery > 0.0)
    if mode == "ablation":
        value = np.where((since >= 1.0) & (since <= float(window)), depth, 0.0)
    else:
        slope = np.divide(recovery, np.maximum(since, 1.0))
        success = 1.0 - np.divide(failures, np.maximum(since, 1.0))
        freshness = np.maximum(0.0, 1.0 - since / (float(window) + 1.0))
        value = np.where(active, depth * np.maximum(slope, 0.0) * np.maximum(success, 0.0) * freshness, 0.0)

    score = pd.DataFrame(value, index=c.index, columns=ordered).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return score.reindex(columns=c.columns), liquid


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"}:
        raise ValueError("expected exactly window, top_k")
    if any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("parameters must be positive integers")
    if VOL_WINDOW + SHOCK_DAYS + p["window"] + 14 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown control mode")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing:
        raise ValueError("times must be unique and increasing")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("assets must be unique")
    score, liquid = signals(data, p["window"], mode)
    return _allocate(score, liquid, data.time, p["top_k"])

def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    selected = selected.reindex(columns=score.columns)
    raw = selected.astype(float) * min(NAME_CAP, 1 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=raw.index)
    weights = raw.where(monday, axis=0).ffill(limit=6).fillna(0.0)
    weights = weights.where(liquid, 0.0)
    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": times, "asset": score.columns},
        name=COMPETITION_TYPE,
    )


def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


if __name__ == "__main__":
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
