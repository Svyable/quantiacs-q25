"""Q25 recursive lattice execution guard — frozen refinement candidate.

Experiment: deadline_20260919_recursive_lattice_execution
Status: PREREGISTERED / UNMEASURED until exact Quantiacs evidence is produced.

This is a robustness refinement of the frozen lattice-consensus family, not a
new independent alpha claim. The signal layer is intentionally kept in the
same family; the experiment asks whether a bounded recursive execution state
can retain the useful signal while reducing ATR-linked trading damage.

Central mechanism
-----------------
1. Build the same five causal support predicates used by lattice-consensus:
   positive 18/50 trend, above-cross-sectional 7-day Sharpe, positive 14-day
   momentum, non-extreme 21-day volatility, and drawdown above -25%.
2. Build the same quality score and >=4/5 admission lattice.
3. Convert it to a capped long-only target book.
4. Execute recursively inside each calendar week:
   - Monday re-anchors exactly to the current target, bounding state memory;
   - liquid-universe and signal exits are immediate;
   - otherwise a resize occurs only when the target-current weight gap exceeds
     0.50 * ATR(14)% for that asset.

The weekly re-anchor is deliberate: terminal output depends only on the current
week plus trailing indicators, so a 365-day live/multipass slice does not carry
hidden unbounded portfolio state. Cash is retained when suppressed entries or
capped capacity leave gross below one.

Only Quantiacs cryptodaily OHLCV + historical is_liquid are used. No symbols,
external data, negative shifts, centered windows, or future-finalized state.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
RESEARCH_START = "2016-01-01"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
EPS = 1e-12

# Frozen execution knobs for this experiment. Changing them creates a new experiment.
ENTRY_SUPPORT = 4.0          # inherited lattice admission rule
RETENTION_SUPPORT = 3.0      # diagnostic control only; not used by central strategy
ATR_DEADBAND_MULT = 0.50     # resize threshold = multiplier * ATR(14)%
WEEKLY_REANCHOR_DAY = 0      # Monday, pandas convention


def _base(data: xr.DataArray):
    close = data.sel(field="close").transpose("time", "asset").astype(float)
    liquid0 = data.sel(field="is_liquid").transpose("time", "asset")
    liquid = xr.where((liquid0 == 1) & np.isfinite(close) & (close > 0), 1.0, 0.0)
    ret = close / close.shift(time=1) - 1.0
    return close, liquid, xr.where(np.isfinite(ret), ret, 0.0)


def _sma(x: xr.DataArray, n: int, min_periods: int):
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=min_periods).mean()


def _std(x: xr.DataArray, n: int, min_periods: int):
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=min_periods).std()


def _max(x: xr.DataArray, n: int, min_periods: int):
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=min_periods).max()


def _mean(x: xr.DataArray, liquid: xr.DataArray):
    n = liquid.sum("asset")
    safe = xr.where(np.isfinite(x), x, 0.0)
    return xr.where(n > 0, (safe * liquid).sum("asset") / n, 0.0)


def _true_range_pct(data: xr.DataArray, close: xr.DataArray):
    high = data.sel(field="high").transpose("time", "asset").astype(float)
    low = data.sel(field="low").transpose("time", "asset").astype(float)
    prev = close.shift(time=1)
    tr = xr.concat(
        [abs(high - low), abs(high - prev), abs(low - prev)], dim="tr_component"
    ).max("tr_component")
    atr = tr.rolling(time=14, min_periods=7).mean()
    pct = atr / (abs(close) + EPS)
    return xr.where(np.isfinite(pct), pct, 0.0).clip(min=0.0, max=0.50)


def _allocate(raw: xr.DataArray, liquid: xr.DataArray):
    raw = xr.where(np.isfinite(raw) & (raw > 0), raw, 0.0) * liquid
    gross = raw.sum("asset")
    normalized = xr.where(gross > EPS, raw / gross, 0.0)
    capped = xr.where(normalized > NAME_CAP, NAME_CAP, normalized) * liquid
    return (
        capped.transpose("time", "asset")
        .fillna(0.0)
        .reset_coords("field", drop=True)
    )


def _signal_state(data: xr.DataArray):
    close, liquid, ret = _base(data)
    vol = _std(ret, 21, 10)
    sharpe7 = np.sqrt(365.0) * _sma(ret, 7, 5) / (vol + EPS)
    sma18 = _sma(close, 18, 10)
    sma50 = _sma(close, 50, 25)
    trend = sma18 / (sma50 + EPS) - 1.0
    mom14 = close / close.shift(time=14) - 1.0
    peak42 = _max(close, 42, 20)
    dd42 = close / (peak42 + EPS) - 1.0
    mean_sharpe = _mean(sharpe7, liquid)
    mean_vol = _mean(vol, liquid)

    support = (
        xr.where(trend > 0, 1.0, 0.0)
        + xr.where(sharpe7 > mean_sharpe, 1.0, 0.0)
        + xr.where(mom14 > 0, 1.0, 0.0)
        + xr.where(vol < 1.25 * mean_vol, 1.0, 0.0)
        + xr.where(dd42 > -0.25, 1.0, 0.0)
    ) * liquid

    quality = (
        xr.where(sharpe7 > mean_sharpe, sharpe7 - mean_sharpe, 0.0)
        + 2.0 * xr.where(trend > 0, trend, 0.0)
        + xr.where(mom14 > 0, mom14, 0.0)
    ) * (support / 5.0)

    raw = xr.where(
        support >= ENTRY_SUPPORT,
        quality / (vol + 0.015),
        0.0,
    ) * liquid
    raw = _sma(raw, 5, 1) * liquid
    target = _allocate(raw, liquid)
    atr_pct = _true_range_pct(data, close)
    return target, support, liquid, atr_pct


def _recursive_execute(
    target: xr.DataArray,
    support: xr.DataArray,
    liquid: xr.DataArray,
    atr_pct: xr.DataArray,
    *,
    use_hysteresis: bool = False,
    atr_aware: bool = True,
):
    """Bounded weekly recursive execution state.

    The central candidate uses ATR-aware deadbanding without hysteresis. The
    optional hysteresis path exists only as a preregistered diagnostic control.
    State is re-anchored every Monday, so recursion is bounded to a week, and
    immediate liquidity exits are never suppressed.
    """
    target = target.transpose("time", "asset")
    support = support.transpose("time", "asset")
    liquid = liquid.transpose("time", "asset")
    atr_pct = atr_pct.transpose("time", "asset")

    tvals = pd.DatetimeIndex(target.time.values)
    desired = np.asarray(target.values, dtype=float)
    supp = np.asarray(support.values, dtype=float)
    liq = np.asarray(liquid.values, dtype=float) > 0.0
    atr = np.asarray(atr_pct.values, dtype=float)
    out = np.zeros_like(desired, dtype=float)

    current = np.zeros(desired.shape[1], dtype=float)
    for i in range(desired.shape[0]):
        d = np.nan_to_num(desired[i], nan=0.0, posinf=0.0, neginf=0.0)
        if i == 0 or tvals[i].dayofweek == WEEKLY_REANCHOR_DAY:
            current = d.copy()
        else:
            force_exit = ~liq[i]
            if use_hysteresis:
                force_exit |= (current > 0.0) & (supp[i] < RETENTION_SUPPORT)
                effective_target = d.copy()
                retained = (
                    (current > 0.0)
                    & (d <= 0.0)
                    & (supp[i] >= RETENTION_SUPPORT)
                    & liq[i]
                )
                effective_target[retained] = current[retained]
            else:
                force_exit |= (current > 0.0) & (d <= 0.0)
                effective_target = d

            current[force_exit] = 0.0
            delta = effective_target - current
            if atr_aware:
                band = ATR_DEADBAND_MULT * np.clip(atr[i], 0.0, 0.50)
            else:
                band = np.full_like(delta, 0.025)
            trade = liq[i] & (~force_exit) & (np.abs(delta) >= band)
            current[trade] = effective_target[trade]

        current = np.nan_to_num(current, nan=0.0, posinf=0.0, neginf=0.0)
        current = np.clip(current, 0.0, NAME_CAP)
        current[~liq[i]] = 0.0
        gross = float(current.sum())
        if gross > 1.0 + 1e-12:
            current *= 1.0 / gross
        out[i] = current

    return xr.DataArray(
        out,
        dims=("time", "asset"),
        coords={"time": target.time.values, "asset": target.asset.values},
        name="q25_recursive_lattice_execution",
    )


def strategy(data: xr.DataArray):
    target, support, liquid, atr_pct = _signal_state(data)
    return _recursive_execute(
        target, support, liquid, atr_pct, use_hysteresis=False, atr_aware=True
    )


def control_weights(data: xr.DataArray, mode: str):
    """Predeclared controls for research only; strategy() remains the contest artifact."""
    target, support, liquid, atr_pct = _signal_state(data)
    if mode == "base_lattice":
        return target
    if mode == "fixed_deadband":
        return _recursive_execute(
            target, support, liquid, atr_pct, use_hysteresis=False, atr_aware=False
        )
    if mode == "hysteresis_atr":
        return _recursive_execute(
            target, support, liquid, atr_pct, use_hysteresis=True, atr_aware=True
        )
    raise ValueError(mode)


def load_data(period: int):
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
        start_date=RESEARCH_START,
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )


if __name__ == "__main__":
    run_multipass()
