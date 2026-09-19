"""Authoritative full-history multipass measurement for recursive execution."""
from __future__ import annotations

import json
import os
import time

os.environ.setdefault("API_KEY", "default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats

from strategies.generated import q25_recursive_lattice_execution as s


START = "2016-01-01"
COSTS = (0.0, 0.04, 0.08, 0.12)
FIELDS = ("sharpe_ratio", "equity", "max_drawdown", "avg_turnover", "volatility")


def _run(strategy_fn):
    started = time.perf_counter()
    result = qnbt.backtest(
        competition_type=s.COMPETITION_TYPE,
        load_data=s.load_data,
        lookback_period=s.LOOKBACK_DAYS,
        start_date=START,
        strategy=strategy_fn,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    elapsed = time.perf_counter() - started
    weights = result[0] if isinstance(result, tuple) else result
    return weights, elapsed


def _ladder(data, weights):
    clean = qnout.clean(weights, data, s.COMPETITION_TYPE).sel(time=slice(START, None))
    out = {}
    for cost in COSTS:
        stat = qnstats.calc_stat(
            data,
            clean,
            slippage_factor=cost,
            points_per_year=365,
        ).sel(time=slice(START, None))
        last = stat.isel(time=-1)
        out[f"{cost:.2f}"] = {
            key: float(last.sel(field=key).item())
            for key in FIELDS
            if key in last.field.values
        }
    return out


def main():
    central_weights, central_seconds = _run(s.strategy)
    base_weights, base_seconds = _run(lambda d: s.control_weights(d, "base_lattice"))
    data = qndata.cryptodaily_load_data(min_date="2015-01-01")

    central = _ladder(data, central_weights)
    base = _ladder(data, base_weights)
    c04 = central["0.04"]
    b04 = base["0.04"]

    out = {
        "strategy_id": "q25_recursive_lattice_execution_v1",
        "evaluation": "full_history_multipass",
        "lookback_days": s.LOOKBACK_DAYS,
        "central_runtime_seconds": central_seconds,
        "base_runtime_seconds": base_seconds,
        "central_cost_ladder": central,
        "base_lattice_cost_ladder": base,
        "cost_0_04_comparison": {
            "sharpe_delta": c04.get("sharpe_ratio", 0.0) - b04.get("sharpe_ratio", 0.0),
            "turnover_delta": c04.get("avg_turnover", 0.0) - b04.get("avg_turnover", 0.0),
            "turnover_ratio": c04.get("avg_turnover", 0.0) / max(b04.get("avg_turnover", 0.0), 1e-12),
            "max_drawdown_delta": c04.get("max_drawdown", 0.0) - b04.get("max_drawdown", 0.0),
        },
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
