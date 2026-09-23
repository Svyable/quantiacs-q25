"""Q25 submission adapter for the frozen holdout-qualified VCB mechanism.

This file intentionally mirrors strategies/generated/q25_volatility_contraction_breakout.py.
No economic parameter or formula is changed; only contest execution/check plumbing is added.
"""
from __future__ import annotations
import os
import numpy as np
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
STRATEGY_ID = "q25_volatility_contraction_breakout_v1"
IN_SAMPLE_START = "2016-01-01"
LOOKBACK_DAYS = 180
NAME_CAP = .25
EPS = 1e-12


def calculate_weights(data):
    c = data.sel(field="close").transpose("time", "asset").astype(float)
    l = xr.where((data.sel(field="is_liquid").transpose("time", "asset") == 1) & np.isfinite(c) & (c > 0), 1., 0.)
    r = c / c.shift(time=1) - 1
    v14 = r.rolling(time=14, min_periods=10).std()
    v56 = r.rolling(time=56, min_periods=35).std()
    peak = c.shift(time=1).rolling(time=28, min_periods=20).max()
    breakout = (c / (peak + EPS) - 1).clip(min=0)
    contraction = (1 - v14 / (v56 + EPS)).clip(min=0, max=1)
    raw = breakout * contraction / (v14 + .01) * l
    raw = raw.rolling(time=3, min_periods=1).mean() * l
    g = raw.sum("asset")
    w = xr.where(g > EPS, raw / g, 0.)
    return xr.where(w > NAME_CAP, NAME_CAP, w).fillna(0).clip(min=0).transpose("time", "asset").reset_coords(drop=True)


def strategy(data):
    return calculate_weights(data).isel(time=-1, drop=True)


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=max(int(period), LOOKBACK_DAYS))


def run_single_pass(write_output=False):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    import qnt.output as qnout
    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    weights = calculate_weights(data)
    cleaned = qnout.clean(weights, data, COMPETITION_TYPE)
    if write_output:
        qnout.check(cleaned, data, COMPETITION_TYPE, check_correlation=True)
        qnout.write(cleaned)
    return cleaned


if __name__ == "__main__":
    run_single_pass(write_output=True)
