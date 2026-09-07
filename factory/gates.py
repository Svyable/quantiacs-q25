"""Hard contest gates + soft cook gates. Parse stats safely; never invent metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class GateResult:
    """Outcome of evaluating hard and/or soft gates."""

    hard_pass: bool
    soft_pass: bool
    hard_failures: list[str] = field(default_factory=list)
    soft_failures: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "hard_pass": self.hard_pass,
            "soft_pass": self.soft_pass,
            "hard_failures": self.hard_failures,
            "soft_failures": self.soft_failures,
            "metrics": self.metrics,
            "notes": self.notes,
        }


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load project YAML configs.

    Prefers PyYAML when installed; otherwise uses a minimal subset parser
    sufficient for configs/contest_q25.yaml and configs/targets.yaml.
    """
    raw = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(raw) or {}
    except ImportError:
        return _minimal_yaml(raw)


def _minimal_yaml(raw: str) -> dict[str, Any]:
    """Tiny YAML subset: nested maps, scalars, booleans, numbers, inline lists."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    def parse_scalar(s: str) -> Any:
        s = s.strip()
        if s == "" or s == "null" or s == "~":
            return None
        if s in ("true", "True"):
            return True
        if s in ("false", "False"):
            return False
        if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"\'":
            return s[1:-1]
        if s.startswith("[") and s.endswith("]"):
            inner = s[1:-1].strip()
            if not inner:
                return []
            return [parse_scalar(p) for p in inner.split(",")]
        try:
            if "." in s or "e" in s.lower():
                return float(s)
            return int(s)
        except ValueError:
            return s

    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        # strip trailing comment when not in quotes
        if " #" in line:
            line = line.split(" #", 1)[0].rstrip()
        indent = len(line) - len(line.lstrip(" "))
        if ":" not in line:
            continue
        key, _, rest = line.lstrip(" ").partition(":")
        key = key.strip()
        rest = rest.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if rest == "" or rest == "|":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(rest)
    return root


def load_hard_config(path: Path | None = None) -> dict[str, Any]:
    return _load_yaml(path or ROOT / "configs" / "contest_q25.yaml")


def load_soft_config(path: Path | None = None) -> dict[str, Any]:
    return _load_yaml(path or ROOT / "configs" / "targets.yaml")


def parse_stats(raw: Any) -> dict[str, float | None]:
    """Safely extract key metrics from heterogeneous backtest outputs.

    Accepts dict-like objects, pandas Series/DataFrame tails, or xarray
    selections. Missing keys become None — never fabricated.
    """
    keys = (
        "sharpe_ratio",
        "sharpe",
        "max_drawdown",
        "equity",
        "relative_return",
        "volatility",
    )
    out: dict[str, float | None] = {k: None for k in ("sharpe_is", "max_drawdown", "equity", "volatility")}

    if raw is None:
        return out

    # dict
    if isinstance(raw, dict):
        data = raw
    else:
        # try .to_dict / last row patterns
        data = {}
        if hasattr(raw, "to_dict"):
            try:
                data = raw.to_dict()
            except Exception:
                data = {}
        if hasattr(raw, "isel") and hasattr(raw, "sel"):
            # xarray DataArray with field dim
            try:
                for field_name in ("sharpe_ratio", "max_drawdown", "equity", "volatility"):
                    try:
                        val = raw.sel(field=field_name).isel(time=-1).item()
                        data[field_name] = val
                    except Exception:
                        pass
            except Exception:
                pass
        if hasattr(raw, "iloc") and hasattr(raw, "columns"):
            try:
                last = raw.iloc[-1]
                data = {str(c): last[c] for c in raw.columns}
            except Exception:
                pass

    def _num(v: Any) -> float | None:
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    sharpe = _num(data.get("sharpe_ratio", data.get("sharpe")))
    out["sharpe_is"] = sharpe
    out["max_drawdown"] = _num(data.get("max_drawdown"))
    out["equity"] = _num(data.get("equity"))
    out["volatility"] = _num(data.get("volatility"))
    # Preserve extras without inventing
    for k, v in data.items():
        if k not in out:
            n = _num(v)
            if n is not None:
                out[k] = n
    return out


def evaluate_hard_gates(
    metrics: dict[str, Any] | None = None,
    *,
    long_only: bool = True,
    liquid_only: bool = True,
    config: dict[str, Any] | None = None,
) -> GateResult:
    """Hard contest eligibility: IS Sharpe > 1.0, long-only, liquid-only.

    Contest gate is 1.0 (not the softer ~0.7 library check).
    """
    cfg = config or load_hard_config()
    gates = cfg.get("hard_gates", {})
    sharpe_min = float(gates.get("sharpe_is_min", 1.0))

    m = dict(metrics or {})
    failures: list[str] = []

    sharpe = m.get("sharpe_is")
    if sharpe is None:
        failures.append("sharpe_is missing (no backtest metrics yet)")
    elif float(sharpe) <= sharpe_min:
        failures.append(f"sharpe_is={sharpe} <= {sharpe_min} (hard gate)")

    if gates.get("long_only", True) and not long_only:
        failures.append("strategy is not long_only")
    if gates.get("liquid_only", True) and not liquid_only:
        failures.append("strategy is not liquid_only (is_liquid)")

    return GateResult(
        hard_pass=len(failures) == 0,
        soft_pass=False,  # caller may merge
        hard_failures=failures,
        metrics=m,
        notes="Hard gates from configs/contest_q25.yaml",
    )


def evaluate_soft_gates(
    metrics: dict[str, Any] | None = None,
    *,
    config: dict[str, Any] | None = None,
) -> GateResult:
    """Soft cook targets: Sharpe>=2, max DD<=40%, equity>=100 (≈100x / ~10000%).

    Equity units: Quantiacs equity is a growth factor. equity>=100 ≈ 100x
    terminal wealth ≈ +9900% ≈ aspirational \"10000%\" return. NOT claimed results.
    """
    cfg = config or load_soft_config()
    soft = cfg.get("soft_cook_gates", {})
    sharpe_min = float(soft.get("sharpe_min", 2.0))
    dd_max = float(soft.get("max_drawdown_max", 0.40))
    equity_min = float(soft.get("equity_min", 100.0))

    m = dict(metrics or {})
    failures: list[str] = []

    sharpe = m.get("sharpe_is")
    if sharpe is None:
        failures.append("sharpe_is missing (no backtest metrics yet)")
    elif float(sharpe) < sharpe_min:
        failures.append(f"sharpe_is={sharpe} < soft {sharpe_min}")

    dd = m.get("max_drawdown")
    if dd is None:
        failures.append("max_drawdown missing (no backtest metrics yet)")
    else:
        # Quantiacs max_drawdown is typically negative (e.g. -0.35) or positive absolute.
        # Accept either: pass if abs(dd) <= dd_max.
        if abs(float(dd)) > dd_max:
            failures.append(f"|max_drawdown|={abs(float(dd))} > soft {dd_max}")

    equity = m.get("equity")
    if equity is None:
        failures.append("equity missing (no backtest metrics yet)")
    elif float(equity) < equity_min:
        failures.append(
            f"equity={equity} < soft {equity_min} "
            f"(growth factor; {equity_min}x ≈ ~10000% return target)"
        )

    return GateResult(
        hard_pass=False,
        soft_pass=len(failures) == 0,
        soft_failures=failures,
        metrics=m,
        notes=(
            "Soft cook gates from configs/targets.yaml — aspirational only; "
            "never claimed without a real run."
        ),
    )


def evaluate_all(
    metrics: dict[str, Any] | None = None,
    *,
    long_only: bool = True,
    liquid_only: bool = True,
) -> GateResult:
    hard = evaluate_hard_gates(metrics, long_only=long_only, liquid_only=liquid_only)
    soft = evaluate_soft_gates(metrics)
    return GateResult(
        hard_pass=hard.hard_pass,
        soft_pass=soft.soft_pass,
        hard_failures=hard.hard_failures,
        soft_failures=soft.soft_failures,
        metrics=dict(metrics or {}),
        notes="Combined hard contest + soft cook evaluation.",
    )


def rank_key(result: GateResult) -> tuple:
    """Sort key: hard pass first, then soft, then sharpe, then equity."""
    m = result.metrics
    sharpe = m.get("sharpe_is")
    equity = m.get("equity")
    return (
        1 if result.hard_pass else 0,
        1 if result.soft_pass else 0,
        float(sharpe) if sharpe is not None else float("-inf"),
        float(equity) if equity is not None else float("-inf"),
    )
