import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "experiments" / "vcb_production_adapter_20260922" / "preregistration.json"
STRATEGY = ROOT / "strategies" / "generated" / "q25_volatility_contraction_breakout.py"


def test_vcb_production_adapter_freeze_is_fail_closed():
    p = json.loads(P.read_text())
    assert p["status"] == "PREREGISTERED"
    assert p["mechanism_frozen"] is True
    assert p["parameters_frozen"] is True
    assert p["production_path"] == "single_pass"
    assert p["cost_atr_percent"] == 4
    assert p["blend_weight_frozen"] == 0.5
    assert p["advancement_gates"]["in_sample_2016_latest_sharpe_gt"] == 1.0
    assert p["advancement_gates"]["contest_check_correlation_enabled"] is True
    assert p["advancement_gates"]["no_post_holdout_retuning"] is True
    assert "formula changes" in p["forbidden"]
    assert "parameter changes" in p["forbidden"]
    assert "post-hoc grids" in p["forbidden"]


def test_frozen_strategy_blob_matches_preregistered_hash():
    p = json.loads(P.read_text())
    # Git blob SHA-1 includes the canonical blob header, unlike a plain file SHA-1.
    content = STRATEGY.read_bytes()
    git_blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
    assert git_blob == p["source_strategy_blob_sha"]
