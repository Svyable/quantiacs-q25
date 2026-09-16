"""Q25 OMNI stock-turbulence IC-health overlay.

Experiment: omni_stock_turbulence_20260915
Preregistration SHA256: cdfb7e2addac2859b153bf7f42dda868a19973caff9090eb48f1197ddb5518bc
Evidence: PENDING / BLOCKED_LOCAL_INFRA until exact Quantiacs measurement runs.

Mechanism
---------
A cross-asset allocator for Q25 Crypto Top-10 Long. The traded alpha remains
crypto-only and asset-agnostic. Sponsor-provided S&P 500 constituent data is
used only to infer a global risk state and size gross exposure.

The stock state combines five causal systemic-risk sensors:
  1. short/long realized-volatility term structure,
  2. covariance commonality (equal-weight market variance / mean asset variance),
  3. downside breadth,
  4. rolling drawdown pressure,
  5. cross-sectional dispersion shock.

Each sensor is robustly normalized with a trailing median/IQR transform. Their
median defines turbulence; median absolute disagreement reduces confidence.
The overlay is allowed to act only when a dual-horizon, fully realized rolling
information coefficient says that prior stock risk-on readings have positively
predicted subsequent crypto-market returns. IC strength is transformed with the
Fisher z statistic and requires agreement across fast and slow windows.

This borrows the abstain-unless-supported idea from lattice-style reasoning,
but makes no claim of logical soundness: markets are stochastic. Weak or
unstable IC means the overlay abstains and leaves the crypto parent untouched.

Controls
--------
mode="base"     : crypto parent only, no stock overlay.
mode="ungated"  : stock turbulence always trusted (IC ablation).
mode="inverted" : same IC health, but calmness is treated as risk (directional falsifier).
mode="gated"    : preregistered candidate.

Contest constraints
-------------------
- output is long-only and limited to contemporaneous crypto ``is_liquid`` names;
- no hard-coded crypto identities;
- gross <= 1 and per-name <= 0.25;
- sponsor-provided Quantiacs data only;
- stock data never selects a coin; it only scales risk;
- cash is allowed;
- calculations use trailing windows only; no negative shift / future target.

Cross-dataset Q25 submission admissibility remains a hosted-precheck item even
though Quantiacs documents multi-dataset strategies and provides the stock data.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import xarray as xr

STRATEGY_ID = "omni_stock_turbulence_ic_overlay_v1"
EXPERIMENT_ID = "omni_stock_turbulence_20260915"
COMPETITION_TYPE = "crypto_daily_long"
RESEARCH_START = "2016-01-01"
DATA_ORIGIN = "2013-01-01"
LOOKBACK_PERIOD = 1200  # calendar days; safely covers 504 stock sessions + IC history.

# Frozen portfolio construction.
TOP_K = 5
NAME_CAP = 0.25
RISK_FLOOR = 0.25
EPS = 1e-12

# Crypto parent windows.
BETA_WINDOW = 126
RESIDUAL_MOM_WINDOW = 63
TREND_WINDOW = 126
DOWNSIDE_WINDOW = 63
HIT_WINDOW = 126
RISK_WINDOW = 63
ATR_WINDOW = 14

# Stock turbulence windows. 504 sessions ~= two trading years.
STOCK_LONG = 504
STOCK_MIN = 252
STOCK_VOL_FAST = 21
STOCK_VOL_SLOW = 126
STOCK_COMMONALITY = 63
STOCK_DRAWDOWN = 252
STOCK_DISPERSION_BASE = 126
STOCK_BREADTH_SMOOTH = 5

# Calendar-day IC windows. Sparse predictor observations occur only after a
# fresh stock session, so rolling valid-pair counts drive Fisher-z scaling.
IC_FAST = 252
IC_SLOW = 504
IC_MIN_FAST = 63
IC_MIN_SLOW = 126

Mode = Literal["gated", "base", "ungated", "inverted"]


def _field(data: xr.DataArray, name: str) -> pd.DataFrame:
    if not {"time", "field", "asset"}.issubset(set(data.dims)):
        raise ValueError(f"expected time/field/asset dimensions, got {data.dims}")
    if name not in set(data.field.values.tolist()):
        raise ValueError(f"required field missing: {name}")
    out = data.sel(field=name).transpose("time", "asset").to_pandas().astype(float)
    out.index = pd.DatetimeIndex(out.index)
    return out


def _safe_log(frame: pd.DataFrame) -> pd.DataFrame:
    valid = frame.notna() & (frame > 0.0)
    return np.log(frame.where(valid, 1.0)).where(valid)


def _centered_rank(values: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    ranked = values.where(mask).rank(axis=1, pct=True, method="average")
    return (2.0 * ranked - 1.0).where(mask, 0.0).fillna(0.0).clip(-1.0, 1.0)


def _rolling_beta(
    asset_return: pd.DataFrame,
    market_return: pd.Series,
    window: int,
    minimum: int,
) -> pd.DataFrame:
    cov = asset_return.rolling(window, min_periods=minimum).cov(market_return)
    var = market_return.rolling(window, min_periods=minimum).var(ddof=1)
    return cov.div(var + EPS, axis=0)


def _true_range_pct(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
) -> pd.DataFrame:
    prev = close.shift(1)
    candidates = np.maximum.reduce(
        [
            (high - low).abs().to_numpy(dtype=float),
            (high - prev).abs().to_numpy(dtype=float),
            (low - prev).abs().to_numpy(dtype=float),
        ]
    )
    tr = pd.DataFrame(candidates, index=close.index, columns=close.columns)
    atr = tr.rolling(ATR_WINDOW, min_periods=7).mean()
    return atr / (close.abs() + EPS)


def _capped_allocate_row(raw: pd.Series, target_gross: float) -> pd.Series:
    values = pd.to_numeric(raw, errors="coerce").replace([np.inf, -np.inf], np.nan)
    values = values.fillna(0.0).clip(lower=0.0)
    out = pd.Series(0.0, index=values.index, dtype=float)
    remaining = float(np.clip(target_gross, 0.0, 1.0))
    active = values > 0.0

    for _ in range(len(values) + 2):
        if remaining <= EPS or not bool(active.any()):
            break
        room = (NAME_CAP - out).clip(lower=0.0)
        eligible = active & (room > EPS)
        if not bool(eligible.any()):
            break
        scores = values.where(eligible, 0.0)
        denominator = float(scores.sum())
        if denominator <= EPS:
            break
        proposal = remaining * scores / denominator
        addition = pd.concat([proposal, room], axis=1).min(axis=1)
        addition = addition.where(eligible, 0.0)
        out += addition
        remaining = float(np.clip(target_gross - out.sum(), 0.0, 1.0))
        active = eligible & (out < NAME_CAP - EPS)

    gross = float(out.sum())
    if gross > 1.0 + 1e-12:
        out /= gross
    return out.clip(0.0, NAME_CAP)


def _crypto_parent(crypto: xr.DataArray) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return daily target allocations at unit gross and the tradable mask."""
    close = _field(crypto, "close")
    high = _field(crypto, "high")
    low = _field(crypto, "low")
    liquid = _field(crypto, "is_liquid").fillna(0.0) > 0.0

    observed = close.notna() & (close > 0.0)
    recent_quotes = observed.rolling(30, min_periods=1).sum() >= 20
    tradable = liquid & observed & recent_quotes

    log_price = _safe_log(close)
    log_ret = log_price.diff()
    market_ret = log_ret.where(tradable).mean(axis=1)
    beta = _rolling_beta(log_ret.where(tradable), market_ret, BETA_WINDOW, 63)
    residual = log_ret - beta.mul(market_ret, axis=0)

    residual_momentum = residual.rolling(RESIDUAL_MOM_WINDOW, min_periods=42).sum()

    displacement = log_price - log_price.shift(TREND_WINDOW)
    path = log_ret.abs().rolling(TREND_WINDOW, min_periods=84).sum()
    path_efficiency = displacement * (displacement.abs() / (path + EPS))

    downside_vol = log_ret.clip(upper=0.0).rolling(
        DOWNSIDE_WINDOW, min_periods=42
    ).std(ddof=1)
    hit_rate = (log_ret > 0.0).where(log_ret.notna()).rolling(
        HIT_WINDOW, min_periods=84
    ).mean()

    score = (
        _centered_rank(residual_momentum, tradable)
        + _centered_rank(path_efficiency, tradable)
        + _centered_rank(-downside_vol, tradable)
        + _centered_rank(hit_rate, tradable)
    ) / 4.0
    score = score.rolling(7, min_periods=3).mean().where(tradable, 0.0).fillna(0.0)

    ranks = score.where(tradable).rank(axis=1, ascending=False, method="first")
    selected = tradable & (ranks <= TOP_K) & (score > 0.0)

    realized_risk = log_ret.rolling(RISK_WINDOW, min_periods=42).std(ddof=1)
    atr_pct = _true_range_pct(high, low, close)
    blended_risk = (0.70 * realized_risk + 0.30 * atr_pct).clip(0.003, 0.50)
    conviction = np.exp(score.clip(-1.0, 1.0))
    raw = (conviction / (blended_risk + EPS)).where(selected, 0.0).fillna(0.0)

    targets = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    for dt in targets.index:
        targets.loc[dt] = _capped_allocate_row(raw.loc[dt], 1.0)
    targets = targets.where(tradable, 0.0).fillna(0.0)
    return targets, tradable


