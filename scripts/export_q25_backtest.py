#!/usr/bin/env python3
"""Run a Q25 strategy on official Quantiacs data and export dashboard evidence.

This script is deliberately boring about provenance: it loads only Quantiacs data,
imports one repository strategy, applies the official crypto_daily_long cleaner,
requires the official qnt.output.check validator to accept the evaluation weights,
computes the strategy and CRYPTO10 statistics with qnt.stats.calc_stat, writes both
full time-series CSV files, and then builds the Backtest Studio JSON packet.

Example
-------
python scripts/export_q25_backtest.py \
  --strategy strategies/generated/my_candidate.py \
  --output-dir results/backtest/my_candidate

The strategy module must expose ``strategy(data)`` unless ``--function`` names a
different callable. The script does not optimize parameters or choose a candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_backtest_dashboard.py"
COMPETITION_TYPE = "crypto_daily_long"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def import_callable(path: Path, function_name: str):
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    sys.path.insert(0, str(ROOT))
    module_name = "q25_export_" + hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import strategy module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, function_name, None)
    if not callable(fn):
        raise AttributeError(f"{path} does not expose callable {function_name}(data)")
    return fn


def validate_weights(output_module, weights, data) -> None:
    """Require Quantiacs' own competition-output validator to accept weights."""
    output_module.check(weights, data, COMPETITION_TYPE)


def write_stat_csv(stat, path: Path) -> None:
    frame = stat.to_pandas()
    frame.index.name = "time"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path)


def run(args: argparse.Namespace) -> dict[str, str]:
    import qnt.data as qndata
    import qnt.output as qnout
    import qnt.stats as qnstats

    strategy_path = args.strategy.resolve()
    strategy = import_callable(strategy_path, args.function)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Warm-up begins before the official 2016-01-01 in-sample boundary by default.
    data = qndata.cryptodaily_load_data(min_date=args.min_date)
    raw_weights = strategy(data)
    weights = qnout.clean(raw_weights, data, COMPETITION_TYPE)

    end = args.end_date or None
    evaluation_weights = weights.sel(time=slice(args.start_date, end))
    # A dashboard packet is publication evidence, so visualizable performance is
    # downstream of the same output validator used in official Quantiacs examples.
    validate_weights(qnout, evaluation_weights, data)

    strategy_stat = qnstats.calc_stat(
        data,
        evaluation_weights,
        slippage_factor=args.slippage_factor,
        points_per_year=365,
    ).sel(time=slice(args.start_date, end))

    benchmark = qndata.index_load_weights(index_name="CRYPTO10", min_date=args.start_date)
    benchmark = benchmark.sel(time=slice(args.start_date, end))
    benchmark_stat = qnstats.calc_stat(
        data,
        benchmark,
        slippage_factor=args.slippage_factor,
        points_per_year=365,
    ).sel(time=slice(args.start_date, end))

    strategy_csv = args.output_dir / "strategy_stats.csv"
    benchmark_csv = args.output_dir / "crypto10_stats.csv"
    dashboard_json = args.dashboard or args.output_dir / "backtest_dashboard.json"
    manifest_path = args.output_dir / "manifest.json"
    write_stat_csv(strategy_stat, strategy_csv)
    write_stat_csv(benchmark_stat, benchmark_csv)

    commit = args.source_commit or os.getenv("GITHUB_SHA") or None
    try:
        source_path = str(strategy_path.relative_to(ROOT))
    except ValueError:
        source_path = str(strategy_path)

    command = [
        sys.executable,
        str(BUILDER),
        "--input", str(strategy_csv),
        "--benchmark", str(benchmark_csv),
        "--output", str(dashboard_json),
        "--source-label", "Official Quantiacs Q25 single-pass export",
        "--source-path", source_path,
        "--note",
        "Strategy weights passed qnt.output.check and strategy/CRYPTO10 statistics were recomputed from official Quantiacs data; the dashboard is a rendering layer, not a second backtester.",
    ]
    if commit:
        command += ["--source-commit", commit]
    subprocess.run(command, check=True, cwd=ROOT)

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "strategy_path": source_path,
        "strategy_sha256": sha256_file(strategy_path),
        "strategy_function": args.function,
        "competition_type": COMPETITION_TYPE,
        "quantiacs_output_check": "passed",
        "benchmark": "CRYPTO10",
        "data_min_date": args.min_date,
        "evaluation_start": args.start_date,
        "evaluation_end": args.end_date,
        "slippage_factor": args.slippage_factor,
        "points_per_year": 365,
        "source_commit": commit,
        "outputs": {
            "strategy_stats": str(strategy_csv),
            "benchmark_stats": str(benchmark_csv),
            "dashboard": str(dashboard_json),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"manifest": str(manifest_path), "dashboard": str(dashboard_json)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", type=Path, required=True, help="Python strategy module exposing strategy(data)")
    parser.add_argument("--function", default="strategy", help="Callable name inside the strategy module")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dashboard", type=Path, help="Optional dashboard JSON destination")
    parser.add_argument("--min-date", default="2015-01-01", help="Quantiacs load start, including warm-up")
    parser.add_argument("--start-date", default="2016-01-01", help="Q25 evaluation start")
    parser.add_argument("--end-date", help="Optional inclusive evaluation end")
    parser.add_argument("--slippage-factor", type=float, default=0.04, help="ATR-linked transaction-cost factor")
    parser.add_argument("--source-commit", help="Git commit recorded in dashboard provenance")
    args = parser.parse_args()
    outputs = run(args)
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()
