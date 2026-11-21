from __future__ import annotations

import json
import runpy
from pathlib import Path
from typing import Any

import pytest
import yaml

pytestmark = pytest.mark.unit

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SHA = "a" * 40


def _aggregator(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.syspath_prepend(str(_PROJECT_ROOT / "scripts"))
    return runpy.run_path(str(_PROJECT_ROOT / "scripts" / "aggregate_env_evidence.py"))


def _workflow_cells() -> list[dict[str, Any]]:
    return [
        {
            "id": "cpython-314-linux",
            "job": "full-matrix",
            "runtime": "CPython",
            "python": "3.14",
            "platform": "linux",
            "tox_envs": ["py314-pytestlatest-coverage-lin", "py314-pytest842-coverage-lin"],
        },
        {
            "id": "remote-socket",
            "job": "remote",
            "runtime": "CPython",
            "python": "3.14",
            "platform": "linux",
            "tox_envs": ["py314-pytestlatest-xdist-remote-socket-lin"],
        },
        {
            "id": "browser-report",
            "job": "browser-report",
            "runtime": "CPython",
            "python": "3.14",
            "platform": "linux",
            "tox_envs": ["py314-pytestlatest-playwright-report"],
        },
        {
            "id": "live-formatters-linux",
            "job": "live-formatters-acceptance",
            "runtime": "CPython",
            "python": "3.13",
            "platform": "linux",
            "tox_envs": ["py313-live-formatters-acceptance-lin"],
        },
        {
            "id": "native-linux",
            "job": "native-go-parser",
            "runtime": "CPython",
            "python": "3.14",
            "platform": "linux",
            "tox_envs": ["native-go-parser"],
        },
        {
            "id": "ruff",
            "job": "quality",
            "runtime": "CPython",
            "python": "3.14",
            "platform": "linux",
            "tox_envs": ["py314-ruff"],
        },
        {
            "id": "struct-bdd-py314-linux",
            "job": "optional-integrations",
            "runtime": "CPython",
            "python": "3.14",
            "platform": "linux",
            "tox_envs": ["py314-struct-bdd"],
        },
    ]


def _write_inventory(tmp_path: Path, cells: list[dict[str, Any]]) -> Path:
    path = tmp_path / "config" / "env-matrix.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.safe_dump(
            {
                "project": {
                    "pytest_floors": {"3.14": "8.4.2", "3.15": "9.1.1"},
                    "evidence": {"aggregate_groups": ["serial", "parallel", "e2e", "external", "quality", "optional"]},
                },
                "workflow_cells": cells,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def _environment(
    *,
    job: str,
    cell: str,
    tox_environment: str,
    group: str,
    pytest_version: str = "8.4.2",
    python: str = "3.14.0",
    selected_tests: int = 2,
    passed_tests: int = 2,
) -> dict[str, Any]:
    version_parts = [int(part) for part in python.split(".")]
    tox_entry = {
        "python": {
            "implementation": "CPython",
            "version_info": [*version_parts, "final", 0],
            "sysplatform": "linux",
        },
        "installed_packages": [f"pytest=={pytest_version}"],
        "result": {"success": True, "exit_code": 0},
        "test": [{"command": ["python", "-m", "pytest", "-q"], "retcode": 0}],
    }
    return {
        "job": job,
        "cell": cell,
        "group": group,
        "tox_environment": tox_environment,
        "git_sha": _SHA,
        "command": ["/usr/bin/tox", "run", "--result-json", "tox-result.json", "-e", tox_environment],
        "runtime": "CPython",
        "python": python,
        "pytest": pytest_version,
        "platform_name": "linux",
        "architecture": "x86_64",
        "job_url": "https://github.com/example/project/actions/runs/1/job/2",
        "run_url": "https://github.com/example/project/actions/runs/1",
        "outcome": "passed",
        "returncode": 0,
        "selected_tests": selected_tests,
        "passed_tests": passed_tests,
        "optional_versions": {
            key: None
            for key in (
                "allure-pytest",
                "gherkin-official",
                "hjson",
                "json5",
                "mcp",
                "mcp-pdb",
                "pandoc",
                "panflute",
                "playwright",
                "pycmarkgfm",
                "pydantic",
                "pypandoc",
                "pyhocon",
                "pytest-xdist",
                "PyYAML",
                "uvicorn",
            )
        },
        "system_tool_versions": {
            key: "4.25.0" if key == "tox" else None
            for key in (
                "tox",
                "node",
                "npm",
                "npx",
                "allure-cli",
                "uv",
                "pandoc",
                "go",
                "native-compiler",
            )
        },
        "system_tool_commands": {
            key: None
            for key in (
                "tox",
                "node",
                "npm",
                "npx",
                "allure-cli",
                "uv",
                "pandoc",
                "go",
                "native-compiler",
            )
        }
        | {"tox": {"executable": "/usr/bin/tox", "argv": ["/usr/bin/tox", "--version"]}},
        "result_json": "tox-results/result.json",
        "tox_result": {"testenvs": {tox_environment: tox_entry}},
    }


def _collect(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    environment: dict[str, Any],
) -> list[str]:
    aggregator = _aggregator(monkeypatch)
    inventory_path = _write_inventory(tmp_path, _workflow_cells())
    evidence_directory = tmp_path / "evidence"
    evidence_directory.mkdir()
    document = {
        "schema_version": 1,
        "git_sha": _SHA,
        "job": environment["job"],
        "cell": environment["cell"],
        "outcome": "passed",
        "environments": [environment],
    }
    (evidence_directory / "evidence-0000.json").write_text(json.dumps(document), encoding="utf-8")
    _summary, errors = aggregator["collect_evidence"](evidence_directory, _SHA, inventory_path)
    assert isinstance(errors, list)
    return errors


def test_aggregation_rejects_pytest_below_the_cpython_floor(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    errors = _collect(
        monkeypatch,
        tmp_path,
        _environment(
            job="full-matrix",
            cell="cpython-314-linux",
            tox_environment="py314-pytestlatest-coverage-lin",
            group="serial",
            pytest_version="8.4.1",
        ),
    )

    assert any("requires at least 8.4.2" in error for error in errors), errors


def test_aggregation_rejects_a_pytest_patch_that_differs_from_the_exact_floor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    errors = _collect(
        monkeypatch,
        tmp_path,
        _environment(
            job="full-matrix",
            cell="cpython-314-linux",
            tox_environment="py314-pytest842-coverage-lin",
            group="serial",
            pytest_version="8.4.3",
        ),
    )

    assert any("requires exactly 8.4.2" in error for error in errors), errors


def test_aggregation_accepts_the_exact_floor_versions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    errors = _collect(
        monkeypatch,
        tmp_path,
        _environment(
            job="full-matrix",
            cell="cpython-314-linux",
            tox_environment="py314-pytest842-coverage-lin",
            group="serial",
            pytest_version="8.4.2",
        ),
    )

    assert not any("requires at least" in error or "requires exactly" in error for error in errors), errors
