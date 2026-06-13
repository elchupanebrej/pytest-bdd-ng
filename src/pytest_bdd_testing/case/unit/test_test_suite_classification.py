"""Guard semantic test-suite classification contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from pytest_bdd.compatibility.tomllib import loads

REPO_ROOT = Path(__file__).resolve().parents[4]
CANONICAL_GROUPS = ("unit", "integration", "contract", "e2e", "compat", "perf", "external")
LEGACY_TEST_PATHS = (
    "tests/unit",
    "tests/feature",
    "tests/messages",
    "tests/e2e",
    "tests/assets/templates",
)

pytestmark = [pytest.mark.unit]


def _pytest_ini_options() -> dict[str, object]:
    return loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["pytest"]["ini_options"]


def _parse_group_path_mapping(mapping: str) -> tuple[str, str]:
    pattern, separator, group = mapping.partition("=")
    assert separator, f"Malformed test_group_paths entry: {mapping!r}"  # pylint: disable=S101  # intentional assert in test
    return pattern.strip(), group.strip()


def test_pytest_groups_are_canonical_semantic_groups() -> None:
    """
    Verify configured test groups match the canonical Phase 12 semantic groups.

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
    pytest_options = _pytest_ini_options()

    assert tuple(pytest_options["test_group_order"]) == CANONICAL_GROUPS  # pylint: disable=S101  # intentional assert in test
    assert pytest_options["test_group_default"] == "integration"  # pylint: disable=S101  # intentional assert in test
    assert set(CANONICAL_GROUPS).issubset({marker.split(":", maxsplit=1)[0] for marker in pytest_options["markers"]})  # pylint: disable=S101  # intentional assert in test


def test_pytest_collects_only_semantic_test_cases_tree() -> None:
    """
    Verify pytest collection roots moved from legacy tests/ to src/pytest_bdd_testing/cases.

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
    pytest_options = _pytest_ini_options()

    assert pytest_options["testpaths"] == ["src/pytest_bdd_testing/case"]  # pylint: disable=S101  # intentional assert in test


def test_each_semantic_cases_path_maps_to_its_matching_group() -> None:
    """
    Verify each src/pytest_bdd_testing/cases group directory maps to exactly its own semantic marker.

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
    pytest_options = _pytest_ini_options()
    mappings = dict(_parse_group_path_mapping(entry) for entry in pytest_options["test_group_paths"])

    assert mappings == {f"src/pytest_bdd_testing/case/{group}/**": group for group in CANONICAL_GROUPS}  # pylint: disable=S101  # intentional assert in test


def test_group_paths_do_not_point_to_legacy_test_locations() -> None:
    """
    Verify group mappings no longer classify legacy test paths.

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
    pytest_options = _pytest_ini_options()
    mapped_patterns = [_parse_group_path_mapping(entry)[0] for entry in pytest_options["test_group_paths"]]

    offenders = [
        pattern
        for pattern in mapped_patterns
        if any(pattern == legacy or pattern.startswith(f"{legacy}/") for legacy in LEGACY_TEST_PATHS)
    ]

    assert offenders == []  # pylint: disable=S101  # intentional assert in test


def test_assets_tree_contains_no_collected_python_tests() -> None:
    """
    Verify testing/assets remains passive fixture data, not collected test modules.

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
    assets_root = REPO_ROOT / "src" / "pytest_bdd" / "testing" / "assets"
    collected_tests = sorted(path.relative_to(REPO_ROOT).as_posix() for path in assets_root.rglob("test_*.py"))

    assert collected_tests == []  # pylint: disable=S101  # intentional assert in test
