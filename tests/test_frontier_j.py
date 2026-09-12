"""Frontier-J synthetic mechanics and frozen-contract tests; no return evidence."""
import json
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest
from research.preregister import sha256_file
from test_frontier_c import panel

CAMPAIGN = "frontier_20260912j"
FAMILIES = ("positive_edge_shedding", "spectral_diversification_gate", "spectral_residual_momentum")
RESERVES = ("nearest_peer_detachment", "subspace_rotation_opportunity", "edge_sign_flip_persistence")


def module(family):
    return load_module(ROOT / f"strategies/generated/{CAMPAIGN}_{family}.py")


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("mode", ("base", "ablation", "falsifier"))
@pytest.mark.parametrize("window", (42, 63, 84))
def test_full_grid_causal_admissible_and_order_invariant(family, mode, window):
    data = panel(n=720)
    m = module(family)
    fn = lambda d: m.strategy(d, {"window": window, "top_k": 5}, mode)
    weights = fn(data)
    assert check_causality(fn, data, weights)["status"] == "PASS"
    check_weights(weights, data)
    assert np.count_nonzero(weights.values) > 0
    assert float(weights.max()) <= 0.25 + 1e-12
    assert float(weights.sum("asset").max()) <= 1.0 + 1e-12
    shuffled = data.sel(asset=list(reversed(data.asset.values)))
    xr.testing.assert_allclose(fn(shuffled).sel(asset=data.asset), weights)


@pytest.mark.parametrize("family", FAMILIES)
def test_controls_change_deployed_capital(family):
    data = panel(n=720)
    m = module(family)
    base = m.strategy(data)
    assert float(abs(base - m.strategy(data, mode="ablation")).sum()) > 0.001
    assert float(abs(base - m.strategy(data, mode="falsifier")).sum()) > 0.001


@pytest.mark.parametrize("family", FAMILIES)
def test_future_asset_cannot_change_existing_history(family):
    data = panel(n=720)
    absent = xr.full_like(data.isel(asset=[0]), np.nan).assign_coords(asset=["FUTURE"])
    absent.loc[dict(field="is_liquid")] = 0
    expanded = xr.concat([data, absent], dim="asset")
    m = module(family)
    xr.testing.assert_allclose(m.strategy(expanded).sel(asset=data.asset), m.strategy(data))


def test_positive_edge_stat_ignores_negative_edges():
    m = module("positive_edge_shedding")
    corr = np.array([[1.0, .8, -.5], [.8, 1.0, .2], [-.5, .2, 1.0]])
    node, level = m._positive_stats(corr, ["A", "B", "C"])
    assert node["A"] > node["C"]
    assert level > 0


def test_leading_share_detects_factor_concentration():
    m = module("spectral_diversification_gate")
    diffuse = np.eye(4)
    concentrated = np.full((4, 4), .8)
    np.fill_diagonal(concentrated, 1.0)
    assert m._leading_share(concentrated) > m._leading_share(diffuse)


def test_spectral_projection_changes_identity_signal():
    m = module("spectral_residual_momentum")
    rng = np.random.default_rng(12)
    common = rng.normal(size=120)
    frame = pd.DataFrame({
        "A": common + rng.normal(scale=.3, size=120),
        "B": .8 * common + rng.normal(scale=.4, size=120),
        "C": -.2 * common + rng.normal(scale=.8, size=120),
        "D": rng.normal(size=120),
    })
    base = m._spectral_score(frame, "base")
    ablation = m._spectral_score(frame, "ablation")
    falsifier = m._spectral_score(frame, "falsifier")
    assert not np.allclose(base, ablation)
    assert not np.allclose(base, falsifier)


def test_campaign_contract_and_preregistration_hashes():
    dest = ROOT / "experiments" / CAMPAIGN
    slate = json.loads((dest / "idea_slate.json").read_text())
    assert len(slate) == 24
    assert len({row["area"] for row in slate}) == 4
    assert all(row["performance_seen_before_score"] is False for row in slate)
    assert all(sum(row["scores"].values()) == row["priority_score"] for row in slate)
    preregs = list(dest.glob("*/preregistration.json"))
    assert len(preregs) == 6
    manifest = load_manifest(dest / "manifest.json")
    assert len(manifest["candidates"]) == 15
    assert {row["family"] for row in manifest["candidates"]} == set(FAMILIES)
    assert manifest["automatic_promotion"] is False
    freeze = json.loads((dest / "implementation_freeze.json").read_text())
    assert freeze["frozen_before_measurement"] is True
    for family in FAMILIES:
        rows = [row for row in manifest["candidates"] if row["family"] == family]
        digest = sha256_file(dest / family / "preregistration.json")
        assert all(row["preregistration_sha256"] == digest for row in rows)
        assert freeze["preregistration_sha256"][family] == digest
        source = (ROOT / rows[0]["path"]).read_text()
        assert digest in source
        assert "PENDING RESEARCH STRATEGY" in source
        assert sorted({row["params"]["window"] for row in rows if row["mode"] == "base"}) == [42, 63, 84]
    for family in RESERVES:
        spec = json.loads((dest / family / "preregistration.json").read_text())
        assert spec["status"] == "PREREGISTERED_NOT_IMPLEMENTED"
        assert spec["code_path"] is None
        assert freeze["preregistration_sha256"][family] == sha256_file(dest / family / "preregistration.json")
