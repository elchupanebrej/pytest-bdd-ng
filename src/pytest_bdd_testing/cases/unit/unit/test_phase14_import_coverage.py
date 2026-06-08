"""Import smoke coverage for non-exempt pytest_bdd modules."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

_EXCLUDED_PATH_PARTS = {
    "__pycache__",
    "_gherkin_go",
    "compatibility",
    "script",
    "testing",
    "types",
}

_EXCLUDED_PLUGIN_PACKAGES = {
    "cucumber_json",
    "cucumber_json_dispatcher",
    "cucumber_json_formatter",
    "cucumber_junit",
    "cucumber_pretty",
    "cucumber_progress",
    "cucumber_progress_bar",
    "cucumber_snippets",
    "cucumber_summary",
    "cucumber_usage",
    "cucumber_usage_json",
    "gherkin_terminal_reporter",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _is_exempt_module(relative_path: Path) -> bool:
    parts = relative_path.parts
    if relative_path.name == "entrypoint.py":
        return True
    if any(part in _EXCLUDED_PATH_PARTS for part in parts):
        return True
    return len(parts) > 2 and parts[0] == "plugin" and parts[1] in _EXCLUDED_PLUGIN_PACKAGES


def _module_name(relative_path: Path) -> str:
    return "pytest_bdd." + ".".join(relative_path.with_suffix("").parts)


@pytest.mark.parametrize(
    "module_name",
    [
        _module_name(path.relative_to(_repo_root() / "src" / "pytest_bdd"))
        for path in sorted((_repo_root() / "src" / "pytest_bdd").rglob("*.py"))
        if not _is_exempt_module(path.relative_to(_repo_root() / "src" / "pytest_bdd"))
    ],
)
def test_non_exempt_modules_import_cleanly(module_name: str) -> None:
    assert importlib.import_module(module_name).__name__ == module_name
