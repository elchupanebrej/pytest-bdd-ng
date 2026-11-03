from __future__ import annotations

import importlib.metadata
from pathlib import Path

from packaging.requirements import Requirement
from pytest_cuke.compatibility.tomllib import loads

from pytest import mark

pytestmark = mark.unit

REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def _load_optional_dependencies() -> dict[str, list[str]]:
    assert PYPROJECT_PATH.is_file(), f"pyproject.toml not found at {PYPROJECT_PATH}"
    data = loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    return data.get("project", {}).get("optional-dependencies", {})


def test_packaging_extras_defined_in_pyproject_toml() -> None:
    optional_deps = _load_optional_dependencies()

    assert "async" in optional_deps, "Expected 'async' extra in [project.optional-dependencies]"
    assert "full" in optional_deps, "Expected 'full' extra in [project.optional-dependencies]"

    assert any(dep.startswith("aiofiles") for dep in optional_deps["async"]), (
        "Expected aiofiles in 'async' optional dependencies"
    )
    assert any(dep.startswith("pytest-cuke") for dep in optional_deps["full"]), (
        "Expected pytest-cuke in 'full' optional dependencies"
    )


def test_packaging_extras_syntax_and_dependencies() -> None:
    optional_deps = _load_optional_dependencies()

    # Verify 'async' dependencies
    async_reqs = [Requirement(dep) for dep in optional_deps["async"]]
    assert len(async_reqs) >= 1
    aiofiles_req = next(r for r in async_reqs if r.name == "aiofiles")
    assert any(spec.operator in (">=", "==") for spec in aiofiles_req.specifier)

    # Verify 'full' dependencies and sub-extras
    full_reqs = [Requirement(dep) for dep in optional_deps["full"]]
    assert len(full_reqs) >= 1
    cuke_req = next(r for r in full_reqs if r.name == "pytest-cuke")

    expected_sub_extras = {"allure", "debug-mcp", "struct-bdd", "cucumber-json", "async"}
    assert expected_sub_extras.issubset(cuke_req.extras), (
        f"Missing expected sub-extras in 'full': {expected_sub_extras - cuke_req.extras}"
    )

    # Verify that each referenced extra actually exists in pyproject.toml
    for extra_name in cuke_req.extras:
        assert extra_name in optional_deps, f"Sub-extra '{extra_name}' not defined in optional-dependencies"
        # Validate syntax of all dependencies under each referenced extra
        for dep in optional_deps[extra_name]:
            req = Requirement(dep)
            assert req.name, f"Invalid requirement name for {dep}"


def test_packaging_metadata_provides_extras() -> None:
    try:
        dist_meta = importlib.metadata.metadata("pytest-cuke")
    except importlib.metadata.PackageNotFoundError:
        return

    provides_extras = dist_meta.get_all("Provides-Extra") or []
    assert "async" in provides_extras, "'async' extra missing from installed metadata Provides-Extra"
    assert "full" in provides_extras, "'full' extra missing from installed metadata Provides-Extra"


def test_migration_docs_contain_extras_table() -> None:
    v2_to_v3 = REPO_ROOT / "docs" / "migration" / "v2-to-v3.md"
    migration_link = REPO_ROOT / "docs" / "MIGRATION.md"

    assert v2_to_v3.is_file(), f"{v2_to_v3} does not exist"
    assert migration_link.exists(), f"{migration_link} does not exist"

    content = v2_to_v3.read_text(encoding="utf-8")
    assert "[async]" in content
    assert "[full]" in content
    assert "aiofiles>=23.0.0" in content
    assert "[env-matrix]" in content

    # docs/MIGRATION.md should point to or contain the migration documentation
    link_content = migration_link.read_text(encoding="utf-8")
    assert "[async]" in link_content
    assert "[full]" in link_content
