"""Post-observation explanatory diagnostics for OMNI cross-asset states.

IMPORTANT: this module is diagnostic only. The candidate strategy results were
already observed before these targets were inspected. Nothing emitted here may
be used to select, tune, or rescue a Q25 strategy in the current campaign.

Question: do stock states forecast crypto expected return, or primarily future
risk (realized volatility / downside loss)? We compare fixed, already-observed
states to forward crypto-market targets over predeclared reporting periods.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA_ORIGIN = "2013-01-01"


def _load_wave2():
    path = Path(__file__).parents[1] / "strategies" / "generated" / "omni_cross_asset_wave2_r1.py"
    spec = importlib.util.spec_from_file_location("omni_wave2_diag", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen wave2 implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


W2 = _load_wave2()
FRONTIER = W2.BASE.FRONTIER
R1 = W2.BASE.R1
OMNI = W2.BASE.OMNI


def _future_sum(r: pd.Series, horizon: int) -> pd.Series:
    return sum((r.shift(-k) for k in range(1, horizon + 1)), start=pd.Series(0.0, index=r.index))


def _future_rms(r: pd.Series, horizon: int) -> pd.Series:
    sq = sum((r.shift(-k).pow(2) for k in range(1, horizon + 1)), start=pd.Series(0.0, index=r.index))
    return np.sqrt(sq / float(horizon))


def _future_downside(r: pd.Series, horizon: int) -> pd.Series:
    return sum((r.shift(-k).clip(upper=0.0) for k in range(1, horizon + 1)), start=pd.Series(0.0, index=r.index))


def _state_frame(spx, ndx) -> pd.DataFrame:
    out: dict[str, pd.Series] = {}
    for panel, stocks in (("spx", spx), ("ndx", ndx)):
        ctx = FRONTIER._stock_context(stocks)
        commonality = FRONTIER._commonality(ctx, 126, 63)
        out[f"commonality_{panel}"] = R1._robust_unit(commonality)

        market = ctx["market"]
        assert isinstance(market, pd.Series)
        vol21 = market.rolling(21, min_periods=14).std(ddof=1)
        vol126 = market.rolling(126, min_periods=63).std(ddof=1)
        out[f"vol_term_{panel}"] = R1._robust_unit(np.log((vol21 + 1e-12) / (vol126 + 1e-12)))

        out[f"tail_{panel}"] = FRONTIER._tail_dependence(ctx)["primary"]
        out[f"omni_v1_{panel}"] = OMNI._stock_turbulence(stocks)["turbulence"]

    frame = pd.concat(out, axis=1).sort_index()
    return frame


def _metrics(state: pd.Series, target: pd.Series) -> dict[str, float | int | None]:
    pair = pd.concat({"state": state, "target": target}, axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    if len(pair) < 100:
        return {"n": int(len(pair)), "spearman": None, "pearson": None, "high_minus_low": None}
    qlo = pair["state"].quantile(0.25)
    qhi = pair["state"].quantile(0.75)
    low = pair.loc[pair["state"] <= qlo, "target"]
    high = pair.loc[pair["state"] >= qhi, "target"]
    return {
        "n": int(len(pair)),
        "spearman": float(pair["state"].corr(pair["target"], method="spearman")),
        "pearson": float(pair["state"].corr(pair["target"], method="pearson")),
        "low_quartile_mean": float(low.mean()),
        "high_quartile_mean": float(high.mean()),
        "high_minus_low": float(high.mean() - low.mean()),
    }


def run(output: Path) -> dict[str, object]:
    import qnt.data as qndata

    crypto = qndata.cryptodaily_load_data(min_date=DATA_ORIGIN)
    spx = qndata.stocks.load_spx_data(min_date=DATA_ORIGIN)
    ndx = qndata.stocks.load_ndx_data(min_date=DATA_ORIGIN)

    r = FRONTIER._crypto_market_return(crypto)
    targets = pd.DataFrame({
        "return_1d": _future_sum(r, 1),
        "return_5d": _future_sum(r, 5),
        "rms_vol_5d": _future_rms(r, 5),
        "downside_sum_5d": _future_downside(r, 5),
    })
    states = _state_frame(spx, ndx)

    periods = {
        "selection_2016_2022": ("2016-01-01", "2022-12-31"),
        "spent_2023_2024": ("2023-01-01", "2024-12-31"),
        "diagnostic_2025_plus": ("2025-01-01", None),
    }
    result: dict[str, object] = {
        "status": "POST_OBSERVATION_EXPLANATORY_ONLY",
        "may_drive_current_strategy_selection": False,
        "targets": list(targets.columns),
        "periods": {},
    }
    for period, (start, end) in periods.items():
        state_slice = states.loc[start:end]
        target_slice = targets.loc[start:end]
        cells: dict[str, object] = {}
        for sname in states.columns:
            cells[sname] = {tname: _metrics(state_slice[sname], target_slice[tname]) for tname in targets.columns}
        result["periods"][period] = cells

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True))

    for period in periods:
        print(f"\n=== {period}: high-risk minus low-risk quartile ===")
        cells = result["periods"][period]
        rows=[]
        for sname, metrics in cells.items():
            rows.append((sname,
                         metrics["return_5d"]["high_minus_low"],
                         metrics["rms_vol_5d"]["high_minus_low"],
                         metrics["downside_sum_5d"]["high_minus_low"],
                         metrics["rms_vol_5d"]["spearman"]))
        for row in rows:
            print(f"{row[0]:24s} dRet5={row[1]: .6f} dVol5={row[2]: .6f} dDown5={row[3]: .6f} rhoVol={row[4]: .4f}")
    return result


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", default="results/omni_cross_asset_diagnostics/diagnostics.json")
    args=parser.parse_args()
    run(Path(args.output))


if __name__ == "__main__":
    main()
