"""

Import smoke coverage for non-exempt pytest_bdd modules.
"""

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
    """
    Test target:
    Verify internal unit invariants and correct behavior of individual code components.
    Test type:
    Unit test
    Test scenario:
    Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    assert importlib.import_module(module_name).__name__ == module_name
