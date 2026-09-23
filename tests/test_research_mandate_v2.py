from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANDATE = ROOT / "configs" / "research_mandate_v2.yaml"
DOC = ROOT / "docs" / "RESEARCH_MANDATE_V2.md"
AGENTS = ROOT / "AGENTS.md"


def test_mandate_v2_uses_completed_history_and_prequential_evidence():
    p = yaml.safe_load(MANDATE.read_text())
    assert p["version"] == 2
    assert p["data_use"]["completed_history_available_for_research"] is True
    assert p["data_use"]["permanent_historical_holdout_required"] is False
    assert p["evaluation"]["primary_design"] == "rolling_origin_prequential"
    assert p["evaluation"]["minimum_origins"] >= 8
    assert p["recency"]["enabled"] is True
    assert p["recency"]["report_unweighted_alongside_weighted"] is True


def test_mandate_v2_expands_search_without_relaxing_contest_integrity():
    p = yaml.safe_load(MANDATE.read_text())
    h = p["hard_invariants"]
    assert p["exploration"]["broad_search_allowed"] is True
    assert p["exploration"]["parameter_search_allowed"] is True
    assert p["exploration"]["search_ledger_required"] is True
    assert p["robustness"]["parameter_neighborhood_required_for_survivors"] is True
    assert h["sponsor_data_only"] is True
    assert h["long_only"] is True
    assert h["manual_symbols_forbidden"] is True
    assert h["lookahead_forbidden"] is True
    assert h["official_cost_atr_fraction"] == 0.04
    assert h["contest_is_sharpe_strictly_gt"] == 1.0


def test_mandate_v2_optimizes_marginal_portfolio_value():
    p = yaml.safe_load(MANDATE.read_text())
    assert p["portfolio_selection"]["standalone_sharpe_is_not_primary"] is True
    assert p["portfolio_selection"]["require_current_portfolio_comparison"] is True
    assert "marginal_sharpe" in p["portfolio_selection"]["required_metrics"]
    assert p["promotion"]["pareto_frontier_required"] is True
    assert p["promotion"]["no_single_scalar_gate"] is True


def test_agent_entrypoint_declares_v2_normative():
    text = AGENTS.read_text()
    assert "Research Mandate V2" in text
    assert "all completed Sponsor history" in text
    assert "rolling-origin" in text
    assert "permanent historical holdout" in text


def test_normative_doc_preserves_historical_evidence_without_historical_embargo():
    text = DOC.read_text()
    assert "Historical one-shot holdout experiments" in text
    assert "not deleted or rewritten" in text
    assert "ADAPTIVE_REUSE" in text
    assert "LIVE_FORWARD" in text


def test_frontier_contract_no_longer_requires_historical_holdout_embargo():
    frontier = yaml.safe_load((ROOT / "configs" / "research_frontier.yaml").read_text())
    c = frontier["candidate_contract"]
    assert c["allow_completed_history_adaptive_reuse"] is True
    assert c["search_ledger_required"] is True
    assert c["forbid_live_forward_tuning"] is True
    assert "forbid_holdout_tuning" not in c
