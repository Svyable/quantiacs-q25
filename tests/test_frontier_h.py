"""Synthetic mechanics and frozen-contract checks, not return evidence."""
import json
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from research.benchmark import ROOT, check_causality, load_module
from research.iteration import load_manifest
from research.preregister import sha256_file
from test_frontier_c import panel

CAMPAIGN = "frontier_20260911h"
FAMILIES = ("clustering_escape", "factor_loading_escape", "neighbor_identity_churn")
WINDOWS = {
    "clustering_escape": (42, 63, 84),
    "factor_loading_escape": (42, 63, 84),
    "neighbor_identity_churn": (42, 63, 84),
}


def module(family):
    return load_module(ROOT / f"strategies/generated/{CAMPAIGN}_{family}.py")


def test_observed_evidence_matches_frozen_implementation_and_classification():
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


def test_onnela_clustering_is_one_on_a_clique_and_nan_on_identity():
    m = module("clustering_escape")
    clique = np.ones((4, 4))
    values = m._clustering(clique)
    assert np.all(np.isfinite(values))
    np.testing.assert_allclose(values, 1.0, atol=1e-6)
    scaled = np.full((4, 4), 0.9)
    np.fill_diagonal(scaled, 1.0)
    np.testing.assert_allclose(m._clustering(scaled), 0.9, atol=1e-6)
    identity = np.eye(4)
    assert np.isnan(m._clustering(identity)).all()


def test_leading_factor_loadings_prefer_the_common_block():
    m = module("factor_loading_escape")
    block = np.array([
        [1.0, 0.9, 0.1, 0.0],
        [0.9, 1.0, 0.1, 0.0],
        [0.1, 0.1, 1.0, 0.8],
        [0.0, 0.0, 0.8, 1.0],
    ])
    loadings, gap = m._leading_factor(block)
    assert np.all(np.isfinite(loadings))
    assert np.isfinite(gap) and gap > 0
    # Either block can own the leading factor; within-block loadings should dominate.
    assert max(loadings[0] + loadings[1], loadings[2] + loadings[3]) > min(loadings[0] + loadings[1], loadings[2] + loadings[3])


def test_neighbor_churn_is_zero_when_identities_are_frozen():
    m = module("neighbor_identity_churn")
    corr = np.array([
        [1.0, 0.9, 0.2, 0.1],
        [0.9, 1.0, 0.3, 0.05],
        [0.2, 0.3, 1.0, 0.8],
        [0.1, 0.05, 0.8, 1.0],
    ])
    labels = ["A", "B", "C", "D"]
    sets = m._neighbor_sets(corr, labels, count=2)
    churn = m._churn(sets, sets)
    np.testing.assert_allclose(churn, 0.0)
    swapped = np.array([
        [1.0, 0.1, 0.9, 0.2],
        [0.1, 1.0, 0.05, 0.8],
        [0.9, 0.05, 1.0, 0.3],
        [0.2, 0.8, 0.3, 1.0],
    ])
    moved = m._churn(m._neighbor_sets(swapped, labels, count=2), sets)
    assert np.nanmean(moved) > 0.2


def test_campaign_contract_and_preregistration_hashes():
    dest = ROOT / "experiments" / CAMPAIGN
    slate = json.loads((dest / "idea_slate.json").read_text())
    assert len(slate) == 24
    assert len({row["area"] for row in slate}) == 4
    assert all(row["performance_seen_before_score"] is False for row in slate)
    manifest = load_manifest(dest / "manifest.json")
    assert len(manifest["candidates"]) == 15
    assert len(list(dest.glob("*/preregistration.json"))) == 6
    freeze = json.loads((dest / "implementation_freeze.json").read_text())
    assert freeze["frozen_before_measurement"] is True
    for path, digest in freeze["sha256"].items():
        assert sha256_file(ROOT / path) == digest
    for family in FAMILIES:
        source = (ROOT / f"strategies/generated/{CAMPAIGN}_{family}.py").read_text()
        spec = json.loads((dest / family / "preregistration.json").read_text())
        assert spec["experiment_id"] == f"{CAMPAIGN}_{family}"
        assert spec["code_path"].endswith(f"{family}.py")
        digest = sha256_file(dest / family / "preregistration.json")
        assert digest in source
        assert spec["novelty_axes_changed"]
        assert spec["classification"] == "discovery_hypothesis"
