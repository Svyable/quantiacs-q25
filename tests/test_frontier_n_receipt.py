"""Keep the first Frontier-N observation bound to its unchanged experiment."""
import json

from research.benchmark import ROOT
from research.iteration import load_manifest
from research.preregister import sha256_file


def test_first_measurement_receipt_matches_frozen_sources_and_complete_grid():
    campaign = "frontier_20260912n"
    receipt = json.loads(
        (ROOT / "evidence/measurement_receipts" / f"{campaign}.json").read_text()
    )
    manifest_path = ROOT / "experiments" / campaign / "manifest.json"
    manifest = load_manifest(manifest_path)
    context = receipt["context"]
    assert sha256_file(manifest_path) == context["manifest_sha256"]
    for path in {row["path"] for row in manifest["candidates"]}:
        assert sha256_file(ROOT / path) == context["source_hashes"][path]
    for row in manifest["candidates"]:
        assert sha256_file(ROOT / row["preregistration"]) == receipt["source"]["preregistration_sha256"]

    cells = {row["id"]: row for row in receipt["cells"]}
    declared = {row["id"] for row in manifest["candidates"]} | set(manifest["controls"])
    assert set(cells) == declared
    assert len(cells) == len(receipt["cells"])
    assert all(row["status"] == "COMPLETE" for row in cells.values())
    assert [fold["id"] for fold in context["folds"]] == ["research", "dev"]
    assert context["costs"] == [0.0, 0.04, 0.08, 0.12]
    assert context["status"] == "DEVELOPMENT_ONLY"
    assert context["quantiacs_access_mode"] == "public_default"

    family = receipt["families"][0]
    base = [row["selection_score"] for row in cells.values() if row["mode"] == "base"]
    assert family["best_robust_sharpe"] == max(base)
    assert family["best_robust_sharpe"] < 1.0
    assert family["falsifier_robust_sharpe"] > family["central_robust_sharpe"]
    assert family["ablation_robust_sharpe"] < family["central_robust_sharpe"]
    assert family["completed_cells"] == family["declared_cells"] == len(manifest["candidates"])
    assert not family["pending_cells"] and not family["invalid_cells"]
    assert family["decision_code"] == "FALSIFIED_DEVELOPMENT"
    assert receipt["decision"] == "PROMOTE_ZERO_FREEZE_ALL"
    assert receipt["receipt_status"] == "MEASURED_ARTIFACT_NOT_CANONICAL_EVIDENCE"
