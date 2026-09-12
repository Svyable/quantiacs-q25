"""Frontier-K subspace rotation opportunity — IMPLEMENTED, UNMEASURED.

Experiment: frontier_20260912k_subspace_rotation_opportunity
Preregistration SHA256: 438b2260c713f8e3c01ce6ee02f6fe25064336c197ec5ff37ce5e12e59fcd2aa
Prior reserve SHA256: e49fdc7d3a2e683bc3684a5f715305046d9839cf1b1e96b35ff564b281130c9d

Mechanism: compare the top-two eigenspaces of eligible residual-correlation
matrices 21 days apart. Score positive-trend assets by their contribution to the
change in the rank-two projection matrix. Projectors remove eigenvector sign and
within-subspace basis ambiguity. The ablation removes subspace rotation and uses
only a leading-eigenvalue concentration transition; the falsifier rotates asset
contributions among currently eligible identities.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
FAMILY = "subspace_rotation_opportunity"
PARAMS = {"window": 63, "top_k": 5}
GRAPH_LAG = 21
TREND_DAYS = 21
SUBSPACE_DIM = 2


def _field(data, name):
    return data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)


def _corr_matrix(frame, labels, min_periods):
    if len(labels) < 3:
        return None
    corr = frame.loc[:, labels].corr(min_periods=min_periods).reindex(index=labels, columns=labels)
    a = corr.to_numpy(dtype=float)
    a = np.where(np.isfinite(a), a, 0.0)
    a = 0.5 * (a + a.T)
    np.fill_diagonal(a, 1.0)
    return a


def _top_projector(corr):
    vals, vecs = np.linalg.eigh(corr)
    order = np.argsort(vals)[::-1]
    k = min(SUBSPACE_DIM, len(vals))
    q = vecs[:, order[:k]]
    projector = q @ q.T
    total = float(np.clip(np.trace(corr), 1e-12, np.inf))
    concentration = float(np.clip(vals[order[0]], 0.0, np.inf) / total)
    return projector, concentration


def _rotate_eligible(values):
    ordered = values.sort_index()
    finite = np.isfinite(ordered.to_numpy(dtype=float))
    loc = np.flatnonzero(finite)
    out = ordered.to_numpy(dtype=float).copy()
    if len(loc) > 1:
        out[loc] = np.roll(out[loc], 1)
    return pd.Series(out, index=ordered.index).reindex(values.index)


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
    minp = max(16, window // 2)
    first = window + GRAPH_LAG + TREND_DAYS + 2

    for i in range(first, len(times)):
        if times[i].dayofweek != 0:
            continue
        cur = residual_s.iloc[i - window + 1:i + 1]
        prev_end = i - GRAPH_LAG
        prev = residual_s.iloc[prev_end - window + 1:prev_end + 1]
        eligible = liquid_s.iloc[i].astype(bool)
        enough_cur = cur.notna().sum() >= minp
        enough_prev = prev.notna().sum() >= minp
        labels = [x for x in ordered if bool(eligible.get(x, False) and enough_cur.get(x, False) and enough_prev.get(x, False))]
        if len(labels) < 3:
            continue
        ccur = _corr_matrix(cur, labels, minp)
        cprev = _corr_matrix(prev, labels, minp)
        if ccur is None or cprev is None:
            continue
        pcur, conc_cur = _top_projector(ccur)
        pprev, conc_prev = _top_projector(cprev)
        # Row-wise Frobenius contribution to the change in the rank-two
        # projection matrix: sign/basis invariant and asset specific.
        displacement = np.sqrt(np.square(pcur - pprev).sum(axis=1))
        node = pd.Series(displacement, index=labels)
        concentration_change = max(conc_cur - conc_prev, 0.0)

        trend = residual_s.iloc[i - TREND_DAYS + 1:i + 1].sum(
            min_count=max(5, TREND_DAYS // 2)
        ).reindex(labels)
        if mode == "base":
            score = node
        elif mode == "ablation":
            # Remove the eigenspace identity change. This becomes positive
            # residual trend conditional only on leading-eigenvalue concentration.
            score = pd.Series(concentration_change, index=labels)
        elif mode == "falsifier":
            score = _rotate_eligible(node)
        else:
            raise ValueError("unknown control mode")

        raw = score.clip(lower=0.0).where(trend > 0, 0.0)
        if mode == "ablation" and concentration_change <= 0:
            raw[:] = 0.0
        out.loc[times[i], labels] = raw.fillna(0.0).to_numpy()

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
    if p["window"] + GRAPH_LAG + TREND_DAYS + 14 >= LOOKBACK_DAYS:
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
