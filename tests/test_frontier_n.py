"""Frontier-N premeasurement mechanics and provenance tests; no economic claims."""
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
FAMILIES = ("wick_rejection_pressure", "range_close_disagreement", "impact_decay_persistence")
CENTRAL = {"wick_rejection_pressure":42, "range_close_disagreement":63, "impact_decay_persistence":42}
GRIDS = {"wick_rejection_pressure":[21,42,63], "range_close_disagreement":[42,63,84], "impact_decay_persistence":[21,42,63]}

def module(family):
    return load_module(ROOT / f"strategies/generated/{CAMPAIGN}_{family}.py")

@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("mode", ("base","ablation","falsifier"))
def test_central_modes_are_causal_admissible_and_order_invariant(family, mode):
    data=panel(n=720); m=module(family)
    fn=lambda d: m.strategy(d, {"window":CENTRAL[family],"top_k":5}, mode)
    weights=fn(data)
    assert check_causality(fn,data,weights)["status"]=="PASS"
    check_weights(weights,data)
    assert np.count_nonzero(weights.values)>0
    assert float(weights.max()) <= 0.25 + 1e-12
    assert float(weights.sum("asset").max()) <= 1.0 + 1e-12
    shuffled=data.sel(asset=list(reversed(data.asset.values)))
    xr.testing.assert_allclose(fn(shuffled).sel(asset=data.asset),weights)

@pytest.mark.parametrize("family", FAMILIES)
def test_controls_change_deployed_capital(family):
    d=panel(n=720); m=module(family)
    base=m.strategy(d); ab=m.strategy(d,mode="ablation"); false=m.strategy(d,mode="falsifier")
    assert float(abs(base-ab).sum()) > 0.001
    assert float(abs(base-false).sum()) > 0.001

@pytest.mark.parametrize("family", FAMILIES)
def test_ineligibility_is_persistent_zero_until_next_rebalance(family):
    m=module(family); idx=pd.date_range("2026-01-05",periods=10,freq="D")
    score=pd.DataFrame({"A":1.0,"B":0.5},index=idx); liquid=pd.DataFrame(True,index=idx,columns=score.columns)
    liquid.loc[idx[2],"A"]=False
    w=m._allocate(score,liquid,idx,2).to_pandas()
    assert w.loc[idx[2],"A"]==0.0 and w.loc[idx[3],"A"]==0.0 and w.loc[idx[4],"A"]==0.0
    assert w.loc[idx[7],"A"]>0.0

def test_daily_bar_primitives_actually_change_scores():
    d=panel(n=720)
    wick=module("wick_rejection_pressure"); base,_=wick.signals(d,42,"base"); changed=d.copy(); changed.loc[dict(field="low")]=changed.sel(field="low")*0.97; altered,_=wick.signals(changed,42,"base"); assert float((base-altered).abs().fillna(0).sum().sum())>0
    rc=module("range_close_disagreement"); base,_=rc.signals(d,63,"base"); changed=d.copy(); changed.loc[dict(field="high")]=changed.sel(field="high")*1.02; altered,_=rc.signals(changed,63,"base"); assert float((base-altered).abs().fillna(0).sum().sum())>0
    impact=module("impact_decay_persistence"); base,_=impact.signals(d,42,"base"); changed=d.copy(); factors=xr.DataArray(np.linspace(0.8,1.2,d.sizes["asset"]),dims=("asset",),coords={"asset":d.asset}); changed.loc[dict(field="vol")]=changed.sel(field="vol")*factors; altered,_=impact.signals(changed,42,"base"); assert float((base-altered).abs().fillna(0).sum().sum())>0

def test_campaign_contract_hashes_and_spent_validation_boundary():
    dest=ROOT/"experiments"/CAMPAIGN; manifest=load_manifest(dest/"manifest.json")
    assert len(manifest["candidates"])==15
    assert {row["family"] for row in manifest["candidates"]}==set(FAMILIES)
    assert set(manifest["controls"])=={"equal_liquid","inverse_vol_trend","persistent_low_vol"}
    assert manifest["selection_folds"]==["research","dev"] and manifest["automatic_promotion"] is False
    assert "forward_validation_2023_2024" in manifest["spent_validation_evidence"]
    freeze=json.loads((dest/"implementation_freeze.json").read_text())
    assert freeze["frozen_before_measurement"] is True and freeze["market_returns_observed_before_freeze"] is False
    assert freeze["activation_type"]=="NEW_PREREGISTERED_FRONTIER"
    assert freeze["known_before_freeze"]["frontier_20260912m_workflow_run"]==34736196639
    slate=json.loads((dest/"idea_slate.json").read_text())
    assert slate["ideation_count"]==24 and slate["preregister_count"]==6 and slate["implement_count"]==3
    assert all(row["performance_seen_before_score"] is False for row in slate["ideas"])
    for family in FAMILIES:
        prereg=dest/family/"preregistration.json"; digest=sha256_file(prereg); rows=[r for r in manifest["candidates"] if r["family"]==family]
        assert all(r["preregistration_sha256"]==digest for r in rows)
        assert freeze["preregistration_sha256"][family]==digest
        assert digest in (ROOT/rows[0]["path"]).read_text()
        assert sorted({r["params"]["window"] for r in rows if r["mode"]=="base"})==GRIDS[family]
        assert json.loads(prereg.read_text())["validation"].startswith("2023-2024 is SPENT")
    for family in ("body_range_efficiency","wick_volume_disagreement","range_impact_convexity"):
        prereg=dest/family/"preregistration.json"
        assert sha256_file(prereg)==freeze["reserve_preregistration_sha256"][family]
        assert json.loads(prereg.read_text())["status"]=="PREREGISTERED_NOT_IMPLEMENTED"
