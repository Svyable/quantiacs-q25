"""Frontier-N premeasurement mechanics and provenance tests; no economic claims."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from research.benchmark import ROOT, check_causality, check_weights, load_module
from research.iteration import load_manifest
from research.preregister import sha256_file
from test_frontier_c import panel

CAMPAIGN = "frontier_20260913n"
FAMILIES = (
    "absorption_release_pressure",
    "elasticity_rank_migration",
    "directional_elasticity_asymmetry",
)
CENTRAL = {
    "absorption_release_pressure": 42,
    "elasticity_rank_migration": 42,
    "directional_elasticity_asymmetry": 63,
}
GRIDS = {
    "absorption_release_pressure": [21, 42, 63],
    "elasticity_rank_migration": [21, 42, 63],
    "directional_elasticity_asymmetry": [42, 63, 84],
}


def module(family):
    return load_module(ROOT / f"strategies/generated/{CAMPAIGN}_{family}.py")


def git_blob_sha1(path):
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("mode", ("base", "ablation", "falsifier"))
def test_central_modes_are_causal_admissible_and_order_invariant(family, mode):
    data = panel(n=720)
    m = module(family)
    window = CENTRAL[family]
    fn = lambda d: m.strategy(d, {"window": window, "top_k": 5}, mode)
    weights = fn(data)
    assert check_causality(fn, data, weights)["status"] == "PASS"
    check_weights(weights, data)
    assert np.count_nonzero(weights.values) > 0
    assert float(weights.min()) >= -1e-12
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
def test_ineligibility_is_persistent_zero_until_next_rebalance(family):
    m = module(family)
    idx = pd.date_range("2026-01-05", periods=10, freq="D")
    score = pd.DataFrame({"A": 1.0, "B": 0.5}, index=idx)
    liquid = pd.DataFrame(True, index=idx, columns=score.columns)
    liquid.loc[idx[2], "A"] = False
    weights = m._allocate(score, liquid, idx, 2).to_pandas()
    assert weights.loc[idx[2], "A"] == 0.0
    assert weights.loc[idx[3], "A"] == 0.0
    assert weights.loc[idx[4], "A"] == 0.0
    assert weights.loc[idx[7], "A"] > 0.0


def test_campaign_contract_is_frozen_before_market_measurement():
    dest = ROOT / "experiments" / CAMPAIGN
    manifest = load_manifest(dest / "manifest.json")
    freeze = json.loads((dest / "implementation_freeze.json").read_text())
    slate = json.loads((dest / "idea_slate.json").read_text())

    assert len(slate["ideas"]) == 24
    assert slate["performance_seen_before_score"] is False
    assert "frontier_20260913m reserve returns have NOT been observed" in slate["contamination_boundary"]
    scored = sorted(slate["ideas"], key=lambda row: (-row["priority_score"], row["id"]))
    assert {row["id"] for row in scored[:3]} == set(FAMILIES)
    assert all(sum(row["scores"].values()) == row["priority_score"] for row in slate["ideas"])

    assert len(manifest["candidates"]) == 15
    assert {row["family"] for row in manifest["candidates"]} == set(FAMILIES)
    assert set(manifest["controls"]) == {"equal_liquid", "inverse_vol_trend", "persistent_low_vol"}
    assert manifest["selection_folds"] == ["research", "dev"]
    assert manifest["automatic_promotion"] is False
    assert manifest["preexisting_unobserved_queue_at_preregistration"] == ["frontier_20260913m"]
    assert "forward_validation_2023_2024" in manifest["spent_validation_evidence"]

    assert freeze["frozen_before_measurement"] is True
    assert freeze["market_returns_observed_before_freeze"] is False
    assert freeze["activation_type"] == "NEW_PREREGISTERED_FRONTIER"
    assert freeze["mutation_after_observation"] == "FORBIDDEN"
    assert freeze["preexisting_unobserved_queue_at_freeze"] == ["frontier_20260913m"]
    assert freeze["candidate_count"] == 15

    for family in FAMILIES:
        prereg = dest / family / "preregistration.json"
        digest = sha256_file(prereg)
        rows = [row for row in manifest["candidates"] if row["family"] == family]
        assert all(row["preregistration_sha256"] == digest for row in rows)
        assert freeze["preregistration_sha256"][family] == digest
        assert git_blob_sha1(prereg) == freeze["preregistration_git_blob_sha1"][family]
        source_path = ROOT / rows[0]["path"]
        assert digest in source_path.read_text()
        assert git_blob_sha1(source_path) == freeze["strategy_git_blob_sha1"][family]
        assert "from research" not in source_path.read_text()
        assert "from factory" not in source_path.read_text()
        spec = json.loads(prereg.read_text())
        assert spec["status"] == "PREREGISTERED_NOT_IMPLEMENTED"
        assert spec["validation"].startswith("2023-2024 is SPENT")
        assert sorted({row["params"]["window"] for row in rows if row["mode"] == "base"}) == GRIDS[family]


@pytest.mark.parametrize("family", FAMILIES)
def test_every_declared_cell_runs_on_synthetic_panel(family):
    dest = ROOT / "experiments" / CAMPAIGN
    manifest = load_manifest(dest / "manifest.json")
    data = panel(n=720)
    m = module(family)
    for row in [row for row in manifest["candidates"] if row["family"] == family]:
        weights = m.strategy(data, row["params"], row["mode"])
        check_weights(weights, data)
        assert float(weights.min()) >= -1e-12
        assert float(weights.max()) <= 0.25 + 1e-12
        assert float(weights.sum("asset").max()) <= 1.0 + 1e-12
