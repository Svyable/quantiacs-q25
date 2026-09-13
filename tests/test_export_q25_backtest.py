from pathlib import Path

import pytest

from scripts.export_q25_backtest import import_callable, sha256_file


def test_import_callable_loads_strategy_from_file(tmp_path: Path):
    path = tmp_path / "candidate.py"
    path.write_text("def strategy(data):\n    return ('ok', data)\n", encoding="utf-8")

    strategy = import_callable(path, "strategy")

    assert strategy("panel") == ("ok", "panel")
    assert sha256_file(path) == sha256_file(path)
    assert len(sha256_file(path)) == 64


def test_import_callable_rejects_missing_entrypoint(tmp_path: Path):
    path = tmp_path / "candidate.py"
    path.write_text("VALUE = 1\n", encoding="utf-8")

    with pytest.raises(AttributeError, match="does not expose callable strategy"):
        import_callable(path, "strategy")