def _robust_unit_score(series: pd.Series) -> pd.Series:
    """Map a causal scalar state into [0,1] using rolling median/IQR."""
    center = series.rolling(STOCK_LONG, min_periods=STOCK_MIN).median()
    q75 = series.rolling(STOCK_LONG, min_periods=STOCK_MIN).quantile(0.75)
    q25 = series.rolling(STOCK_LONG, min_periods=STOCK_MIN).quantile(0.25)
    sigma = ((q75 - q25) / 1.349).clip(lower=1e-8)
    z = ((series - center) / sigma).clip(-8.0, 8.0)
    return (0.5 + 0.5 * np.tanh(z / 2.0)).where(z.notna())


def _stock_turbulence(stocks: xr.DataArray) -> pd.DataFrame:
    close = _field(stocks, "close")
    liquid = _field(stocks, "is_liquid").fillna(0.0) > 0.0
    observed = close.notna() & (close > 0.0)
    mask = liquid & observed

    log_ret = _safe_log(close).diff().where(mask)
    market_ret = log_ret.mean(axis=1)

    vol_fast = market_ret.rolling(STOCK_VOL_FAST, min_periods=14).std(ddof=1)
    vol_slow = market_ret.rolling(STOCK_VOL_SLOW, min_periods=63).std(ddof=1)
    vol_term = np.log((vol_fast + EPS) / (vol_slow + EPS))

    market_var = market_ret.rolling(STOCK_COMMONALITY, min_periods=42).var(ddof=1)
    asset_var = log_ret.rolling(STOCK_COMMONALITY, min_periods=42).var(ddof=1)
    avg_asset_var = asset_var.where(mask).mean(axis=1)
    commonality = (market_var / (avg_asset_var + EPS)).clip(0.0, 2.0)

    downside_breadth = (log_ret < 0.0).where(log_ret.notna()).mean(axis=1)
    downside_breadth = downside_breadth.rolling(
        STOCK_BREADTH_SMOOTH, min_periods=3
    ).mean()

    curve = np.exp(market_ret.fillna(0.0).cumsum().clip(-30.0, 30.0))
    rolling_peak = curve.rolling(STOCK_DRAWDOWN, min_periods=126).max()
    drawdown = (1.0 - curve / (rolling_peak + EPS)).clip(0.0, 1.0)

    dispersion = log_ret.std(axis=1, ddof=1)
    dispersion_base = dispersion.rolling(
        STOCK_DISPERSION_BASE, min_periods=63
    ).median()
    dispersion_shock = np.log((dispersion + EPS) / (dispersion_base + EPS))

    components = pd.concat(
        {
            "vol_term": _robust_unit_score(vol_term),
            "commonality": _robust_unit_score(commonality),
            "downside_breadth": _robust_unit_score(downside_breadth),
            "drawdown": _robust_unit_score(drawdown),
            "dispersion_shock": _robust_unit_score(dispersion_shock),
        },
        axis=1,
    )

    turbulence = components.median(axis=1, skipna=True)
    disagreement = components.sub(turbulence, axis=0).abs().median(axis=1, skipna=True)
    consensus = (1.0 - 2.0 * disagreement).clip(0.0, 1.0)
    enough = components.notna().sum(axis=1) >= 4
    turbulence = turbulence.where(enough)
    consensus = consensus.where(enough, 0.0)

    result = components.copy()
    result["turbulence"] = turbulence
    result["consensus"] = consensus
    result["risk_on"] = 1.0 - turbulence
    return result


