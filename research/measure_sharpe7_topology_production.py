"""Measure the exact self-contained Sharpe7 + topology production artifact."""
from __future__ import annotations

import json
import os

os.environ.setdefault("API_KEY", "default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats

from submissions import q25_sharpe7_topology_blend_multipass as candidate

START = "2016-01-01"
COSTS = (0.0, 0.04, 0.08, 0.10, 0.12)


def main():
    result = qnbt.backtest(
        competition_type=candidate.COMPETITION_TYPE,
        load_data=candidate.load_data,
        lookback_period=candidate.LOOKBACK_DAYS,
        start_date=START,
        strategy=candidate.strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    if isinstance(result, tuple):
        result = result[0]

    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    clean = qnout.clean(result, data, candidate.COMPETITION_TYPE).sel(
        time=slice(START, None)
    )
    report = {
        "candidate": "q25_sharpe7_topology_equal_blend_v1",
        "artifact": "submissions/q25_sharpe7_topology_blend_multipass.py",
        "evaluation": "full_history_multipass_production_artifact",
        "cost_ladder": {},
    }
    for cost in COSTS:
        stat = qnstats.calc_stat(
            data, clean, slippage_factor=cost, points_per_year=365
        ).sel(time=slice(START, None))
        last = stat.isel(time=-1)
        report["cost_ladder"][f"{cost:.2f}"] = {
            field: float(last.sel(field=field).item())
            for field in (
                "sharpe_ratio",
                "equity",
                "max_drawdown",
                "avg_turnover",
                "volatility",
            )
            if field in last.field.values
        }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
