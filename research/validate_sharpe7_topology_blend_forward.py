"""One-time 2023+ validation/diagnostic for frozen Sharpe7 + topology blend.

The exact 50/50 blend and both member sources are frozen. Results may affect
confidence or submission-slate selection only; they may not trigger formula,
parameter, member, or blend-weight tuning.
"""
from __future__ import annotations

import json
import os

import pandas as pd

os.environ.setdefault("API_KEY", "default")

import qnt.backtester as qnbt
import qnt.data as qndata
import qnt.output as qnout
import qnt.stats as qnstats

from research import measure_sharpe7_topology_blend as blend

BACKTEST_START = "2023-01-01"


def latest_stats(data, weights, start, end, cost):
    w = weights.sel(time=slice(start, end))
    st = qnstats.calc_stat(
        data, w, slippage_factor=cost, points_per_year=365
    ).sel(time=slice(start, end))
    if st.sizes.get("time", 0) == 0:
        return {}
    last = st.isel(time=-1)
    return {
        k: float(last.sel(field=k).item())
        for k in ("sharpe_ratio", "equity", "max_drawdown", "avg_turnover", "volatility")
        if k in last.field.values
    }


def main():
    result = qnbt.backtest(
        competition_type=blend.COMPETITION_TYPE,
        load_data=blend.load_data,
        lookback_period=blend.LOOKBACK_DAYS,
        start_date=BACKTEST_START,
        strategy=blend.strategy,
        analyze=False,
        build_plots=False,
        check_correlation=False,
    )
    if isinstance(result, tuple):
        result = result[0]

    data = qndata.cryptodaily_load_data(min_date="2022-01-01")
    clean = qnout.clean(result, data, blend.COMPETITION_TYPE)

    last_date = str(pd.Timestamp(clean.time.values[-1]).date())
    report = {
        "candidate": "q25_sharpe7_topology_equal_blend_v1",
        "measurement_source_blob_sha": "cd987190e971e6b09ad2514fd1baa237ff8a2879",
        "protected_live_start": "2026-10-01",
        "last_market_date": last_date,
        "validation_2023_2024": {},
        "diagnostic_2025_pre_live": {},
        "calendar_years_at_0_04": {},
        "last_365_days_at_0_04": {},
    }

    for cost in (0.04, 0.10):
        report["validation_2023_2024"][f"{cost:.2f}"] = latest_stats(
            data, clean, "2023-01-01", "2024-12-31", cost
        )
        report["diagnostic_2025_pre_live"][f"{cost:.2f}"] = latest_stats(
            data, clean, "2025-01-01", last_date, cost
        )

    for year in (2023, 2024, 2025, 2026):
        start = f"{year}-01-01"
        end = min(f"{year}-12-31", last_date)
        if start <= last_date:
            report["calendar_years_at_0_04"][str(year)] = latest_stats(
                data, clean, start, end, 0.04
            )

    final = pd.Timestamp(clean.time.values[-1])
    start365 = str((final - pd.Timedelta(days=364)).date())
    report["last_365_days_at_0_04"] = {
        "start": start365,
        "end": last_date,
        "stats": latest_stats(data, clean, start365, last_date, 0.04),
    }

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
