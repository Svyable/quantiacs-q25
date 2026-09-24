"""Frozen 2%-band VCB x breadth-dispersion ensemble.

Preregistered in research/preregistrations/vcb_breadth_turnover_ensemble_20260924.md.
No parameters in this module were selected from this mechanism's economic result.
"""
from __future__ import annotations
import importlib
import numpy as np
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
STRATEGY_ID = "q25_vcb_breadth_turnover_ensemble_v1"
BAND = 0.02
EPS = 1e-12


def apply_no_trade_band(target: xr.DataArray, band: float = BAND) -> xr.DataArray:
    """Causally implement target weights, retaining prior weight inside the band."""
    target = target.fillna(0).clip(min=0).transpose("time", "asset")
    values = np.asarray(target.values, dtype=float)
    out = np.zeros_like(values)
    prev = np.zeros(values.shape[1], dtype=float)
    for i in range(values.shape[0]):
        cur = values[i]
        nxt = np.where(np.abs(cur - prev) < band, prev, cur)
        nxt = np.maximum(nxt, 0.0)
        gross = float(nxt.sum())
        if gross > 1.0 + EPS:
            nxt = nxt / gross
        out[i] = nxt
        prev = nxt
    return xr.DataArray(out, coords=target.coords, dims=target.dims).reset_coords(drop=True)


def calculate_weights(data):
    ff = importlib.import_module("strategies.generated.q25_factor_factory")
    vcb = importlib.import_module("strategies.generated.q25_volatility_contraction_breakout")
    breadth = ff.FACTORS["breadth_dispersion_interaction"](data)
    target = 0.5 * breadth + 0.5 * vcb.calculate_weights(data)
    return apply_no_trade_band(target)


def strategy(data):
    return calculate_weights(data)


def load_data(period):
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=max(int(period), 730))
