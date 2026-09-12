"""Frontier-K cohort residual divergence — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260912k_cohort_residual_divergence
Preregistration SHA256: 9b95e58d47c288ee9beaac384553f72033ea351f79971ca31a8bee27a166c144
Prior reserve SHA256: ab8868ca75e1d6225dd68322589fe8f82260b1f81cbd580f3e584dc60e134bd6

Mechanism: form a causal high-residual-trend cohort from the historical liquid
universe. Among those leaders, deploy capital only to the more-divergent half,
where divergence means lower correlation to the equal-weight path of the *other*
cohort leaders. The ablation is plain residual trend inside the same cohort; the
destructive control deploys to the more-conforming half instead. The median split
is a rank/state transform rather than a fitted numeric threshold, and ensures the
mechanism changes the fixed-slot portfolio rather than only rescaling scores.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "cohort_residual_divergence"
PARAMS = {"window": 63, "top_k": 5}
PATH_DAYS = 21


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _peer_corr(path, labels):
    """Correlation to equal-weight cohort path excluding self."""
    out = pd.Series(np.nan, index=labels, dtype=float)
    if len(labels) < 3:
        return out
    block = path.loc[:, labels]
    for label in labels:
        peers = [x for x in labels if x != label]
        peer_path = block[peers].mean(axis=1)
        pair = pd.concat([block[label], peer_path], axis=1).dropna()
        if len(pair) >= max(8, PATH_DAYS // 2):
            a = pair.iloc[:, 0].to_numpy(dtype=float)
            b = pair.iloc[:, 1].to_numpy(dtype=float)
            if np.nanstd(a) > 1e-12 and np.nanstd(b) > 1e-12:
                out[label] = float(np.corrcoef(a, b)[0, 1])
    return out


def _split_by_peer_correlation(trend, corr, mode):
    """Make the mechanism change membership under fixed-slot allocation.

    Base keeps the lower-correlation (more divergent) half; falsifier keeps the
    higher-correlation (more conforming) half. The ablation removes the split.
    Ties at the cross-sectional median are broken deterministically by asset label
    through stable ranking rather than by adding a fitted threshold.
    """
    valid = pd.concat([trend.rename("trend"), corr.rename("corr")], axis=1).dropna()
    if valid.empty:
        return pd.Series(dtype=float)
    if mode == "ablation":
        return valid["trend"].clip(lower=0.0)

    ascending = mode == "base"
    ordered = valid.sort_index()
    ranks = ordered["corr"].rank(method="first", ascending=ascending)
    keep_n = max(1, int(np.ceil(len(ordered) / 2)))
    keep = ranks <= keep_n
    return ordered["trend"].clip(lower=0.0).where(keep, 0.0)


def signals(data, window, mode="base"):
    close = _field(data, "close").where(lambda x: np.isfinite(x) & (x > 0))
    liquid = _field(data, "is_liquid").eq(1) & close.notna()
    returns = np.log(close / close.shift(1))
    market = returns.where(liquid).sort_index(axis=1).mean(axis=1)
    residual = returns.sub(market, axis=0).where(liquid)

    ordered = sorted(close.columns)
    residual_s = residual.reindex(columns=ordered)
    liquid_s = liquid.reindex(columns=ordered)
    out = pd.DataFrame(0.0, index=close.index, columns=ordered)
    times = pd.DatetimeIndex(close.index)
    first = window + PATH_DAYS + 2

    for i in range(first, len(times)):
        if times[i].dayofweek != 0:
            continue
        eligible = liquid_s.iloc[i].astype(bool)
        trend = residual_s.iloc[i - window + 1:i + 1].sum(min_count=max(16, window // 2))
        positive = trend.where(eligible & (trend > 0)).dropna()
        if len(positive) < 3:
            continue
        # High-trend cohort is causal and identity-free: positive leaders at or
        # above the current eligible median positive residual trend.
        threshold = float(positive.median())
        labels = sorted(positive[positive >= threshold].index.tolist())
        if len(labels) < 3:
            labels = sorted(positive.nlargest(min(3, len(positive))).index.tolist())
        if len(labels) < 3:
            continue

        path = residual_s.iloc[i - PATH_DAYS + 1:i + 1]
        corr = _peer_corr(path, labels).clip(-1.0, 1.0)
        t = trend.reindex(labels).clip(lower=0.0)
        if mode not in {"base", "ablation", "falsifier"}:
            raise ValueError("unknown control mode")
        score = _split_by_peer_correlation(t, corr, mode)
        out.loc[times[i], score.index] = score.replace([np.inf, -np.inf], np.nan).fillna(0.0).to_numpy()

    return out.reindex(columns=close.columns), liquid


def _allocate(score, liquid, times, top_k):
    ranked = score.where(liquid & np.isfinite(score) & (score > 0)).sort_index(axis=1)
    selected = ranked.rank(axis=1, ascending=False, method="first") <= top_k
    target = selected.reindex(columns=score.columns).astype(float) * min(NAME_CAP, 1.0 / top_k)
    monday = pd.Series(pd.DatetimeIndex(times).dayofweek == 0, index=target.index)
    events = target.where(monday, axis=0).mask(~liquid, 0.0)
    weights = events.ffill(limit=6).fillna(0.0).where(liquid, 0.0)
    return xr.DataArray(
        weights.to_numpy(dtype=float), dims=("time", "asset"),
        coords={"time": times, "asset": score.columns}, name=COMPETITION_TYPE,
    )


def strategy(data, params=None, mode="base"):
    p = dict(PARAMS if params is None else params)
    if set(p) != {"window", "top_k"} or any(type(v) is not int or v < 1 for v in p.values()):
        raise ValueError("expected positive integer window and top_k")
    if p["window"] not in {42, 63, 84} or p["top_k"] != 5:
        raise ValueError("outside preregistered Frontier-K grid")
    if p["window"] + PATH_DAYS + 30 >= LOOKBACK_DAYS:
        raise ValueError("parameters exceed finite replay horizon")
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
    qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date="2016-01-01",
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )
