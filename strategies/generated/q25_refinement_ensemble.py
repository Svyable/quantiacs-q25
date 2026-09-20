"""Q25 multi-depth refinement ensemble — frozen pure-crypto research candidate.

Experiment: refinement_ensemble_20260920

The strategy treats asset selection as a set of partial-information states instead
of forcing one terminal gate. It builds one quality-root state, then follows two
fixed refinement orders. Every surviving prefix state produces its own capped
long-only portfolio. The final book is the equal-weight average of all nine
partial-state portfolios, followed by a causal 3-day smoothing pass.

This is inspired by multi-solution aggregation and iterative refinement, not by
a learned neural solver. No formal soundness claim is transferred to markets.

Data: Quantiacs cryptodaily OHLCV + historical is_liquid only.
Constraints: automatic selection, long-only, top-10 liquid universe, 25% name
cap, gross <= 1, cash permitted. No symbols or external data are referenced.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import xarray as xr

COMPETITION_TYPE = "crypto_daily_long"
STRATEGY_ID = "q25_refinement_ensemble_v1"
EXPERIMENT_ID = "refinement_ensemble_20260920"
RESEARCH_START = "2016-01-01"
LOOKBACK_DAYS = 365
NAME_CAP = 0.25
EPS = 1e-12

PATH_A = ("trend", "drawdown", "momentum", "volatility")
PATH_B = ("volatility", "momentum", "drawdown", "trend")


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
    n = liquid.sum("asset")
    safe = xr.where(np.isfinite(x), x, 0.0)
    return xr.where(n > 0, (safe * liquid).sum("asset") / n, 0.0)


def _cs_std(x: xr.DataArray, liquid: xr.DataArray):
    mean = _cs_mean(x, liquid)
    n = liquid.sum("asset")
    safe = xr.where(np.isfinite(x), x, mean)
    var = xr.where(n > 0, (((safe - mean) ** 2) * liquid).sum("asset") / n, 0.0)
    return np.sqrt(xr.where(var > 0, var, 0.0))


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

    quality = xr.where(s7 > mean_s + 0.20 * sd_s, 1.0, 0.0) * liquid
    predicates = {
        "trend": xr.where(trend > 0.0, 1.0, 0.0) * liquid,
        "drawdown": xr.where(dd30 > -0.22, 1.0, 0.0) * liquid,
        "momentum": xr.where(mom14 > 0.0, 1.0, 0.0) * liquid,
        "volatility": xr.where((vol14 > 0.0) & (vol14 < 1.35 * mean_v), 1.0, 0.0) * liquid,
    }

    q = xr.where(s7 > mean_s + 0.20 * sd_s, s7 - (mean_s + 0.20 * sd_s), 0.0)
    raw_score = (q.clip(min=0.0) ** 1.25) / (vol14 + 0.015)
    raw_score = xr.where(np.isfinite(raw_score), raw_score, 0.0) * liquid
    return liquid, quality, predicates, raw_score


def _path_states(
    root: xr.DataArray,
    predicates: dict[str, xr.DataArray],
    order: tuple[str, ...],
):
    mask = root
    states = []
    for name in order:
        mask = mask * predicates[name]
        states.append(mask)
    return states


def _state_portfolio(
    score: xr.DataArray,
    mask: xr.DataArray,
    liquid: xr.DataArray,
):
    return _allocate(score * mask, liquid)


def _ensemble(
    score: xr.DataArray,
    root: xr.DataArray,
    predicates: dict[str, xr.DataArray],
    liquid: xr.DataArray,
    path_a: tuple[str, ...] = PATH_A,
    path_b: tuple[str, ...] = PATH_B,
):
    states = [root]
    states += _path_states(root, predicates, path_a)
    states += _path_states(root, predicates, path_b)
    books = [_state_portfolio(score, state, liquid) for state in states]
    avg = sum(books) / float(len(books))
    avg = _sma(avg, 3, 1) * liquid
    # Averages of capped long-only books preserve the name cap and gross <= 1.
    return avg.transpose("time", "asset").fillna(0.0)


def _base_sharpe7(data: xr.DataArray):
    """Exact promoted Sharpe7 Vol2 formula, used only as frozen incumbent control."""
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
    q = xr.where(s7 > hurdle, s7 - hurdle, 0.0)
    gate = (sma12 > sma48) & (mom14 > 0.0) & (dd30 > -0.22) & (vol14 > 0.0)
    raw = xr.where(gate, (q.clip(min=0.0) ** 1.25) / (vol14 + 0.015), 0.0) * liquid
    raw = _sma(raw, 3, 1) * liquid
    return _allocate(raw, liquid)


def calculate_weights(data: xr.DataArray, mode: str = "ensemble"):
    liquid, root, predicates, score = _features(data)

    if mode == "base_sharpe7":
        return _base_sharpe7(data)

    if mode == "ensemble":
        return _ensemble(score, root, predicates, liquid)

    if mode == "single_path":
        states = [root] + _path_states(root, predicates, PATH_A)
        books = [_state_portfolio(score, state, liquid) for state in states]
        out = _sma(sum(books) / float(len(books)), 3, 1) * liquid
        return out.transpose("time", "asset").fillna(0.0)

    if mode == "terminal":
        mask = root
        for name in PATH_A:
            mask = mask * predicates[name]
        return _allocate(_sma(score * mask, 3, 1) * mask * liquid, liquid)

    if mode == "vote4":
        support = root
        for name in ("trend", "drawdown", "momentum", "volatility"):
            support = support + predicates[name]
        mask = xr.where(support >= 4.0, 1.0, 0.0) * liquid
        return _allocate(_sma(score * mask, 3, 1) * mask * liquid, liquid)

    if mode == "anti_quality":
        anti_root = xr.where((liquid > 0) & (root <= 0), 1.0, 0.0)
        anti_score = xr.where(anti_root > 0, 1.0 / (1.0 + score), 0.0) * liquid
        return _ensemble(anti_score, anti_root, predicates, liquid)

    raise ValueError(f"unknown mode: {mode}")


def strategy(data: xr.DataArray):
    return calculate_weights(data, "ensemble")


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
        "terminal",
        "vote4",
        "single_path",
        "anti_quality",
        "ensemble",
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
        "paths": {"A": list(PATH_A), "B": list(PATH_B)},
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
