"""Synthetic mechanics and frozen-contract checks, not return evidence."""
import json
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from research.benchmark import ROOT, check_causality, load_module
from research.iteration import load_manifest
from test_frontier_c import panel

CAMPAIGN = "frontier_20260911g"
FAMILIES = ("edge_uncertainty", "forecast_agreement", "cost_relative_persistence")
WINDOWS = {
    "edge_uncertainty": (42, 63, 84),
    "forecast_agreement": (21, 42, 63),
    "cost_relative_persistence": (42, 63, 84),
}


def module(family):
    return load_module(ROOT / f"strategies/generated/{CAMPAIGN}_{family}.py")


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("mode", ("base", "ablation", "falsifier"))
@pytest.mark.parametrize("grid_index", (0, 1, 2))
def test_full_grid_causality_replay_and_column_invariance(family, mode, grid_index):
    window = WINDOWS[family][grid_index]
    data = panel(n=720)
    m = module(family)
    fn = lambda d: m.strategy(d, {"window": window, "top_k": 5}, mode)
    weights = fn(data)
    assert check_causality(fn, data, weights)["status"] == "PASS"
    assert (weights.values > 0).any()
    xr.testing.assert_allclose(fn(data.sel(asset=data.asset.values[::-1])).sel(asset=data.asset), weights)


@pytest.mark.parametrize("family", FAMILIES)
def test_ablation_and_falsifier_change_deployed_weights(family):
    data = panel(n=720)
    m = module(family)
    base = m.strategy(data)
    for mode in ("ablation", "falsifier"):
        assert float(abs(base - m.strategy(data, mode=mode)).sum()) > 0.001


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("mode", ("base", "falsifier"))
def test_future_asset_cannot_change_active_history(family, mode):
    data = panel(n=720)
    absent = xr.full_like(data.isel(asset=[0]), np.nan).assign_coords(asset=["FUTURE"])
    absent.loc[dict(field="is_liquid")] = 0
    expanded = xr.concat([data, absent], dim="asset")
    m = module(family)
    xr.testing.assert_allclose(m.strategy(expanded, mode=mode).sel(asset=data.asset), m.strategy(data, mode=mode))


def test_edge_uncertainty_is_zero_on_identity_and_positive_on_dispersion():
    m = module("edge_uncertainty")
    identity = np.eye(4)
    np.testing.assert_allclose(m._edge_uncertainty(identity), 0)
    mixed = np.array([
        [1.0, 0.9, 0.1, 0.0],
        [0.9, 1.0, 0.1, 0.0],
        [0.1, 0.1, 1.0, 0.8],
        [0.0, 0.0, 0.8, 1.0],
    ])
    values = m._edge_uncertainty(mixed)
    assert np.all(np.isfinite(values))
    assert values[0] > 0


def test_weights_keep_input_asset_order_for_unsorted_labels():
    data = panel(n=400)
    data = data.assign_coords(asset=["Z", "M", "A", "Q", "B", "C", "D", "E"])
    for family in FAMILIES:
        weights = module(family).strategy(data)
        assert list(weights.asset.values) == list(data.asset.values)


def test_forecast_agreement_prefers_matching_ranks():
    m = module("forecast_agreement")
    dates = pd.date_range("2020-01-06", periods=80)
    close = pd.DataFrame({
        "A": 100 * np.exp(np.linspace(0, 0.4, 80)),
        "B": 100 * np.exp(np.linspace(0, -0.2, 80)),
        "C": 100 * np.exp(np.sin(np.linspace(0, 12, 80)) * 0.05),
    }, index=dates)
    high = close * 1.01
    low = close * 0.99
    vol = pd.DataFrame(1.0, index=dates, columns=close.columns)
    liquid = pd.DataFrame(1.0, index=dates, columns=close.columns)
    data = xr.DataArray(
        np.stack([close.to_numpy(), high.to_numpy(), low.to_numpy(), close.to_numpy(), vol.to_numpy(), liquid.to_numpy()]),
        dims=("field", "time", "asset"),
        coords={"field": ["open", "high", "low", "close", "vol", "is_liquid"], "time": dates, "asset": close.columns},
        name="cryptodaily",
    )
    score, _ = m.signals(data, 21, "base")
    inverse, _ = m.signals(data, 21, "falsifier")
    monday = score.index.dayofweek == 0
    assert float(score.loc[monday].sum().sum()) > 0
    assert float(abs(score - inverse).sum().sum()) > 0


def test_cost_density_falls_when_atr_rises():
    m = module("cost_relative_persistence")
    expected = pd.DataFrame({"A": [0.1, 0.1], "B": [0.1, 0.1]})
    cheap = pd.DataFrame({"A": [0.01, 0.01], "B": [0.04, 0.04]})
    expensive = cheap * 4
    cheap_score = m._density(expected, cheap)
    expensive_score = m._density(expected, expensive)
    assert cheap_score.A.iloc[-1] > expensive_score.A.iloc[-1]
    assert cheap_score.A.iloc[-1] > cheap_score.B.iloc[-1]


def test_registered_campaign_is_finite_and_unpromoted():
    dest = ROOT / "experiments" / CAMPAIGN
    manifest = load_manifest(dest / "manifest.json")
    assert len(manifest["candidates"]) == 15
    assert len(list(dest.glob("*/preregistration.json"))) == 6
    slate = json.loads((dest / "idea_slate.json").read_text())
    assert len(slate) == 24
    assert len({x["area"] for x in slate}) == 4
    assert all(sum(x["scores"].values()) == x["priority_score"] for x in slate)
    assert not manifest["automatic_promotion"]
    assert all(json.loads((dest / name / "preregistration.json").read_text())["classification"] == "discovery_hypothesis"
               for name in FAMILIES)


def test_observed_evidence_matches_frozen_implementation_and_classification():
    from research.preregister import sha256_file
    dest = ROOT / "experiments" / CAMPAIGN
    evidence = ROOT / "evidence" / CAMPAIGN
    freeze = json.loads((dest / "implementation_freeze.json").read_text())
    assert all(sha256_file(ROOT / path) == h for path, h in freeze["sha256"].items())
    manifest = load_manifest(dest / "manifest.json")
    context = json.loads((evidence / "context.json").read_text())
    assert context["manifest_sha256"] == sha256_file(dest / "manifest.json")
    for job in manifest["candidates"]:
        row = json.loads((evidence / "candidate_packets" / (job["id"] + ".json")).read_text())
        assert row["data_sha256"] == context["data_sha256"]
        assert row["strategy_source_sha256"] == sha256_file(ROOT / job["path"])
        assert row["preregistration_sha256"] == job["preregistration_sha256"]
        assert row["params"] == job["params"]
        assert row["classification"] == "discovery_hypothesis"
    matrix = json.loads((evidence / "matrix.json").read_text())
    assert len(matrix["candidates"]) == 18
    assert all(row["status"] == "COMPLETE" for row in matrix["candidates"])
    assert all(row["decision"] == "FREEZE" for row in matrix["families"])
    codes = {row["family"]: row["decision_code"] for row in matrix["families"]}
    assert codes["forecast_agreement"] == "KILL_WEAK_ALPHA"
    assert codes["edge_uncertainty"] == "FALSIFIED_DEVELOPMENT"
    assert codes["cost_relative_persistence"] == "FALSIFIED_DEVELOPMENT"
