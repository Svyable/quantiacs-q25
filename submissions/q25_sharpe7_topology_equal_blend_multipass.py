"""Q25 fixed Sharpe7 + topology-migration equal blend.

Self-contained production packaging of the exact frozen 50/50 synthesis measured
in deadline_20260918_sharpe7_topology_blend and opened once on the protected
2023-2024 window in deadline_20260919_sharpe7_topology_blend_forward_validation.

No blend-weight search. No hard-coded assets. Quantiacs crypto-daily close and
historical is_liquid only. Long-only; unused gross stays cash.

This artifact is a qualified submission candidate pending account-bound
Quantiacs uniqueness/correlation clearance.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
START_DATE = "2016-01-01"
NAME_CAP = 0.25
EPS = 1e-12

# Frozen topology member configuration.
TOPO_WINDOW = 84
TOPO_TOP_K = 5
GRAPH_LAG = 21
TREND_DAYS = 21


# ---------------------------------------------------------------------------
# Frozen Sharpe7 member (window=7, base mode)
# ---------------------------------------------------------------------------
def _sh7_close_liquid(data):
    close = data.sel(field="close").transpose("time", "asset").astype(float)
    liq0 = data.sel(field="is_liquid").transpose("time", "asset")
    liquid = xr.where((liq0 == 1) & np.isfinite(close) & (close > 0), 1.0, 0.0)
    return close, liquid


def _sh7_returns(close):
    r = close / close.shift(time=1) - 1.0
    return xr.where(np.isfinite(r), r, 0.0)


def _sh7_sma(x, n, min_periods=None):
    m = n if min_periods is None else min_periods
    if x.sizes["time"] < m:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=m).mean()


def _sh7_std(x, n, min_periods=None):
    m = max(2, n // 2) if min_periods is None else min_periods
    if x.sizes["time"] < m:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=m).std()


def _sh7_max(x, n, min_periods):
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(
        time=min(n, x.sizes["time"]), min_periods=min_periods
    ).max()


def _sh7_liquid_cs_mean(x, liquid):
    n = liquid.sum("asset")
    return xr.where(
        n > 0,
        (xr.where(np.isfinite(x), x, 0.0) * liquid).sum("asset") / n,
        0.0,
    )


def _sh7_liquid_cs_std(x, liquid):
    mean = _sh7_liquid_cs_mean(x, liquid)
    n = liquid.sum("asset")
    var = xr.where(
        n > 0,
        (((xr.where(np.isfinite(x), x, 0.0) - mean) ** 2) * liquid).sum("asset")
        / n,
        0.0,
    )
    return np.sqrt(xr.where(var > 0, var, 0.0))


def _sh7_allocate(raw, liquid):
    raw = xr.where(np.isfinite(raw) & (raw > 0), raw, 0.0) * liquid
    gross = raw.sum("asset")
    normalized = xr.where(gross > EPS, raw / gross, 0.0)
    capped = xr.where(normalized > NAME_CAP, NAME_CAP, normalized) * liquid
    return (
        capped.transpose("time", "asset")
        .fillna(0.0)
        .reset_coords("field", drop=True)
    )


def _sh7_strategy(data):
    close, liquid = _sh7_close_liquid(data)
    r = _sh7_returns(close)
    mu7 = _sh7_sma(r, 7, 5)
    vol14 = _sh7_std(r, 14, 7)
    s7 = np.sqrt(365.0) * mu7 / (vol14 + EPS)
    sma12 = _sh7_sma(close, 12, 8)
    sma48 = _sh7_sma(close, 48, 24)
    mom14 = close / close.shift(time=14) - 1.0
    peak30 = _sh7_max(close, 30, 15)
    dd30 = close / (peak30 + EPS) - 1.0
    mean = _sh7_liquid_cs_mean(s7, liquid)
    sd = _sh7_liquid_cs_std(s7, liquid)
    hurdle = mean + 0.20 * sd
    quality = xr.where(s7 > hurdle, s7 - hurdle, 0.0)
    gate = (
        (sma12 > sma48)
        & (mom14 > 0.0)
        & (dd30 > -0.22)
        & (vol14 > 0.0)
    )
    raw = (
        xr.where(
            gate,
            (quality.clip(min=0.0) ** 1.25) / (vol14 + 0.015),
            0.0,
        )
        * liquid
    )
    raw = _sh7_sma(raw, 3, 1) * liquid
    return _sh7_allocate(raw, liquid)


# ---------------------------------------------------------------------------
# Frozen topology-migration member (window=84, top_k=5, base mode)
# ---------------------------------------------------------------------------
def _topo_field(data, name):
    return (
        data.sel(field=name)
        .transpose("time", "asset")
        .to_pandas()
        .astype(float)
    )


def _topo_centrality(frame, min_periods):
    corr = frame.corr(min_periods=min_periods)
    values = corr.to_numpy(dtype=float).copy()
    if values.size == 0:
        return pd.Series(dtype=float), np.nan
    np.fill_diagonal(values, np.nan)
    central = np.nanmean(np.abs(values), axis=1)
    global_level = (
        float(np.nanmean(np.abs(values))) if np.isfinite(values).any() else np.nan
    )
    return pd.Series(central, index=corr.index), global_level


def _topo_signals(data):
    c = _topo_field(data, "close").where(
        lambda x: np.isfinite(x) & (x > 0)
    )
    liquid = _topo_field(data, "is_liquid").eq(1) & c.notna()
    r = np.log(c / c.shift(1))
    market = r.where(liquid).mean(axis=1)
    residual = r.sub(market, axis=0)

    ordered = sorted(c.columns)
    residual_s = residual.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=c.index, columns=ordered)
    times = pd.DatetimeIndex(c.index)
    minp = max(16, TOPO_WINDOW // 2)
    first = TOPO_WINDOW + GRAPH_LAG + 2

    for i in range(first, len(times)):
        if times[i].dayofweek != 0:
            continue
        cur = residual_s.iloc[i - TOPO_WINDOW + 1 : i + 1]
        prev_end = i - GRAPH_LAG
        prev = residual_s.iloc[
            prev_end - TOPO_WINDOW + 1 : prev_end + 1
        ]
        cur_cent, cur_global = _topo_centrality(cur, minp)
        prev_cent, prev_global = _topo_centrality(prev, minp)
        if not np.isfinite(cur_global) or not np.isfinite(prev_global):
            continue
        fragmentation = max(prev_global - cur_global, 0.0)
        if fragmentation <= 0:
            continue
        migration = (prev_cent - cur_cent).replace(
            [np.inf, -np.inf], np.nan
        )
        trend = residual_s.iloc[
            max(0, i - TREND_DAYS + 1) : i + 1
        ].sum(min_count=max(5, TREND_DAYS // 2))

        raw = migration.clip(lower=0.0) * fragmentation
        raw = raw.where(trend > 0, 0.0)
        out.iloc[i] = raw.reindex(ordered).fillna(0.0).to_numpy()

    return out.reindex(columns=c.columns), liquid


def _topo_allocate(score, liquid, times):
    ranked = score.where(liquid & (score > 0)).sort_index(axis=1)
    selected = (
        ranked.rank(axis=1, ascending=False, method="first") <= TOPO_TOP_K
    )
    selected = selected.reindex(columns=score.columns)
    raw = selected.astype(float) * min(NAME_CAP, 1 / TOPO_TOP_K)
    monday = pd.Series(
        pd.DatetimeIndex(times).dayofweek == 0, index=raw.index
    )
    weights = raw.where(monday, axis=0).ffill(limit=6).fillna(0.0)
    weights = weights.where(liquid, 0.0)
    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": times, "asset": score.columns},
        name=COMPETITION_TYPE,
    )


def _topo_strategy(data):
    if 2 * TOPO_WINDOW + GRAPH_LAG + TREND_DAYS + 14 >= LOOKBACK_DAYS:
        raise ValueError("frozen parameters exceed finite replay horizon")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing:
        raise ValueError("times must be unique and increasing")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("assets must be unique")
    score, liquid = _topo_signals(data)
    return _topo_allocate(score, liquid, data.time)


# ---------------------------------------------------------------------------
# Exact frozen 50/50 synthesis
# ---------------------------------------------------------------------------
def strategy(data):
    a = _sh7_strategy(data)
    if "time" in a.dims:
        a = a.isel(time=-1, drop=True)

    b = _topo_strategy(data)
    if "time" in b.dims:
        b = b.isel(time=-1, drop=True)

    a, b = xr.align(a, b, join="outer", fill_value=0.0)
    w = 0.5 * a + 0.5 * b
    liquid = data.sel(field="is_liquid").isel(time=-1, drop=True)
    return xr.where((liquid == 1) & (w > 0), w, 0.0).fillna(0.0)


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata

    return qndata.cryptodaily_load_data(tail=period)


def run_multipass():
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt

    return qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date=START_DATE,
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )


if __name__ == "__main__":
    run_multipass()
