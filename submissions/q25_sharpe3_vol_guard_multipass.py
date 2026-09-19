"""Ebenezar-profile Q25 translation: sharpe3_vol_guard — IMPLEMENTED, UNMEASURED.

Experiment: ebenezar_20260912_sharpe3_vol_guard
Preregistration SHA256: 0c12aa833752bdf58026752e72c87076c5b13131f0f9337dc34d058175461bc1

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
    m = n if min_periods is None else min_periods
    if x.sizes["time"] < m:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=m).mean()


def _std(x, n, min_periods=None):
    m = max(2, n // 2) if min_periods is None else min_periods
    if x.sizes["time"] < m:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=m).std()


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
    _params(params, 3)
    if mode != "base":
        raise ValueError("this translation screen freezes base mode only")
    close, liquid = _close_liquid(data)
    r = _returns(close)
    mu3 = _sma(r, 3, 3)
    vol21 = _std(r, 21, 10)
    s3 = np.sqrt(365.0) * mu3 / (vol21 + EPS)
    mom7 = close / close.shift(time=7) - 1.0
    trend34 = close / (_sma(close, 34, 20) + EPS) - 1.0
    mean = _liquid_cs_mean(s3, liquid)
    sd = _liquid_cs_std(s3, liquid)
    hurdle = mean + 0.10 * sd
    conviction = xr.where(s3 > hurdle, s3 - hurdle, 0.0)
    gate = (mom7 > 0.0) & (trend34 > 0.0) & (vol21 > 0.0)
    raw = xr.where(gate, conviction / (vol21 + 0.01), 0.0) * liquid
    raw = _sma(raw, 2, 1) * liquid
    return _allocate(raw, liquid)


if __name__ == "__main__":
    _run_backtest(strategy)
