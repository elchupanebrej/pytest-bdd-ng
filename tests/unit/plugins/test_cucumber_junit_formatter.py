from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from pytest_cuke.cucumber_junit_formatter import (
    replay_cucumber_junit_formatter_request,
    selected_cucumber_junit_formatter_requests,
)
from pytest_cuke.formatter_api import FormatterSelection


def test_live_request_uses_selected_path_and_official_runtime(tmp_path: Path) -> None:
    config = SimpleNamespace(
        rootpath=tmp_path,
        option=SimpleNamespace(cuke_junit="reports/live.xml"),
        getini=lambda _: "",
    )

    (request,) = selected_cucumber_junit_formatter_requests(config)

    assert request.name == "cucumber-junit"
    assert request.output_path == Path("reports/live.xml")
    assert request.working_directory == tmp_path
    assert request.required_executables == ("node", "npm")
    assert request.required_npm_packages == ("@cucumber/junit-xml-formatter",)


def test_live_request_is_absent_when_not_selected(tmp_path: Path) -> None:
    config = SimpleNamespace(rootpath=tmp_path, option=SimpleNamespace(cuke_junit=None), getini=lambda _: "")

    assert selected_cucumber_junit_formatter_requests(config) == ()


def test_replay_request_preserves_selection(tmp_path: Path) -> None:
    selection = FormatterSelection(
        name="cucumber-junit",
        destination=Path("reports/replayed.xml"),
        working_directory=tmp_path,
    )

    request = replay_cucumber_junit_formatter_request(selection)

    assert request.name == "cucumber-junit"
    assert request.output_path == selection.destination
    assert request.working_directory == selection.working_directory
