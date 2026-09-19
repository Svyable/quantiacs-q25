"""Q25 SOTA meta-ensemble — multi-mechanism research synthesis.

PENDING RESEARCH STRATEGY. NO PERFORMANCE METRICS ARE CLAIMED.

This file synthesizes mechanism classes that survived prior Q25 research without
pretending to reproduce any historical champion. Historical V10/V11/V12/etc.
metrics MUST NOT be attached to this implementation unless an explicit parity
study proves that claim.

Design:
- Quantiacs crypto-daily OHLCV + historical ``is_liquid`` only.
- Long-only, automatic cross-sectional selection, cash allowed.
- Five causal sleeves:
    1) market-residual momentum,
    2) abnormal-volume -> next-return response,
    3) co-crash safety,
    4) low residual skewness,
    5) path-efficient trend.
- Universe-level breadth / market-trend / volatility regime gate.
- Inverse-risk sizing, internal 25% name cap, maximum unit gross.
- No hard-coded coin identities and no external data.

The point of this strategy is not to maximize an already observed backtest. It
is a compact executable hypothesis that can be attacked with the repository's
full testing pyramid: static audit, prefix invariance, chronological folds,
cost ladder, incumbent residualization, multiple-testing diagnostics, then the
current Quantiacs cleaner/checker/multipass/correlation checks.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr


STRATEGY_ID = "q25_sota_meta_ensemble_v1"
COMPETITION_TYPE = "crypto_daily_long"
RESEARCH_START = "2016-01-01"
LOOKBACK_DAYS = 900

# Frozen design knobs. Treat changes as a new experiment, not a silent tune.
BETA_WINDOW = 126
RESIDUAL_MOM_WINDOW = 63
FLOW_WINDOW = 126
VOLUME_Z_WINDOW = 63
COCRASH_WINDOW = 126
COCRASH_QUANTILE_WINDOW = 252
SKEW_WINDOW = 252
TREND_WINDOW = 126
RISK_WINDOW = 63
ATR_WINDOW = 14
BREADTH_WINDOW = 63

TOP_K = 5
NAME_CAP = 0.25
SCORE_EWM_ALPHA = 0.20
EPS = 1e-12

# Mechanism weights sum to one. These are hypothesis weights, not fitted ICs.
SLEEVE_WEIGHTS = {
    "residual_momentum": 0.28,
    "volume_response": 0.22,
    "cocrash_safety": 0.20,
    "low_residual_skew": 0.15,
    "path_efficient_trend": 0.15,
}


def _field(data: xr.DataArray, name: str) -> pd.DataFrame:
    """Return a time x asset frame for a required Quantiacs field."""
    if not {"time", "field", "asset"}.issubset(set(data.dims)):
        raise ValueError(f"expected time/field/asset data, got {data.dims}")
    value = data.sel(field=name).transpose("time", "asset")
    frame = value.to_pandas().astype(float)
    frame.index = pd.DatetimeIndex(frame.index)
    return frame


def _safe_log(values: pd.DataFrame) -> pd.DataFrame:
    """Natural log without evaluating non-positive domains."""
    valid = values > 0.0
    safe = values.where(valid, 1.0)
    return np.log(safe).where(valid)


def _safe_log_ratio(numerator: pd.DataFrame, denominator: pd.DataFrame) -> pd.DataFrame:
    valid = (
        numerator.notna()
        & denominator.notna()
        & (numerator > 0.0)
        & (denominator > 0.0)
    )
    n = numerator.where(valid, 1.0)
    d = denominator.where(valid, 1.0)
    return np.log(n / d).where(valid)


def _centered_rank(values: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional percentile rank on each date, mapped into [-1, +1]."""
    ranked = values.where(mask).rank(axis=1, pct=True, method="average")
    return (2.0 * ranked - 1.0).where(mask, 0.0).fillna(0.0).clip(-1.0, 1.0)


def _rolling_beta(
    asset_return: pd.DataFrame,
    market_return: pd.Series,
    window: int,
    minimum: int,
) -> pd.DataFrame:
    covariance = asset_return.rolling(window, min_periods=minimum).cov(market_return)
    variance = market_return.rolling(window, min_periods=minimum).var(ddof=1)
    return covariance.div(variance + EPS, axis=0)


