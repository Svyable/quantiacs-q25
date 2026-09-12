"""frontier_20260910b_topology_rank_stability — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260910b_topology_rank_stability
Preregistration SHA256: a14cfe3d1aaf565bc16965a5e632b4dce9f827b2c4308f6b042380982e0cf354
Mechanism: stable residual-correlation topology rank while raw-return ranks churn.
Nearest incumbent: V10 residual momentum.
Novelty axes: information_primitive, transform.

This file implements the already-preregistered object without changing its declared
window grid, allocation rule, controls, universe, or evaluation objective. It makes
no performance or submission claim.

Completed Quantiacs daily OHLCV + historical ``is_liquid`` only. The evaluator
applies the execution lag. All signal state is reconstructable from <=365 daily
observations and asset selection is fully systematic.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr


COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "topology_rank_stability"
PARAMS = {"window": 63, "top_k": 5}
RANK_LAG = 21
RAW_RANK_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _centrality(frame, min_periods):
    """Mean absolute residual-correlation centrality using completed rows only."""
    corr = frame.corr(min_periods=min_periods)
    values = corr.to_numpy(dtype=float).copy()
    if values.size == 0:
        return pd.Series(dtype=float)
    np.fill_diagonal(values, np.nan)
    central = np.nanmean(np.abs(values), axis=1)
    return pd.Series(central, index=corr.index).replace([np.inf, -np.inf], np.nan)


def _rank01(series):
    """Cross-sectional percentile rank in [0, 1], deterministic on tied values."""
    clean = series.replace([np.inf, -np.inf], np.nan)
    return clean.rank(method="average", pct=True)


def _label_permutation(series):
    """Deterministic asset-label permutation preserving the rank distribution.

    The preregistered falsifier shuffles topology-rank histories across assets while
    preserving the cross-sectional distribution. A fixed one-step rotation over
    sorted labels is deterministic and therefore legal for repeated contest runs.
    """
    ordered = sorted(series.index)
    values = series.reindex(ordered).to_numpy(dtype=float)
    if len(values) <= 1:
        return series.copy()
    return pd.Series(np.roll(values, 1), index=ordered).reindex(series.index)


def signals(data, window, mode="base"):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))

    # Remove the contemporaneous equal-weight liquid-market return. Topology is
    # therefore measured on residual co-movement rather than the common crypto beta.
    market = returns.where(liquid).mean(axis=1)
    residual = returns.sub(market, axis=0)

    ordered = sorted(close.columns)
    residual_s = residual.reindex(columns=ordered)
    returns_s = returns.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=close.index, columns=ordered)
    times = pd.DatetimeIndex(close.index)

    minp = max(16, window // 2)
    first = window + RANK_LAG + RAW_RANK_DAYS + 2

    for i in range(first, len(times)):
        if times[i].dayofweek != 0:
            continue

        cur_topology = residual_s.iloc[i - window + 1 : i + 1]
        prev_end = i - RANK_LAG
        prev_topology = residual_s.iloc[prev_end - window + 1 : prev_end + 1]

        current_cent = _centrality(cur_topology, minp)
        previous_cent = _centrality(prev_topology, minp)
        if current_cent.empty or previous_cent.empty:
            continue

        current_topology_rank = _rank01(current_cent)
        previous_topology_rank = _rank01(previous_cent)

        current_raw = returns_s.iloc[i - RAW_RANK_DAYS + 1 : i + 1].sum(
            min_count=max(5, RAW_RANK_DAYS // 2)
        )
        previous_raw = returns_s.iloc[
            prev_end - RAW_RANK_DAYS + 1 : prev_end + 1
        ].sum(min_count=max(5, RAW_RANK_DAYS // 2))
        current_raw_rank = _rank01(current_raw)
        previous_raw_rank = _rank01(previous_raw)
        raw_rank_churn = (current_raw_rank - previous_raw_rank).abs().clip(0.0, 1.0)

        if mode == "ablation":
            # Declared control: current topology rank only.
            score = current_topology_rank
        elif mode in {"base", "falsifier"}:
            history_rank = previous_topology_rank
            if mode == "falsifier":
                history_rank = _label_permutation(history_rank)

            topology_stability = (
                1.0 - (current_topology_rank - history_rank).abs()
            ).clip(0.0, 1.0)

            # Durable structural leadership is most interesting when superficial
            # raw-return ordering is changing. This is a product of three [0,1]
            # terms and introduces no fitted coefficient or post-hoc threshold.
            score = current_topology_rank * topology_stability * raw_rank_churn
        else:
            raise ValueError("unknown control mode")

        eligible = liquid.iloc[i].reindex(ordered).fillna(False)
        score = score.reindex(ordered).where(eligible, 0.0).fillna(0.0)
        out.iloc[i] = score.to_numpy(dtype=float)

    return out.reindex(columns=close.columns), liquid


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"}:
        raise ValueError("expected exactly window, top_k")
    if any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("parameters must be positive integers")
    if p["top_k"] > 10:
        raise ValueError("top_k cannot exceed the liquid top-10 universe")
    if p["window"] + RANK_LAG + RAW_RANK_DAYS + 14 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
    if mode not in {"base", "ablation", "falsifier"}:
        raise ValueError("unknown control mode")

    times = pd.DatetimeIndex(data.time.values)
    if not times.is_unique or not times.is_monotonic_increasing:
        raise ValueError("times must be unique and increasing")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("assets must be unique")

    score, liquid = signals(data, p["window"], mode)
    return _allocate(score, liquid, data.time, p["top_k"])


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    selected = selected.reindex(columns=score.columns)

    # Preregistered fixed slots. Unused slots remain cash rather than renormalizing
    # the active names up to 100% gross exposure.
    raw = selected.astype(float) * min(NAME_CAP, 1.0 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=raw.index)
    weights = raw.where(monday, axis=0).ffill(limit=6).fillna(0.0)

    # Immediate liquidity-loss exits even between scheduled rebalances.
    weights = weights.where(liquid, 0.0)
    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": times, "asset": score.columns},
        name=COMPETITION_TYPE,
    )


def load_data(period):
    import qnt.data as qndata

    return qndata.cryptodaily_load_data(tail=period)


if __name__ == "__main__":
    import qnt.backtester as qnbt

    qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date="2016-01-01",
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )
