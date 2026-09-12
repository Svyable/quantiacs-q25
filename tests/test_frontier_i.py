"""Frontier-I synthetic mechanics and frozen-contract tests; no return evidence."""
import json
import numpy as np
import pytest
import xarray as xr
from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest
from research.preregister import sha256_file
from test_frontier_c import panel

CAMPAIGN = "frontier_20260912i"
FAMILIES = ("conditional_decoupling", "partial_edge_entropy", "trend_dispersion_gate")


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


def test_precision_transform_is_symmetric_and_not_marginal_corr():
    m = module("conditional_decoupling")
    rng = np.random.default_rng(9)
    x = rng.normal(size=200)
    y = 0.8 * x + rng.normal(scale=0.5, size=200)
    z = 0.8 * y + rng.normal(scale=0.5, size=200)
    import pandas as pd
    corr, partial = m._corr_partial(pd.DataFrame({"x": x, "y": y, "z": z}))
    np.testing.assert_allclose(corr, corr.T)
    np.testing.assert_allclose(partial, partial.T)
    np.testing.assert_allclose(np.diag(partial), 1.0)
    assert abs(partial[0, 2]) < abs(corr[0, 2])


def test_edge_entropy_distinguishes_concentrated_from_diffuse_dependence():
    m = module("partial_edge_entropy")
    concentrated = np.array([[1.0, .9, .05, .05], [.9, 1.0, .05, .05], [.05, .05, 1.0, .9], [.05, .05, .9, 1.0]])
    diffuse = np.array([[1.0, .33, .33, .33], [.33, 1.0, .33, .33], [.33, .33, 1.0, .33], [.33, .33, .33, 1.0]])
    labels = ["A", "B", "C", "D"]
    assert m._concentration(concentrated, labels).mean() > m._concentration(diffuse, labels).mean()


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
        source = (ROOT / rows[0]["path"]).read_text()
        assert digest in source
        assert "PENDING RESEARCH STRATEGY" in source
    for family in ("signed_partial_balance", "precision_bridge", "cohort_residual_divergence"):
        spec = json.loads((dest / family / "preregistration.json").read_text())
        assert spec["status"] == "PREREGISTERED_NOT_IMPLEMENTED"
        assert spec["code_path"] is None
