from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from pytest_cuke.formatter_api import FormatterRequest, FormatterSelection
from pytest_cuke.formatter_catalog import (
    FormatterCatalogError,
    resolve_formatter_requests,
    resolve_replay_formatter_requests,
)


class FormatterHook:
    def __init__(self, requests: tuple[FormatterRequest, ...]) -> None:
        self.requests = requests

    def pytest_cuke_formatter_requests(self, *, config: object) -> tuple[FormatterRequest, ...]:
        del config
        return self.requests


def _config(
    root: Path,
    requests: tuple[FormatterRequest, ...],
    *,
    options: dict[str, str | None] | None = None,
    ini: dict[str, str] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        rootpath=root,
        hook=FormatterHook(requests),
        option=SimpleNamespace(**(options or {})),
        getini=lambda name: (ini or {}).get(name, ""),
    )


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


def test_catalog_rejects_duplicate_reserved_outputs_through_symlink_alias(tmp_path: Path) -> None:
    report_directory = tmp_path / "reports"
    report_directory.mkdir()
    report_directory_alias = tmp_path / "report-alias"
    try:
        report_directory_alias.symlink_to(report_directory, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"directory symlinks are unavailable: {error}")
    requests: tuple[FormatterRequest, ...] = ()
    config = _config(
        tmp_path,
        requests,
        options={"cuke_json": str(report_directory_alias / "report.json"), "cuke_json_backend": "native"},
        ini={"cuke_messages_ndjson": str(report_directory / "report.json")},
    )

    with pytest.raises(
        pytest.UsageError,
        match=r"--cuke-json and --cuke-messages-ndjson resolve to the same output path",
    ):
        resolve_formatter_requests(config)