def _rolling_ic_health(
    stock_state: pd.DataFrame,
    crypto: xr.DataArray,
) -> pd.DataFrame:
    """Causal IC: yesterday's fresh stock risk-on vs today's realized crypto return."""
    close = _field(crypto, "close")
    liquid = _field(crypto, "is_liquid").fillna(0.0) > 0.0
    crypto_ret = _safe_log(close).diff().where(liquid).mean(axis=1)
    idx = crypto_ret.index

    stock_risk_on = stock_state["risk_on"].reindex(idx).ffill()
    stock_turbulence = stock_state["turbulence"].reindex(idx).ffill()
    stock_consensus = stock_state["consensus"].reindex(idx).ffill().fillna(0.0)
    fresh = pd.Series(idx.isin(stock_state.index), index=idx, dtype=bool)

    # Pair x[s] with y[s+1] only once y is realized. At decision date t this
    # uses x[t-1] and y[t], never a future target or negative shift.
    fresh_lag = fresh.shift(1, fill_value=False)
    predictor = stock_risk_on.shift(1).where(fresh_lag)
    valid = predictor.notna() & crypto_ret.notna()

    def _window_health(window: int, minimum: int) -> tuple[pd.Series, pd.Series, pd.Series]:
        ic = predictor.rolling(window, min_periods=minimum).corr(crypto_ret)
        n = valid.astype(float).rolling(window, min_periods=minimum).sum()
        clipped = ic.clip(-0.999999, 0.999999)
        fisher_z = np.arctanh(clipped) * np.sqrt((n - 3.0).clip(lower=0.0))
        strength = (fisher_z / 2.0).clip(0.0, 1.0).fillna(0.0)
        return ic, fisher_z, strength

    ic_fast, z_fast, strength_fast = _window_health(IC_FAST, IC_MIN_FAST)
    ic_slow, z_slow, strength_slow = _window_health(IC_SLOW, IC_MIN_SLOW)
    health = pd.concat([strength_fast, strength_slow], axis=1).min(axis=1)

    return pd.DataFrame(
        {
            "turbulence": stock_turbulence,
            "consensus": stock_consensus,
            "ic_fast": ic_fast,
            "ic_slow": ic_slow,
            "z_fast": z_fast,
            "z_slow": z_slow,
            "health": health.clip(0.0, 1.0),
        },
        index=idx,
    )


