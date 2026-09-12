"""Frontier-K premeasurement mechanics and provenance tests; no economic claims."""
import json

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest
from research.preregister import sha256_file
from test_frontier_c import panel

CAMPAIGN = "frontier_20260912k"
FAMILIES = (
    "nearest_peer_detachment",
    "subspace_rotation_opportunity",
    "cohort_residual_divergence",
)


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
    assert float(weights.max()) <= 0.25 + 1e-12
    assert float(weights.sum("asset").max()) <= 1.0 + 1e-12
    shuffled = data.sel(asset=list(reversed(data.asset.values)))
    xr.testing.assert_allclose(fn(shuffled).sel(asset=data.asset), weights)


@pytest.mark.parametrize("family", FAMILIES)
def test_controls_change_deployed_capital_on_synthetic_panel(family):
    data = panel(n=720)
    m = module(family)
    base = m.strategy(data)
    ablation = m.strategy(data, mode="ablation")
    falsifier = m.strategy(data, mode="falsifier")
    assert float(abs(base - ablation).sum()) > 0.001
    assert float(abs(base - falsifier).sum()) > 0.001


@pytest.mark.parametrize("family", FAMILIES)
def test_future_ineligible_asset_cannot_change_existing_history(family):
    data = panel(n=720)
    absent = xr.full_like(data.isel(asset=[0]), np.nan).assign_coords(asset=["FUTURE"])
    absent.loc[dict(field="is_liquid")] = 0
    expanded = xr.concat([data, absent], dim="asset")
    m = module(family)
    xr.testing.assert_allclose(m.strategy(expanded).sel(asset=data.asset), m.strategy(data))


@pytest.mark.parametrize("family", FAMILIES)
def test_ineligibility_is_persistent_zero_until_next_rebalance(family):
    m = module(family)
    idx = pd.date_range("2026-01-05", periods=10, freq="D")  # starts Monday
    score = pd.DataFrame({"A": 1.0, "B": 0.5}, index=idx)
    liquid = pd.DataFrame(True, index=idx, columns=score.columns)
    liquid.loc[idx[2], "A"] = False
    weights = m._allocate(score, liquid, idx, 2).to_pandas()
    assert weights.loc[idx[2], "A"] == 0.0
    # eligibility recovery on Thursday must not revive Monday's stale target
    assert weights.loc[idx[3], "A"] == 0.0
    assert weights.loc[idx[4], "A"] == 0.0
    # next Monday may set a new target
    assert weights.loc[idx[7], "A"] > 0.0


def test_nearest_peer_falsifier_rotates_only_eligible_finite_values():
    m = module("nearest_peer_detachment")
    values = pd.Series({"A": 1.0, "B": 2.0, "C": 3.0, "D": np.nan})
    eligible = pd.Series({"A": True, "B": False, "C": True, "D": True})
    rotated = m._rotate_eligible(values, eligible)
    assert rotated["B"] == values["B"]
    assert np.isnan(rotated["D"])
    assert rotated["A"] == 3.0 and rotated["C"] == 1.0


def test_subspace_projector_is_basis_sign_invariant():
    m = module("subspace_rotation_opportunity")
    corr = np.array([
        [1.0, .7, .2, -.1],
        [.7, 1.0, .25, 0.0],
        [.2, .25, 1.0, .4],
        [-.1, 0.0, .4, 1.0],
    ])
    p, concentration = m._top_projector(corr)
    assert np.allclose(p, p.T)
    assert np.allclose(p @ p, p)
    assert 0 < concentration <= 1


def test_cohort_peer_corr_excludes_self():
    m = module("cohort_residual_divergence")
    x = np.linspace(-1, 1, 21)
    path = pd.DataFrame({"A": x, "B": x, "C": -x})
    corr = m._peer_corr(path, ["A", "B", "C"])
    # For A, peers B and C cancel to a flat path; self is not leaking into peers.
    assert np.isnan(corr["A"])


def test_campaign_contract_hashes_and_spent_validation_boundary():
    dest = ROOT / "experiments" / CAMPAIGN
    manifest = load_manifest(dest / "manifest.json")
    assert len(manifest["candidates"]) == 15
    assert {row["family"] for row in manifest["candidates"]} == set(FAMILIES)
    assert set(manifest["controls"]) == {"equal_liquid", "inverse_vol_trend", "persistent_low_vol"}
    assert manifest["selection_folds"] == ["research", "dev"]
    assert manifest["automatic_promotion"] is False
    assert "forward_validation_2023_2024" in manifest["spent_validation_evidence"]

    freeze = json.loads((dest / "implementation_freeze.json").read_text())
    assert freeze["frozen_before_measurement"] is True
    assert freeze["activation_type"] == "PREEXISTING_UNMEASURED_RESERVES"
    for family in FAMILIES:
        prereg = dest / family / "preregistration.json"
        digest = sha256_file(prereg)
        rows = [row for row in manifest["candidates"] if row["family"] == family]
        assert all(row["preregistration_sha256"] == digest for row in rows)
        assert freeze["preregistration_sha256"][family] == digest
        source = (ROOT / rows[0]["path"]).read_text()
        assert digest in source
        spec = json.loads(prereg.read_text())
        assert spec["status"] == "IMPLEMENTED_PENDING_EVIDENCE"
        assert spec["validation"].startswith("2023-2024 is SPENT")
        assert spec["prior_preregistration_sha256"] == freeze["prior_reserve_sha256"][family]
        assert sorted({row["params"]["window"] for row in rows if row["mode"] == "base"}) == [42, 63, 84]
