"""OMNI cross-asset attribution campaign for Q25.

This is a research driver, not a submission claim. It keeps the frozen crypto
parent from omni_stock_turbulence_ic_overlay_v1 and tests three preregistered,
structurally different stock->crypto gross-risk mechanisms on both historical
S&P-500 and Nasdaq-100 constituent panels.

Wave 1 families:
  - tail_dependence: downside breadth, downside synchronization, tail acceleration
  - fragility_recovery: breadth/price divergence, failed recovery, correlation snap
  - online_ridge: tiny causal rolling ridge forecast of next-session crypto market return

Each family has a primary, a simpler ablation and a sign-inverted destructive
control. Stock data never chooses coin identity. Output positions remain long,
liquid-only and inherit the frozen parent's name/gross limits. No 2023+ result is
used to fit or select parameters in this experiment.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

EPS = 1e-12
EXPERIMENT_ID = "omni_cross_asset_frontier_20260915"
DATA_ORIGIN = "2013-01-01"
RISK_FLOOR = 0.25
NORM_WINDOW = 504
NORM_MIN = 252


def _load_parent():
    path = Path(__file__).with_name("omni_stock_turbulence_ic_overlay.py")
    spec = importlib.util.spec_from_file_location("omni_parent", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen OMNI parent")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PARENT = _load_parent()


def _robust_unit(series: pd.Series) -> pd.Series:
    center = series.rolling(NORM_WINDOW, min_periods=NORM_MIN).median()
    q75 = series.rolling(NORM_WINDOW, min_periods=NORM_MIN).quantile(0.75)
    q25 = series.rolling(NORM_WINDOW, min_periods=NORM_MIN).quantile(0.25)
    sigma = ((q75 - q25) / 1.349).clip(lower=1e-8)
    z = ((series - center) / sigma).clip(-8.0, 8.0)
    return (0.5 + 0.5 * np.tanh(z / 2.0)).where(z.notna())


def _stock_context(stocks: xr.DataArray) -> dict[str, object]:
    close = PARENT._field(stocks, "close")
    liquid = PARENT._field(stocks, "is_liquid").fillna(0.0) > 0.0
    observed = close.notna() & (close > 0.0)
    mask = liquid & observed
    log_price = PARENT._safe_log(close)
    ret = log_price.diff().where(mask)
    market = ret.mean(axis=1)
    asset_vol = ret.rolling(63, min_periods=42).std(ddof=1)
    zret = ret / (asset_vol + EPS)
    dispersion = ret.std(axis=1, ddof=1)
    breadth = (close > close.rolling(63, min_periods=42).mean()).where(mask).mean(axis=1)
    return {
        "close": close,
        "mask": mask,
        "ret": ret,
        "market": market,
        "asset_vol": asset_vol,
        "zret": zret,
        "dispersion": dispersion,
        "breadth": breadth,
    }


def _commonality(ctx: dict[str, object], window: int, minimum: int) -> pd.Series:
    ret = ctx["ret"]
    market = ctx["market"]
    assert isinstance(ret, pd.DataFrame)
    assert isinstance(market, pd.Series)
    market_var = market.rolling(window, min_periods=minimum).var(ddof=1)
    asset_var = ret.rolling(window, min_periods=minimum).var(ddof=1).mean(axis=1)
    return (market_var / (asset_var + EPS)).clip(0.0, 4.0)


def _tail_dependence(ctx: dict[str, object]) -> dict[str, pd.Series]:
    zret = ctx["zret"]
    market = ctx["market"]
    assert isinstance(zret, pd.DataFrame)
    assert isinstance(market, pd.Series)

    tail_breadth = (zret < -1.5).where(zret.notna()).mean(axis=1)
    market_z = zret.mean(axis=1)
    mean_sq = zret.pow(2).mean(axis=1)
    downside_sync = ((market_z.clip(upper=0.0).abs() ** 2) / (mean_sq + EPS)).clip(0.0, 2.0)
    downside_sync = downside_sync.where(market < 0.0, 0.0).rolling(5, min_periods=3).mean()
    tail_accel = tail_breadth.rolling(5, min_periods=3).mean() - tail_breadth.rolling(63, min_periods=42).mean()

    components = pd.concat(
        {
            "tail_breadth": _robust_unit(tail_breadth),
            "downside_sync": _robust_unit(downside_sync),
            "tail_accel": _robust_unit(tail_accel),
        }, axis=1,
    )
    primary = components.median(axis=1, skipna=True).where(components.notna().sum(axis=1) >= 2)
    ablation = components["tail_breadth"]
    inverted = 1.0 - primary
    return {"primary": primary.clip(0.0, 1.0), "ablation": ablation.clip(0.0, 1.0), "inverted": inverted.clip(0.0, 1.0)}


def _failed_recovery(market: pd.Series) -> pd.Series:
    threshold = market.shift(1).rolling(252, min_periods=126).quantile(0.10)
    out = pd.Series(0.0, index=market.index, dtype=float)
    age = 999
    magnitude = 0.0
    recovery = 0.0
    for i, dt in enumerate(market.index):
        r = float(market.iloc[i]) if np.isfinite(market.iloc[i]) else 0.0
        q = threshold.iloc[i]
        if np.isfinite(q) and r < float(q):
            age = 0
            magnitude = max(-r, 1e-6)
            recovery = 0.0
            out.iloc[i] = 1.0
            continue
        if age < 10 and magnitude > 0.0:
            age += 1
            recovery += r
            out.iloc[i] = float(np.clip(1.0 - recovery / magnitude, 0.0, 2.0))
        else:
            out.iloc[i] = 0.0
    return out


def _fragility_recovery(ctx: dict[str, object]) -> dict[str, pd.Series]:
    market = ctx["market"]
    breadth = ctx["breadth"]
    assert isinstance(market, pd.Series)
    assert isinstance(breadth, pd.Series)

    price_trend = market.rolling(63, min_periods=42).sum()
    breadth_change = breadth - breadth.shift(21)
    price_z = 2.0 * _robust_unit(price_trend) - 1.0
    breadth_z = 2.0 * _robust_unit(breadth_change) - 1.0
    divergence = price_z - breadth_z

    recovery_pressure = _failed_recovery(market)
    common_fast = _commonality(ctx, 21, 14)
    common_slow = _commonality(ctx, 126, 63)
    correlation_snap = common_fast - common_slow

    components = pd.concat(
        {
            "breadth_divergence": _robust_unit(divergence),
            "failed_recovery": _robust_unit(recovery_pressure),
            "correlation_snap": _robust_unit(correlation_snap),
        }, axis=1,
    )
    primary = components.median(axis=1, skipna=True).where(components.notna().sum(axis=1) >= 2)
    ablation = components["breadth_divergence"]
    inverted = 1.0 - primary
    return {"primary": primary.clip(0.0, 1.0), "ablation": ablation.clip(0.0, 1.0), "inverted": inverted.clip(0.0, 1.0)}


def _ridge_features(ctx: dict[str, object]) -> pd.DataFrame:
    market = ctx["market"]
    breadth = ctx["breadth"]
    zret = ctx["zret"]
    dispersion = ctx["dispersion"]
    assert isinstance(market, pd.Series)
    assert isinstance(breadth, pd.Series)
    assert isinstance(zret, pd.DataFrame)
    assert isinstance(dispersion, pd.Series)

    vol21 = market.rolling(21, min_periods=14).std(ddof=1)
    vol126 = market.rolling(126, min_periods=63).std(ddof=1)
    tail_breadth = (zret < -1.5).where(zret.notna()).mean(axis=1)
    commonality = _commonality(ctx, 63, 42)
    disp_base = dispersion.rolling(126, min_periods=63).median()
    return pd.DataFrame(
        {
            "market_mom5": market.rolling(5, min_periods=3).sum(),
            "vol_term": np.log((vol21 + EPS) / (vol126 + EPS)),
            "breadth": 2.0 * breadth - 1.0,
            "tail_breadth": tail_breadth,
            "commonality": commonality,
            "dispersion_shock": np.log((dispersion + EPS) / (disp_base + EPS)),
        }
    )


def _crypto_market_return(crypto: xr.DataArray) -> pd.Series:
    close = PARENT._field(crypto, "close")
    liquid = PARENT._field(crypto, "is_liquid").fillna(0.0) > 0.0
    return PARENT._safe_log(close).diff().where(liquid).mean(axis=1)


def _rolling_ridge_predict(features: pd.DataFrame, crypto: xr.DataArray, columns: list[str]) -> pd.DataFrame:
    x = features[columns].copy()
    y_daily = _crypto_market_return(crypto)
    y_next = y_daily.shift(-1).reindex(x.index)
    pred = pd.Series(np.nan, index=x.index, dtype=float)
    yscale = pd.Series(np.nan, index=x.index, dtype=float)

    values = x.to_numpy(dtype=float)
    target = y_next.to_numpy(dtype=float)
    for i in range(len(x)):
        start = max(0, i - 504)
        if i - start < 252:
            continue
        xt = values[start:i]
        yt = target[start:i]
        valid = np.isfinite(yt) & np.isfinite(xt).all(axis=1)
        if int(valid.sum()) < 252 or not np.isfinite(values[i]).all():
            continue
        train_x = xt[valid]
        train_y = yt[valid]
        mu = train_x.mean(axis=0)
        sd = train_x.std(axis=0, ddof=1)
        sd = np.where(np.isfinite(sd) & (sd > 1e-8), sd, 1.0)
        zx = (train_x - mu) / sd
        znow = (values[i] - mu) / sd
        ymu = float(train_y.mean())
        yc = train_y - ymu
        gram = zx.T @ zx + 10.0 * np.eye(zx.shape[1])
        coef = np.linalg.solve(gram, zx.T @ yc)
        pred.iloc[i] = ymu + float(znow @ coef)
        yscale.iloc[i] = max(float(train_y.std(ddof=1)), 1e-6)
    return pd.DataFrame({"prediction": pred, "yscale": yscale})


def _online_ridge(ctx: dict[str, object], crypto: xr.DataArray) -> dict[str, pd.Series]:
    features = _ridge_features(ctx)
    primary_fit = _rolling_ridge_predict(features, crypto, list(features.columns))
    ablation_fit = _rolling_ridge_predict(features, crypto, ["market_mom5"])

    primary_signed = primary_fit["prediction"] / (2.0 * primary_fit["yscale"] + EPS)
    ablation_signed = ablation_fit["prediction"] / (2.0 * ablation_fit["yscale"] + EPS)
    primary = (-primary_signed).clip(0.0, 1.0)
    ablation = (-ablation_signed).clip(0.0, 1.0)
    inverted = primary_signed.clip(0.0, 1.0)
    return {"primary": primary, "ablation": ablation, "inverted": inverted}


def _risk_to_weights(base: xr.DataArray, risk: pd.Series) -> xr.DataArray:
    frame = base.transpose("time", "asset").to_pandas().astype(float)
    idx = frame.index
    aligned = risk.reindex(idx).ffill().fillna(0.0).clip(0.0, 1.0)
    gross = np.exp(np.log(RISK_FLOOR) * aligned)
    out = frame.mul(gross, axis=0).clip(lower=0.0)
    return xr.DataArray(out.to_numpy(), dims=("time", "asset"), coords={"time": out.index, "asset": out.columns}, name="weights")


def _validate(crypto: xr.DataArray, weights: xr.DataArray) -> None:
    values = weights.transpose("time", "asset").values
    if not np.isfinite(values).all() or values.min(initial=0.0) < -1e-12:
        raise ValueError("non-finite or short exposure")
    if values.max(initial=0.0) > 0.25 + 1e-12:
        raise ValueError("name cap")
    if values.sum(axis=1).max(initial=0.0) > 1.0 + 1e-12:
        raise ValueError("gross cap")
    liquid = crypto.sel(field="is_liquid").transpose("time", "asset").reindex(time=weights.time, asset=weights.asset).fillna(0.0)
    forbidden = weights.where(liquid <= 0.0, 0.0)
    if np.abs(forbidden.values).max(initial=0.0) > 1e-12:
        raise ValueError("non-liquid exposure")


def _fold_metrics(rr: xr.DataArray, start: str, end: str | None) -> dict[str, float | int | None]:
    import qnt.stats as qnstats
    sliced = rr.sel(time=slice(start, end)).fillna(0.0)
    if sliced.sizes.get("time", 0) < 10:
        return {"n": int(sliced.sizes.get("time", 0)), "sharpe": None, "equity": None, "max_drawdown": None}
    sharpe_series = qnstats.calc_sharpe_ratio_annualized(sliced)
    sharpe = float(sharpe_series.isel(time=-1).item())
    r = sliced.to_pandas().astype(float).fillna(0.0)
    equity = (1.0 + r).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    return {"n": int(len(r)), "sharpe": sharpe, "equity": float(equity.iloc[-1]), "max_drawdown": float(drawdown.min())}


def _evaluate(crypto: xr.DataArray, weights: xr.DataArray) -> dict[str, object]:
    import qnt.stats as qnstats
    _validate(crypto, weights)
    rr = qnstats.calc_relative_return(crypto, weights)
    scopes = {
        "research_2016_2020": ("2016-01-01", "2020-12-31"),
        "dev_2021_2022": ("2021-01-01", "2022-12-31"),
        "selection_2016_2022": ("2016-01-01", "2022-12-31"),
        "spent_validation_2023_2024": ("2023-01-01", "2024-12-31"),
        "diagnostic_2025_plus": ("2025-01-01", None),
        "full_is": ("2016-01-01", None),
    }
    return {name: _fold_metrics(rr, start, end) for name, (start, end) in scopes.items()}


def run(output: Path) -> dict[str, object]:
    import qnt.data as qndata

    crypto = qndata.cryptodaily_load_data(min_date=DATA_ORIGIN)
    spx = qndata.stocks.load_spx_data(min_date=DATA_ORIGIN)
    ndx = qndata.stocks.load_ndx_data(min_date=DATA_ORIGIN)

    base = PARENT.calculate_weights({"crypto": crypto, "stocks": spx}, mode="base")
    old_omni = PARENT.calculate_weights({"crypto": crypto, "stocks": spx}, mode="ungated")
    candidates: dict[str, xr.DataArray] = {"base": base, "omni_v1_ungated_spx": old_omni}

    for panel_name, stocks in (("spx", spx), ("ndx", ndx)):
        ctx = _stock_context(stocks)
        families = {
            "tail_dependence": _tail_dependence(ctx),
            "fragility_recovery": _fragility_recovery(ctx),
            "online_ridge": _online_ridge(ctx, crypto),
        }
        for family, modes in families.items():
            for mode, risk in modes.items():
                candidates[f"{family}__{panel_name}__{mode}"] = _risk_to_weights(base, risk)

    metrics: dict[str, object] = {}
    for name, weights in candidates.items():
        print(f"evaluating {name}", flush=True)
        metrics[name] = _evaluate(crypto, weights)
        print(json.dumps(metrics[name], indent=2, sort_keys=True), flush=True)

    base_sel = metrics["base"]["selection_2016_2022"]["sharpe"]
    decisions: dict[str, object] = {}
    for family in ("tail_dependence", "fragility_recovery", "online_ridge"):
        decisions[family] = {}
        for panel in ("spx", "ndx"):
            prefix = f"{family}__{panel}__"
            p = metrics[prefix + "primary"]["selection_2016_2022"]["sharpe"]
            a = metrics[prefix + "ablation"]["selection_2016_2022"]["sharpe"]
            inv = metrics[prefix + "inverted"]["selection_2016_2022"]["sharpe"]
            support = bool(p is not None and a is not None and inv is not None and base_sel is not None and p > base_sel and p > inv)
            complexity_earned = bool(p is not None and a is not None and p > a)
            decisions[family][panel] = {
                "primary_selection_sharpe": p,
                "ablation_selection_sharpe": a,
                "inverted_selection_sharpe": inv,
                "base_selection_sharpe": base_sel,
                "direction_supported": support,
                "complexity_earned": complexity_earned,
            }

    payload = {
        "experiment_id": EXPERIMENT_ID,
        "evidence": "OBSERVED_LOCAL_PUBLIC_DEFAULT",
        "selection_cutoff": "2022-12-31",
        "post_2022_is_diagnostic_only": true,
        "candidate_count": len(candidates),
        "metrics": metrics,
        "family_decisions": decisions,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=f"results/{EXPERIMENT_ID}/summary.json")
    args = parser.parse_args()
    payload = run(Path(args.output))
    print(json.dumps(payload["family_decisions"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