def _overlay_scale(diagnostics: pd.DataFrame, mode: Mode) -> pd.Series:
    turbulence = diagnostics["turbulence"].fillna(0.5).clip(0.0, 1.0)
    consensus = diagnostics["consensus"].fillna(0.0).clip(0.0, 1.0)

    if mode == "base":
        return pd.Series(1.0, index=diagnostics.index)
    if mode == "ungated":
        health = pd.Series(1.0, index=diagnostics.index)
        directional = turbulence
    elif mode == "inverted":
        health = diagnostics["health"].fillna(0.0).clip(0.0, 1.0)
        directional = 1.0 - turbulence
    elif mode == "gated":
        health = diagnostics["health"].fillna(0.0).clip(0.0, 1.0)
        directional = turbulence
    else:
        raise ValueError(f"unknown mode: {mode}")

    activation = (health * consensus * directional).clip(0.0, 1.0)
    scale = np.exp(math.log(RISK_FLOOR) * activation)
    return pd.Series(scale, index=diagnostics.index).clip(RISK_FLOOR, 1.0)


def _liquidity_change(mask: pd.DataFrame) -> pd.Series:
    values = mask.fillna(False).to_numpy(dtype=bool)
    changed = np.zeros(len(values), dtype=bool)
    if len(values) > 1:
        changed[1:] = np.any(values[1:] != values[:-1], axis=1)
    return pd.Series(changed, index=mask.index)


def _execute(
    parent_target: pd.DataFrame,
    tradable: pd.DataFrame,
    desired_scale: pd.Series,
) -> pd.DataFrame:
    """Weekly alpha rotation; immediate large risk cuts; slow re-risk."""
    idx = parent_target.index
    columns = parent_target.columns
    desired_scale = desired_scale.reindex(idx).ffill().fillna(1.0).clip(RISK_FLOOR, 1.0)
    universe_change = _liquidity_change(tradable)
    monday = pd.Series(idx.dayofweek == 0, index=idx)

    out = pd.DataFrame(0.0, index=idx, columns=columns)
    held = pd.Series(0.0, index=columns, dtype=float)

    for dt in idx:
        allowed = tradable.loc[dt].fillna(False)
        held = held.where(allowed, 0.0)
        current_gross = float(held.sum())
        target_scale = float(desired_scale.loc[dt])
        scheduled = bool(monday.loc[dt] or universe_change.loc[dt] or current_gross <= EPS)

        if scheduled:
            held = parent_target.loc[dt].where(allowed, 0.0) * target_scale
        elif target_scale < current_gross - 0.15:
            # Turbulence warning may de-risk immediately. Re-risk waits for the
            # normal weekly rebalance, reducing ATR-linked turnover drag.
            if current_gross > EPS:
                held = held * (target_scale / current_gross)

        held = held.where(allowed, 0.0).clip(lower=0.0, upper=NAME_CAP)
        gross = float(held.sum())
        if gross > 1.0 + 1e-12:
            held /= gross
        out.loc[dt] = held

    return out.fillna(0.0)


