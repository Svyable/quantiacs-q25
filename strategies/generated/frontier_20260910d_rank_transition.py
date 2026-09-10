"""frontier_20260910d_rank_transition — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260910d_rank_transition
Preregistration SHA256: 6beba6d363a24fb38823053454680fb59c4c26e69911241fa802e6c2766e48e4
Mechanism: Positive cross-sectional rank migration with low transition noise identifies durable leadership.
Nearest incumbent: Trend_hit126 / V10 residual momentum / Frontier-B topology migration
Novelty axes: information primitive, transform, timing/state.
Completed daily sponsor bars only. Toolbox applies the next-bar execution lag.
Weekly fixed-slot targets, persistent eligibility exits, <=365-day replay.
No performance, novelty-by-returns, or submission claim.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
PARAMS = {"window": 63, "top_k": 5}
SHORT_DAYS = 5
STATE_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    return close, liquid, returns


def _rotate_eligible(frame, eligible):
    """Preserve each day's eligible finite marginal, independent of column order.

    Never rotate through future-listed or ineligible names. A singleton cannot
    be permuted, so it is left intact; no diagnostic power is claimed there.
    """
    ordered = frame.sort_index(axis=1)
    mask = eligible.reindex(columns=ordered.columns) & np.isfinite(ordered)
    out = ordered.copy()
    for i in range(len(out)):
        locations = np.flatnonzero(mask.iloc[i].to_numpy())
        if len(locations) > 1:
            out.iloc[i, locations] = np.roll(ordered.iloc[i, locations].to_numpy(), 1)
    return out.reindex(columns=frame.columns)


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = (ranked.rank(axis=1, ascending=False, method="first") <= top_k)
    target = selected.reindex(columns=score.columns).astype(float) * min(NAME_CAP, 1 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=score.index)
    # An exit is an explicit zero event, so eligibility recovery cannot revive
    # a stale target. Six-bar carry limit bounds state even on incomplete input.
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(), dims=("time", "asset"),
                        coords={"time": times, "asset": score.columns},
                        name=COMPETITION_TYPE)


def signals(data, window, mode="base"):
    _, liquid, returns = _context(data)
    recent = returns.rolling(SHORT_DAYS).sum().where(liquid)
    ranks = recent.rank(axis=1, pct=True, method="average")
    ranks = ranks.where(recent.notna().sum(axis=1) >= 2, axis=0)
    migration = ranks - ranks.shift(STATE_DAYS)
    noise = ranks.diff().rolling(window).std().shift(1)
    reliability = (1.0 - 2.0 * noise).clip(lower=0)
    if mode == "ablation":
        reliability = pd.DataFrame(1.0, index=ranks.index, columns=ranks.columns).where(noise.notna())
    elif mode == "falsifier":
        reliability = _rotate_eligible(reliability, liquid & migration.notna())
    score = migration.clip(lower=0) * reliability
    score = score.where(returns.rolling(STATE_DAYS).sum() > 0, 0.0)
    return score, liquid


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] + SHORT_DAYS + STATE_DAYS + 8 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed bounded replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown mode")
    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing or len(times) == 0:
        raise ValueError("nonempty increasing unique dates required")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("unique asset coordinates required")
    score, liquid = signals(data, p["window"], mode)
    return _allocate(score, liquid, data.time, p["top_k"])


def load_data(period):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


if __name__ == "__main__":
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt
    qnbt.backtest(competition_type=COMPETITION_TYPE, load_data=load_data,
                 lookback_period=LOOKBACK_DAYS, start_date="2016-01-01",
                 strategy=strategy, analyze=True, check_correlation=True)
