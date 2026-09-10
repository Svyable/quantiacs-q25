"""frontier_20260910_vol_curve — PENDING RESEARCH STRATEGY; no performance or submission claim.
Experiment: frontier_20260910_vol_curve
Preregistration SHA256: 2723da4e46b234345cc572c994e51af493497b5814ba6ecf3118b74f45169536
Mechanism: Concave descending vol curves with positive recovery returns identify stabilization
Nearest incumbent: C165 / inverse-vol trend
Novelty axes: transform, timing_or_state_condition

Signals use completed daily OHLCV and historical is_liquid. The evaluator
applies the execution lag; do not shift these targets again. All state has a
finite rolling horizon and is reconstructable from 365 daily observations.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "vol_curve"
PARAMS = {'window': 21, 'persistence': 5, 'top_k': 5}


def signals(data, window, persistence, mode="base"):
    def field(name):
        return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)
    c = field("close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = field("is_liquid").eq(1) & c.notna()
    r = np.log(c / c.shift(1))
    if FAMILY == "forecast_surprise":
        market = r.where(liquid).mean(axis=1)
        residual = r.sub(market, axis=0)
        x = residual.shift(1)
        slope = residual.rolling(window).cov(x) / x.rolling(window).var().clip(lower=1e-10)
        intercept = residual.rolling(window).mean() - slope * x.rolling(window).mean()
        # Coefficients through yesterday predict today's realized residual.
        predicted = intercept.shift(1) + slope.shift(1) * x
        surprise = residual - predicted
        if mode == "ablation":
            surprise = residual
        elif mode == "falsifier":
            # Destroy prediction/asset pairing, deterministically and causally.
            predicted = predicted.loc[:, sorted(predicted.columns)]
            swapped = pd.DataFrame(np.roll(predicted.to_numpy(), 1, axis=1),
                                   index=predicted.index, columns=predicted.columns)
            surprise = residual - swapped
        score = surprise.rolling(persistence).mean()
    elif FAMILY == "flow_absorption":
        o, h, l, v = field("open"), field("high"), field("low"), field("vol")
        flow = np.log((c * v).where((v > 0) & np.isfinite(v)))
        flow_z = (flow - flow.rolling(window).mean().shift(1)) / flow.rolling(window).std().shift(1).clip(lower=1e-8)
        span = (h - l).where((h > l) & (o > 0))
        location = ((c - l) / span).clip(0, 1)
        displacement = ((c - o).abs() / span).clip(0, 1)
        if mode == "falsifier":
            # Preserve today's marginal flow distribution; destroy own-asset pairing.
            flow_z = flow_z.loc[:, sorted(flow_z.columns)]
            flow_z = pd.DataFrame(np.roll(flow_z.to_numpy(), 1, axis=1),
                                  index=flow_z.index, columns=flow_z.columns)
        score = flow_z.clip(0, 3) * (2 * location - 1).clip(lower=0) * (1 - displacement)
        if mode == "ablation":
            score = flow_z.clip(0, 3)
        score = score.rolling(persistence).mean()
    elif FAMILY == "vol_curve":
        short = r.rolling(window).std().clip(lower=1e-8)
        middle = r.rolling(2 * window).std().clip(lower=1e-8)
        long = r.rolling(4 * window).std().clip(lower=1e-8)
        curvature = np.log(short / middle) - np.log(middle / long)
        gate = (short < middle) & (middle < long) & (curvature < 0)
        if mode == "falsifier":
            gate = (short > middle) & (middle > long) & (curvature > 0)
        score = np.log(long / short).abs().where(gate & (r.rolling(persistence).sum() > 0), 0)
        if mode == "ablation":
            score = 1 / long
    else:
        raise ValueError(FAMILY)
    return score.replace([np.inf, -np.inf], np.nan).reindex(columns=liquid.columns), liquid


def strategy(data, params=None, mode="base"):
    """Vectorized causal targets, with no imports from this repository."""
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "persistence", "top_k"}:
        raise ValueError("expected exactly window, persistence, top_k")
    if any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("parameters must be positive integers")
    if p["window"] * 4 + p["persistence"] + 8 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown control mode")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing:
        raise ValueError("times must be unique and increasing")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("assets must be unique")
    score, liquid = signals(data, p["window"], p["persistence"], mode)
    # Label ordering is only deterministic tie-breaking, never coin selection.
    ranked = score.where(liquid & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= p["top_k"]
    selected = selected.reindex(columns=score.columns)
    # Fixed per-slot sizing retains cash when fewer than K names qualify.
    raw = selected.astype(float) * min(NAME_CAP, 1 / p["top_k"])
    monday = pd.Series(times.dayofweek == 0, index=raw.index)
    weights = raw.where(monday, axis=0).ffill(limit=6).fillna(0)
    # Eligibility loss always exits, including between scheduled rebalances.
    weights = weights.where(liquid, 0)
    return xr.DataArray(weights.to_numpy(), dims=("time", "asset"),
                        coords={"time": data.time, "asset": data.asset}, name=COMPETITION_TYPE)


def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


if __name__ == "__main__":
    import qnt.backtester as qnbt
    qnbt.backtest(competition_type=COMPETITION_TYPE, load_data=load_data,
                 lookback_period=LOOKBACK_DAYS, start_date="2016-01-01",
                 strategy=strategy, analyze=True, check_correlation=True)
