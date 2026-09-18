"""Q25 deadline candidate: causal co-crash shelter.

Submission-hardening adapter for the documented co-crash-shelter mechanism.
This implementation is NEW and does not inherit historical performance claims.

Mechanism
---------
During broad crypto stress, estimate each currently liquid asset's trailing
sensitivity to the equal-weight liquid-universe return. Prefer assets with the
lowest crash beta / crash correlation, then inverse-risk size a sparse book.
A simple market-level trend/breadth guard can reduce gross exposure in broad
bear states. The allocation is refreshed weekly to limit ATR-linked turnover.

Hard constraints
----------------
- Quantiacs crypto-daily data only.
- Historical is_liquid only; no hard-coded asset identities.
- Long-only; automatic cross-sectional selection; cash allowed.
- Causal trailing windows only; no centered windows or future shifts.
- Fixed parameters. Retuning after observing this experiment is a new study.
"""

from __future__ import annotations

import json
import os
from typing import Dict

import numpy as np
import pandas as pd
import xarray as xr

STRATEGY_ID = "q25_deadline_cocrash_shelter_v1"
COMPETITION_TYPE = "crypto_daily_long"
IN_SAMPLE_START = "2016-01-01"
LOOKBACK_DAYS = 420

CRASH_THRESHOLD_WINDOW = 252
CRASH_WINDOW = 126
MIN_STRESS_OBS = 20
RISK_WINDOW = 63
MARKET_TREND_WINDOW = 63
BREADTH_WINDOW = 126

TOP_K = 4
NAME_CAP = 0.30
PANIC_GROSS = 0.35
NORMAL_GROSS = 1.00
EPS = 1e-12


def _frame(data: xr.DataArray, field: str) -> pd.DataFrame:
    out = data.sel(field=field).transpose("time", "asset").to_pandas().astype(float)
    out.index = pd.DatetimeIndex(out.index)
    return out


def _waterfill(raw: pd.Series, target_gross: float, cap: float) -> pd.Series:
    raw = pd.to_numeric(raw, errors="coerce").replace([np.inf, -np.inf], np.nan)
    raw = raw.fillna(0.0).clip(lower=0.0)
    w = pd.Series(0.0, index=raw.index, dtype=float)
    target = float(np.clip(target_gross, 0.0, 1.0))

    active = raw > 0.0
    for _ in range(12):
        remaining = target - float(w.sum())
        if remaining <= 1e-12:
            break
        room = (cap - w).clip(lower=0.0)
        eligible = active & (room > 1e-12)
        if not bool(eligible.any()):
            break
        scores = raw.where(eligible, 0.0)
        denom = float(scores.sum())
        if denom <= EPS:
            break
        add = remaining * scores / denom
        add = pd.concat([add, room], axis=1).min(axis=1)
        w = (w + add.where(eligible, 0.0)).clip(lower=0.0, upper=cap)

    if float(w.sum()) > 1.0 + 1e-12:
        w /= float(w.sum())
    return w


def _context(data: xr.DataArray) -> Dict[str, object]:
    close = _frame(data, "close")
    liquid = _frame(data, "is_liquid").fillna(0.0) > 0.0
    observed = close.notna() & (close > 0.0)
    tradable = liquid & observed

    log_close = np.log(close.where(close > 0.0))
    asset_ret = log_close.diff()
    market_ret = asset_ret.where(tradable).mean(axis=1)

    threshold = market_ret.rolling(
        CRASH_THRESHOLD_WINDOW, min_periods=126
    ).quantile(0.20)
    stress = market_ret <= threshold

    stress_market = market_ret.where(stress)
    stress_asset = asset_ret.where(stress, axis=0)

    crash_cov = stress_asset.rolling(
        CRASH_WINDOW, min_periods=MIN_STRESS_OBS
    ).cov(stress_market)
    crash_var = stress_market.rolling(
        CRASH_WINDOW, min_periods=MIN_STRESS_OBS
    ).var(ddof=1)
    crash_beta = crash_cov.div(crash_var + EPS, axis=0)
    crash_corr = stress_asset.rolling(
        CRASH_WINDOW, min_periods=MIN_STRESS_OBS
    ).corr(stress_market)

    beta_rank = (-crash_beta).where(tradable).rank(
        axis=1, pct=True, method="average"
    )
    corr_rank = (-crash_corr).where(tradable).rank(
        axis=1, pct=True, method="average"
    )
    safety = (0.70 * beta_rank + 0.30 * corr_rank).where(tradable)

    risk = asset_ret.rolling(RISK_WINDOW, min_periods=42).std(ddof=1)
    risk = risk.clip(lower=0.003, upper=0.50)

    market_momentum = market_ret.rolling(
        MARKET_TREND_WINDOW, min_periods=42
    ).sum()
    slow_mean = close.rolling(BREADTH_WINDOW, min_periods=84).mean()
    breadth = (close > slow_mean).where(tradable).mean(axis=1)
    panic = (market_momentum < 0.0) & (breadth < 0.40)
    target_gross = pd.Series(
        np.where(panic.fillna(True), PANIC_GROSS, NORMAL_GROSS),
        index=close.index,
        dtype=float,
    )

    return {
        "close": close,
        "liquid": liquid,
        "tradable": tradable,
        "asset_ret": asset_ret,
        "market_ret": market_ret,
        "safety": safety,
        "risk": risk,
        "target_gross": target_gross,
    }


