"""Q25 constraint-descent candidate.

A pure-crypto, long-only research strategy inspired by monotone refinement over a
partial-information state. Each day starts from the Quantiacs liquid universe
and applies a fixed sequence of causal predicates. A refinement is accepted
only when it preserves at least MIN_SURVIVORS candidates; otherwise the step
abstains and leaves the current candidate set unchanged.

This is not a learned Lattice Deduction Transformer and makes no claim that the
paper's soundness guarantees transfer to markets. The borrowed structural idea
is simply: refine a finite candidate state monotonically, detect over-pruning,
and abstain rather than force an invalidly narrow state.

Only Quantiacs crypto daily OHLCV + historical is_liquid are used. No symbols,
external data, negative shifts, centered windows, or manual asset selection.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
STRATEGY_ID = "q25_constraint_descent_v1"
EXPERIMENT_ID = "constraint_descent_20260919"
RESEARCH_START = "2016-01-01"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
MIN_SURVIVORS = 3.0
EPS = 1e-12


def _close_liquid(data: xr.DataArray):
    close = data.sel(field="close").transpose("time", "asset").astype(float)
    liq0 = data.sel(field="is_liquid").transpose("time", "asset")
    liquid = xr.where((liq0 == 1) & np.isfinite(close) & (close > 0), 1.0, 0.0)
    return close, liquid


def _returns(close: xr.DataArray):
    r = close / close.shift(time=1) - 1.0
    return xr.where(np.isfinite(r), r, 0.0)


def _sma(x: xr.DataArray, n: int, min_periods: int):
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=min_periods).mean()


def _std(x: xr.DataArray, n: int, min_periods: int):
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=min_periods).std()


def _max(x: xr.DataArray, n: int, min_periods: int):
    if x.sizes["time"] < min_periods:
        return xr.full_like(x, np.nan, dtype=float)
    return x.rolling(time=min(n, x.sizes["time"]), min_periods=min_periods).max()


def _cs_mean(x: xr.DataArray, liquid: xr.DataArray):
    safe = xr.where(np.isfinite(x), x, 0.0)
    n = liquid.sum("asset")
    return xr.where(n > 0, (safe * liquid).sum("asset") / n, 0.0)


def _cs_std(x: xr.DataArray, liquid: xr.DataArray):
    mean = _cs_mean(x, liquid)
    safe = xr.where(np.isfinite(x), x, mean)
    n = liquid.sum("asset")
    var = xr.where(n > 0, (((safe - mean) ** 2) * liquid).sum("asset") / n, 0.0)
    return np.sqrt(xr.where(var > 0, var, 0.0))


def _z(x: xr.DataArray, liquid: xr.DataArray):
    mean = _cs_mean(x, liquid)
    sd = _cs_std(x, liquid)
    return xr.where(liquid > 0, (x - mean) / (sd + EPS), 0.0)


def _allocate(raw: xr.DataArray, liquid: xr.DataArray):
    raw = xr.where(np.isfinite(raw) & (raw > 0), raw, 0.0) * liquid
    gross = raw.sum("asset")
    w = xr.where(gross > EPS, raw / gross, 0.0)
    w = xr.where(w > NAME_CAP, NAME_CAP, w) * liquid
    return (
        w.transpose("time", "asset")
        .fillna(0.0)
        .reset_coords("field", drop=True)
    )


def _features(data: xr.DataArray):
    close, liquid = _close_liquid(data)
    r = _returns(close)

    mu7 = _sma(r, 7, 5)
    vol14 = _std(r, 14, 7)
    s7 = np.sqrt(365.0) * mu7 / (vol14 + EPS)

    sma12 = _sma(close, 12, 8)
    sma48 = _sma(close, 48, 24)
    trend = sma12 / (sma48 + EPS) - 1.0

    mom14 = close / close.shift(time=14) - 1.0
    peak30 = _max(close, 30, 15)
    dd30 = close / (peak30 + EPS) - 1.0

    mean_s = _cs_mean(s7, liquid)
    sd_s = _cs_std(s7, liquid)
    mean_v = _cs_mean(vol14, liquid)

    predicates = {
        "quality": xr.where(s7 > mean_s + 0.20 * sd_s, 1.0, 0.0) * liquid,
        "trend": xr.where(trend > 0.0, 1.0, 0.0) * liquid,
        "momentum": xr.where(mom14 > 0.0, 1.0, 0.0) * liquid,
        "drawdown": xr.where(dd30 > -0.22, 1.0, 0.0) * liquid,
        "volatility": xr.where(vol14 < 1.35 * mean_v, 1.0, 0.0) * liquid,
    }

    z_s = _z(s7, liquid).clip(min=-2.5, max=2.5)
    z_t = _z(trend, liquid).clip(min=-2.5, max=2.5)
    z_m = _z(mom14, liquid).clip(min=-2.5, max=2.5)
    z_v = _z(vol14, liquid).clip(min=-2.5, max=2.5)
    z_d = _z(dd30, liquid).clip(min=-2.5, max=2.5)

    log_score = (
        0.55 * z_s
        + 0.25 * z_t
        + 0.20 * z_m
        - 0.15 * z_v
        + 0.15 * z_d
    ).clip(min=-3.0, max=3.0)
    score = np.exp(log_score) / (vol14 + 0.02)
    score = xr.where(np.isfinite(score), score, 0.0) * liquid

    return close, liquid, score, predicates


def _refine(mask: xr.DataArray, predicate: xr.DataArray, min_survivors: float):
    proposed = mask * predicate
    enough = proposed.sum("asset") >= float(min_survivors)
    return xr.where(enough, proposed, mask)


def _descent_mask(
    liquid: xr.DataArray,
    predicates: dict[str, xr.DataArray],
    order: tuple[str, ...],
    min_survivors: float = MIN_SURVIVORS,
):
    mask = liquid
    for name in order:
        mask = _refine(mask, predicates[name], min_survivors)
    return mask


def _base_sharpe7(data: xr.DataArray):
    """Exact promoted Sharpe7 Vol2 formula, retained as a frozen control."""
    close, liquid = _close_liquid(data)
    r = _returns(close)
    mu7 = _sma(r, 7, 5)
    vol14 = _std(r, 14, 7)
    s7 = np.sqrt(365.0) * mu7 / (vol14 + EPS)
    sma12 = _sma(close, 12, 8)
    sma48 = _sma(close, 48, 24)
    mom14 = close / close.shift(time=14) - 1.0
    peak30 = _max(close, 30, 15)
    dd30 = close / (peak30 + EPS) - 1.0
    mean = _cs_mean(s7, liquid)
    sd = _cs_std(s7, liquid)
    hurdle = mean + 0.20 * sd
    quality = xr.where(s7 > hurdle, s7 - hurdle, 0.0)
    gate = (sma12 > sma48) & (mom14 > 0.0) & (dd30 > -0.22) & (vol14 > 0.0)
    raw = xr.where(
        gate,
        (quality.clip(min=0.0) ** 1.25) / (vol14 + 0.015),
        0.0,
    ) * liquid
    raw = _sma(raw, 3, 1) * liquid
    return _allocate(raw, liquid)


def calculate_weights(data: xr.DataArray, mode: str = "descent"):
    _, liquid, score, predicates = _features(data)

    if mode == "base_sharpe7":
        return _base_sharpe7(data)

    if mode == "descent":
        order = ("quality", "trend", "drawdown", "momentum", "volatility")
        mask = _descent_mask(liquid, predicates, order)
    elif mode == "reverse_descent":
        order = ("volatility", "momentum", "drawdown", "trend", "quality")
        mask = _descent_mask(liquid, predicates, order)
    elif mode == "forced_all":
        mask = liquid
        for name in ("quality", "trend", "drawdown", "momentum", "volatility"):
            mask = mask * predicates[name]
    elif mode == "vote4":
        support = sum(predicates.values())
        mask = xr.where(support >= 4.0, 1.0, 0.0) * liquid
    elif mode == "anti_quality":
        anti = dict(predicates)
        quality = predicates["quality"]
        anti["quality"] = xr.where((liquid > 0) & (quality <= 0), 1.0, 0.0)
        order = ("quality", "trend", "drawdown", "momentum", "volatility")
        mask = _descent_mask(liquid, anti, order)
    else:
        raise ValueError(f"unknown mode: {mode}")

    raw = _sma(score * mask, 3, 1) * mask * liquid
    return _allocate(raw, liquid)


def strategy(data: xr.DataArray):
    return calculate_weights(data, "descent")


def load_data(period: int):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata

    return qndata.cryptodaily_load_data(tail=max(int(period), LOOKBACK_DAYS))


def _snapshot(stat: xr.DataArray):
    if stat.sizes.get("time", 0) == 0:
        return {}
    row = stat.isel(time=-1).to_pandas()
    out = {}
    for field in (
        "sharpe_ratio",
        "mean_return",
        "volatility",
        "max_drawdown",
        "equity",
        "avg_turnover",
    ):
        if field in row.index:
            value = float(row[field])
            out[field] = value if np.isfinite(value) else None
    return out


def run_research(output: str | None = None):
    os.environ.setdefault("API_KEY", "default")
    import qnt.data as qndata
    import qnt.output as qnout
    import qnt.stats as qnstats

    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    modes = (
        "base_sharpe7",
        "forced_all",
        "vote4",
        "reverse_descent",
        "anti_quality",
        "descent",
    )
    folds = {
        "research_2016_2020": ("2016-01-01", "2020-12-31"),
        "dev_2021_2022": ("2021-01-01", "2022-12-31"),
        "selection_2016_2022": ("2016-01-01", "2022-12-31"),
        "spent_validation_2023_2024": ("2023-01-01", "2024-12-31"),
        "diagnostic_2025_plus": ("2025-01-01", None),
        "full_2016_plus": ("2016-01-01", None),
    }

    payload = {
        "experiment_id": EXPERIMENT_ID,
        "strategy_id": STRATEGY_ID,
        "evidence_class": "NEW_PREREGISTERED_PURE_CRYPTO_MECHANISM",
        "selection_cutoff": "2022-12-31",
        "post_2022_may_not_drive_parameter_tuning": True,
        "modes": {},
    }

    for mode in modes:
        print(f"calculating {mode}", flush=True)
        raw = calculate_weights(data, mode).sel(time=slice(RESEARCH_START, None))
        clean = qnout.clean(raw, data, COMPETITION_TYPE, debug=False)
        clean = clean.sel(time=raw.time, asset=raw.asset)
        result = {}
        for fold_name, (start, end) in folds.items():
            result[fold_name] = {}
            for cost in (0.04, 0.08, 0.12):
                w = clean.sel(time=slice(start, end))
                d = data.sel(time=slice(None, end))
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


def run_multipass(check_correlation: bool = False):
    os.environ.setdefault("API_KEY", "default")
    import qnt.backtester as qnbt

    return qnbt.backtest(
        competition_type=COMPETITION_TYPE,
        load_data=load_data,
        lookback_period=LOOKBACK_DAYS,
        start_date=RESEARCH_START,
        strategy=strategy,
        analyze=True,
        build_plots=False,
        check_correlation=check_correlation,
    )


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research", action="store_true")
    parser.add_argument("--multipass", action="store_true")
    parser.add_argument("--check-correlation", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    if args.research:
        run_research(args.output)
    elif args.multipass:
        run_multipass(args.check_correlation)
    else:
        parser.print_help()


if __name__ == "__main__":
    _main()
