"""Evaluate the preregistered 5% sparse-trigger VCB x breadth ensemble without retuning.

Preregistration: research/preregistrations/vcb_breadth_sparse_trigger_20260924.md.
Reuses the audited turnover-ensemble evaluator helpers so the only change versus
the falsified 2%-band measurement is the execution operator under test.

Also measures the static 50/50 production adapter
(submissions/q25_vcb_breadth_ensemble_singlepass.py) on the same Sponsor panel:
exact parity with the research composition, prefix/bounded-replay causality and
current-IS 4/8/12% ATR economics.

Gate interpretations fixed before observation:
* "extra-day-lag control must not materially outperform" -> PASS iff the lag
  control's stitched 4%-ATR Sharpe does not exceed the candidate's.
* "no integrity/leakage failure" -> weights contract + prefix invariance.
  Sparse-trigger holdings are path-dependent by design, so bounded (365-day)
  replay agreement is reported as a production diagnostic, not a gate.
"""
from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
os.environ.setdefault("API_KEY", "default")
import qnt.data as qndata
from research.benchmark import QuantiacsEvaluator, check_causality, check_weights, validate_panel
from research.prequential import rolling_origins, exponential_recency_weights
from research.measure_turnover_ensemble import corr, emit, summary, turnover
from strategies.generated import q25_factor_factory as ff
from strategies.generated import q25_volatility_contraction_breakout as vcb
from strategies.generated.q25_vcb_breadth_sparse_trigger_ensemble import TRIGGER_DISPLACEMENT, apply_sparse_trigger

START = "2015-01-01"; IS_START = "2016-01-01"; LIVE_START = "2026-10-01"; COSTS = [.04, .08, .12]
ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "submissions" / "q25_vcb_breadth_ensemble_singlepass.py"
GATES = {"stitched_sharpe_min": 1.65748, "vol10_return_min": .1657, "max_drawdown_min": -.1227, "turnover_reduction_min": .10}


def _adapter():
    spec = importlib.util.spec_from_file_location("q25_vcb_breadth_ensemble_singlepass", ADAPTER)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def _prefix_check(fn, data, full, checkpoints=7):
    cuts = sorted(set(np.linspace(20, data.sizes["time"] - 1, checkpoints, dtype=int)))
    worst = 0.0
    for i in cuts:
        with xr.set_options(use_bottleneck=False):
            got = fn(data.isel(time=slice(0, i + 1)))
        worst = max(worst, float(np.max(np.abs(got.values - full.isel(time=slice(0, i + 1)).values))))
    return {"status": "PASS" if worst <= 1e-10 else "FAIL", "checkpoints": len(cuts), "max_abs_difference": worst}


def _bounded_replay(fn, data, full, checkpoints=7, window=365):
    cuts = sorted(set(np.linspace(window + 30, data.sizes["time"] - 1, checkpoints, dtype=int)))
    diffs = []
    for i in cuts:
        with xr.set_options(use_bottleneck=False):
            got = fn(data.isel(time=slice(i - window + 1, i + 1))).isel(time=-1)
        diffs.append(float(np.max(np.abs(got.values - full.isel(time=i).values))))
    return {"checkpoints": len(cuts), "matching_checkpoints": int(sum(d <= 1e-10 for d in diffs)), "max_abs_difference": max(diffs)}


def _ge(value, threshold, strict=False):
    if value is None or not np.isfinite(value):
        return False
    return bool(value > threshold) if strict else bool(value >= threshold)


def _finite(value):
    value = float(value)
    return value if np.isfinite(value) else None


def _stitch(returns, origins):
    x = pd.concat([returns[f"o{i:02d}"] for i in range(len(origins))]).sort_index()
    return x[~x.index.duplicated(keep="first")]


