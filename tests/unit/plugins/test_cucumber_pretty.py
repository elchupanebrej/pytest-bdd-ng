from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from pytest_cuke.cucumber_pretty import selected_pretty_formatter_requests
from pytest_cuke.formatter_api import FormatterRequest


@pytest.mark.parametrize(
    ("cli_value", "ini_value"),
    [(None, False), (None, "")],
)
def test_pretty_formatter_is_unselected_by_default(cli_value: bool | None, ini_value: bool | str) -> None:
    config = Mock()
    config.getoption.return_value = cli_value
    config.getini.return_value = ini_value

    assert selected_pretty_formatter_requests(config) == ()
    config.getoption.assert_called_once_with("cuke_pretty", default=None)


@pytest.mark.parametrize(
    ("cli_value", "ini_value"),
    [(True, False), (None, True)],
)
def test_selected_pretty_formatter_uses_shared_terminal_runtime(cli_value: bool | None, ini_value: bool) -> None:
    root = Path("consumer root")
    config = Mock()
    config.getoption.return_value = cli_value
    config.getini.return_value = ini_value
    config.rootpath = root

    requests = selected_pretty_formatter_requests(config)

    assert len(requests) == 1
    request = requests[0]
    assert isinstance(request, FormatterRequest)
    assert request.name == "cucumber-pretty"
    assert request.output_path is None
    assert request.bypass_capture is True
    assert request.working_directory == root
    assert request.required_executables == ("node",)
    assert request.required_npm_packages == ("@cucumber/pretty-formatter",)
    assert "PrettyPrinter" in request.command[-1]


def test_pretty_formatter_falls_back_to_ini_when_cli_is_unset() -> None:
    config = SimpleNamespace(
        getoption=lambda name, default=None: default,
        getini=lambda name: True,
        rootpath=Path("consumer"),
    )

    assert selected_pretty_formatter_requests(config)
