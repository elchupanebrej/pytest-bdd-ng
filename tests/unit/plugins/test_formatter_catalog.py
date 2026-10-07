from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from pytest_cuke.formatter_api import FormatterRequest
from pytest_cuke.formatter_catalog import resolve_formatter_requests


class FormatterHook:
    def __init__(self, requests: tuple[FormatterRequest, ...]) -> None:
        self.requests = requests

    def pytest_cuke_formatter_requests(self, *, config: object) -> tuple[FormatterRequest, ...]:
        del config
        return self.requests


def _config(root: Path, requests: tuple[FormatterRequest, ...]) -> SimpleNamespace:
    return SimpleNamespace(rootpath=root, hook=FormatterHook(requests))


def test_catalog_sorts_requests_and_resolves_paths_from_root(tmp_path: Path) -> None:
    requests = (
        FormatterRequest(name="zeta", command=(sys.executable,), output_path=Path("zeta.ndjson")),
        FormatterRequest(name="alpha", command=(sys.executable,), output_path=Path("alpha.ndjson")),
    )

    resolved = resolve_formatter_requests(_config(tmp_path, requests))

    assert [request.name for request in resolved] == ["alpha", "zeta"]
    assert [request.output_path for request in resolved] == [
        (tmp_path / "alpha.ndjson").resolve(),
        (tmp_path / "zeta.ndjson").resolve(),
    ]
    assert all(request.working_directory == tmp_path.resolve() for request in resolved)


def test_catalog_rejects_duplicate_normalized_destinations(tmp_path: Path) -> None:
    requests = (
        FormatterRequest(name="alpha", command=(sys.executable,), output_path=Path("shared.ndjson")),
        FormatterRequest(name="zeta", command=(sys.executable,), output_path=tmp_path / "shared.ndjson"),
    )

    with pytest.raises(pytest.UsageError, match="same output path"):
        resolve_formatter_requests(_config(tmp_path, requests))


def test_catalog_does_not_check_optional_runtime_when_no_formatter_is_selected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_checked(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("unselected formatter runtime was checked")

    monkeypatch.setattr("pytest_cuke.formatter_catalog.shutil.which", fail_if_checked)

    assert resolve_formatter_requests(_config(tmp_path, ())) == ()


def test_catalog_rejects_multiple_terminal_formatters(tmp_path: Path) -> None:
    requests = (
        FormatterRequest(name="alpha", command=(sys.executable,)),
        FormatterRequest(name="zeta", command=(sys.executable,)),
    )

    with pytest.raises(pytest.UsageError, match="Only one live formatter may write to the terminal"):
        resolve_formatter_requests(_config(tmp_path, requests))