def _true_range_pct(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
) -> pd.DataFrame:
    previous = close.shift(1)
    candidates = np.maximum.reduce(
        [
            (high - low).abs().to_numpy(dtype=float),
            (high - previous).abs().to_numpy(dtype=float),
            (low - previous).abs().to_numpy(dtype=float),
        ]
    )
    tr = pd.DataFrame(candidates, index=close.index, columns=close.columns)
    return tr.rolling(ATR_WINDOW, min_periods=max(5, ATR_WINDOW // 2)).mean() / (
        close.abs() + EPS
    )


def _capped_allocate(raw: pd.Series, target_gross: float, cap: float) -> pd.Series:
    """Proportional capped water-fill. Capacity that cannot be used stays cash."""
    values = pd.to_numeric(raw, errors="coerce").replace([np.inf, -np.inf], np.nan)
    values = values.fillna(0.0).clip(lower=0.0)
    weights = pd.Series(0.0, index=values.index, dtype=float)
    target = float(np.clip(target_gross, 0.0, 1.0))

    active = values > 0.0
    for _ in range(12):
        remaining = target - float(weights.sum())
        room = (cap - weights).clip(lower=0.0)
        eligible = active & (room > 1e-12)
        if remaining <= 1e-12 or not bool(eligible.any()):
            break
        scores = values.where(eligible, 0.0)
        score_sum = float(scores.sum())
        if score_sum <= EPS:
            break
        proposed = remaining * scores / score_sum
        addition = pd.concat([proposed, room], axis=1).min(axis=1)
        weights = (weights + addition.where(eligible, 0.0)).clip(lower=0.0, upper=cap)

    gross = float(weights.sum())
    if gross > 1.0 + 1e-12:
        weights *= 1.0 / gross
    return weights


def _build_context(data: xr.DataArray) -> dict[str, pd.DataFrame | pd.Series]:
    close = _field(data, "close")
    high = _field(data, "high")
    low = _field(data, "low")
    volume = _field(data, "vol") if "vol" in data.field.values else _field(data, "volume")
    liquid = _field(data, "is_liquid").fillna(0.0) > 0.0

    observed = close.notna() & (close > 0.0)
    recent_quotes = observed.rolling(30, min_periods=1).sum() >= 20
    active_volume = (volume.fillna(0.0) > 0.0).rolling(30, min_periods=1).sum() >= 15
    tradable = liquid & observed & recent_quotes & active_volume

    log_price = _safe_log(close)
    log_return = log_price.diff()
    market_return = log_return.where(tradable).mean(axis=1)

    beta = _rolling_beta(log_return.where(tradable), market_return, BETA_WINDOW, 63)
    residual = log_return - beta.mul(market_return, axis=0)
    atr_pct = _true_range_pct(high, low, close)

    return {
        "close": close,
        "volume": volume,
        "liquid": liquid,
        "tradable": tradable,
        "log_return": log_return,
        "market_return": market_return,
        "beta": beta,
        "residual": residual,
        "atr_pct": atr_pct,
    }


def _signals(ctx: dict[str, pd.DataFrame | pd.Series]) -> tuple[pd.DataFrame, pd.Series]:
    close = ctx["close"]
    volume = ctx["volume"]
    tradable = ctx["tradable"]
    log_return = ctx["log_return"]
    market_return = ctx["market_return"]
    residual = ctx["residual"]

    assert isinstance(close, pd.DataFrame)
    assert isinstance(volume, pd.DataFrame)
    assert isinstance(tradable, pd.DataFrame)
    assert isinstance(log_return, pd.DataFrame)
    assert isinstance(market_return, pd.Series)
    assert isinstance(residual, pd.DataFrame)

    # 1) Residual momentum: continuation after removing the common crypto factor.
    residual_momentum = residual.rolling(
        RESIDUAL_MOM_WINDOW, min_periods=42
    ).sum()

    # 2) Causal abnormal-volume response. Estimate x[t-1] -> residual_return[t]
    # from trailing observations, then apply that known coefficient to x[t].
    dollar_volume = (close * volume).where((close > 0.0) & (volume > 0.0))
    log_dollar_volume = _safe_log(dollar_volume)
    median = log_dollar_volume.rolling(VOLUME_Z_WINDOW, min_periods=42).median()
    scale = log_dollar_volume.rolling(VOLUME_Z_WINDOW, min_periods=42).std(ddof=1)
    abnormal_volume = (log_dollar_volume - median) / (scale + EPS)
    lagged_volume = abnormal_volume.shift(1)
    flow_cov = residual.rolling(FLOW_WINDOW, min_periods=63).cov(lagged_volume)
    flow_var = lagged_volume.rolling(FLOW_WINDOW, min_periods=63).var(ddof=1)
    flow_beta = flow_cov / (flow_var + EPS)
    volume_response = abnormal_volume * flow_beta

    # 3) Co-crash safety. Lower crash-state market correlation is preferred.
    crash_threshold = market_return.rolling(
        COCRASH_QUANTILE_WINDOW, min_periods=126
    ).quantile(0.20)
    crash_mask = market_return <= crash_threshold
    crash_market = market_return.where(crash_mask)
    crash_asset = log_return.where(crash_mask, axis=0)
    cocrash = crash_asset.rolling(COCRASH_WINDOW, min_periods=30).corr(crash_market)
    cocrash_safety = -cocrash

    # 4) Higher moments. Negative residual skew gets the higher score, matching
    # the prior low-residual-skew research direction.
    residual_skew = residual.rolling(SKEW_WINDOW, min_periods=126).skew()
    low_residual_skew = -residual_skew

    # 5) Path-efficient trend: reward directional displacement that required
    # less noisy travel, then risk-normalize its sign/magnitude.
    momentum = _safe_log_ratio(close, close.shift(TREND_WINDOW))
    path = log_return.abs().rolling(TREND_WINDOW, min_periods=84).sum()
    efficiency = momentum.abs() / (path + EPS)
    realized_risk = log_return.rolling(RISK_WINDOW, min_periods=42).std(ddof=1)
    path_efficient_trend = momentum * efficiency / (realized_risk + EPS)

    ranked = {
        "residual_momentum": _centered_rank(residual_momentum, tradable),
        "volume_response": _centered_rank(volume_response, tradable),
        "cocrash_safety": _centered_rank(cocrash_safety, tradable),
        "low_residual_skew": _centered_rank(low_residual_skew, tradable),
        "path_efficient_trend": _centered_rank(path_efficient_trend, tradable),
    }

    score = sum(SLEEVE_WEIGHTS[name] * ranked[name] for name in SLEEVE_WEIGHTS)
    score = score.ewm(alpha=SCORE_EWM_ALPHA, adjust=False, min_periods=1).mean()
    score = score.where(tradable, 0.0).fillna(0.0)

    # Universe-level regime gate. This decides gross exposure, not coin identity.
    breadth = (close > close.rolling(BREADTH_WINDOW, min_periods=42).mean()).where(
        tradable
    ).mean(axis=1)
    market_momentum = market_return.rolling(63, min_periods=42).sum()
    short_vol = market_return.rolling(21, min_periods=14).std(ddof=1)
    long_vol = market_return.rolling(126, min_periods=63).std(ddof=1)
    vol_ratio = short_vol / (long_vol + EPS)

    trend_gate = ((market_momentum + 0.05) / 0.25).clip(0.0, 1.0)
    breadth_gate = ((breadth - 0.25) / 0.50).clip(0.0, 1.0)
    vol_gate = ((1.25 - vol_ratio) / 0.75).clip(0.0, 1.0)
    regime = (0.45 * trend_gate + 0.35 * breadth_gate + 0.20 * vol_gate).clip(0.0, 1.0)
    target_gross = (0.10 + 0.85 * regime).clip(0.10, 0.95).fillna(0.10)

    return score, target_gross


def strategy(data: xr.DataArray) -> xr.DataArray:
    """Return the latest causal long-only Q25 allocation."""
    ctx = _build_context(data)
    score, target_gross = _signals(ctx)

    tradable = ctx["tradable"]
    log_return = ctx["log_return"]
    atr_pct = ctx["atr_pct"]
    assert isinstance(tradable, pd.DataFrame)
    assert isinstance(log_return, pd.DataFrame)
    assert isinstance(atr_pct, pd.DataFrame)

    latest_score = score.iloc[-1].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    latest_tradable = tradable.iloc[-1].fillna(False)

    # Sparse top-K selection with a small positive-score admission floor.
    rank = latest_score.where(latest_tradable).rank(ascending=False, method="first")
    selected = latest_tradable & (rank <= TOP_K) & (latest_score > 0.05)

    realized_risk = log_return.rolling(RISK_WINDOW, min_periods=42).std(ddof=1)
    blended_risk = (
        0.70 * realized_risk.iloc[-1] + 0.30 * atr_pct.iloc[-1]
    ).clip(lower=0.003, upper=0.50)

    conviction = np.exp(1.25 * latest_score.clip(-1.0, 1.0))
    raw = (conviction / (blended_risk + EPS)).where(selected, 0.0).fillna(0.0)

    gross = float(target_gross.iloc[-1])
    weights = _capped_allocate(raw, gross, NAME_CAP)
    weights = weights.where(latest_tradable, 0.0).clip(lower=0.0, upper=NAME_CAP)

    total = float(weights.sum())
    if total > 1.0 + 1e-12:
        weights *= 1.0 / total

    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("asset",),
        coords={"asset": weights.index.to_numpy()},
        name=STRATEGY_ID,
    ).fillna(0.0)


def load_data(period: int):
    import qnt.data as qndata

    return qndata.cryptodaily_load_data(tail=period)


def run_multipass():
    """Run the current Quantiacs multipass research path; does not submit."""
    import qnt.backtester as qnbt

    return qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date=RESEARCH_START,
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )


if __name__ == "__main__":
    run_multipass()
