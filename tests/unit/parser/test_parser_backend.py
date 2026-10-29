from __future__ import annotations

import logging
from typing import Any

import pytest

from pytest_cuke.parser_backend import ParserBackend, resolve_parser_backend


class _Config:
    def __init__(self, option: str | None, ini: str = "auto") -> None:
        self.option = option
        self.ini = ini

    def getoption(self, name: str) -> str | None:
        assert name == "cuke_parser"
        return self.option

    def getini(self, name: str) -> str:
        assert name == "cuke_parser"
        return self.ini


@pytest.mark.parametrize(
    ("option", "ini", "expected"),
    [
        ("python", "go", ParserBackend.PYTHON),
        ("go", "python", ParserBackend.GO),
        (None, "go", ParserBackend.GO),
        (None, "auto", ParserBackend.AUTO),
        (None, "python", ParserBackend.PYTHON),
    ],
)
def test_parser_option_overrides_ini_and_ini_selects_when_option_is_unset(
    option: str | None,
    ini: str,
    expected: ParserBackend,
) -> None:
    assert resolve_parser_backend(_Config(option, ini)) is expected


def test_unknown_parser_value_warns_and_uses_auto(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        actual = resolve_parser_backend(_Config("native", "python"))

    assert actual is ParserBackend.AUTO
    assert "native" in caplog.text
    assert "auto" in caplog.text


@pytest.mark.parametrize("value", ["AUTO", "Python", "GO"])
def test_parser_value_is_case_insensitive(value: str) -> None:
    assert resolve_parser_backend(_Config(value)) is ParserBackend(value.lower())


def test_config_without_pytest_option_methods_uses_auto() -> None:
    class PartialConfig:
        def getini(self, _name: str) -> str:
            raise ValueError("ini unavailable")

    assert resolve_parser_backend(PartialConfig()) is ParserBackend.AUTO


def test_no_config_uses_auto() -> None:
    assert resolve_parser_backend(None) is ParserBackend.AUTO


def test_parser_backend_accepts_config_protocol() -> None:
    class ConfigLike:
        def getoption(self, _name: str) -> Any:
            return None

        def getini(self, _name: str) -> str:
            return "python"

    assert resolve_parser_backend(ConfigLike()) is ParserBackend.PYTHON
