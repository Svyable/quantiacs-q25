"""Exact Quantiacs development benchmark; no synthetic-return fallback."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import yaml
from research.static_audit import audit_weights

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("sharpe_ratio", "mean_return", "volatility", "max_drawdown", "equity", "avg_turnover")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def load_module(path):
    spec = importlib.util.spec_from_file_location("candidate_" + hashlib.sha256(str(path).encode()).hexdigest()[:12], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_panel(data, start, end):
    if set(data.dims) != {"time", "asset", "field"} or data.name != "cryptodaily":
        raise ValueError("expected named cryptodaily field/time/asset DataArray (arithmetic crypto stats)")
    if not {"open", "high", "low", "close", "vol", "is_liquid"} <= set(data.field.values):
        raise ValueError("missing required sponsor fields")
    times = pd.DatetimeIndex(data.time.values)
    if times.has_duplicates or not times.is_monotonic_increasing:
        raise ValueError("timestamps must be unique and increasing")
    if len(set(data.asset.values.tolist())) != data.sizes["asset"]:
        raise ValueError("duplicate assets")
    expected = pd.date_range(start, end, freq="D")
    if not expected.isin(times).all():
        raise ValueError("incomplete daily evaluation coverage")
    if times.max() >= pd.Timestamp("2026-10-01"):
        raise ValueError("live data forbidden in research engine")
    if times.min() > pd.Timestamp(start) - pd.Timedelta(days=365):
        raise ValueError("at least 365 warm-up days required")


def panel_hash(data):
    canonical = data.sortby("asset").transpose("field", "time", "asset")
    h = hashlib.sha256()
    for dim in canonical.dims:
        h.update(json.dumps(canonical[dim].values.astype(str).tolist()).encode())
    values = np.asarray(canonical.values, dtype="<f8").copy()
    values[np.isnan(values)] = np.nan
    h.update(values.tobytes())
    h.update(str(data.name).encode())
    return h.hexdigest()


def _cap_without_renormalizing(raw, cap=0.25):
    """Normalize to <=1 gross, then cap names. Cash is allowed by design."""
    raw = raw.replace([np.inf, -np.inf], np.nan).fillna(0).clip(lower=0)
    weights = raw.div(raw.sum(axis=1).clip(lower=1), axis=0)
    return weights.clip(upper=cap)


def control_weights(data, name):
    c = data.sel(field="close").transpose("time", "asset").to_pandas()
    liquid = data.sel(field="is_liquid").transpose("time", "asset").to_pandas().eq(1) & np.isfinite(c) & (c > 0)
    r = np.log(c.where(c > 0) / c.where(c > 0).shift(1))
    vol = r.rolling(90).std().clip(lower=1e-8)
    if name == "equal_liquid":
        raw = liquid.astype(float)
    elif name == "inverse_vol_trend":
        raw = (1 / vol).where(liquid & (c > c.rolling(90).mean()), 0)
    elif name == "persistent_low_vol":
        ranked = vol.where(liquid).sort_index(axis=1).rank(axis=1, method="first")
        raw = (ranked <= 5).reindex(columns=c.columns).astype(float)
        raw = raw.where(pd.Series(pd.DatetimeIndex(c.index).dayofweek == 0, index=c.index), axis=0).ffill(limit=6).fillna(0)
        raw = raw.where(liquid, 0)
    else:
        raise ValueError(name)
    weights = _cap_without_renormalizing(raw)
    return xr.DataArray(weights.to_numpy(), dims=("time", "asset"), coords={"time": data.time, "asset": data.asset})


def check_weights(weights, data):
    if weights.dims != ("time", "asset"):
        raise ValueError("strategy must return full time/asset path")
    if not weights.time.equals(data.time) or not weights.asset.equals(data.asset):
        raise ValueError("weights coordinates differ from data")
    liq = data.sel(field="is_liquid").transpose("time", "asset")
    result = audit_weights(weights, liq.where(np.isfinite(liq), 0))
    if not result.ok or float(weights.max()) > 0.25 + 1e-10:
        raise ValueError("inadmissible weights: " + str(result.messages))


def check_causality(fn, data, full=None, checkpoints=7):
    full = fn(data) if full is None else full
    check_weights(full, data)
    cuts = sorted(set(np.linspace(min(20, data.sizes["time"] - 1), data.sizes["time"] - 1, checkpoints, dtype=int)))
    maximum = 0.0
    for i in cuts:
        prefix = data.isel(time=slice(0, i + 1))
        got = fn(prefix)
        check_weights(got, prefix)
        difference = np.max(np.abs(got.values - full.isel(time=slice(0, i + 1)).values))
        if not np.isfinite(difference) or difference > 1e-10:
            raise ValueError(f"prefix causality failed at {i}: {difference}")
        maximum = max(maximum, float(difference))
        if i >= 365:
            replay = fn(data.isel(time=slice(i - 364, i + 1))).isel(time=-1)
            try:
                np.testing.assert_allclose(replay.values, full.isel(time=i).values, atol=1e-10, rtol=0)
            except AssertionError as e:
                raise ValueError(f"bounded replay failed at {i}") from e
    return dict(status="PASS", checkpoints=len(cuts), max_abs_difference=maximum)


def derived_return_metrics(relative_return, points_per_year=365):
    """Transparent metrics derived from the exact Quantiacs relative-return stream."""
    r = pd.Series(relative_return).replace([np.inf, -np.inf], np.nan).dropna()
    if len(r) == 0:
        return dict(cagr=None, sortino_ratio=None, hit_rate=None)
    wealth = float(np.prod(1.0 + r.to_numpy()))
    cagr = wealth ** (points_per_year / len(r)) - 1.0 if wealth > 0 else None
    downside = np.minimum(r.to_numpy(), 0.0)
    downside_dev = float(np.sqrt(np.mean(np.square(downside))))
    sortino = float(np.sqrt(points_per_year) * r.mean() / downside_dev) if downside_dev > 0 else None
    return dict(cagr=cagr, sortino_ratio=sortino, hit_rate=float((r > 0).mean()))


def cleaner_impact(raw, cleaned, data, tolerance=1e-10):
    """Measure official platform translation; mutation is evidence, not automatically failure."""
    raw = raw.transpose("time", "asset")
    cleaned = cleaned.sel(time=raw.time, asset=raw.asset).transpose("time", "asset")
    delta = np.abs(np.asarray(cleaned.values, float) - np.asarray(raw.values, float))
    changed = np.isfinite(delta) & (delta > tolerance)
    changed_days = changed.any(axis=1)
    close = data.sel(field="close").transpose("time", "asset").sel(time=raw.time, asset=raw.asset)
    liquid = data.sel(field="is_liquid").transpose("time", "asset").sel(time=raw.time, asset=raw.asset)
    missing_close = ~np.isfinite(np.asarray(close.values, float))
    non_liquid = np.asarray(liquid.values, float) != 1
    raw_gross = np.abs(np.asarray(raw.values, float)).sum(axis=1)
    clean_gross = np.abs(np.asarray(cleaned.values, float)).sum(axis=1)
    max_delta = float(np.nanmax(delta)) if delta.size else 0.0
    return {
        "status": "UNCHANGED" if not bool(changed.any()) else "MUTATED_BY_PLATFORM_CLEANER",
        "max_abs_difference": max_delta if np.isfinite(max_delta) else None,
        "changed_cells": int(changed.sum()),
        "changed_days": int(changed_days.sum()),
        "changed_fraction": float(changed.mean()) if changed.size else 0.0,
        "changed_on_missing_close_cells": int((changed & missing_close).sum()),
        "changed_on_non_liquid_cells": int((changed & non_liquid).sum()),
        "raw_mean_gross": float(np.mean(raw_gross)),
        "cleaned_mean_gross": float(np.mean(clean_gross)),
        "raw_max_gross": float(np.max(raw_gross)),
        "cleaned_max_gross": float(np.max(clean_gross)),
    }


class QuantiacsEvaluator:
    def __init__(self, data):
        import qnt.stats as stats
        import qnt.output as output
        self.data, self.stats, self.output = data, stats, output

    def evaluate(self, weights, folds, costs):
        check_weights(weights, self.data)
        cleaned = self.output.clean(weights, self.data, "crypto_daily_long")
        cleaned = cleaned.sel(time=weights.time, asset=weights.asset).transpose("time", "asset")
        check_weights(cleaned, self.data)
        impact = cleaner_impact(weights, cleaned, self.data)
        result, returns = {"cleaner_impact": impact}, {}
        for fold in folds:
            key = fold["id"]
            result[key] = {}
            for cost in costs:
                w = cleaned.sel(time=slice(fold["start"], fold["end"]))
                d = self.data.sel(time=slice(None, fold["end"]))
                stat = self.stats.calc_stat(d, w, slippage_factor=cost, points_per_year=365)
                row = {}
                for field in FIELDS:
                    number = float(stat.sel(field=field).isel(time=-1))
                    row[field] = number if np.isfinite(number) else None
                rr = stat.sel(field="relative_return").to_pandas()
                extra = derived_return_metrics(rr)
                row.update(extra)
                dd = row["max_drawdown"]
                row["calmar_ratio"] = extra["cagr"] / abs(dd) if extra["cagr"] is not None and dd is not None and dd < 0 else None
                result[key][f"{cost:.2f}"] = row
                if cost == 0.04:
                    returns[key] = rr
        return result, returns


def selection_score(metrics):
    values = [metrics[fold][cost]["sharpe_ratio"] for fold in ("research", "dev") for cost in ("0.04", "0.08", "0.12")]
    if any(v is None or not np.isfinite(v) for v in values):
        return None
    return min(values)


def residual_diagnostics(target, controls):
    """Research-only regression: train exposures in research, evaluate in dev."""
    train = pd.concat([target["research"].rename("target")] + [v["research"].rename(k) for k, v in controls.items()], axis=1).dropna()
    dev = pd.concat([target["dev"].rename("target")] + [v["dev"].rename(k) for k, v in controls.items()], axis=1).dropna()
    if len(train) < 100 or len(dev) < 100:
        return {"status": "PENDING_INSUFFICIENT_MATCHED_RETURNS"}
    beta = np.linalg.lstsq(np.column_stack([np.ones(len(train)), train.iloc[:, 1:]]), train.target, rcond=None)[0]
    residual = dev.target.to_numpy() - np.column_stack([np.ones(len(dev)), dev.iloc[:, 1:]]) @ beta
    sd = residual.std()
    return dict(status="LOCAL_CONTROL_DIAGNOSTIC_ONLY", observations=len(dev),
        residual_sharpe=float(np.sqrt(365) * residual.mean() / sd) if sd > 0 else None,
        correlations={k: (float(v) if np.isfinite(v) else None) for k, v in dev.corr()["target"].drop("target").items()},
        historical_core_comparison="PENDING: historical V10/V11/V12 return streams absent")


def policy():
    folds = yaml.safe_load((ROOT / "configs/chronological_folds.yaml").read_text())["folds"]
    selected = [f for f in folds if f["id"] in {"research", "dev"}]
    costs = yaml.safe_load((ROOT / "configs/cost_ladder.yaml").read_text())["cost_ladder"]
    if [f["id"] for f in selected] != ["research", "dev"] or not {0.04, 0.08, 0.12} <= set(costs):
        raise ValueError("unsupported selection policy")
    if any(pd.Timestamp(f["end"]) >= pd.Timestamp("2023-01-01") for f in selected):
        raise ValueError("development selection cannot inspect validation/diagnostic/live")
    return selected, costs
