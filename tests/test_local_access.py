from __future__ import annotations

import os

import pytest

from factory.runner import (
    PUBLIC_API_KEY,
    ensure_local_data_access,
    has_authenticated_api_key,
    quantiacs_access_mode,
    require_authenticated_api_key,
)


def test_missing_api_key_uses_public_default(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setattr("factory.runner.load_dotenv", lambda path=None: None)

    assert ensure_local_data_access() == PUBLIC_API_KEY == "default"
    assert os.environ["API_KEY"] == "default"
    assert quantiacs_access_mode() == "public_default"
    assert has_authenticated_api_key() is False


def test_blank_api_key_uses_public_default(monkeypatch):
    monkeypatch.setenv("API_KEY", "   ")
    monkeypatch.setattr("factory.runner.load_dotenv", lambda path=None: None)

    assert ensure_local_data_access() == "default"
    assert quantiacs_access_mode() == "public_default"


def test_real_key_is_preserved_but_never_returned_by_mode(monkeypatch):
    monkeypatch.setenv("API_KEY", "participant-secret-example")
    monkeypatch.setattr("factory.runner.load_dotenv", lambda path=None: None)

    assert ensure_local_data_access() == "participant-secret-example"
    assert has_authenticated_api_key() is True
    assert quantiacs_access_mode() == "authenticated"


def test_account_bound_guard_rejects_public_default(monkeypatch):
    monkeypatch.setenv("API_KEY", "default")
    monkeypatch.setattr("factory.runner.load_dotenv", lambda path=None: None)

    with pytest.raises(RuntimeError, match="account-bound"):
        require_authenticated_api_key()