def test_catalog_rejects_reserved_output_conflict_before_formatter_runtime_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "artifacts").mkdir()
    request = FormatterRequest(
        name="extension-json",
        command=(sys.executable,),
        output_path=Path("artifacts/../artifacts/report.json"),
    )
    config = _config(
        tmp_path,
        (request,),
        options={
            "cuke_json": str(tmp_path / "artifacts" / "report.json"),
            "cuke_json_backend": "native",
        },
    )

    def fail_if_checked(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("formatter runtime was checked before the output collision")

    monkeypatch.setattr("pytest_cuke.formatter_catalog._check_request_runtime", fail_if_checked)

    with pytest.raises(
        pytest.UsageError,
        match=r"'extension-json' and --cuke-json resolve to the same output path",
    ):
        resolve_formatter_requests(config)


@pytest.mark.parametrize(
    ("option_name", "output_flag"),
    (
        ("cuke_html", "--cuke-html"),
        ("cuke_allure", "--cuke-allure"),
        ("xmlpath", "--junitxml"),
    ),
)
def test_catalog_rejects_formatter_conflicts_with_each_reserved_sink(
    tmp_path: Path,
    option_name: str,
    output_flag: str,
) -> None:
    (tmp_path / "artifacts").mkdir()
    request = FormatterRequest(
        name="extension-json",
        command=(sys.executable,),
        output_path=Path("artifacts/../artifacts/report.json"),
    )
    config = _config(
        tmp_path,
        (request,),
        options={option_name: str(tmp_path / "artifacts" / "report.json")},
    )

    with pytest.raises(
        pytest.UsageError,
        match=rf"'extension-json' and {output_flag} resolve to the same output path",
    ):
        resolve_formatter_requests(config)


def test_catalog_rejects_cucumber_junit_conflict_with_native_pytest_junit(tmp_path: Path) -> None:
    (tmp_path / "artifacts").mkdir()
    destination = tmp_path / "artifacts" / "report.xml"
    request = FormatterRequest(
        name="cucumber-junit",
        command=(sys.executable,),
        output_path=Path("artifacts/../artifacts/report.xml"),
    )
    config = _config(tmp_path, (request,), options={"xmlpath": str(destination)})

    with pytest.raises(
        pytest.UsageError,
        match=r"'cucumber-junit' and --junitxml resolve to the same output path",
    ):
        resolve_formatter_requests(config)


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


def test_replay_catalog_loads_selected_factory_and_uses_shared_preflight(tmp_path: Path, monkeypatch) -> None:
    seen: list[FormatterSelection] = []

    class Extension:
        name = "probe"

        @staticmethod
        def load():
            def factory(selection: FormatterSelection) -> FormatterRequest:
                seen.append(selection)
                return FormatterRequest(
                    name=selection.name,
                    command=(sys.executable,),
                    output_path=None,
                    working_directory=selection.working_directory,
                )

            return factory

    monkeypatch.setattr("pytest_cuke.formatter_catalog.entry_points", lambda *, group: [Extension()])
    selection = FormatterSelection("probe", Path("rendered.ndjson"), tmp_path)

    requests = resolve_replay_formatter_requests((selection,), root=tmp_path)

    assert seen == [selection]
    assert requests[0].name == "probe"
    assert requests[0].output_path == (tmp_path / "rendered.ndjson").resolve()
    assert requests[0].working_directory == tmp_path.resolve()


def test_replay_catalog_rejects_destination_conflicts_before_process_start(tmp_path: Path, monkeypatch) -> None:
    class Extension:
        def __init__(self, name: str) -> None:
            self.name = name

        def load(self):
            return lambda selection: FormatterRequest(name=selection.name, command=(sys.executable,))

    monkeypatch.setattr(
        "pytest_cuke.formatter_catalog.entry_points",
        lambda *, group: [Extension("probe"), Extension("probe-copy")],
    )
    selections = (
        FormatterSelection("probe", Path("shared.ndjson"), tmp_path),
        FormatterSelection("probe-copy", Path("shared.ndjson"), tmp_path),
    )

    with pytest.raises(FormatterCatalogError, match=r"Replay formatters 'probe' and 'probe-copy'.*shared.ndjson"):
        resolve_replay_formatter_requests(selections, root=tmp_path)


def test_replay_catalog_rejects_multiple_terminal_formatters(tmp_path: Path, monkeypatch) -> None:
    class Extension:
        def __init__(self, name: str) -> None:
            self.name = name

        def load(self):
            return lambda selection: FormatterRequest(name=selection.name, command=(sys.executable,))

    monkeypatch.setattr(
        "pytest_cuke.formatter_catalog.entry_points",
        lambda *, group: [Extension("probe"), Extension("probe-copy")],
    )
    selections = (
        FormatterSelection("probe", None, tmp_path),
        FormatterSelection("probe-copy", None, tmp_path),
    )

    with pytest.raises(FormatterCatalogError, match="Only one replay formatter may write to the terminal"):
        resolve_replay_formatter_requests(selections, root=tmp_path)


def test_replay_catalog_reports_missing_selected_npm_package(tmp_path: Path, monkeypatch) -> None:
    class Extension:
        name = "probe"

        @staticmethod
        def load():
            return lambda selection: FormatterRequest(
                name=selection.name,
                command=(sys.executable,),
                working_directory=selection.working_directory,
                required_npm_packages=("missing-probe-package",),
            )

    monkeypatch.setattr("pytest_cuke.formatter_catalog.entry_points", lambda *, group: [Extension()])
    monkeypatch.setattr("pytest_cuke.formatter_catalog.shutil.which", lambda executable: "/usr/bin/tool")
    monkeypatch.setattr(
        "pytest_cuke.formatter_catalog.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr="ERR_MODULE_NOT_FOUND"),
    )
    selection = FormatterSelection("probe", Path("rendered.ndjson"), tmp_path)

    with pytest.raises(FormatterCatalogError, match="Replay formatter 'probe' requires npm package"):
        resolve_replay_formatter_requests((selection,), root=tmp_path)
