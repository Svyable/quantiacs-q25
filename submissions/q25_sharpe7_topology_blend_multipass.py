"""Q25 production candidate: frozen 50/50 Sharpe7 + topology blend.

Self-contained Quantiacs submission artifact for the preregistered
q25_sharpe7_topology_equal_blend_v1 candidate. Member formulas and blend weights
are frozen; unused gross remains cash.
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
SHARPE7_WINDOW = 7
TOPOLOGY_WINDOW = 84
TOPOLOGY_TOP_K = 5
TOPOLOGY_GRAPH_LAG = 21
TOPOLOGY_TREND_DAYS = 21


def _sma(x, n, min_periods=None):
    m = n if min_periods is None else min_periods
    if x.sizes["time"] < m:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=m).mean()


def _std(x, n, min_periods=None):
    m = max(2, n // 2) if min_periods is None else min_periods
    if x.sizes["time"] < m:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=m).std()


def _max(x, n, min_periods):
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=min_periods).max()


def _cs_mean(x, liquid):
    n = liquid.sum("asset")
    return xr.where(
        n > 0,
        (xr.where(np.isfinite(x), x, 0.0) * liquid).sum("asset") / n,
        0.0,
    )


def _cs_std(x, liquid):
    mean = _cs_mean(x, liquid)
    n = liquid.sum("asset")
    var = xr.where(
        n > 0,
        (((xr.where(np.isfinite(x), x, 0.0) - mean) ** 2) * liquid).sum("asset") / n,
        0.0,
    )
    return np.sqrt(xr.where(var > 0, var, 0.0))


def _sharpe7_member(data):
    close = data.sel(field="close").transpose("time", "asset").astype(float)
    liq0 = data.sel(field="is_liquid").transpose("time", "asset")
    liquid = xr.where((liq0 == 1) & np.isfinite(close) & (close > 0), 1.0, 0.0)
    r = close / close.shift(time=1) - 1.0
    r = xr.where(np.isfinite(r), r, 0.0)
    mu7 = _sma(r, 7, 5)
    vol14 = _std(r, 14, 7)
    s7 = np.sqrt(365.0) * mu7 / (vol14 + EPS)
    sma12 = _sma(close, 12, 8)
    sma48 = _sma(close, 48, 24)
    mom14 = close / close.shift(time=14) - 1.0
    peak30 = _max(close, 30, 15)
    dd30 = close / (peak30 + EPS) - 1.0
    mean = _cs_mean(s7, liquid)
    sd = _cs_std(s7, liquid)
    hurdle = mean + 0.20 * sd
    quality = xr.where(s7 > hurdle, s7 - hurdle, 0.0)
    gate = (sma12 > sma48) & (mom14 > 0.0) & (dd30 > -0.22) & (vol14 > 0.0)
    raw = xr.where(
        gate,
        (quality.clip(min=0.0) ** 1.25) / (vol14 + 0.015),
        0.0,
    ) * liquid
    raw = _sma(raw, 3, 1) * liquid
    raw = xr.where(np.isfinite(raw) & (raw > 0), raw, 0.0) * liquid
    gross = raw.sum("asset")
    normalized = xr.where(gross > EPS, raw / gross, 0.0)
    capped = xr.where(normalized > NAME_CAP, NAME_CAP, normalized) * liquid
    return capped.transpose("time", "asset").fillna(0.0).reset_coords("field", drop=True)


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _centrality(frame, min_periods):
    corr = frame.corr(min_periods=min_periods)
    values = corr.to_numpy(dtype=float).copy()
    if values.size == 0:
        return pd.Series(dtype=float), np.nan
    np.fill_diagonal(values, np.nan)
    central = np.nanmean(np.abs(values), axis=1)
    global_level = float(np.nanmean(np.abs(values))) if np.isfinite(values).any() else np.nan
    return pd.Series(central, index=corr.index), global_level


def _topology_member(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).mean(axis=1)
    residual = returns.sub(market, axis=0)

    ordered = sorted(close.columns)
    residual_s = residual.reindex(columns=ordered)
    score = pd.DataFrame(0.0, index=close.index, columns=ordered)
    times = pd.DatetimeIndex(close.index)
    minp = max(16, TOPOLOGY_WINDOW // 2)
    first = TOPOLOGY_WINDOW + TOPOLOGY_GRAPH_LAG + 2

    for i in range(first, len(times)):
        if times[i].dayofweek != 0:
            continue
        cur = residual_s.iloc[i - TOPOLOGY_WINDOW + 1:i + 1]
        prev_end = i - TOPOLOGY_GRAPH_LAG
        prev = residual_s.iloc[prev_end - TOPOLOGY_WINDOW + 1:prev_end + 1]
        cur_cent, cur_global = _centrality(cur, minp)
        prev_cent, prev_global = _centrality(prev, minp)
        if not np.isfinite(cur_global) or not np.isfinite(prev_global):
            continue
        fragmentation = max(prev_global - cur_global, 0.0)
        if fragmentation <= 0:
            continue
        migration = (prev_cent - cur_cent).replace([np.inf, -np.inf], np.nan)
        trend = residual_s.iloc[
            max(0, i - TOPOLOGY_TREND_DAYS + 1):i + 1
        ].sum(min_count=max(5, TOPOLOGY_TREND_DAYS // 2))
        raw = migration.clip(lower=0.0) * fragmentation
        raw = raw.where(trend > 0, 0.0)
        score.iloc[i] = raw.reindex(ordered).fillna(0.0).to_numpy()

    score = score.reindex(columns=close.columns)
    ranked = score.where(liquid & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= TOPOLOGY_TOP_K
    selected = selected.reindex(columns=score.columns)
    raw = selected.astype(float) * min(NAME_CAP, 1.0 / TOPOLOGY_TOP_K)
    monday = pd.Series(times.dayofweek == 0, index=raw.index)
    weights = raw.where(monday, axis=0).ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": times, "asset": score.columns},
        name=COMPETITION_TYPE,
    )


def _latest(weights):
    return weights.isel(time=-1, drop=True) if "time" in weights.dims else weights


def strategy(data):
    a = _latest(_sharpe7_member(data))
    b = _latest(_topology_member(data))
    a, b = xr.align(a, b, join="outer", fill_value=0.0)
    blended = 0.5 * a + 0.5 * b
    liquid = data.sel(field="is_liquid").isel(time=-1, drop=True)
    return xr.where(
        (liquid == 1) & np.isfinite(blended) & (blended > 0),
        blended,
        0.0,
    ).fillna(0.0)


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


def run_backtest():
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
    run_backtest()
