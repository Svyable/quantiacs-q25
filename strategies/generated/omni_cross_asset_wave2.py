"""OMNI cross-asset preregistered wave 2 for Q25.

Implemented before observing wave-1 family returns. These mechanisms were fixed
in experiments/omni_cross_asset_frontier_20260915/preregistration.json:
  1) correlation/commonality acceleration with dispersion-collapse interaction;
  2) realized-volatility surface curvature + vol-of-vol + cross-sectional vol spread;
  3) S&P-vs-Nasdaq turbulence disagreement and fixed 5-session lead direction.

Stock data only scales gross risk. Coin selection remains the unchanged frozen
crypto parent. 2023+ periods are diagnostic only and never drive selection.
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
EXPERIMENT_ID = "omni_cross_asset_wave2_20260915"
DATA_ORIGIN = "2013-01-01"


def _load(path_name: str, module_name: str):
    path = Path(__file__).with_name(path_name)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R1 = _load("omni_cross_asset_frontier_r1.py", "omni_frontier_r1_wave2")
FRONTIER = R1.BASE
OMNI = FRONTIER.PARENT


def _correlation_acceleration(ctx: dict[str, object]) -> dict[str, pd.Series]:
    market = ctx["market"]
    dispersion = ctx["dispersion"]
    assert isinstance(market, pd.Series)
    assert isinstance(dispersion, pd.Series)

    fast = FRONTIER._commonality(ctx, 21, 14)
    slow = FRONTIER._commonality(ctx, 126, 63)
    acceleration = fast - slow

    disp_fast = dispersion.rolling(21, min_periods=14).median()
    disp_slow = dispersion.rolling(126, min_periods=63).median()
    collapse = -np.log((disp_fast + EPS) / (disp_slow + EPS))

    accel_risk = R1._robust_unit(acceleration)
    collapse_risk = R1._robust_unit(collapse)
    primary = np.sqrt((accel_risk.clip(0.0, 1.0) * collapse_risk.clip(0.0, 1.0)).astype(float))
    primary = pd.Series(primary, index=acceleration.index, dtype=float).where(accel_risk.notna() & collapse_risk.notna())
    ablation = R1._robust_unit(slow)
    inverted = 1.0 - primary
    return {"primary": primary.clip(0.0, 1.0), "ablation": ablation.clip(0.0, 1.0), "inverted": inverted.clip(0.0, 1.0)}


def _vol_surface_curvature(ctx: dict[str, object]) -> dict[str, pd.Series]:
    market = ctx["market"]
    asset_vol = ctx["asset_vol"]
    assert isinstance(market, pd.Series)
    assert isinstance(asset_vol, pd.DataFrame)

    vols: dict[int, pd.Series] = {}
    for w, minimum in ((10,7),(21,14),(63,42),(126,63)):
        vols[w] = market.rolling(w, min_periods=minimum).std(ddof=1)

    front_slope = np.log((vols[10] + EPS) / (vols[21] + EPS))
    back_slope = np.log((vols[63] + EPS) / (vols[126] + EPS))
    curvature = front_slope - back_slope

    vol21 = vols[21]
    vol_change = np.log((vol21 + EPS) / (vol21.shift(1) + EPS))
    vov_fast = vol_change.rolling(21, min_periods=14).std(ddof=1)
    vov_slow = vol_change.rolling(126, min_periods=63).std(ddof=1)
    vov_accel = np.log((vov_fast + EPS) / (vov_slow + EPS))

    constituent_vol = asset_vol
    vol_spread = constituent_vol.std(axis=1, ddof=1) / (constituent_vol.median(axis=1) + EPS)

    components = pd.concat(
        {
            "curvature": R1._robust_unit(curvature),
            "vol_of_vol": R1._robust_unit(vov_accel),
            "cross_sectional_vol_spread": R1._robust_unit(vol_spread),
        }, axis=1,
    )
    primary = components.median(axis=1, skipna=True).where(components.notna().sum(axis=1) >= 2)
    ablation = R1._robust_unit(np.log((vols[21] + EPS) / (vols[126] + EPS)))
    inverted = 1.0 - primary
    return {"primary": primary.clip(0.0, 1.0), "ablation": ablation.clip(0.0, 1.0), "inverted": inverted.clip(0.0, 1.0)}


def _panel_disagreement(spx: xr.DataArray, ndx: xr.DataArray) -> dict[str, pd.Series]:
    spx_state = OMNI._stock_turbulence(spx)["turbulence"]
    ndx_state = OMNI._stock_turbulence(ndx)["turbulence"]
    union = spx_state.index.union(ndx_state.index)
    s = spx_state.reindex(union).ffill()
    n = ndx_state.reindex(union).ffill()

    mean_risk = ((s + n) / 2.0).clip(0.0, 1.0)
    disagreement = R1._robust_unit((s - n).abs())
    ndx_lead = R1._robust_unit(n - s.shift(5))
    spx_lead = R1._robust_unit(s - n.shift(5))

    primary_parts = pd.concat({"mean":mean_risk,"disagreement":disagreement,"ndx_lead":ndx_lead}, axis=1)
    swap_parts = pd.concat({"mean":mean_risk,"disagreement":disagreement,"spx_lead":spx_lead}, axis=1)
    primary = primary_parts.median(axis=1, skipna=True).where(primary_parts.notna().sum(axis=1) >= 2)
    falsifier = swap_parts.median(axis=1, skipna=True).where(swap_parts.notna().sum(axis=1) >= 2)
    return {"primary":primary.clip(0.0,1.0), "ablation":mean_risk.clip(0.0,1.0), "inverted":falsifier.clip(0.0,1.0)}


def run(output: Path) -> dict[str, object]:
    import qnt.data as qndata

    crypto = qndata.cryptodaily_load_data(min_date=DATA_ORIGIN)
    spx = qndata.stocks.load_spx_data(min_date=DATA_ORIGIN)
    ndx = qndata.stocks.load_ndx_data(min_date=DATA_ORIGIN)

    base = OMNI.calculate_weights({"crypto":crypto,"stocks":spx}, mode="base")
    candidates: dict[str, xr.DataArray] = {"base":base}

    for panel_name, stocks in (("spx",spx),("ndx",ndx)):
        ctx = FRONTIER._stock_context(stocks)
        for family, modes in (
            ("correlation_acceleration", _correlation_acceleration(ctx)),
            ("vol_surface_curvature", _vol_surface_curvature(ctx)),
        ):
            for mode, risk in modes.items():
                candidates[f"{family}__{panel_name}__{mode}"] = FRONTIER._risk_to_weights(base, risk)

    for mode, risk in _panel_disagreement(spx, ndx).items():
        candidates[f"panel_disagreement__dual__{mode}"] = FRONTIER._risk_to_weights(base, risk)

    metrics: dict[str, object] = {}
    for name, weights in candidates.items():
        print(f"evaluating {name}", flush=True)
        metrics[name] = FRONTIER._evaluate(crypto, weights)
        print(json.dumps(metrics[name], indent=2, sort_keys=True), flush=True)

    base_sel = metrics["base"]["selection_2016_2022"]["sharpe"]
    decisions: dict[str, object] = {}
    for family in ("correlation_acceleration","vol_surface_curvature"):
        decisions[family] = {}
        for panel in ("spx","ndx"):
            prefix=f"{family}__{panel}__"
            p=metrics[prefix+"primary"]["selection_2016_2022"]["sharpe"]
            a=metrics[prefix+"ablation"]["selection_2016_2022"]["sharpe"]
            inv=metrics[prefix+"inverted"]["selection_2016_2022"]["sharpe"]
            decisions[family][panel]={
                "primary_selection_sharpe":p,
                "ablation_selection_sharpe":a,
                "inverted_selection_sharpe":inv,
                "base_selection_sharpe":base_sel,
                "direction_supported":bool(p is not None and inv is not None and base_sel is not None and p>base_sel and p>inv),
                "complexity_earned":bool(p is not None and a is not None and p>a),
            }

    prefix="panel_disagreement__dual__"
    p=metrics[prefix+"primary"]["selection_2016_2022"]["sharpe"]
    a=metrics[prefix+"ablation"]["selection_2016_2022"]["sharpe"]
    swap=metrics[prefix+"inverted"]["selection_2016_2022"]["sharpe"]
    decisions["panel_disagreement"]={"dual":{
        "primary_selection_sharpe":p,
        "ablation_selection_sharpe":a,
        "swapped_lead_selection_sharpe":swap,
        "base_selection_sharpe":base_sel,
        "direction_supported":bool(p is not None and swap is not None and base_sel is not None and p>base_sel and p>swap),
        "complexity_earned":bool(p is not None and a is not None and p>a),
    }}

    payload={
        "experiment_id":EXPERIMENT_ID,
        "evidence":"OBSERVED_LOCAL_PUBLIC_DEFAULT",
        "implemented_before_wave1_returns_observed":true if False else True,
        "selection_cutoff":"2022-12-31",
        "post_2022_is_diagnostic_only":True,
        "candidate_count":len(candidates),
        "metrics":metrics,
        "family_decisions":decisions,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", default=f"results/{EXPERIMENT_ID}/summary.json")
    args=parser.parse_args()
    payload=run(Path(args.output))
    print(json.dumps(payload["family_decisions"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
