"""frontier_20260910b_liquidity_hysteresis — PENDING RESEARCH STRATEGY; no performance or submission claim.
Experiment: frontier_20260910b_liquidity_hysteresis
Preregistration SHA256: 0b0082f4e472874d1666d064ee97b1bf70091c1776b841343ec1f02f12440f61
Mechanism: historical liquidity-eligibility re-entry, maturity and transition hysteresis
Nearest incumbent: V11 simple liquidity lifecycle sleeve
Novelty axes: information_primitive, transform, timing_or_state_condition

Completed daily Quantiacs close + historical is_liquid only. The evaluator applies
the execution lag. Episode state is capped/rolled so 365 observations reconstruct it.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "liquidity_hysteresis"
PARAMS = {"window": 42, "top_k": 5}
STATE_WINDOW = 126
TREND_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _episode_age(liquid):
    values = liquid.to_numpy(dtype=bool)
    out = np.zeros_like(values, dtype=float)
    for i in range(len(values)):
        if i == 0:
            out[i] = values[i].astype(float)
        else:
            out[i] = np.where(values[i], np.minimum(out[i - 1] + 1.0, STATE_WINDOW), 0.0)
    return pd.DataFrame(out, index=liquid.index, columns=liquid.columns)


def signals(data, window, mode="base"):
    c = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & c.notna()
    ordered = sorted(c.columns)
    c_s = c.reindex(columns=ordered)
    liq_s = liquid.reindex(columns=ordered)

    age = _episode_age(liq_s)
    flips = liq_s.ne(liq_s.shift(1))
    if len(flips):
        flips.iloc[0] = False
    churn = flips.astype(float).rolling(STATE_WINDOW, min_periods=1).sum()
    recent_gap = (~liq_s).shift(1).astype(float).rolling(STATE_WINDOW, min_periods=1).max().fillna(0.0)

    width = max(7.0, 0.75 * float(window))
    maturity = np.exp(-(age - float(window)).abs() / width)
    stability = 1.0 / (1.0 + churn)
    metadata = maturity * stability * recent_gap

    if mode == "ablation":
        metadata = maturity
    elif mode == "falsifier":
        vals = metadata.to_numpy(dtype=float)
        metadata = pd.DataFrame(np.roll(vals, 1, axis=1), index=metadata.index, columns=metadata.columns)
    elif mode != "base":
        raise ValueError("unknown control mode")

    trend = c_s.pct_change(TREND_DAYS, fill_method=None) > 0
    score = metadata.where(liq_s & trend, 0.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return score.reindex(columns=c.columns), liquid


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"}:
        raise ValueError("expected exactly window, top_k")
    if any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("parameters must be positive integers")
    if max(STATE_WINDOW, p["window"], TREND_DAYS) + 14 >= LOOKBACK_DAYS:
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
