from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_backtest_dashboard", ROOT / "scripts" / "build_backtest_dashboard.py"
)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def args(strategy: Path, benchmark: Path | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        input=strategy,
        benchmark=benchmark,
        output=Path("unused.json"),
        source_label="test",
        source_path="results/test.csv",
        source_commit="abc123",
        note=None,
    )


def test_builder_emits_q25_scaled_score_from_daily_returns(tmp_path: Path) -> None:
    strategy = tmp_path / "strategy.csv"
    benchmark = tmp_path / "benchmark.csv"
    strategy.write_text(
        "time,equity,relative_return,underwater,volatility,max_drawdown,sharpe_ratio,mean_return,avg_turnover,bias,instruments,avg_holding_time\n"
        "2026-01-01,1,0,0,0.15,0,1.2,0.18,0.04,1,4,8\n"
        "2026-01-02,1.01,0.01,-0.01,0.14,-0.01,1.3,0.19,0.05,1,5,9\n",
        encoding="utf-8",
    )
    benchmark.write_text(
        "time,equity,relative_return,volatility\n"
        "2026-01-01,1,0,0.20\n"
        "2026-01-02,1.005,0.005,0.19\n",
        encoding="utf-8",
    )

    packet = MOD.build(args(strategy, benchmark))

    assert packet["status"] == "available"
    assert packet["period"] == {"start": "2026-01-01", "end": "2026-01-02"}
    assert packet["metrics"]["sharpe"] == 1.3
    assert packet["metrics"]["observations"] == 2
    assert packet["series"][-1]["sharpe"] == 1.3
    assert packet["series"][-1]["mean_return"] == 0.19
    assert packet["series"][-1]["turnover"] == 0.05
    assert packet["series"][-1]["bias"] == 1.0
    assert packet["series"][-1]["instruments"] == 5.0
    assert packet["series"][-1]["avg_holding_time"] == 9.0
    assert packet["live_model"]["strategy_scale"] == 0.1 / 0.14
    assert packet["live_model"]["benchmark_scale"] == 0.1 / 0.19
    assert packet["live_model"]["relative_score"] is not None
    assert packet["series"][-1]["score"] == packet["live_model"]["relative_score"]


def test_builder_does_not_invent_benchmark_or_live_score(tmp_path: Path) -> None:
    strategy = tmp_path / "strategy.csv"
    strategy.write_text(
        "time,equity,relative_return,underwater,volatility,max_drawdown,sharpe_ratio\n"
        "2026-01-01,1,0,0,0.08,0,1.1\n"
        "2026-01-02,1.01,0.01,-0.01,0.08,-0.01,1.2\n",
        encoding="utf-8",
    )

    packet = MOD.build(args(strategy))

    assert packet["series"][-1]["benchmark_equity"] is None
    assert packet["series"][-1]["score"] is None
    assert packet["live_model"]["benchmark_scale"] is None
    assert packet["live_model"]["relative_score"] is None
