"""Render Idea -> strategy Python source (from template)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .ideas import Idea

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
GENERATED = ROOT / "strategies" / "generated"

# Map family -> which strategy body block to inject
FAMILY_BODIES: dict[str, str] = {
    "sma_cross": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    sma_fast = qnta.sma(close, {sma_fast})
    sma_slow = qnta.sma(close, {sma_slow})
    weights = xr.where(sma_fast > sma_slow, 1.0, 0.0) * is_liquid
    return weights
''',
    "breakout": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    high = data.sel(field="high")
    # Rolling max of prior highs (exclude current bar via shift)
    prior_high = high.shift(time=1)
    donchian = prior_high.rolling(time={breakout_lookback}).max()
    exit_level = close.shift(time=1).rolling(time={exit_lookback}).min()
    long_sig = xr.where(close >= donchian, 1.0, 0.0)
    # Hold until close breaks exit lookback low — simplified binary long
    hold = xr.where(close >= exit_level, 1.0, 0.0)
    weights = long_sig * hold * is_liquid
    return weights
''',
    "rsi_bands": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    rsi = qnta.rsi(close, {rsi_period})
    # Long when oversold or in recovery band below rsi_high
    weights = xr.where(rsi < {rsi_low}, 1.0, 0.0) * is_liquid
    # Optionally keep exposure until RSI exceeds mid — simple binary
    mid = ({rsi_low} + {rsi_high}) / 2.0
    weights = xr.where(rsi < mid, 1.0, weights) * is_liquid
    return weights
''',
    "bollinger": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    mid = qnta.sma(close, {bb_period})
    # Use std of close as band width proxy
    std = close.rolling(time={bb_period}).std()
    lower = mid - float({bb_std}) * std
    weights = xr.where(close <= lower, 1.0, 0.0) * is_liquid
    return weights
''',
    "inv_vol_trend": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    sma_fast = qnta.sma(close, {sma_fast})
    sma_slow = qnta.sma(close, {sma_slow})
    ret = qnta.change(close)
    vol = ret.rolling(time={vol_lookback}).std()
    inv_vol = 1.0 / (vol + 1e-8)
    trend = xr.where(sma_fast > sma_slow, 1.0, 0.0)
    raw = trend * inv_vol * is_liquid
    # Normalize across assets per day (avoid div0)
    total = raw.sum(dim="asset")
    weights = xr.where(total > 0, raw / total, 0.0)
    return weights
''',
    "rel_strength": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    mom = close / close.shift(time={mom_lookback}) - 1.0
    mom = mom * is_liquid
    # Rank and take top_k liquid names
    rank = mom.rank(dim="asset", ascending=False)
    weights = xr.where(rank <= {top_k}, 1.0, 0.0) * is_liquid
    total = weights.sum(dim="asset")
    weights = xr.where(total > 0, weights / total, 0.0)
    return weights
''',
    "volume_spike": '''\
    close = data.sel(field="close")
    vol = data.sel(field="vol")
    is_liquid = data.sel(field="is_liquid")
    sma_fast = qnta.sma(close, {sma_fast})
    sma_slow = qnta.sma(close, {sma_slow})
    vol_ma = qnta.sma(vol, {vol_ma})
    trend = xr.where(sma_fast > sma_slow, 1.0, 0.0)
    spike = xr.where(vol > vol_ma, 1.0, 0.0)
    weights = trend * spike * is_liquid
    return weights
''',
    "signal_intersection": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    sma_fast = qnta.sma(close, {sma_fast})
    sma_slow = qnta.sma(close, {sma_slow})
    rsi = qnta.rsi(close, {rsi_period})
    sma_signal = xr.where(sma_fast > sma_slow, 1.0, 0.0) * is_liquid
    rsi_signal = xr.where((rsi < {rsi_low}) | (rsi > {rsi_high}), 1.0, 0.0)
    return sma_signal * rsi_signal
''',
    # Fallbacks for families used as tags
    "ema_cross": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    ema_fast = qnta.ema(close, {sma_fast})
    ema_slow = qnta.ema(close, {sma_slow})
    weights = xr.where(ema_fast > ema_slow, 1.0, 0.0) * is_liquid
    return weights
''',
    "ts_momentum": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    mom = close / close.shift(time={sma_slow}) - 1.0
    weights = xr.where(mom > 0, 1.0, 0.0) * is_liquid
    return weights
''',
    "return_zscore": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    ret = qnta.change(close)
    mu = ret.rolling(time={rsi_period}).mean()
    sd = ret.rolling(time={rsi_period}).std()
    z = (ret - mu) / (sd + 1e-8)
    weights = xr.where(z < -1.0, 1.0, 0.0) * is_liquid
    return weights
''',
    "vol_premia_proxy": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    ret = qnta.change(close)
    vol = ret.rolling(time={vol_lookback}).std()
    # Prefer lower-vol liquid names with positive trend
    sma = qnta.sma(close, {sma_slow})
    trend = xr.where(close > sma, 1.0, 0.0)
    inv = 1.0 / (vol + 1e-8)
    raw = trend * inv * is_liquid
    total = raw.sum(dim="asset")
    return xr.where(total > 0, raw / total, 0.0)
''',
    "volume_persistence": '''\
    close = data.sel(field="close")
    vol = data.sel(field="vol")
    is_liquid = data.sel(field="is_liquid")
    vol_ma = qnta.sma(vol, {vol_ma})
    persist = xr.where(vol > vol_ma, 1.0, 0.0)
    trend = xr.where(close > qnta.sma(close, {sma_slow}), 1.0, 0.0)
    return persist * trend * is_liquid
''',
    "atr_scaled": '''\
    close = data.sel(field="close")
    high = data.sel(field="high")
    low = data.sel(field="low")
    is_liquid = data.sel(field="is_liquid")
    tr = xr.ufuncs.maximum(high - low, xr.ufuncs.maximum(abs(high - close.shift(time=1)), abs(low - close.shift(time=1))))
    atr = tr.rolling(time={vol_lookback}).mean()
    sma_fast = qnta.sma(close, {sma_fast})
    sma_slow = qnta.sma(close, {sma_slow})
    trend = xr.where(sma_fast > sma_slow, 1.0, 0.0)
    inv = 1.0 / (atr + 1e-8)
    raw = trend * inv * is_liquid
    total = raw.sum(dim="asset")
    return xr.where(total > 0, raw / total, 0.0)
''',
    "vol_target": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    sma_fast = qnta.sma(close, {sma_fast})
    sma_slow = qnta.sma(close, {sma_slow})
    ret = qnta.change(close)
    vol = ret.rolling(time={vol_lookback}).std()
    trend = xr.where(sma_fast > sma_slow, 1.0, 0.0)
    scale = 0.02 / (vol + 1e-8)  # crude daily vol target proxy
    raw = trend * scale * is_liquid
    total = raw.sum(dim="asset")
    return xr.where(total > 0, raw / total, 0.0)
''',
    "range_break": '''\
    close = data.sel(field="close")
    high = data.sel(field="high")
    low = data.sel(field="low")
    is_liquid = data.sel(field="is_liquid")
    rng = (high - low).rolling(time={breakout_lookback}).mean()
    compress = rng < rng.shift(time={breakout_lookback})
    breakout = close >= high.shift(time=1).rolling(time={breakout_lookback}).max()
    weights = xr.where(compress & breakout, 1.0, 0.0) * is_liquid
    return weights
''',
    "efficiency_ratio": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    change = abs(close - close.shift(time={sma_slow}))
    volatility = abs(qnta.change(close)).rolling(time={sma_slow}).sum()
    er = change / (volatility + 1e-8)
    weights = xr.where(er > 0.5, 1.0, 0.0) * is_liquid
    return weights
''',
    "equal_blend": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    sma_fast = qnta.sma(close, {sma_fast})
    sma_slow = qnta.sma(close, {sma_slow})
    rsi = qnta.rsi(close, {rsi_period})
    t = xr.where(sma_fast > sma_slow, 1.0, 0.0)
    r = xr.where(rsi < {rsi_low}, 1.0, 0.0)
    weights = ((t + r) / 2.0) * is_liquid
    return weights
''',
    "rank_blend": '''\
    close = data.sel(field="close")
    is_liquid = data.sel(field="is_liquid")
    mom = close / close.shift(time={mom_lookback}) - 1.0
    rsi = qnta.rsi(close, {rsi_period})
    # Prefer high momentum and moderate RSI
    score = mom.rank(dim="asset") + (-abs(rsi - 50)).rank(dim="asset")
    score = score * is_liquid
    rank = score.rank(dim="asset", ascending=False)
    weights = xr.where(rank <= {top_k}, 1.0, 0.0) * is_liquid
    total = weights.sum(dim="asset")
    return xr.where(total > 0, weights / total, 0.0)
''',
}


def _format_body(family: str, params: dict[str, Any]) -> str:
    """Fill family body with params; missing keys get sensible defaults."""
    defaults: dict[str, Any] = {
        "sma_fast": 15,
        "sma_slow": 34,
        "rsi_period": 14,
        "rsi_low": 30,
        "rsi_high": 70,
        "bb_period": 20,
        "bb_std": 2.0,
        "vol_lookback": 20,
        "breakout_lookback": 20,
        "exit_lookback": 10,
        "mom_lookback": 30,
        "top_k": 5,
        "vol_ma": 20,
    }
    merged = {**defaults, **params}
    # Integer-ize known int params for clean source
    int_keys = {
        "sma_fast",
        "sma_slow",
        "rsi_period",
        "rsi_low",
        "rsi_high",
        "bb_period",
        "vol_lookback",
        "breakout_lookback",
        "exit_lookback",
        "mom_lookback",
        "top_k",
        "vol_ma",
    }
    for k in int_keys:
        if k in merged:
            merged[k] = int(round(float(merged[k])))
    if "bb_std" in merged:
        merged["bb_std"] = float(merged["bb_std"])

    template = FAMILY_BODIES.get(family) or FAMILY_BODIES["sma_cross"]
    try:
        return template.format(**merged)
    except KeyError:
        # Fallback: sma_cross with whatever we have
        return FAMILY_BODIES["sma_cross"].format(**merged)


def _safe_module_name(idea: Idea) -> str:
    raw = f"gen_{idea.id}_g{idea.generation}"
    name = re.sub(r"[^a-zA-Z0-9_]", "_", raw)
    if name[0].isdigit():
        name = "s_" + name
    return name.lower()


def render_source(idea: Idea, template_path: Path | None = None) -> str:
    """Render full strategy .py source for an Idea."""
    tpl_path = template_path or (TEMPLATES / "strategy_multipass.py.tpl")
    tpl = tpl_path.read_text(encoding="utf-8")
    raw_body = _format_body(idea.family, idea.params)

    # Convert `return <expr>` into `weights = <expr>` (skip no-op `return weights`),
    # then append multipass last-day slice.
    lines: list[str] = []
    for line in raw_body.splitlines():
        stripped = line.strip()
        if stripped.startswith("return "):
            expr = stripped[len("return ") :]
            indent = line[: len(line) - len(line.lstrip())]
            if expr == "weights":
                # already assigned earlier in the body
                continue
            lines.append(f"{indent}weights = {expr}")
        else:
            lines.append(line)
    body = "\n".join(lines) + "\n"
    body += (
        '    if "time" in getattr(weights, "dims", ()):\n'
        "        weights = weights.isel(time=-1)\n"
        "    return weights\n"
    )

    params_comment = ", ".join(f"{k}={v!r}" for k, v in sorted(idea.params.items()))
    source = (
        tpl.replace("{{STRATEGY_NAME}}", idea.name)
        .replace("{{IDEA_ID}}", idea.id)
        .replace("{{DESK_ID}}", idea.desk_id)
        .replace("{{FAMILY}}", idea.family)
        .replace("{{THESIS}}", idea.thesis.replace("\n", " "))
        .replace("{{PARAMS_COMMENT}}", params_comment)
        .replace("{{STRATEGY_BODY}}", body.rstrip() + "\n")
    )
    return source



def render_to_file(idea: Idea, out_dir: Path | None = None) -> Path:
    """Write rendered strategy under strategies/generated/ and return path."""
    out = out_dir or GENERATED
    out.mkdir(parents=True, exist_ok=True)
    module = _safe_module_name(idea)
    path = out / f"{module}.py"
    path.write_text(render_source(idea), encoding="utf-8")
    return path
