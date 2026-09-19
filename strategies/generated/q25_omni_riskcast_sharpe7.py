"""Q25 OMNI RiskCast: stock tail/volatility expert overlay on frozen Sharpe7.

Research candidate for Quantiacs Q25 Crypto Top-10 Long.

The crypto carrier is the frozen Sharpe7 Vol2 mechanism. Sponsor-provided
historical S&P 500 and Nasdaq-100 constituent panels are used only to size gross
risk; they never choose crypto identities.

RiskCast forecasts *future crypto downside variance*, not next-day return. Four
causal experts are used:
  1) S&P 500 tail-dependence stress,
  2) Nasdaq-100 tail-dependence stress,
  3) S&P 500 21/126 realized-volatility term stress,
  4) Nasdaq-100 21/126 realized-volatility term stress.

Expert weights are inverse-loss/DMA style: each expert is scored only after a
5-day future downside target is fully revealed. Rolling 252-observation losses
are mapped to exponential weights. The ensemble is allowed to reduce exposure
only when its trailing revealed forecast loss beats a persistence benchmark;
otherwise it abstains (gross multiplier = 1). The entire state is bounded-memory
and reproducible from the lookback window.

Modes:
  base             frozen Sharpe7 carrier only
  static_median    median of four stock experts, no forecast-skill gate
  dynamic_ungated  loss-weighted expert mixture, skill gate forced to 1
  inverted         dynamic mixture direction inverted; destructive control
  dynamic          candidate: loss-weighted mixture + forecast-skill abstention

Cross-dataset admissibility remains a hosted/preclear item. This file is fully
self-contained and uses only Quantiacs-provided daily datasets.
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

STRATEGY_ID = "q25_omni_riskcast_sharpe7_v1"
EXPERIMENT_ID = "omni_riskcast_experts_20260919"
COMPETITION_TYPE = "crypto_daily_long"
RESEARCH_START = "2016-01-01"
DATA_ORIGIN = "2012-01-01"
LOOKBACK_DAYS = 1400
NAME_CAP = 0.25
EPS = 1e-12

SHARPE_WINDOW = 7

NORM_WINDOW = 504
NORM_MIN = 252
TAIL_VOL_WINDOW = 63
TAIL_VOL_MIN = 42
VOL_FAST = 21
VOL_SLOW = 126
VOL_FAST_MIN = 14
VOL_SLOW_MIN = 63

TARGET_HORIZON = 5
CRYPTO_DOWNSIDE_BASE = 63
EXPERT_LOSS_WINDOW = 252
EXPERT_LOSS_MIN = 126
HEALTH_WINDOW = 126
HEALTH_MIN = 63
EXPERT_ETA = 4.0
FULL_HEALTH_REL_IMPROVEMENT = 0.10
RISK_FLOOR = 0.35
SCALE_CUT_BAND = 0.10

Mode = Literal["base", "static_median", "dynamic_ungated", "inverted", "dynamic"]


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
    return components.median(axis=1, skipna=True).where(components.notna().sum(axis=1) >= 2).clip(0.0, 1.0)


def _volterm_stress(ctx: dict[str, object]) -> pd.Series:
    market = ctx["market"]
    assert isinstance(market, pd.Series)
    fast = market.rolling(VOL_FAST, min_periods=VOL_FAST_MIN).std(ddof=1)
    slow = market.rolling(VOL_SLOW, min_periods=VOL_SLOW_MIN).std(ddof=1)
    raw = np.log((fast + EPS) / (slow + EPS))
    return _robust_unit(raw).clip(0.0, 1.0)


def _expert_panel(spx: xr.DataArray, ndx: xr.DataArray, crypto_index: pd.DatetimeIndex) -> pd.DataFrame:
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
    aligned = experts.reindex(crypto_index).ffill().shift(1)
    return aligned.clip(0.0, 1.0)


def _crypto_market_return(crypto: xr.DataArray) -> pd.Series:
    close = _field(crypto, "close")
    liquid = _field(crypto, "is_liquid").fillna(0.0) > 0.0
    return _safe_log(close).diff().where(liquid).mean(axis=1)


def _future_downside_target(crypto: xr.DataArray) -> pd.Series:
    r = _crypto_market_return(crypto)
    downside = r.clip(upper=0.0)
    future_sq = pd.concat(
        {f"h{k}": downside.shift(-k).pow(2) for k in range(1, TARGET_HORIZON + 1)},
        axis=1,
    )
    future_rms = np.sqrt(future_sq.mean(axis=1, skipna=False))
    past_rms = np.sqrt(
        downside.pow(2).rolling(CRYPTO_DOWNSIDE_BASE, min_periods=42).mean()
    )
    log_ratio = np.log((future_rms + 1e-8) / (past_rms + 1e-8)).clip(-8.0, 8.0)
    unit = 0.5 + 0.5 * np.tanh(log_ratio / 2.0)
    return pd.Series(unit, index=r.index, dtype=float).where(future_rms.notna() & past_rms.notna())


def _dynamic_risk_state(experts: pd.DataFrame, target_unit: pd.Series) -> pd.DataFrame:
    target = target_unit.reindex(experts.index)
    origin_loss = experts.sub(target, axis=0).pow(2)
    revealed_loss = origin_loss.shift(TARGET_HORIZON)
    mse = revealed_loss.rolling(EXPERT_LOSS_WINDOW, min_periods=EXPERT_LOSS_MIN).mean()

    raw_w = np.exp((-EXPERT_ETA * mse).clip(-50.0, 0.0))
    denom = raw_w.sum(axis=1)
    weights = raw_w.div(denom.where(denom > EPS), axis=0)
    weights = weights.where(mse.notna())

    mixture = (weights * experts).sum(axis=1, min_count=1)
    static = experts.median(axis=1, skipna=True).where(experts.notna().sum(axis=1) >= 2)

    model_origin_loss = (mixture - target).pow(2)
    baseline_origin_loss = (0.5 - target).pow(2)
    model_mse = model_origin_loss.shift(TARGET_HORIZON).rolling(
        HEALTH_WINDOW, min_periods=HEALTH_MIN
    ).mean()
    baseline_mse = baseline_origin_loss.shift(TARGET_HORIZON).rolling(
        HEALTH_WINDOW, min_periods=HEALTH_MIN
    ).mean()
    rel_improvement = (baseline_mse - model_mse) / (baseline_mse + EPS)
    health = (rel_improvement / FULL_HEALTH_REL_IMPROVEMENT).clip(0.0, 1.0).fillna(0.0)

    out = pd.DataFrame(index=experts.index)
    out["dynamic_risk"] = mixture.clip(0.0, 1.0)
    out["static_risk"] = static.clip(0.0, 1.0)
    out["health"] = health
    out["relative_mse_improvement"] = rel_improvement
    for c in experts.columns:
        out[f"w_{c}"] = weights[c]
        out[f"mse_{c}"] = mse[c]
    return out


def _desired_scale(state: pd.DataFrame, mode: Mode) -> pd.Series:
    idx = state.index
    if mode == "base":
        return pd.Series(1.0, index=idx, dtype=float)
    if mode == "static_median":
        activation = state["static_risk"].fillna(0.0).clip(0.0, 1.0)
    elif mode == "dynamic_ungated":
        activation = state["dynamic_risk"].fillna(0.0).clip(0.0, 1.0)
    elif mode == "inverted":
        risk = state["dynamic_risk"].fillna(0.5).clip(0.0, 1.0)
        activation = ((1.0 - risk) * state["health"].fillna(0.0)).clip(0.0, 1.0)
    elif mode == "dynamic":
        activation = (
            state["dynamic_risk"].fillna(0.0) * state["health"].fillna(0.0)
        ).clip(0.0, 1.0)
    else:
        raise ValueError(mode)
    scale = np.exp(math.log(RISK_FLOOR) * activation)
    return pd.Series(scale, index=idx, dtype=float).clip(RISK_FLOOR, 1.0)


def _banded_scale(desired: pd.Series) -> pd.Series:
    desired = desired.astype(float).ffill().fillna(1.0).clip(RISK_FLOOR, 1.0)
    out = pd.Series(1.0, index=desired.index, dtype=float)
    held = 1.0
    for dt in desired.index:
        d = float(desired.loc[dt])
        if d >= 1.0 - 1e-12:
            held = 1.0
        elif d < held - SCALE_CUT_BAND or dt.dayofweek == 0:
            held = d
        out.loc[dt] = held
    return out


def calculate_weights(data: dict[str, xr.DataArray], mode: Mode = "dynamic") -> xr.DataArray:
    crypto = data["crypto"]
    spx = data["spx"]
    ndx = data["ndx"]
    base = _sharpe7_carrier(crypto).transpose("time", "asset")
    idx = pd.DatetimeIndex(base.time.values)
    experts = _expert_panel(spx, ndx, idx)
    target = _future_downside_target(crypto).reindex(idx)
    state = _dynamic_risk_state(experts, target)
    scale = _banded_scale(_desired_scale(state, mode)).reindex(idx).fillna(1.0)

    frame = base.to_pandas().astype(float).mul(scale, axis=0).clip(lower=0.0)
    out = xr.DataArray(
        frame.to_numpy(dtype=float),
        dims=("time", "asset"),
        coords={"time": frame.index.to_numpy(), "asset": frame.columns.to_numpy()},
        name=STRATEGY_ID,
    )
    return out.fillna(0.0)


def strategy(data: dict[str, xr.DataArray]) -> xr.DataArray:
    return calculate_weights(data, mode="dynamic").isel(time=-1, drop=True)


def load_data(period: int):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata

    period = int(max(period, LOOKBACK_DAYS + 30))
    crypto = qndata.cryptodaily_load_data(tail=period)
    spx = qndata.stocks.load_spx_data(tail=period)
    ndx = qndata.stocks.load_ndx_data(tail=period)
    return {"crypto": crypto, "spx": spx, "ndx": ndx}, crypto.time.values


def window(data: dict[str, xr.DataArray], max_date: np.datetime64, lookback_period: int):
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
    for f in ("sharpe_ratio", "mean_return", "volatility", "max_drawdown", "equity", "avg_turnover"):
        if f in row.index:
            v = float(row[f])
            out[f] = v if np.isfinite(v) else None
    return out


def run_research(output: str | None = None) -> dict[str, object]:
    import qnt.output as qnout
    import qnt.stats as qnstats

    data = _full_data()
    crypto = data["crypto"]
    modes: tuple[Mode, ...] = ("base", "static_median", "dynamic_ungated", "inverted", "dynamic")
    folds = {
        "selection_2016_2022": ("2016-01-01", "2022-12-31"),
        "spent_validation_2023_2024": ("2023-01-01", "2024-12-31"),
        "diagnostic_2025_plus": ("2025-01-01", None),
        "full_2016_plus": ("2016-01-01", None),
    }
    payload: dict[str, object] = {
        "experiment_id": EXPERIMENT_ID,
        "strategy_id": STRATEGY_ID,
        "evidence_class": "POST_PRIOR_OMNI_RESEARCH_NEW_MECHANISM",
        "selection_cutoff": "2022-12-31",
        "post_2022_may_not_drive_parameter_tuning": True,
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
                stat = qnstats.calc_stat(
                    crypto.sel(time=slice(None, end)),
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
