"""Contract tests for cucumber JSON dispatcher registration and isolation."""

from __future__ import annotations

from pathlib import Path

import tomllib

from pytest_bdd.plugin.cucumber_json_dispatcher.const import CucumberJsonDispatcher

REPO_ROOT = Path(__file__).resolve().parents[4]
DISPATCHER_DIR = REPO_ROOT / "src" / "pytest_bdd" / "plugin" / "cucumber_json_dispatcher"


def test_dispatcher_entry_point_in_pyproject() -> None:
    pyproject_path = REPO_ROOT / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    pytest11 = pyproject["project"]["entry-points"]["pytest11"]

    assert "pytest-bdd-cucumber-json-dispatcher" in pytest11
    assert pytest11["pytest-bdd-cucumber-json-dispatcher"] == ("pytest_bdd.plugin.cucumber_json_dispatcher.entrypoint")


def test_dispatcher_const_values_match_expected() -> None:
    assert str(CucumberJsonDispatcher.Ini.PATH_OPTION) == "cucumber_json_path"
    assert str(CucumberJsonDispatcher.Cli.OPTION_ATTR) == "cucumber_js_json_path"
    assert str(CucumberJsonDispatcher.Cli.FLAG) == "--cucumber-json"


def test_dispatcher_no_cross_plugin_imports() -> None:
    banned_patterns = (
        "from pytest_bdd.plugin.cucumber_json",
        "from pytest_bdd.plugin.cucumber_json_formatter",
        "import pytest_bdd.plugin.cucumber_json ",
    )
    violations: list[str] = []

    for py_file in sorted(DISPATCHER_DIR.rglob("*.py")):
        source = py_file.read_text(encoding="utf-8")
        for pattern in banned_patterns:
            if pattern in source:
                relative_path = py_file.relative_to(REPO_ROOT)
                violations.append(f"{relative_path}: contains {pattern!r}")

    assert violations == []


def test_dispatcher_required_files_exist() -> None:
    for filename in ("__init__.py", "entrypoint.py", "hook.py", "plugin.py"):
        assert (DISPATCHER_DIR / filename).exists()
