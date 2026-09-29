"""Q25 submission adapter for the static 50/50 VCB x breadth-dispersion ensemble.

Members mirror, formula for formula, the frozen research sources:

* strategies/generated/q25_volatility_contraction_breakout.py (VCB)
* strategies/generated/q25_factor_factory.py::breadth_dispersion_interaction

Evidence: research/evidence/breadth_prequential_20260924.md (39 completed
90-day origins, ADAPTIVE_REUSE). The 50/50 blend is the incumbent reference
that both execution overlays (2% band, 5% sparse trigger) must beat.

No economic parameter or formula is changed here; only contest execution/check
plumbing is added. The file is self-contained so it can be pasted into a
Quantiacs notebook without the research package.
"""
from __future__ import annotations
import os
import numpy as np
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
STRATEGY_ID = "q25_vcb_breadth_static_ensemble_v1"
IN_SAMPLE_START = "2016-01-01"
LOOKBACK_DAYS = 365
NAME_CAP = .25
EPS = 1e-12
VCB_WEIGHT = .5
BREADTH_WEIGHT = .5


def _inputs(data):
    c = data.sel(field="close").transpose("time", "asset").astype(float)
    l = xr.where((data.sel(field="is_liquid").transpose("time", "asset") == 1) & np.isfinite(c) & (c > 0), 1., 0.)
    r = c / c.shift(time=1) - 1
    return c, l, r


def vcb_weights(data):
    c, l, r = _inputs(data)
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


def breadth_dispersion_weights(data):
    c, l, r = _inputs(data)
    m = c / c.shift(time=35) - 1
    rel = m - m.mean("asset")
    breadth = (m > 0).mean("asset")
    disp = m.std("asset")
    bmed = breadth.rolling(time=63, min_periods=42).median()
    dmed = disp.rolling(time=63, min_periods=42).median()
    gate = ((breadth - bmed).clip(min=0) / (1 - bmed + EPS)) * ((disp - dmed).clip(min=0) / (disp + dmed + EPS))
    v = r.rolling(time=28, min_periods=18).std()
    raw = rel.clip(min=0) * gate / (v + .01)
    raw = raw.where(np.isfinite(raw), 0).clip(min=0) * l
    raw = raw.rolling(time=3, min_periods=1).mean() * l
    g = raw.sum("asset")
    w = xr.where(g > EPS, raw / g, 0.)
    return xr.where(w > NAME_CAP, NAME_CAP, w).fillna(0).clip(min=0).transpose("time", "asset").reset_coords(drop=True)


def calculate_weights(data):
    w = BREADTH_WEIGHT * breadth_dispersion_weights(data) + VCB_WEIGHT * vcb_weights(data)
    return w.transpose("time", "asset").reset_coords(drop=True)


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
