"""Contract tests for allure-formatter CLI entry point."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from pytest_bdd.compatibility.tomllib import loads

pytestmark = [pytest.mark.contract]


def _load_pyproject() -> dict:
    """Load and parse the project pyproject.toml."""
    path = Path(__file__).resolve().parents[5] / "pyproject.toml"
    return loads(path.read_text(encoding="utf-8"))


def test_cli_registered_in_pyproject() -> None:
    """allure-formatter entry exists in pyproject.toml [project.scripts]."""
    config = _load_pyproject()
    scripts = config.get("project", {}).get("scripts", {})
    assert "allure-formatter" in scripts, (
        f"allure-formatter not found in [project.scripts]; found: {list(scripts.keys())}"
    )


def test_converter_has_no_allure_python_runtime_dependency() -> None:
    """Converter stays independent from allure-pytest, and standalone converter doesn't import allure_commons."""
    config = _load_pyproject()
    project = config.get("project", {})
    dependencies = list(project.get("dependencies", []))
    optional = project.get("optional-dependencies", {})
    for values in optional.values():
        dependencies.extend(values)

    forbidden = ("allure-pytest",)
    normalized = [dependency.lower().replace("_", "-") for dependency in dependencies]
    assert not any(dependency.startswith(forbidden_name) for dependency in normalized for forbidden_name in forbidden)

    source_root = Path(__file__).resolve().parents[5] / "src" / "pytest_bdd" / "plugin" / "allure_formatter"

    # Check standalone converter and CLI only
    files_to_check = [*list((source_root / "converter").rglob("*.py")), source_root / "cli.py"]
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in files_to_check)
    assert "allure_commons" not in source_text
    assert "allure_pytest" not in source_text


def test_cli_help_exits_zero() -> None:
    """CLI --help prints usage and exits with code 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest_bdd.plugin.allure_formatter.cli", "--help"],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"--help exited {result.returncode}, stderr: {result.stderr}"
    assert "usage" in result.stdout.lower() or "convert" in result.stdout.lower(), (
        f"Help output missing expected keywords: {result.stdout[:200]}"
    )


def test_cli_nonexistent_file_exits_one() -> None:
    """CLI with nonexistent NDJSON file exits with code 1."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest_bdd.plugin.allure_formatter.cli",
            "/nonexistent/path/messages.ndjson",
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"
    assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


def test_cli_valid_ndjson_succeeds(tmp_path: Path, sample_ndjson: Path) -> None:
    """CLI with valid NDJSON produces output files."""
    output = tmp_path / "allure-output"
    output.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest_bdd.plugin.allure_formatter.cli",
            str(sample_ndjson),
            "--output",
            str(output),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"CLI failed: {result.returncode}, stderr: {result.stderr}"
    json_files = list(output.glob("*.json"))
    assert len(json_files) >= 1, f"Expected output files, found: {json_files}"


def test_cli_resolves_relative_input_to_absolute(tmp_path: Path) -> None:
    """CLI resolves relative input paths to absolute, preventing path traversal."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    ndjson_file = input_dir / "messages.ndjson"
    ndjson_file.write_text(
        '{"testRunStarted":{"id":"r1","timestamp":{"seconds":0,"nanos":0}}}\n',
        encoding="utf-8",
    )
    output = tmp_path / "allure-output"
    output.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest_bdd.plugin.allure_formatter.cli",
            str(Path("..") / "input" / "messages.ndjson"),
            "--output",
            str(output),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
        cwd=str(work_dir),
    )
    assert result.returncode == 0, f"CLI failed: {result.returncode}, stderr: {result.stderr}"
    json_files = list(output.glob("*.json"))
    assert len(json_files) >= 1, f"Expected output files from resolved path, found: {json_files}"
