"""Q25 deadline candidate: residual-dispersion switch.

Fresh contest adapter for the documented residual-dispersion mechanism. This
source does NOT inherit any historical performance number from the archived
research roster.

Hypothesis
----------
When cross-sectional idiosyncratic return dispersion is elevated relative to
its own trailing history, common-market neutralization leaves enough
asset-specific structure for persistent residual winners to carry information.
During low-dispersion states the strategy holds cash rather than forcing a bet.

Implementation
--------------
- Quantiacs crypto-daily close + historical is_liquid only.
- Equal-weight liquid-universe market factor.
- 126-day trailing beta, 63-day residual quality score.
- Dispersion state: 21-day smoothed cross-sectional residual dispersion above
  its trailing 252-day median (all trailing/causal).
- Weekly Monday rebalance; off-cycle liquidity exits allowed.
- Top four positive residual-quality names, inverse residual-risk sizing.
- Long-only, 25% name cap, max gross 1.0, cash allowed.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import xarray as xr

STRATEGY_ID = "q25_deadline_residual_dispersion_v1"
COMPETITION_TYPE = "crypto_daily_long"
IN_SAMPLE_START = "2016-01-01"
LOOKBACK_DAYS = 500

BETA_WINDOW = 126
BETA_MIN = 63
SCORE_WINDOW = 63
SCORE_MIN = 42
DISPERSION_SMOOTH = 21
DISPERSION_HISTORY = 252
DISPERSION_MIN = 126
RISK_WINDOW = 63
RISK_MIN = 42
TOP_K = 4
NAME_CAP = 0.25
EPS = 1e-12


def _frame(data: xr.DataArray, field: str) -> pd.DataFrame:
    out = data.sel(field=field).transpose("time", "asset").to_pandas().astype(float)
    out.index = pd.DatetimeIndex(out.index)
    return out


def _waterfill(raw: pd.Series, cap: float = NAME_CAP) -> pd.Series:
    raw = pd.to_numeric(raw, errors="coerce").replace([np.inf, -np.inf], np.nan)
    raw = raw.fillna(0.0).clip(lower=0.0)
    w = pd.Series(0.0, index=raw.index, dtype=float)
    for _ in range(12):
        remaining = 1.0 - float(w.sum())
        if remaining <= 1e-12:
            break
        room = (cap - w).clip(lower=0.0)
        eligible = (raw > 0.0) & (room > 1e-12)
        if not bool(eligible.any()):
            break
        score = raw.where(eligible, 0.0)
        denom = float(score.sum())
        if denom <= EPS:
            break
        add = remaining * score / denom
        add = pd.concat([add, room], axis=1).min(axis=1)
        w = (w + add.where(eligible, 0.0)).clip(lower=0.0, upper=cap)
    if float(w.sum()) > 1.0 + 1e-12:
        w /= float(w.sum())
    return w


def _signals(data: xr.DataArray):
    close = _frame(data, "close")
    liquid = _frame(data, "is_liquid").fillna(0.0) > 0.0
    observed = close.notna() & (close > 0.0)
    tradable = liquid & observed

    log_close = np.log(close.where(close > 0.0))
    ret = log_close.diff()
    market = ret.where(tradable).mean(axis=1)

    cov = ret.where(tradable).rolling(BETA_WINDOW, min_periods=BETA_MIN).cov(market)
    var = market.rolling(BETA_WINDOW, min_periods=BETA_MIN).var(ddof=1)
    beta = cov.div(var + EPS, axis=0)
    residual = ret - beta.mul(market, axis=0)

    residual_mean = residual.rolling(SCORE_WINDOW, min_periods=SCORE_MIN).mean()
    residual_risk = residual.rolling(RISK_WINDOW, min_periods=RISK_MIN).std(ddof=1)
    quality = residual_mean / (residual_risk + EPS)

    # Cross-sectional opportunity state. Requiring a trailing median comparison
    # makes the gate adaptive without fitting an arbitrary absolute threshold.
    xs_dispersion = residual.where(tradable).std(axis=1, ddof=1)
    smoothed_dispersion = xs_dispersion.rolling(
        DISPERSION_SMOOTH, min_periods=10
    ).mean()
    historical_median = smoothed_dispersion.rolling(
        DISPERSION_HISTORY, min_periods=DISPERSION_MIN
    ).median()
    active_state = (smoothed_dispersion > historical_median).fillna(False)

    return tradable, quality, residual_risk, active_state


def compute_weights(data: xr.DataArray) -> xr.DataArray:
    """Return the complete causal time x asset allocation panel."""
    tradable, quality, risk, active_state = _signals(data)
    dates = pd.DatetimeIndex(quality.index)
    rebalance = pd.Series(dates.dayofweek == 0, index=dates)
    target = pd.DataFrame(np.nan, index=dates, columns=quality.columns, dtype=float)

    for dt in dates[rebalance.to_numpy()]:
        if not bool(active_state.loc[dt]):
            target.loc[dt] = 0.0
            continue

        q = quality.loc[dt].replace([np.inf, -np.inf], np.nan)
        valid = tradable.loc[dt].fillna(False) & q.notna() & (q > 0.0)
        rank = q.where(valid).rank(ascending=False, method="first")
        selected = valid & (rank <= TOP_K)
        if not bool(selected.any()):
            target.loc[dt] = 0.0
            continue

        # Rank conviction avoids letting one numerically extreme residual score
        # monopolize the book; inverse residual risk still drives sizing.
        pct = q.where(selected).rank(pct=True, method="average")
        conviction = (0.5 + pct).where(selected, 0.0)
        raw = (conviction / (risk.loc[dt] + EPS)).where(selected, 0.0)
        target.loc[dt] = _waterfill(raw)

    weights = target.ffill().fillna(0.0)
    weights = weights.where(tradable, 0.0)

    # Once an eligibility exit zeroes a held name, do not resurrect it between
    # scheduled rebalances merely because is_liquid turns back on.
    held = pd.Series(False, index=weights.columns)
    active = pd.DataFrame(False, index=dates, columns=weights.columns)
    for i, dt in enumerate(dates):
        if bool(rebalance.iloc[i]):
            held = weights.loc[dt] > 0.0
        held = held & tradable.loc[dt].fillna(False)
        active.loc[dt] = held
    weights = weights.where(active, 0.0).clip(lower=0.0, upper=NAME_CAP)

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
    return compute_weights(data).isel(time=-1, drop=True)


def load_data(period: int):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    return qndata.cryptodaily_load_data(tail=period)


def run_single_pass(write_output: bool = False):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    import qnt.output as qnout
    import qnt.stats as qnstats

    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    weights = compute_weights(data)
    cleaned = qnout.clean(weights, data, COMPETITION_TYPE)
    in_sample = cleaned.sel(time=slice(IN_SAMPLE_START, None))

    report = {"strategy_id": STRATEGY_ID, "cost_ladder": {}}
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
