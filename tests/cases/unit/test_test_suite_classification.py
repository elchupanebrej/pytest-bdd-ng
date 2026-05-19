"""Guard semantic test-suite classification contracts."""

from __future__ import annotations

from pathlib import Path

import tomllib

REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_GROUPS = ("unit", "integration", "contract", "e2e", "compat", "perf", "external")
LEGACY_TEST_PATHS = (
    "tests/unit",
    "tests/feature",
    "tests/messages",
    "tests/e2e",
    "tests/support",
)


def _pytest_ini_options() -> dict[str, object]:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["pytest"]["ini_options"]


def _parse_group_path_mapping(mapping: str) -> tuple[str, str]:
    pattern, separator, group = mapping.partition("=")
    assert separator, f"Malformed test_group_paths entry: {mapping!r}"
    return pattern.strip(), group.strip()


def test_pytest_groups_are_canonical_semantic_groups() -> None:
    """Verify configured test groups match the canonical Phase 12 semantic groups."""
    pytest_options = _pytest_ini_options()

    assert tuple(pytest_options["test_group_order"]) == CANONICAL_GROUPS
    assert pytest_options["test_group_default"] == "unit"
    assert set(CANONICAL_GROUPS).issubset({marker.split(":", maxsplit=1)[0] for marker in pytest_options["markers"]})


def test_pytest_collects_only_semantic_test_cases_tree() -> None:
    """Verify pytest collection roots moved from legacy tests/ to tests/cases."""
    pytest_options = _pytest_ini_options()

    assert pytest_options["testpaths"] == ["tests/cases"]


def test_each_semantic_cases_path_maps_to_its_matching_group() -> None:
    """Verify each tests/cases group directory maps to exactly its own semantic marker."""
    pytest_options = _pytest_ini_options()
    mappings = dict(_parse_group_path_mapping(entry) for entry in pytest_options["test_group_paths"])

    assert mappings == {f"tests/cases/{group}/**": group for group in CANONICAL_GROUPS}


def test_group_paths_do_not_point_to_legacy_test_locations() -> None:
    """Verify group mappings no longer classify legacy test paths."""
    pytest_options = _pytest_ini_options()
    mapped_patterns = [_parse_group_path_mapping(entry)[0] for entry in pytest_options["test_group_paths"]]

    offenders = [
        pattern
        for pattern in mapped_patterns
        if any(pattern == legacy or pattern.startswith(f"{legacy}/") for legacy in LEGACY_TEST_PATHS)
    ]

    assert offenders == []


def test_assets_tree_contains_no_collected_python_tests() -> None:
    """Verify tests/assets remains passive fixture data, not collected test modules."""
    assets_root = REPO_ROOT / "tests" / "assets"
    collected_tests = sorted(path.relative_to(REPO_ROOT).as_posix() for path in assets_root.rglob("test_*.py"))

    assert collected_tests == []
