import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "experiments/lattice_closure_20260921/economic_result.json"


def test_lattice_closure_falsification_is_machine_guarded():
    p = json.loads(RESULT.read_text())
    assert p["status"] == "FALSIFIED_DEVELOPMENT"
    assert p["repaired_source_blob"] == "77552a563db0368ed38a1df24694c015df82e06e"
    assert p["authoritative_workflow_run"] == 35683487432

    gates = p["gates"]
    assert gates["sharpe_0p04_gt_1"]
    assert gates["sharpe_0p08_gt_1"]
    assert gates["sharpe_0p12_gt_1"]
    assert not gates["beats_root_only_0p04"]
    assert not gates["beats_base_in_dev_0p04"]

    sel = p["selection_2016_2022"]
    dev = p["development_2021_2022_0p04"]
    assert sel["closure"]["0.04"] > sel["base_pareto"]["0.04"]
    assert sel["closure"]["0.04"] < sel["root_only"]["0.04"]
    assert dev["closure"] < dev["base_pareto"]

    adjudication = p["adjudication"].lower()
    assert "do not retune" in adjudication
    assert "do not promote" in adjudication
