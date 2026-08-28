from __future__ import annotations

import io

import pytest
from pytest_bdd.compatibility.tomllib import TOMLDecodeError, load, loads


def test_tomllib_loads() -> None:
    data = loads('title = "TOML Test"\n[table]\nkey = "value"')
    assert data == {"title": "TOML Test", "table": {"key": "value"}}


def test_tomllib_load() -> None:
    stream = io.BytesIO(b'val = 42\nname = "foo"')
    data = load(stream)
    assert data == {"val": 42, "name": "foo"}


def test_tomllib_decode_error() -> None:
    with pytest.raises(TOMLDecodeError):
        loads("invalid toml ====")