def main():
    data = qndata.cryptodaily_load_data(min_date=START)
    data = data.sel(time=data.time < np.datetime64(LIVE_START))
    latest = str(data.time.values[-1])[:10]
    validate_panel(data, IS_START, latest)

    bw = ff.FACTORS["breadth_dispersion_interaction"](data); vw = vcb.calculate_weights(data)
    static = .5 * bw + .5 * vw
    liquid = data.sel(field="is_liquid").fillna(0) > 0
    trigger = lambda d: apply_sparse_trigger(.5 * ff.FACTORS["breadth_dispersion_interaction"](d) + .5 * vcb.calculate_weights(d), d.sel(field="is_liquid").fillna(0) > 0)
    sparse = apply_sparse_trigger(static, liquid)
    lag = apply_sparse_trigger(static.shift(time=1).fillna(0), liquid)
    for w in (bw, vw, static, sparse, lag):
        check_weights(w, data)

    adapter = _adapter(); prod = adapter.calculate_weights(data)
    adapter_parity = float(np.max(np.abs(prod.values - static.transpose("time", "asset").values)))
    adapter_causality = check_causality(adapter.calculate_weights, data, full=prod)
    sparse_prefix = _prefix_check(trigger, data, sparse)
    sparse_replay = _bounded_replay(trigger, data, sparse)

    origins = rolling_origins(data.time.values, min_train_days=730, forward_days=90, step_days=90, live_start=LIVE_START)
    folds = [{"id": f"o{i:02d}", "start": o.score_start.strftime("%Y-%m-%d"), "end": o.score_end.strftime("%Y-%m-%d")} for i, o in enumerate(origins)]
    full = [{"id": "current_is", "start": IS_START, "end": latest}]
    e = QuantiacsEvaluator(data)
    pm, pr = e.evaluate(sparse, folds, [.04]); sm, sr = e.evaluate(static, folds, [.04]); lm, lr = e.evaluate(lag, folds, [.04])
    _, cr = e.evaluate(bw, folds, [.04]); _, vr = e.evaluate(vw, folds, [.04])
    pf, _ = e.evaluate(sparse, full, COSTS); sf, _ = e.evaluate(static, full, COSTS); af, _ = e.evaluate(prod, full, COSTS)

    p, s, l, c, v = (_stitch(x, origins) for x in (pr, sr, lr, cr, vr))
    p, s = p.align(s, join="inner"); p, l = p.align(l, join="inner")
    rows = [{"window": o.as_dict(), "sparse_sharpe_4pct": pm[f"o{i:02d}"]["0.04"]["sharpe_ratio"],
             "static_sharpe_4pct": sm[f"o{i:02d}"]["0.04"]["sharpe_ratio"], "lag_control_sharpe_4pct": lm[f"o{i:02d}"]["0.04"]["sharpe_ratio"]}
            for i, o in enumerate(origins)]
    ends = [pd.Timestamp(o.score_end) for o in origins]
    rw = exponential_recency_weights(ends, half_life_days=730, as_of=max(ends))
    osh = pd.Series([r["sparse_sharpe_4pct"] for r in rows], index=pd.DatetimeIndex(ends), dtype=float)

    tstatic = turnover(static.sel(time=slice(IS_START, latest))); tsparse = turnover(sparse.sel(time=slice(IS_START, latest)))
    agg = {"sparse_4pct": summary(p), "static_4pct": summary(s), "lag_control_4pct": summary(l)}
    cur = pf["current_is"]
    gates = {
        "current_is_sharpe_4pct_gt_1": _ge(cur["0.04"]["sharpe_ratio"], 1.0, strict=True),
        "turnover_reduction_ge_10pct": _ge(1 - tsparse / tstatic, GATES["turnover_reduction_min"]),
        "stitched_sharpe_ge_1_65748": _ge(agg["sparse_4pct"]["sharpe"], GATES["stitched_sharpe_min"]),
        "vol10_return_ge_16_57pct": _ge(agg["sparse_4pct"]["vol10_normalized_return"], GATES["vol10_return_min"]),
        "max_drawdown_ge_neg_12_27pct": _ge(agg["sparse_4pct"]["max_drawdown"], GATES["max_drawdown_min"]),
        "current_is_sharpe_12pct_gt_1": _ge(cur["0.12"]["sharpe_ratio"], 1.0, strict=True),
        "integrity_prefix_and_weights": sparse_prefix["status"] == "PASS",
        "lag_control_not_better": _ge(agg["sparse_4pct"]["sharpe"], agg["lag_control_4pct"]["sharpe"] if agg["lag_control_4pct"]["sharpe"] is not None else np.inf),
    }
    out = {
        "schema_version": 1, "experiment_id": "vcb_breadth_sparse_trigger_20260924", "evidence_label": "ADAPTIVE_REUSE",
        "latest_sponsor_date": latest, "origin_count": len(origins),
        "parameters": {"trigger_displacement": TRIGGER_DISPLACEMENT, "cost_atr_percent": [4, 8, 12]},
        "current_is": {"sparse": cur, "static": sf["current_is"], "static_turnover": tstatic, "sparse_turnover": tsparse, "turnover_reduction": 1 - tsparse / tstatic},
        "aggregate": {**agg, "correlation_breadth": corr(p, c), "correlation_vcb": corr(p, v), "correlation_static": corr(p, s),
                      "positive_origin_fraction": float((osh > 0).mean()), "mean_origin_sharpe": _finite(osh.mean()),
                      "scored_origin_count": int(osh.notna().sum()), "recency_weighted_origin_sharpe": _finite((osh * rw).sum())},
        "integrity": {"sparse_prefix": sparse_prefix, "sparse_bounded_replay_diagnostic": sparse_replay},
        "gates": gates, "decision": "ADVANCE" if all(gates.values()) else "FALSIFIED",
        "production_adapter": {"path": str(ADAPTER.relative_to(ROOT)), "max_abs_diff_vs_research_static": adapter_parity,
                               "causality": adapter_causality, "current_is": af["current_is"]},
        "origin_level": rows,
    }
    emit(out)


if __name__ == "__main__":
    main()
