"""Ebenezar-profile Q25 translation: sharpe7_vol2 — IMPLEMENTED, UNMEASURED.

Experiment: ebenezar_20260912_sharpe7_vol2
Preregistration SHA256: 53641b0fe2964ac3ef4de7ed0227ae22f37f3041cc40fa6abef1a1437bc625d7

This is explicitly a user-directed family-refinement screen, not a novelty claim.
It uses only completed Quantiacs daily OHLCV plus historical is_liquid, is long
only, automatic, capped at 25% per name, and permits cash.
"""

from __future__ import annotations

import os
import numpy as np
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
EPS = 1e-12


def _close_liquid(data):
    close = data.sel(field="close").transpose("time", "asset").astype(float)
    liq0 = data.sel(field="is_liquid").transpose("time", "asset")
    liquid = xr.where((liq0 == 1) & np.isfinite(close) & (close > 0), 1.0, 0.0)
    return close, liquid


def _returns(close):
    r = close / close.shift(time=1) - 1.0
    return xr.where(np.isfinite(r), r, 0.0)


def _sma(x, n, min_periods=None):
    return x.rolling(time=n, min_periods=n if min_periods is None else min_periods).mean()


def _std(x, n, min_periods=None):
    return x.rolling(time=n, min_periods=max(2, n // 2) if min_periods is None else min_periods).std()


def _liquid_cs_mean(x, liquid):
    n = liquid.sum("asset")
    return xr.where(n > 0, (xr.where(np.isfinite(x), x, 0.0) * liquid).sum("asset") / n, 0.0)


def _liquid_cs_std(x, liquid):
    mean = _liquid_cs_mean(x, liquid)
    n = liquid.sum("asset")
    var = xr.where(n > 0, (((xr.where(np.isfinite(x), x, 0.0) - mean) ** 2) * liquid).sum("asset") / n, 0.0)
    return np.sqrt(xr.where(var > 0, var, 0.0))


def _allocate(raw, liquid):
    """Normalize positive scores to <=1 gross, cap names at 25%, retain cash."""
    raw = xr.where(np.isfinite(raw) & (raw > 0), raw, 0.0) * liquid
    gross = raw.sum("asset")
    normalized = xr.where(gross > EPS, raw / gross, 0.0)
    capped = xr.where(normalized > NAME_CAP, NAME_CAP, normalized) * liquid
    return capped.transpose("time", "asset").fillna(0.0).reset_coords("field", drop=True)


def _params(params, canonical_window):
    p = {"window": canonical_window} if params is None else dict(params)
    if set(p) != {"window"} or p["window"] != canonical_window:
        raise ValueError(f"expected frozen window={canonical_window}")
    return p


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


def _run_backtest(strategy_fn):
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt
    qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date="2016-01-01",
        strategy=strategy_fn,
        analyze=True,
        check_correlation=True,
    )


def strategy(data, params=None, mode="base"):
    _params(params, 7)
    if mode != "base":
        raise ValueError("this translation screen freezes base mode only")
    close, liquid = _close_liquid(data)
    r = _returns(close)
    mu7 = _sma(r, 7, 5)
    vol14 = _std(r, 14, 7)
    s7 = np.sqrt(365.0) * mu7 / (vol14 + EPS)
    sma12 = _sma(close, 12, 8)
    sma48 = _sma(close, 48, 24)
    mom14 = close / close.shift(time=14) - 1.0
    peak30 = close.rolling(time=30, min_periods=15).max()
    dd30 = close / (peak30 + EPS) - 1.0
    mean = _liquid_cs_mean(s7, liquid)
    sd = _liquid_cs_std(s7, liquid)
    hurdle = mean + 0.20 * sd
    quality = xr.where(s7 > hurdle, s7 - hurdle, 0.0)
    gate = (sma12 > sma48) & (mom14 > 0.0) & (dd30 > -0.22) & (vol14 > 0.0)
    raw = xr.where(gate, (quality.clip(min=0.0) ** 1.25) / (vol14 + 0.015), 0.0) * liquid
    raw = _sma(raw, 3, 1) * liquid
    return _allocate(raw, liquid)


if __name__ == "__main__":
    _run_backtest(strategy)
