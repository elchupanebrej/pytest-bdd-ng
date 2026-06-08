"""Unit tests for T1 stub correctness.

Validates:
- stubs/py.typed exists (PEP 561 marker)
- src/pytest_bdd/py.typed exists (PEP 561 marker)
- Zero ignore_missing_imports entries in pyproject.toml
- mypy --strict src/ produces zero import-untyped errors
- Critical stub types are importable at type-checking level
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import tomllib

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[5]
PYPROJECT_TOML = REPO_ROOT / "pyproject.toml"


# ── PEP 561 markers ─────────────────────────────────────────────────────


def test_stubs_py_typed_exists() -> None:
    """stubs/py.typed PEP 561 marker file exists."""
    marker = REPO_ROOT / "stubs" / "py.typed"
    assert marker.exists(), f"PEP 561 marker missing at {marker}"


def test_src_pytest_bdd_py_typed_exists() -> None:
    """src/pytest_bdd/py.typed PEP 561 marker file exists."""
    marker = REPO_ROOT / "src" / "pytest_bdd" / "py.typed"
    assert marker.exists(), f"PEP 561 marker missing at {marker}"


# ── No ignore_missing_imports ───────────────────────────────────────────


def test_zero_ignore_missing_imports() -> None:
    """pyproject.toml has zero ignore_missing_imports = true entries."""
    data = tomllib.loads(PYPROJECT_TOML.read_text(encoding="utf-8"))
    overrides = data.get("tool", {}).get("mypy", {}).get("overrides", [])
    for override in overrides:
        if isinstance(override, dict):
            assert not override.get("ignore_missing_imports", False), (
                f"ignore_missing_imports should be removed: {override.get('module', override)}"
            )


# ── No import-untyped errors ────────────────────────────────────────────


def test_mypy_strict_no_import_untyped() -> None:
    """mypy --strict src/ produces zero import-untyped errors."""
    src_dir = str(REPO_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", src_dir, "--no-error-summary"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    import_untyped_lines = [line for line in result.stdout.splitlines() if "import-untyped" in line]
    assert len(import_untyped_lines) == 0, "Zero import-untyped errors expected. Found:\n" + "\n".join(
        import_untyped_lines[:20],
    )


# ── Critical stub type importability ────────────────────────────────────

CRITICAL_TYPES = [
    # (stub_package, symbol_name)
    # pytest
    ("pytest", "Config"),
    ("pytest", "Item"),
    ("pytest", "Stash"),
    ("pytest", "Metafunc"),
    # pluggy
    ("pluggy", "Result"),
    # cucumber_messages
    ("cucumber_messages", "Envelope"),
    ("cucumber_messages", "GherkinDocument"),
    ("cucumber_messages", "Pickle"),
    # gherkin
    ("gherkin", "Parser"),
    # ordered_set
    ("ordered_set", "OrderedSet"),
    # parse
    ("parse", "parse"),
    # decopatch
    ("decopatch", "function_decorator"),
    # makefun
    ("makefun", "wraps"),
    # xdist — workermanage is a stub class
    ("xdist", "workermanage"),
    # cucumber_expressions
    ("cucumber_expressions", "ParameterTypeRegistry"),
    # ci_environment — actually exports detect_ci_environment
    ("ci_environment", "detect_ci_environment"),
    # aiofiles — optional, stub exists with "open"
    ("aiofiles", "open"),
    # hjson / json5 / pyhocon
    ("hjson", "loads"),
    ("json5", "loads"),
    ("pyhocon", "ConfigFactory"),
]


@pytest.mark.parametrize("package_name,attr_name", CRITICAL_TYPES)
def test_critical_stub_defines_symbol(package_name: str, attr_name: str) -> None:
    """Each critical symbol's stub file exists and contains the expected symbol name."""
    stubs_dir = REPO_ROOT / "stubs"

    stub_file = stubs_dir / package_name / "__init__.pyi"
    assert stub_file.exists(), f"Stub file missing: {stub_file}"

    content = stub_file.read_text(encoding="utf-8")
    assert attr_name in content, f"Symbol '{attr_name}' not found in stub {stub_file}. Content preview: {content[:200]}"


# ── Stubs directory structure ───────────────────────────────────────────

EXPECTED_STUB_PACKAGES = [
    "pytest",
    "pluggy",
    "cucumber_messages",
    "gherkin",
    "decopatch",
    "parse",
    "parse_type",
    "ordered_set",
    "makefun",
    "ci_environment",
    "cucumber_expressions",
    "cucumber_tag_expressions",
    "hjson",
    "json5",
    "pyhocon",
    "xdist",
    "aiofiles",
    "coverage",
]


def test_all_expected_stub_packages_exist() -> None:
    """All 18 expected stub packages have __init__.pyi."""
    stubs_dir = REPO_ROOT / "stubs"
    missing = []
    for pkg in EXPECTED_STUB_PACKAGES:
        init_pyi = stubs_dir / pkg / "__init__.pyi"
        if not init_pyi.exists():
            missing.append(pkg)
    assert len(missing) == 0, f"Missing stub packages: {missing}"
