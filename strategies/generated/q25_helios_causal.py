"""Q25 HELIOS causal factor refinement — self-contained research candidate.

Experiment: helios_20260914. PENDING until the separate evidence packet is read.
Preregistrations (factor learning / diagonal risk / no ATR admission):
2750dba67cce799732131b39ae606e42ef6d5d8e3a8a373b45a85832805e8cdf
44cbf098c0fdb76e5acfeef76598e729dd6470cb121cc09683ca71f9808d7dd9
a8b8fe9311d6a478983773e94e0d12e6f45381e88b825ecaa460e110a29e1a6b

Inspired by the supplied VIPER-HELIOS v22; nearest incumbents are V10 and slow
factor balance. Changed axes: factor-skill transform and portfolio construction.
This is a family refinement, not independent alpha or a reproduction of v22.

Four orthogonalized factors -> matured nonoverlapping rank-IC learning ->
structured covariance risk budgets -> volatility/cost-aware weekly targets.
Only sponsor OHLCV + historical is_liquid. No symbols, external features,
negative shifts, random training, disk state, or dependence on qnt at import.

Target dated t uses completed bar t; Quantiacs applies execution lag ONCE.
Learning uses outcomes completed by t-1. Finite memory is <=343 daily rows
at the largest preregistered window, so a 365-day replay reconstructs targets.
Weekly updates hold TARGET WEIGHTS, not units; official stats charge drift
rebalancing too. ATR admission is a conviction/scale proxy, not expected P&L.
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
TARGET_VOL = 0.40
FACTOR_NAMES = ("momentum", "flow", "quality", "low_risk")
DEFAULT_PARAMS = dict(window=126, top_k=6, risk_model="structured", cost_gate=True)
EPS = 1e-12


def _frames(data):
    if set(data.dims) != {"field", "time", "asset"}:
        raise ValueError("expected field/time/asset data")
    required = {"close", "high", "low", "vol", "is_liquid"}
    if not required <= set(data.field.values):
        raise ValueError("missing sponsor OHLCV/liquidity fields")
    dates = pd.DatetimeIndex(data.time.values)
    if dates.has_duplicates or not dates.is_monotonic_increasing:
        raise ValueError("timestamps must be unique and increasing")
    if len(dates) > 1 and not (np.diff(dates.values) == np.timedelta64(1, "D")).all():
        raise ValueError("daily observations must be contiguous")
    assets = pd.Index(data.asset.values)
    if assets.has_duplicates:
        raise ValueError("duplicate asset labels")
    # Canonical order makes ties, cross-sectional reductions and linear algebra
    # invariant to the ordering supplied by a loader or a replay.
    return {
        f: data.sel(field=f, drop=True).transpose("time", "asset")
        .to_pandas().astype(float).sort_index(axis=1)
        for f in required
    }


def _rank(values, mask):
    """Ties average; a singleton/flat cross-section has zero conviction."""
    v = values.where(mask & np.isfinite(values))
    ranks = v.rank(axis=1, method="average")
    count = v.count(axis=1)
    centered = ranks.sub((count + 1) / 2, axis=0)
    return (2 * centered.div((count - 1).clip(lower=1), axis=0)).fillna(0.0)


def _orthogonalize(value, anchor, mask):
    n = mask.sum(axis=1).clip(lower=1)
    x = value.where(mask, 0).sub(value.where(mask, 0).sum(axis=1) / n, axis=0).where(mask, 0)
    a = anchor.where(mask, 0).sub(anchor.where(mask, 0).sum(axis=1) / n, axis=0).where(mask, 0)
    slope = (x * a).sum(axis=1) / ((a * a).sum(axis=1) + EPS)
    residual = x - a.mul(slope, axis=0)
    scale = residual.abs().max(axis=1).clip(lower=EPS)
    return residual.div(scale, axis=0).where(mask, 0).clip(-1, 1)


def _context(data):
    f = _frames(data)
    raw_close, high, low, volume = (f[k] for k in ("close", "high", "low", "vol"))
    close = raw_close.where(np.isfinite(raw_close) & (raw_close > 0))
    returns = np.log(close).diff()
    liquid = f["is_liquid"].eq(1)
    bars = (np.isfinite(high) & np.isfinite(low) & np.isfinite(volume)
            & (high >= close) & (low <= close) & (low > 0) & (volume > 0))
    complete = returns.notna().rolling(126, min_periods=126).sum().eq(126)
    eligible = liquid & close.notna() & bars & complete
    vol = returns.rolling(63, min_periods=63).std(ddof=0)
    eligible &= vol.gt(1e-6)
    momentum = sum(
        (np.log(close) - np.log(close).shift(h)) / (vol * np.sqrt(h) + EPS)
        for h in (21, 63, 126)
    ) / 3
    location = ((2 * close - high - low) / (high - low).where(high > low)).fillna(0)
    valid_volume = volume.where(bars)
    flow = (location * valid_volume).rolling(21, min_periods=21).sum() / (
        valid_volume.rolling(21, min_periods=21).sum() + EPS)
    downside = np.sqrt(returns.clip(upper=0).pow(2).rolling(63, min_periods=63).mean())
    quality = returns.rolling(63, min_periods=63).sum() / (
        returns.abs().rolling(63, min_periods=63).sum() + EPS) - downside / (vol + EPS)
    raw_factors = dict(momentum=momentum, flow=flow, quality=quality, low_risk=-vol)
    factor_mask = eligible.copy()
    for v in raw_factors.values():
        factor_mask &= np.isfinite(v)
    factors = {k: _rank(v, factor_mask) for k, v in raw_factors.items()}
    for k in FACTOR_NAMES[1:]:
        factors[k] = _orthogonalize(factors[k], factors["momentum"], factor_mask)
    previous = close.shift(1)
    tr = np.maximum.reduce([(high - low).to_numpy(), (high - previous).abs().to_numpy(),
                            (low - previous).abs().to_numpy()])
    # Finite simple ATR estimate for admission, not a replacement for qnt costs.
    atr = pd.DataFrame(tr, index=close.index, columns=close.columns).rolling(14, min_periods=14).mean() / close
    trend = close > close.rolling(126, min_periods=126).mean()
    # Realized basket return uses membership known at the start of the interval.
    market = returns.where(liquid.shift(1, fill_value=False)).mean(axis=1).fillna(0)
    breadth = trend.astype(float).where(eligible).mean(axis=1).fillna(0)
    regime = ((breadth - 0.20) / 0.60).clip(0, 1)
    # Reconstruct each drawdown path locally: no cumulative all-history state.
    m = market.to_numpy()
    brake = np.ones(len(m))
    for t in range(len(m)):
        path = np.r_[0.0, np.cumsum(m[max(0, t - 62):t + 1])]
        dd = 1 - np.exp(path[-1] - np.max(path))
        brake[t] = np.clip(1 - dd / 0.40, 0, 1)
    regime *= brake
    return dict(close=close, returns=returns, eligible=eligible, factor_mask=factor_mask,
                factors=factors, vol=vol, atr=atr, trend=trend, market=market, regime=regime)


def _completed_ic(factor, close, source_mask, horizon):
    """At u, compare factor[u-h] with observed return u-h -> u.

    Membership is the source-day mask, not the surviving u-day universe.
    Missing prices make a label unavailable; they are never filled with zero.
    Nonoverlapping observations reduce pseudo-replication of multi-day labels.
    """
    observed = close.notna().rolling(horizon + 1, min_periods=horizon + 1).sum().eq(horizon + 1)
    realized = np.log(close) - np.log(close).shift(horizon)
    valid = source_mask.shift(horizon, fill_value=False) & observed & np.isfinite(realized)
    x = _rank(factor.shift(horizon), valid)
    y = _rank(realized, valid)
    den = np.sqrt(x.pow(2).sum(axis=1) * y.pow(2).sum(axis=1))
    ic = (x * y).sum(axis=1) / den.where(den > EPS)
    day = close.index.to_numpy().astype("datetime64[D]").astype(np.int64)
    return ic.where((valid.sum(axis=1) >= 3) & (day % horizon == 0))


def _factor_weights(ctx, window, mode="base"):
    learned = pd.DataFrame(0.0, index=ctx["close"].index, columns=FACTOR_NAMES)
    for h in (5, 21):
        for name in FACTOR_NAMES:
            ic = _completed_ic(ctx["factors"][name], ctx["close"], ctx["factor_mask"], h)
            rolling = ic.rolling(window, min_periods=4)
            count = rolling.count()
            mean, sd = rolling.mean(), rolling.std(ddof=1)
            confidence = mean / (sd / np.sqrt(count.clip(lower=1)) + 0.10)
            evidence = (count / (count + 12)) * np.tanh(confidence)
            learned[name] += 0.5 * evidence.fillna(0)
    # An extra embargo day: changes to today's returns cannot change today's
    # learned coefficients. Current factors can of course react to today's bar.
    learned = learned.shift(1).fillna(0)
    probability = np.exp(2 * learned)
    probability = probability.div(probability.sum(axis=1), axis=0)
    weights = 0.65 / len(FACTOR_NAMES) + 0.35 * probability
    if mode == "ablation":
        weights[:] = 1 / len(FACTOR_NAMES)
    elif mode == "falsifier":
        weights.iloc[:, :] = np.roll(weights.to_numpy(), 1, axis=1)
    return weights


def _covariance(asset_returns, market_returns, diagonal=False):
    """PSD finite EW sample / single-factor target blend in daily units."""
    r = np.asarray(asset_returns, dtype=float)
    m = np.asarray(market_returns, dtype=float)
    if r.ndim != 2 or len(r) < 2 or len(m) != len(r) or not np.isfinite(r).all() or not np.isfinite(m).all():
        raise ValueError("risk model requires complete finite observations")
    w = 0.97 ** np.arange(len(r) - 1, -1, -1)
    w /= w.sum()
    centered = r - w @ r
    market = m - w @ m
    sample = (centered * w[:, None]).T @ centered
    market_var = float(w @ np.square(market))
    beta = (centered * w[:, None]).T @ market / max(market_var, EPS)
    residual = centered - market[:, None] * beta
    idio = w @ np.square(residual)
    target = np.outer(beta, beta) * market_var + np.diag(idio)
    covariance = 0.5 * sample + 0.5 * target + np.eye(r.shape[1]) * 1e-6
    return np.diag(np.diag(covariance)) if diagonal else covariance


def _risk_budget(covariance, budget):
    """Solve 0.5*x'Σ*x - sum(b*log(x)) by cyclic coordinate descent.

    Unlike a naive multiplicative ERC update this also converges for correlated
    assets. Normalized x has proportional risk contributions equal to b.
    """
    cov = np.asarray(covariance, dtype=float)
    b = np.asarray(budget, dtype=float)
    if cov.shape != (len(b), len(b)) or not len(b) or not np.isfinite(cov).all():
        raise ValueError("invalid risk model shape/values")
    if not np.allclose(cov, cov.T) or np.linalg.eigvalsh(cov).min() <= 0:
        raise ValueError("covariance must be positive definite")
    if not np.isfinite(b).all() or (b <= 0).any():
        raise ValueError("risk budgets must be positive")
    b = b / b.sum()
    x = np.sqrt(b / np.diag(cov))
    for _ in range(100):
        old = x.copy()
        for j in range(len(x)):
            cross = cov[j] @ x - cov[j, j] * x[j]
            x[j] = (np.sqrt(cross * cross + 4 * cov[j, j] * b[j]) - cross) / (2 * cov[j, j])
        if np.max(np.abs(x - old)) <= 1e-10 * max(1, np.max(x)):
            break
    else:
        raise ArithmeticError("risk-budget solver did not converge")
    return x / x.sum()


def _weekly_targets(desired, eligible, risk_ceiling):
    """Bounded weekly carry. An exit cannot resurrect before the next Monday."""
    out = np.zeros_like(desired.to_numpy())
    held = np.zeros(desired.shape[1])
    for t, date in enumerate(desired.index):
        if date.dayofweek == 0:
            held = desired.iloc[t].to_numpy().copy()
        held[~eligible.iloc[t].to_numpy()] = 0
        gross = held.sum()
        ceiling = float(risk_ceiling.iloc[t])
        if gross > ceiling:
            held *= max(0, ceiling) / gross
        out[t] = held
    return pd.DataFrame(out, index=desired.index, columns=desired.columns)


def build_diagnostics(data, params=None, mode="base"):
    """Return inspectable factors, learned coefficients and raw/held targets."""
    p = dict(DEFAULT_PARAMS)
    if params:
        if set(params) - set(p):
            raise ValueError("unknown strategy parameters")
        p.update(params)
    if p["window"] not in (63, 126, 189) or p["top_k"] != 6:
        raise ValueError("parameters outside the frozen campaign")
    if p["risk_model"] not in ("structured", "diagonal") or not isinstance(p["cost_gate"], bool):
        raise ValueError("invalid risk/cost configuration")
    if mode not in ("base", "ablation", "falsifier"):
        raise ValueError("unknown experiment mode")
    ctx = _context(data)
    # Secondary ablations keep adaptation, removing only their named component.
    learning_mode = mode
    if mode == "ablation" and (p["risk_model"] == "diagonal" or not p["cost_gate"]):
        learning_mode = "base"
    coefficients = _factor_weights(ctx, p["window"], learning_mode)
    score = sum(ctx["factors"][k].mul(coefficients[k], axis=0) for k in FACTOR_NAMES)
    tradable = ctx["eligible"] & ctx["trend"] & ctx["factor_mask"]
    scale_proxy = score.clip(lower=0) * ctx["vol"] * np.sqrt(7)
    hurdle = 2 * 0.04 * ctx["atr"] if p["cost_gate"] else 0.0
    admitted = tradable & score.gt(0) & (scale_proxy > hurdle)
    close = ctx["close"]
    desired = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    ceilings = pd.Series(0.0, index=close.index)
    r, m = ctx["returns"].to_numpy(), ctx["market"].to_numpy()
    for t in range(126, len(close)):
        ids = np.flatnonzero(admitted.iloc[t].to_numpy())
        if not len(ids):
            continue
        ranked = np.argsort(-score.iloc[t].to_numpy()[ids], kind="stable")
        ids = ids[ranked[:p["top_k"]]]
        cov = _covariance(r[t - 62:t + 1, ids], m[t - 62:t + 1], p["risk_model"] == "diagonal")
        budget = np.exp(score.iloc[t].to_numpy()[ids])
        allocated = np.minimum(_risk_budget(cov, budget), NAME_CAP)
        annual_vol = np.sqrt(365 * (allocated @ cov @ allocated))
        multiplier = min(1.0, TARGET_VOL * ctx["regime"].iloc[t] / max(annual_vol, EPS))
        allocated *= multiplier
        desired.iloc[t, ids] = allocated
        ceilings.iloc[t] = allocated.sum()
    held = _weekly_targets(desired, tradable, ceilings)
    return dict(ctx, coefficients=coefficients, score=score, admitted=admitted,
                desired=desired, risk_ceiling=ceilings, weights=held)


def strategy(data: xr.DataArray, params=None, mode="base") -> xr.DataArray:
    """Full causal target path; standalone, deterministic, long-only, liquid-only."""
    held = build_diagnostics(data, params, mode)["weights"].reindex(columns=data.asset.values)
    return xr.DataArray(held.to_numpy(), dims=("time", "asset"),
                        coords={"time": data.time, "asset": data.asset})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--end", default="2022-12-31", help="development endpoint; 2023+ is excluded")
    parser.add_argument("--window", type=int, choices=(63, 126, 189), default=126)
    parser.add_argument("--mode", choices=("base", "ablation", "falsifier"), default="base")
    parser.add_argument("--write", action="store_true", help="write Quantiacs weights locally; does not submit")
    parser.add_argument("--platform-output", action="store_true",
                        help="generate latest default-strategy weights for platform evaluation; no metrics or submission")
    args = parser.parse_args(argv)
    if not pd.Timestamp("2016-01-01") <= pd.Timestamp(args.end) <= pd.Timestamp("2022-12-31"):
        parser.error("research CLI endpoints must stay within 2016-2022")
    if not os.environ.get("API_KEY", "").strip():
        os.environ["API_KEY"] = "default"
    import qnt.data as qndata
    import qnt.output as qnout
    import qnt.stats as qnstats

    if args.platform_output:
        if args.mode != "base" or args.window != DEFAULT_PARAMS["window"]:
            parser.error("platform output uses only the frozen central candidate")
        data = qndata.cryptodaily_load_data(min_date="2015-01-01")
        weights = qnout.clean(strategy(data), data, COMPETITION_TYPE)
        qnout.write(weights)
        print("Wrote default candidate weights for evaluation. No qualification or submission claimed.")
        return weights

    data = qndata.cryptodaily_load_data(min_date="2015-01-01", max_date=args.end)
    data = data.sel(time=slice("2015-01-01", args.end))
    weights = qnout.clean(strategy(data, dict(window=args.window), args.mode), data, COMPETITION_TYPE)
    stat = qnstats.calc_stat(data, weights.sel(time=slice("2016-01-01", args.end)),
                             slippage_factor=0.04, points_per_year=365)
    print("Local development only; not contest eligibility or submission evidence.")
    print(stat.isel(time=-1).to_pandas().to_string())
    if args.write:
        qnout.write(weights)
    return weights


if __name__ == "__main__":
    main()