def compute_weights(data: xr.DataArray) -> xr.DataArray:
    """Return the complete causal time x asset allocation panel."""
    ctx = _context(data)
    tradable = ctx["tradable"]
    safety = ctx["safety"]
    risk = ctx["risk"]
    target_gross = ctx["target_gross"]
    assert isinstance(tradable, pd.DataFrame)
    assert isinstance(safety, pd.DataFrame)
    assert isinstance(risk, pd.DataFrame)
    assert isinstance(target_gross, pd.Series)

    dates = pd.DatetimeIndex(safety.index)
    rebalance = pd.Series(dates.dayofweek == 0, index=dates)
    # The first row may not be Monday. Keep it cash rather than inventing an
    # off-schedule initial rebalance; sufficient pre-2016 warmup is loaded.
    target = pd.DataFrame(np.nan, index=dates, columns=safety.columns, dtype=float)

    for dt in dates[rebalance.to_numpy()]:
        s = safety.loc[dt].replace([np.inf, -np.inf], np.nan)
        valid = tradable.loc[dt].fillna(False) & s.notna()
        rank = s.where(valid).rank(ascending=False, method="first")
        selected = valid & (rank <= TOP_K)
        if not bool(selected.any()):
            target.loc[dt] = 0.0
            continue

        # Slightly reward stronger safety rank while keeping risk sizing dominant.
        conviction = np.exp(1.25 * (s.clip(0.0, 1.0) - 0.5))
        raw = (conviction / (risk.loc[dt] + EPS)).where(selected, 0.0)
        target.loc[dt] = _waterfill(raw, float(target_gross.loc[dt]), NAME_CAP)

    weights = target.ffill().fillna(0.0)
    # Off-cycle eligibility exits are mandatory. A newly liquid name is not
    # entered until the next scheduled rebalance.
    weights = weights.where(tradable, 0.0)

    # Prevent off-cycle resurrection after a temporary liquidity loss.
    active = pd.DataFrame(False, index=dates, columns=weights.columns)
    held = pd.Series(False, index=weights.columns)
    for i, dt in enumerate(dates):
        if bool(rebalance.iloc[i]):
            held = weights.loc[dt] > 0.0
        held = held & tradable.loc[dt].fillna(False)
        active.loc[dt] = held
    weights = weights.where(active, 0.0)

    weights = weights.clip(lower=0.0, upper=NAME_CAP)
    gross = weights.sum(axis=1)
    over = gross > 1.0 + 1e-12
    if bool(over.any()):
        weights.loc[over] = weights.loc[over].div(gross.loc[over], axis=0)

    return xr.DataArray(
        weights.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": weights.index.to_numpy(), "asset": weights.columns.to_numpy()},
        name=STRATEGY_ID,
    ).fillna(0.0)


def strategy(data: xr.DataArray) -> xr.DataArray:
    """Quantiacs multipass entry point: latest allocation only."""
    return compute_weights(data).isel(time=-1, drop=True)


def load_data(period: int):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata

    return qndata.cryptodaily_load_data(tail=period)


def run_single_pass(write_output: bool = False):
    """Exact current-data Quantiacs evaluation for research / CI."""
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    import qnt.output as qnout
    import qnt.stats as qnstats

    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    weights = compute_weights(data)
    cleaned = qnout.clean(weights, data, COMPETITION_TYPE)

    report = {"strategy_id": STRATEGY_ID, "cost_ladder": {}}
    in_sample = cleaned.sel(time=slice(IN_SAMPLE_START, None))
    for cost in (0.00, 0.04, 0.08, 0.12):
        stats = qnstats.calc_stat(
            data,
            in_sample,
            slippage_factor=cost,
            points_per_year=365,
        ).sel(time=slice(IN_SAMPLE_START, None))
        last = stats.isel(time=-1)
        values = {}
        for field in (
            "sharpe_ratio",
            "equity",
            "max_drawdown",
            "avg_turnover",
            "volatility",
        ):
            if field in last.field.values:
                values[field] = float(last.sel(field=field).item())
        report["cost_ladder"][f"{cost:.2f}"] = values

    print(json.dumps(report, indent=2, sort_keys=True))
    if write_output:
        qnout.write(cleaned)
    return cleaned, report


def run_multipass():
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt

    return qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date=IN_SAMPLE_START,
        strategy=strategy,
        analyze=True,
        check_correlation=True,
    )


if __name__ == "__main__":
    if os.environ.get("Q25_MULTIPASS") == "1":
        run_multipass()
    else:
        run_single_pass(write_output=os.environ.get("Q25_WRITE") == "1")
