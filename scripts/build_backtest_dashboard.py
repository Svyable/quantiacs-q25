#!/usr/bin/env python3
"""Build docs/data/backtest_dashboard.json from exported Quantiacs statistics.

Input is a CSV produced from ``qnt.stats.calc_stat(...).to_pandas()``. The
builder does not run a strategy, infer missing metrics, or fabricate a series.
If a Crypto10 benchmark CSV is supplied it is joined by date and the Q25
relative-score fields are emitted. All derived values are deterministic and
based only on the supplied files.

Examples
--------
python scripts/build_backtest_dashboard.py --input results/stats.csv
python scripts/build_backtest_dashboard.py --input results/stats.csv \
    --benchmark results/crypto10_stats.csv --source-commit "$GITHUB_SHA"
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "data" / "backtest_dashboard.json"


def finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path} contains no data rows")
    return rows


def date_key(row: dict[str, str]) -> str:
    for key in ("time", "date", "index", "Unnamed: 0"):
        value = row.get(key)
        if value:
            return value[:10]
    raise ValueError("CSV needs a time/date/index column")


def last_value(rows: list[dict[str, str]], field: str) -> float | None:
    for row in reversed(rows):
        value = finite(row.get(field))
        if value is not None:
            return value
    return None


def mean_value(rows: list[dict[str, str]], field: str) -> float | None:
    values = [v for row in rows if (v := finite(row.get(field))) is not None]
    return sum(values) / len(values) if values else None


def metric(rows: list[dict[str, str]], field: str, *, average: bool = False) -> float | None:
    return mean_value(rows, field) if average else last_value(rows, field)


def monthly_returns(series: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_month: dict[tuple[int, int], list[float]] = {}
    for row in series:
        value = finite(row.get("strategy_equity"))
        if value is None:
            continue
        d = datetime.fromisoformat(row["date"])
        by_month.setdefault((d.year, d.month), []).append(value)
    if not by_month:
        return []
    month_ret: dict[tuple[int, int], float] = {}
    keys = sorted(by_month)
    prev_close: float | None = None
    for key in keys:
        close = by_month[key][-1]
        if prev_close is not None and prev_close != 0:
            month_ret[key] = close / prev_close - 1.0
        prev_close = close
    years = range(min(y for y, _ in keys), max(y for y, _ in keys) + 1)
    return [{"year": year, "months": [month_ret.get((year, month)) for month in range(1, 13)]} for year in years]


def build(args: argparse.Namespace) -> dict[str, Any]:
    rows = load_csv(args.input)
    benchmark_rows = load_csv(args.benchmark) if args.benchmark else []
    benchmark = {date_key(row): row for row in benchmark_rows}

    strategy_vol = metric(rows, "volatility")
    benchmark_vol = metric(benchmark_rows, "volatility") if benchmark_rows else None
    strategy_scale = min(0.1 / strategy_vol, 1.0) if strategy_vol and strategy_vol > 0 else None
    benchmark_scale = min(0.1 / benchmark_vol, 1.0) if benchmark_vol and benchmark_vol > 0 else None

    scaled_strategy = 1.0
    scaled_benchmark = 1.0
    can_scale_strategy = strategy_scale is not None
    can_scale_benchmark = benchmark_scale is not None and bool(benchmark_rows)
    series: list[dict[str, Any]] = []
    for row in rows:
        date = date_key(row)
        equity = finite(row.get("equity"))
        if equity is None:
            continue
        b_row = benchmark.get(date, {})
        b_equity = finite(b_row.get("equity"))
        strategy_return = finite(row.get("relative_return"))
        benchmark_return = finite(b_row.get("relative_return"))

        if can_scale_strategy:
            if strategy_return is None:
                can_scale_strategy = False
            else:
                scaled_strategy *= 1.0 + strategy_scale * strategy_return
        if can_scale_benchmark:
            if benchmark_return is None:
                can_scale_benchmark = False
            else:
                scaled_benchmark *= 1.0 + benchmark_scale * benchmark_return

        score = None
        if can_scale_strategy and can_scale_benchmark:
            score = scaled_strategy / max(scaled_benchmark, 1.0)
        series.append({
            "date": date,
            "strategy_equity": equity,
            "benchmark_equity": b_equity,
            "score": score,
            "drawdown": finite(row.get("underwater")),
            "rolling_volatility": finite(row.get("volatility")),
            "sharpe": finite(row.get("sharpe_ratio")),
            "mean_return": finite(row.get("mean_return")),
            "turnover": finite(row.get("avg_turnover")),
        })
    if not series:
        raise ValueError("No finite equity observations found in input CSV")

    first_eq, last_eq = series[0]["strategy_equity"], series[-1]["strategy_equity"]
    total_return = last_eq / first_eq - 1.0 if first_eq else None
    strategy_equity_scaled = scaled_strategy if can_scale_strategy else None
    benchmark_equity_scaled = scaled_benchmark if can_scale_benchmark else None
    relative_score = series[-1]["score"] if series else None

    metrics = {
        "sharpe": metric(rows, "sharpe_ratio"),
        "total_return": total_return,
        "mean_return": metric(rows, "mean_return"),
        "volatility": strategy_vol,
        "max_drawdown": metric(rows, "max_drawdown"),
        "avg_turnover": metric(rows, "avg_turnover"),
        "bias": metric(rows, "bias", average=True),
        "instruments": metric(rows, "instruments", average=True),
        "avg_holding_time": metric(rows, "avg_holding_time"),
        "observations": len(series),
    }
    note = args.note or "Rendered from committed Quantiacs calc_stat output; missing fields are preserved as null. Q25 scaled score requires relative_return in both strategy and benchmark exports."
    return {
        "schema_version": 1,
        "status": "available",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "period": {"start": series[0]["date"], "end": series[-1]["date"]},
        "source": {"label": args.source_label, "path": args.source_path or str(args.input), "commit": args.source_commit, "note": note},
        "metrics": metrics,
        "live_model": {
            "strategy_scale": strategy_scale,
            "benchmark_scale": benchmark_scale,
            "strategy_equity": strategy_equity_scaled,
            "benchmark_equity": benchmark_equity_scaled,
            "relative_score": relative_score,
        },
        "series": series,
        "monthly_returns": monthly_returns(series),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV from qnt.stats.calc_stat(...).to_pandas()")
    parser.add_argument("--benchmark", type=Path, help="Optional Crypto10 benchmark stats CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--source-label", default="Quantiacs calc_stat export")
    parser.add_argument("--source-path")
    parser.add_argument("--source-commit")
    parser.add_argument("--note")
    args = parser.parse_args()
    payload = build(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
