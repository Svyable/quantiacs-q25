"""Single-pass diagnostics and destructive controls for frozen recursive execution."""
from __future__ import annotations

import json
import os

os.environ.setdefault("API_KEY", "default")

import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats

from strategies.generated import q25_recursive_lattice_execution as s


START = "2016-01-01"
COSTS = (0.0, 0.04, 0.08, 0.12)
FIELDS = ("sharpe_ratio", "equity", "max_drawdown", "avg_turnover", "volatility")


def _metrics(data, weights, cost: float):
    clean = qnout.clean(weights, data, s.COMPETITION_TYPE).sel(time=slice(START, None))
    stat = qnstats.calc_stat(
        data,
        clean,
        slippage_factor=cost,
        points_per_year=365,
    ).sel(time=slice(START, None))
    last = stat.isel(time=-1)
    return {
        key: float(last.sel(field=key).item())
        for key in FIELDS
        if key in last.field.values
    }


def main():
    data = qndata.cryptodaily_load_data(min_date="2015-01-01")
    central = s.strategy(data)

    out = {
        "strategy_id": "q25_recursive_lattice_execution_v1",
        "evaluation": "single_pass_diagnostic",
        "central_cost_ladder": {},
        "controls_at_cost_0_04": {},
    }
    for cost in COSTS:
        out["central_cost_ladder"][f"{cost:.2f}"] = _metrics(data, central, cost)

    for mode in ("base_lattice", "fixed_deadband", "hysteresis_atr"):
        out["controls_at_cost_0_04"][mode] = _metrics(
            data, s.control_weights(data, mode), 0.04
        )

    base_turnover = out["controls_at_cost_0_04"]["base_lattice"].get("avg_turnover")
    central_turnover = out["central_cost_ladder"]["0.04"].get("avg_turnover")
    if base_turnover is not None and central_turnover is not None:
        out["turnover_ratio_central_to_base"] = central_turnover / max(base_turnover, 1e-12)

    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
