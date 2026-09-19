"""Q25 OMNI Policy Health: objective-aligned stock-risk gate on frozen Sharpe7.

This research candidate keeps two policies completely frozen:
  A) plain Sharpe7 Vol2;
  B) Sharpe7 Vol2 multiplied by the fixed static stock-risk overlay from the
     frozen OMNI RiskCast experiment.

The only new mechanism is a causal policy selector. It computes hypothetical
close-to-close returns for A and B using previous-day weights. Every Monday it
compares their trailing annualized Sharpe ratios over 126 and 252 calendar
crypto sessions. The candidate enables policy B for the coming week only when B
beats A on both horizons; otherwise it abstains to A.

The internal selector deliberately uses a cost-free realized-return proxy. It
does not pretend to reproduce Quantiacs slippage. Final evidence is evaluated
with the exact Quantiacs 4%, 8%, and 12%-of-ATR slippage ladder.

Stocks never select crypto identities. They only size aggregate gross exposure.
Cross-dataset Q25 admissibility remains a hosted/preclear item.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import xarray as xr

STRATEGY_ID = "q25_omni_policy_health_sharpe7_v1"
EXPERIMENT_ID = "omni_policy_health_20260919"
COMPETITION_TYPE = "crypto_daily_long"
RESEARCH_START = "2016-01-01"
DATA_ORIGIN = "2012-01-01"
LOOKBACK_DAYS = 1400
NAME_CAP = 0.25
EPS = 1e-12

NORM_WINDOW = 504
NORM_MIN = 252
TAIL_VOL_WINDOW = 63
TAIL_VOL_MIN = 42
VOL_FAST = 21
VOL_SLOW = 126
VOL_FAST_MIN = 14
VOL_SLOW_MIN = 63

RISK_FLOOR = 0.35
SCALE_CUT_BAND = 0.10

HEALTH_FAST = 126
HEALTH_FAST_MIN = 63
HEALTH_SLOW = 252
HEALTH_SLOW_MIN = 126

Mode = Literal["base", "always_static", "fast_only", "slow_only", "inverted_dual", "dual"]


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


def _robust_unit(series: pd.Series) -> pd.Series:
    source = pd.to_numeric(series, errors="coerce").astype(float)
    center = source.rolling(NORM_WINDOW, min_periods=NORM_MIN).median()
    q75 = source.rolling(NORM_WINDOW, min_periods=NORM_MIN).quantile(0.75)
    q25 = source.rolling(NORM_WINDOW, min_periods=NORM_MIN).quantile(0.25)
    sigma = ((q75 - q25) / 1.349).clip(lower=1e-8)
    z = ((source - center) / sigma).clip(-8.0, 8.0)
    mapped = 0.5 + 0.5 * np.tanh(z.to_numpy(dtype=float) / 2.0)
    return pd.Series(mapped, index=z.index, dtype=float).where(z.notna())


# --- Frozen Sharpe7 carrier -------------------------------------------------

def _xr_returns(close: xr.DataArray) -> xr.DataArray:
    r = close / close.shift(time=1) - 1.0
    return xr.where(np.isfinite(r), r, 0.0)


def _xr_sma(x: xr.DataArray, n: int, min_periods: int) -> xr.DataArray:
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=min_periods).mean()


def _xr_std(x: xr.DataArray, n: int, min_periods: int) -> xr.DataArray:
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=min_periods).std()


def _xr_max(x: xr.DataArray, n: int, min_periods: int) -> xr.DataArray:
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=min_periods).max()


def _liquid_cs_mean(x: xr.DataArray, liquid: xr.DataArray) -> xr.DataArray:
    n = liquid.sum("asset")
    return xr.where(n > 0, (xr.where(np.isfinite(x), x, 0.0) * liquid).sum("asset") / n, 0.0)


def _liquid_cs_std(x: xr.DataArray, liquid: xr.DataArray) -> xr.DataArray:
    mean = _liquid_cs_mean(x, liquid)
    n = liquid.sum("asset")
    var = xr.where(
        n > 0,
        (((xr.where(np.isfinite(x), x, 0.0) - mean) ** 2) * liquid).sum("asset") / n,
        0.0,
    )
    return np.sqrt(xr.where(var > 0, var, 0.0))


def _allocate(raw: xr.DataArray, liquid: xr.DataArray) -> xr.DataArray:
    raw = xr.where(np.isfinite(raw) & (raw > 0), raw, 0.0) * liquid
    gross = raw.sum("asset")
    normalized = xr.where(gross > EPS, raw / gross, 0.0)
    capped = xr.where(normalized > NAME_CAP, NAME_CAP, normalized) * liquid
    return capped.transpose("time", "asset").fillna(0.0).reset_coords("field", drop=True)


def _sharpe7_carrier(crypto: xr.DataArray) -> xr.DataArray:
    close = crypto.sel(field="close").transpose("time", "asset").astype(float)
    liq0 = crypto.sel(field="is_liquid").transpose("time", "asset")
    liquid = xr.where((liq0 == 1) & np.isfinite(close) & (close > 0), 1.0, 0.0)
    r = _xr_returns(close)
    mu7 = _xr_sma(r, 7, 5)
    vol14 = _xr_std(r, 14, 7)
    s7 = np.sqrt(365.0) * mu7 / (vol14 + EPS)
    sma12 = _xr_sma(close, 12, 8)
    sma48 = _xr_sma(close, 48, 24)
    mom14 = close / close.shift(time=14) - 1.0
    peak30 = _xr_max(close, 30, 15)
    dd30 = close / (peak30 + EPS) - 1.0
    mean = _liquid_cs_mean(s7, liquid)
    sd = _liquid_cs_std(s7, liquid)
    hurdle = mean + 0.20 * sd
    quality = xr.where(s7 > hurdle, s7 - hurdle, 0.0)
    gate = (sma12 > sma48) & (mom14 > 0.0) & (dd30 > -0.22) & (vol14 > 0.0)
    raw = xr.where(gate, (quality.clip(min=0.0) ** 1.25) / (vol14 + 0.015), 0.0) * liquid
    raw = _xr_sma(raw, 3, 1) * liquid
    return _allocate(raw, liquid)


# --- Frozen static stock-risk policy from RiskCast -------------------------

def _stock_context(stocks: xr.DataArray) -> dict[str, object]:
    close = _field(stocks, "close")
    liquid = _field(stocks, "is_liquid").fillna(0.0) > 0.0
    observed = close.notna() & (close > 0.0)
    mask = liquid & observed
    ret = _safe_log(close).diff().where(mask)
    market = ret.mean(axis=1)
    asset_vol = ret.rolling(TAIL_VOL_WINDOW, min_periods=TAIL_VOL_MIN).std(ddof=1)
    zret = ret / (asset_vol + EPS)
    return {"ret": ret, "market": market, "zret": zret}


def _tail_stress(ctx: dict[str, object]) -> pd.Series:
    zret = ctx["zret"]
    market = ctx["market"]
    assert isinstance(zret, pd.DataFrame)
    assert isinstance(market, pd.Series)

    tail_breadth = (zret < -1.5).where(zret.notna()).mean(axis=1)
    market_z = zret.mean(axis=1)
    mean_sq = zret.pow(2).mean(axis=1)
    downside_sync = ((market_z.clip(upper=0.0).abs() ** 2) / (mean_sq + EPS)).clip(0.0, 2.0)
    downside_sync = downside_sync.where(market < 0.0, 0.0).rolling(5, min_periods=3).mean()
    tail_accel = tail_breadth.rolling(5, min_periods=3).mean() - tail_breadth.rolling(
        63, min_periods=42
    ).mean()

    components = pd.concat(
        {
            "tail_breadth": _robust_unit(tail_breadth),
            "downside_sync": _robust_unit(downside_sync),
            "tail_accel": _robust_unit(tail_accel),
        },
        axis=1,
    )
    return (
        components.median(axis=1, skipna=True)
        .where(components.notna().sum(axis=1) >= 2)
        .clip(0.0, 1.0)
    )


def _volterm_stress(ctx: dict[str, object]) -> pd.Series:
    market = ctx["market"]
    assert isinstance(market, pd.Series)
    fast = market.rolling(VOL_FAST, min_periods=VOL_FAST_MIN).std(ddof=1)
    slow = market.rolling(VOL_SLOW, min_periods=VOL_SLOW_MIN).std(ddof=1)
    return _robust_unit(np.log((fast + EPS) / (slow + EPS))).clip(0.0, 1.0)


def _static_stock_risk(
    spx: xr.DataArray,
    ndx: xr.DataArray,
    crypto_index: pd.DatetimeIndex,
) -> pd.Series:
    spx_ctx = _stock_context(spx)
    ndx_ctx = _stock_context(ndx)
    experts = pd.concat(
        {
            "tail_spx": _tail_stress(spx_ctx),
            "tail_ndx": _tail_stress(ndx_ctx),
            "volterm_spx": _volterm_stress(spx_ctx),
            "volterm_ndx": _volterm_stress(ndx_ctx),
        },
        axis=1,
    )
    # Completed stock session t is not used for crypto decision t. Reindex,
    # forward-fill weekends, then lag one crypto day.
    aligned = experts.reindex(crypto_index).ffill().shift(1)
    return (
        aligned.median(axis=1, skipna=True)
        .where(aligned.notna().sum(axis=1) >= 2)
        .fillna(0.0)
        .clip(0.0, 1.0)
    )


def _banded_static_scale(risk: pd.Series) -> pd.Series:
    desired = np.exp(math.log(RISK_FLOOR) * risk.astype(float).clip(0.0, 1.0))
    desired = pd.Series(desired, index=risk.index, dtype=float).clip(RISK_FLOOR, 1.0)
    out = pd.Series(1.0, index=desired.index, dtype=float)
    held = 1.0
    for dt in desired.index:
        d = float(desired.loc[dt])
        if d < held - SCALE_CUT_BAND or dt.dayofweek == 0:
            held = d
        out.loc[dt] = held
    return out


def _static_policy(
    base: xr.DataArray,
    spx: xr.DataArray,
    ndx: xr.DataArray,
) -> xr.DataArray:
    frame = base.transpose("time", "asset").to_pandas().astype(float)
    idx = pd.DatetimeIndex(frame.index)
    risk = _static_stock_risk(spx, ndx, idx)
    scale = _banded_static_scale(risk).reindex(idx).fillna(1.0)
    out = frame.mul(scale, axis=0).clip(lower=0.0)
    return xr.DataArray(
        out.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": out.index.to_numpy(), "asset": out.columns.to_numpy()},
        name="static_stock_risk_policy",
    ).fillna(0.0)


# --- New objective-aligned policy-health gate ------------------------------

def _hypothetical_policy_return(
    crypto: xr.DataArray,
    weights: xr.DataArray,
) -> pd.Series:
    close = _field(crypto, "close").reindex(
        index=pd.DatetimeIndex(weights.time.values),
        columns=weights.asset.values,
    )
    ret = close / close.shift(1) - 1.0
    ret = ret.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    w = weights.transpose("time", "asset").to_pandas().astype(float)
    # Decision t-1 earns close-to-close return ending at t.
    return (w.shift(1).fillna(0.0) * ret).sum(axis=1)


def _rolling_sharpe(
    r: pd.Series,
    window: int,
    minimum: int,
) -> pd.Series:
    mu = r.rolling(window, min_periods=minimum).mean()
    sd = r.rolling(window, min_periods=minimum).std(ddof=1)
    return np.sqrt(365.0) * mu / (sd + EPS)


def _policy_health_state(
    crypto: xr.DataArray,
    base: xr.DataArray,
    static: xr.DataArray,
) -> pd.DataFrame:
    rb = _hypothetical_policy_return(crypto, base)
    rs = _hypothetical_policy_return(crypto, static)

    out = pd.DataFrame(index=rb.index)
    out["base_fast"] = _rolling_sharpe(rb, HEALTH_FAST, HEALTH_FAST_MIN)
    out["static_fast"] = _rolling_sharpe(rs, HEALTH_FAST, HEALTH_FAST_MIN)
    out["base_slow"] = _rolling_sharpe(rb, HEALTH_SLOW, HEALTH_SLOW_MIN)
    out["static_slow"] = _rolling_sharpe(rs, HEALTH_SLOW, HEALTH_SLOW_MIN)

    out["fast_better"] = out["static_fast"] > out["base_fast"]
    out["slow_better"] = out["static_slow"] > out["base_slow"]
    enough_fast = out[["base_fast", "static_fast"]].notna().all(axis=1)
    enough_slow = out[["base_slow", "static_slow"]].notna().all(axis=1)
    out["fast_better"] = out["fast_better"] & enough_fast
    out["slow_better"] = out["slow_better"] & enough_slow
    return out


def _weekly_choice(state: pd.DataFrame, mode: Mode) -> pd.Series:
    idx = pd.DatetimeIndex(state.index)
    if mode == "base":
        return pd.Series(False, index=idx, dtype=bool)
    if mode == "always_static":
        return pd.Series(True, index=idx, dtype=bool)
    if mode == "fast_only":
        raw = state["fast_better"].astype(bool)
    elif mode == "slow_only":
        raw = state["slow_better"].astype(bool)
    elif mode == "dual":
        raw = (state["fast_better"] & state["slow_better"]).astype(bool)
    elif mode == "inverted_dual":
        fast_bad = (
            state[["base_fast", "static_fast"]].notna().all(axis=1)
            & (state["static_fast"] < state["base_fast"])
        )
        slow_bad = (
            state[["base_slow", "static_slow"]].notna().all(axis=1)
            & (state["static_slow"] < state["base_slow"])
        )
        raw = (fast_bad & slow_bad).astype(bool)
    else:
        raise ValueError(mode)

    monday = pd.Series(idx.dayofweek == 0, index=idx)
    # Update only on Mondays. Before the first eligible Monday, abstain to base.
    return raw.where(monday).ffill().fillna(False).astype(bool)


def calculate_weights(
    data: dict[str, xr.DataArray],
    mode: Mode = "dual",
) -> xr.DataArray:
    crypto = data["crypto"]
    base = _sharpe7_carrier(crypto).transpose("time", "asset")
    static = _static_policy(base, data["spx"], data["ndx"]).transpose("time", "asset")

    if mode == "base":
        return base.fillna(0.0)
    if mode == "always_static":
        return static.fillna(0.0)

    state = _policy_health_state(crypto, base, static)
    choose_static = _weekly_choice(state, mode)
    b = base.to_pandas().astype(float)
    s = static.to_pandas().astype(float)
    out = b.where(~choose_static, s, axis=0).fillna(0.0)

    result = xr.DataArray(
        out.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": out.index.to_numpy(), "asset": out.columns.to_numpy()},
        name=STRATEGY_ID,
    )
    return result.fillna(0.0)


def strategy(data: dict[str, xr.DataArray]) -> xr.DataArray:
    return calculate_weights(data, mode="dual").isel(time=-1, drop=True)


def load_data(period: int):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata

    period = int(max(period, LOOKBACK_DAYS + 30))
    crypto = qndata.cryptodaily_load_data(tail=period)
    spx = qndata.stocks.load_spx_data(tail=period)
    ndx = qndata.stocks.load_ndx_data(tail=period)
    return {"crypto": crypto, "spx": spx, "ndx": ndx}, crypto.time.values


def window(
    data: dict[str, xr.DataArray],
    max_date: np.datetime64,
    lookback_period: int,
):
    min_date = max_date - np.timedelta64(int(lookback_period), "D")
    return {
        "crypto": data["crypto"].sel(time=slice(min_date, max_date)),
        "spx": data["spx"].sel(time=slice(min_date, max_date)),
        "ndx": data["ndx"].sel(time=slice(min_date, max_date)),
    }


def run_multipass(check_correlation: bool = False):
    import qnt.backtester as qnbt

    return qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        window=window,
        lookback_period=LOOKBACK_DAYS,
        start_date=RESEARCH_START,
        strategy=strategy,
        analyze=True,
        build_plots=False,
        check_correlation=check_correlation,
    )


def _full_data() -> dict[str, xr.DataArray]:
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata

    return {
        "crypto": qndata.cryptodaily_load_data(min_date=DATA_ORIGIN),
        "spx": qndata.stocks.load_spx_data(min_date=DATA_ORIGIN),
        "ndx": qndata.stocks.load_ndx_data(min_date=DATA_ORIGIN),
    }


def _snapshot(stat: xr.DataArray) -> dict[str, float | None]:
    if stat.sizes.get("time", 0) == 0:
        return {}
    row = stat.isel(time=-1).to_pandas()
    out: dict[str, float | None] = {}
    for f in (
        "sharpe_ratio",
        "mean_return",
        "volatility",
        "max_drawdown",
        "equity",
        "avg_turnover",
    ):
        if f in row.index:
            value = float(row[f])
            out[f] = value if np.isfinite(value) else None
    return out


def run_research(output: str | None = None) -> dict[str, object]:
    import qnt.output as qnout
    import qnt.stats as qnstats

    data = _full_data()
    crypto = data["crypto"]
    modes: tuple[Mode, ...] = (
        "base",
        "always_static",
        "fast_only",
        "slow_only",
        "inverted_dual",
        "dual",
    )
    folds = {
        "selection_2016_2022": ("2016-01-01", "2022-12-31"),
        "spent_validation_2023_2024": ("2023-01-01", "2024-12-31"),
        "diagnostic_2025_plus": ("2025-01-01", None),
        "full_2016_plus": ("2016-01-01", None),
    }
    payload: dict[str, object] = {
        "experiment_id": EXPERIMENT_ID,
        "strategy_id": STRATEGY_ID,
        "evidence_class": "NEW_PREREGISTERED_POLICY_HEALTH_MECHANISM",
        "selection_cutoff": "2022-12-31",
        "post_2022_may_not_drive_parameter_tuning": True,
        "internal_health_cost_model": "NONE_COST_FREE_PROXY",
        "costs": [0.04, 0.08, 0.12],
        "modes": {},
    }

    for mode in modes:
        print(f"calculating {mode}", flush=True)
        raw = calculate_weights(data, mode=mode).sel(time=slice(RESEARCH_START, None))
        clean = qnout.clean(raw, crypto, COMPETITION_TYPE, debug=False)
        clean = clean.sel(time=raw.time, asset=raw.asset)

        result: dict[str, object] = {}
        for fold_name, (start, end) in folds.items():
            result[fold_name] = {}
            for cost in (0.04, 0.08, 0.12):
                w = clean.sel(time=slice(start, end))
                d = crypto.sel(time=slice(None, end))
                stat = qnstats.calc_stat(
                    d,
                    w,
                    slippage_factor=cost,
                    points_per_year=365,
                ).sel(time=slice(start, end))
                result[fold_name][f"{cost:.2f}"] = _snapshot(stat)
        payload["modes"][mode] = result
        print(json.dumps({mode: result}, indent=2, sort_keys=True), flush=True)

    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research", action="store_true")
    parser.add_argument("--multipass", action="store_true")
    parser.add_argument("--check-correlation", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.multipass:
        run_multipass(check_correlation=args.check_correlation)
    elif args.research:
        run_research(output=args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    _main()
