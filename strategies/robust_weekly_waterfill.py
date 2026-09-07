# robust_weekly_waterfill — robustness-track baseline
# Quantiacs Q25 Crypto Top-10 Long
#
# Design patterns (robustness track):
# - Quantiacs cryptodaily data only
# - Weekly rebalance (reduce ATR-linked turnover cost)
# - Permit cash (gross < 1 OK)
# - Capped water-fill allocation (unused capacity stays cash)
# - Long-only * is_liquid
# - No hand-picked assets; SMA trend signal among liquid names
# - Inverse-vol or equal among selected; per-name cap
# - Execution delay left to evaluator
#
# NO METRICS ARE CLAIMED. This file is a design baseline only.
# Do not invent Sharpe / returns / drawdown. Unrun = PENDING.
#
# API_KEY is REQUIRED. Empty/blank does NOT work — the toolbox exits if API_KEY is ''.
#   export API_KEY=...   # from https://quantiacs.com/personalpage/homepage
#   or copy .env.example -> .env and fill API_KEY=

import os
import sys

if not os.environ.get("API_KEY"):
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_path = os.path.abspath(env_path)
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if not _line or _line.startswith("#") or "=" not in _line:
                    continue
                _k, _v = _line.split("=", 1)
                if _k.strip() == "API_KEY" and _v.strip() and "API_KEY" not in os.environ:
                    os.environ["API_KEY"] = _v.strip().strip('"').strip("'")
if not os.environ.get("API_KEY"):
    sys.exit(
        "API_KEY is missing or empty. Get a free profile key at "
        "https://quantiacs.com/personalpage/homepage and export API_KEY=..."
    )

import warnings

warnings.filterwarnings("ignore")

import xarray as xr
import numpy as np

import qnt.ta as qnta
import qnt.data as qndata
import qnt.output as qnout
import qnt.backtester as qnbt
import qnt.stats as qnstats

# --- robustness knobs (fixed design; not optimized here) ---
SMA_FAST = 20
SMA_SLOW = 60
VOL_LOOKBACK = 20
NAME_CAP = 0.10          # max weight per name
WEEKLY_STEP = 7          # rebalance every 7 calendar days in the panel
USE_INV_VOL = True       # False → equal weight among selected


def load_data(period):
    return qndata.cryptodaily_load_data(tail=period)


def _capped_waterfill(raw: xr.DataArray, cap: float) -> xr.DataArray:
    """Allocate proportional to positive raw scores with per-name cap; unused = cash.

    raw should be non-negative scores on the asset dimension (single time slice OK).
    """
    # Work in numpy for a simple water-fill
    assets = raw.asset.values if "asset" in raw.dims else None
    vals = np.asarray(raw.values, dtype=float).copy()
    vals = np.nan_to_num(vals, nan=0.0, posinf=0.0, neginf=0.0)
    vals = np.maximum(vals, 0.0)
    if vals.sum() <= 0:
        out = np.zeros_like(vals)
    else:
        # Proportional then cap; leftover stays cash (not redistributed beyond cap loop)
        w = vals / vals.sum()
        w = np.minimum(w, cap)
        # One redistribution pass of residual among uncapped names
        for _ in range(3):
            residual = 1.0 - w.sum()
            if residual <= 1e-12:
                break
            room = np.maximum(cap - w, 0.0)
            if room.sum() <= 0:
                break
            add = residual * (room / room.sum())
            w = np.minimum(w + add, cap)
        out = w
    if assets is not None:
        return xr.DataArray(out, dims=("asset",), coords={"asset": assets})
    return xr.DataArray(out)


def strategy(data):
    """Weekly SMA trend + capped water-fill among liquid names; cash permitted.

    No performance claims — structural robustness-track baseline only.
    """
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")

    sma_fast = qnta.sma(close, SMA_FAST)
    sma_slow = qnta.sma(close, SMA_SLOW)
    trend = xr.where(sma_fast > sma_slow, 1.0, 0.0) * is_liquid

    if USE_INV_VOL:
        # Realized vol proxy (same pattern as vol_scaled_trend.py)
        ret = qnta.change(close)
        vol = ret.rolling(time=VOL_LOOKBACK).std()
        inv = 1.0 / (vol + 1e-8)
        score = trend * inv
    else:
        score = trend

    # Weekly mask: keep prior allocation between rebalance days (simple hold)
    # For multipass last-day evaluation we compute allocation on the last bar,
    # but still zero scores on non-rebalance days in the full panel path.
    if "time" in score.dims:
        n_t = score.sizes["time"]
        rebalance = np.zeros(n_t, dtype=bool)
        rebalance[::WEEKLY_STEP] = True
        rebalance[-1] = True  # always allocate on evaluation day for multipass
        rb = xr.DataArray(
            rebalance, dims=("time",), coords={"time": score.time}
        )
        # Forward-fill scores on non-rebalance days from last rebalance
        score = score.where(rb)
        score = score.ffill(dim="time")

        # Per-day capped water-fill
        weights_list = []
        for t in range(n_t):
            sl = score.isel(time=t)
            sl = sl.fillna(0.0)
            # where trend/liquid off → zero
            sl = sl * (trend.isel(time=t).fillna(0.0) > 0)
            w = _capped_waterfill(sl, NAME_CAP)
            weights_list.append(w)
        weights = xr.concat(weights_list, dim="time")
        weights = weights.assign_coords(time=score.time)
        weights = weights.fillna(0.0)
        # Multipass: last-day slice
        weights = weights.isel(time=-1)
    else:
        score = score.fillna(0.0)
        weights = _capped_waterfill(score, NAME_CAP)

    return weights


if __name__ == "__main__":
    # Multipass with load_data. NO METRICS CLAIMED in this repository file.
    weights = qnbt.backtest(
        competition_type="crypto_daily_long",
        load_data=load_data,
        lookback_period=365,
        start_date="2016-01-01",
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )
