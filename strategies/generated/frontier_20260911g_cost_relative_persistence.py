"""frontier_20260911g_cost_relative_persistence — PENDING RESEARCH STRATEGY.
Experiment: frontier_20260911g_cost_relative_persistence
Preregistration SHA256: 1ceaef0d2e5d62364a1d533ba8bfaed9d9b201244e26cdac117a593d44e010a3
Classification: discovery_hypothesis
Mechanism: Persistent residual leadership scaled by own relative ATR is more deployable than raw residual leadership.
Nearest incumbent: V10 residual momentum / unimplemented Frontier-D/E execution hurdle
Novelty axes: information_primitive, transform, timing_or_state_condition
No performance or submission claim. Fully realized data only; toolbox owns the
candidate execution lag. Weekly entries, persistent eligibility exits, cash,
explicit risk caps, and <=365-day replay. Evidence is recorded separately.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
PARAMS = {"top_k": 5, "window": 63}
ATR_DAYS = 14
PERSISTENCE_LAG = 7


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _context(data):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    high = _field(data, "high")
    low = _field(data, "low")
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    return close, high, low, liquid, returns


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
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    target = (selected.reindex(columns=score.columns).astype(float)
              * score.clip(0, 1).fillna(0) * min(NAME_CAP, 1 / top_k))
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=score.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(weights.to_numpy(), dims=("time", "asset"),
                        coords={"time": times, "asset": score.columns},
                        name=COMPETITION_TYPE)


def _market(returns, liquid):
    observed = returns.where(liquid).sort_index(axis=1)
    return observed.mean(axis=1)


def _relative_atr(high, low, close):
    previous = close.shift(1)
    true_range = np.maximum.reduce([
        (high - low).abs().to_numpy(),
        (high - previous).abs().to_numpy(),
        (low - previous).abs().to_numpy(),
    ])
    atr = pd.DataFrame(true_range, index=close.index, columns=close.columns).rolling(ATR_DAYS).mean()
    return atr.div(close).where(np.isfinite(close) & (close > 0))


def _density(expected, rel_atr):
    expected = expected.clip(lower=0)
    denom = expected.add(rel_atr.clip(lower=0), fill_value=np.nan)
    return expected.div(denom).where(expected > 0, 0.0)


def signals(data, window, mode="base"):
    close, high, low, liquid, returns = _context(data)
    residual = returns.sub(_market(returns, liquid), axis=0).where(liquid)
    expected = residual.rolling(window).sum() * residual.rolling(window).corr(residual.shift(PERSISTENCE_LAG)).clip(lower=0)
    rel_atr = _relative_atr(high, low, close)
    if mode == "ablation":
        score = expected.clip(0, 1).where(liquid, 0.0)
        return score.fillna(0.0), liquid
    if mode == "falsifier":
        rel_atr = _rotate_eligible(rel_atr, liquid & rel_atr.notna())
    score = _density(expected, rel_atr).where(liquid, 0.0)
    return score.clip(0, 1).fillna(0.0), liquid


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] + 100 >= LOOKBACK_DAYS:
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
