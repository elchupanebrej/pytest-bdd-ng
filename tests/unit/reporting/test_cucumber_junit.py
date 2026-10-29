from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from pytest_cuke.cucumber_junit import (
    DEFAULT_CUCUMBER_JUNIT_PATH,
    add_options,
    configured_cucumber_junit_output_value,
)


def test_add_options() -> None:
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    add_options(parser)

    parser.getgroup.assert_called_once_with("cuke", "Cucumber JUnit XML")
    group.addoption.assert_called_once()
    args, kwargs = group.addoption.call_args
    assert "--cuke-junit" in args
    assert kwargs["dest"] == "cuke_junit"
    assert kwargs["nargs"] == "?"
    assert kwargs["const"] == DEFAULT_CUCUMBER_JUNIT_PATH == "cucumber.xml"
    parser.addini.assert_called_once_with("cuke_junit", "Cucumber JUnit XML report path.", default="", type="string")


def test_configured_output_prefers_cli_over_ini() -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(cuke_junit="reports/live.xml"),
        getini=lambda name: "reports/from-ini.xml" if name == "cuke_junit" else "",
    )

    assert configured_cucumber_junit_output_value(config) == "reports/live.xml"


def test_configured_output_uses_ini_when_cli_is_unset() -> None:
    config = SimpleNamespace(
        option=SimpleNamespace(cuke_junit=None),
        getini=lambda name: "reports/from-ini.xml" if name == "cuke_junit" else "",
    )

    assert configured_cucumber_junit_output_value(config) == "reports/from-ini.xml"


def test_configured_output_ignores_empty_selection() -> None:
    config = SimpleNamespace(option=SimpleNamespace(cuke_junit=None), getini=lambda _: "")

    assert configured_cucumber_junit_output_value(config) is None