def calculate_weights(data: dict[str, xr.DataArray], mode: Mode = "gated") -> xr.DataArray:
    crypto = data["crypto"]
    stocks = data["stocks"]
    parent, tradable = _crypto_parent(crypto)
    stock_state = _stock_turbulence(stocks)
    diagnostics = _rolling_ic_health(stock_state, crypto)
    scale = _overlay_scale(diagnostics, mode)
    executed = _execute(parent, tradable, scale)

    result = xr.DataArray(
        executed.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": executed.index.to_numpy(), "asset": executed.columns.to_numpy()},
        name=STRATEGY_ID,
    )
    return result.fillna(0.0)


def strategy(data: dict[str, xr.DataArray]) -> xr.DataArray:
    return calculate_weights(data, mode="gated").isel(time=-1, drop=True)


def load_data(period: int):
    import qnt.data as qndata

    period = int(max(period, LOOKBACK_PERIOD + 30))
    crypto = qndata.cryptodaily_load_data(tail=period)
    stocks = qndata.stocks.load_spx_data(tail=period)
    return {"crypto": crypto, "stocks": stocks}, crypto.time.values


def window(data: dict[str, xr.DataArray], max_date: np.datetime64, lookback_period: int):
    min_date = max_date - np.timedelta64(int(lookback_period), "D")
    return {
        "crypto": data["crypto"].sel(time=slice(min_date, max_date)),
        "stocks": data["stocks"].sel(time=slice(min_date, max_date)),
    }


def run_multipass(check_correlation: bool = False):
    import qnt.backtester as qnbt

    return qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        window=window,
        lookback_period=LOOKBACK_PERIOD,
        start_date=RESEARCH_START,
        strategy=strategy,
        analyze=True,
        build_plots=False,
        check_correlation=check_correlation,
    )


def _full_research_data():
    import qnt.data as qndata

    crypto = qndata.cryptodaily_load_data(min_date=DATA_ORIGIN)
    stocks = qndata.stocks.load_spx_data(min_date=DATA_ORIGIN)
    return {"crypto": crypto, "stocks": stocks}


def _stat_snapshot(stat: xr.DataArray) -> dict[str, float | None]:
    last = stat.isel(time=-1).to_pandas()
    fields = [
        "equity",
        "relative_return",
        "volatility",
        "underwater",
        "max_drawdown",
        "sharpe_ratio",
        "mean_return",
        "bias",
        "instruments",
        "avg_turnover",
    ]
    out: dict[str, float | None] = {}
    for field in fields:
        if field in last.index:
            value = float(last[field])
            out[field] = value if np.isfinite(value) else None
    return out


def run_research(output: str | None = None) -> dict[str, object]:
    import qnt.output as qnout
    import qnt.stats as qnstats

    data = _full_research_data()
    crypto = data["crypto"]
    results: dict[str, object] = {
        "experiment_id": EXPERIMENT_ID,
        "strategy_id": STRATEGY_ID,
        "evidence": "OBSERVED_LOCAL_PUBLIC_DEFAULT" if output else "OBSERVED_RUNTIME",
        "modes": {},
    }

    for mode in ("base", "ungated", "inverted", "gated"):
        raw = calculate_weights(data, mode=mode)  # type: ignore[arg-type]
        raw = raw.sel(time=slice(RESEARCH_START, None))
        cleaned = qnout.clean(raw, crypto, COMPETITION_TYPE, debug=False)
        cleaned = cleaned.sel(time=raw.time, asset=raw.asset)
        stat = qnstats.calc_stat(crypto, cleaned).sel(time=slice(RESEARCH_START, None))
        results["modes"][mode] = _stat_snapshot(stat)
        print(f"\n=== {mode} ===")
        print(json.dumps(results["modes"][mode], indent=2, sort_keys=True))

    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
        print(f"wrote {path}")
    return results


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research", action="store_true", help="run single-pass exact Quantiacs stats for candidate + controls")
    parser.add_argument("--multipass", action="store_true", help="run causal Quantiacs multi-pass candidate")
    parser.add_argument("--check-correlation", action="store_true")
    parser.add_argument("--output", default=None, help="JSON path for --research")
    args = parser.parse_args()

    if args.multipass:
        run_multipass(check_correlation=args.check_correlation)
    elif args.research:
        run_research(output=args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    _main()
