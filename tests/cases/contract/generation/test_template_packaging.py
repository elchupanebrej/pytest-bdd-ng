"""Provide test template packaging helpers."""

from pathlib import Path

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.compatibility.tomllib import loads

PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _load_pyproject() -> dict:
    return loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_template_assets_are_available_through_package_resources() -> None:
    """Verify template assets are available through package resources."""
    template_package = files("pytest_bdd.template")

    assert template_package.joinpath("test.py.jinja2").is_file()
    assert template_package.joinpath("features_index.rst.jinja2").is_file()
    assert template_package.joinpath("features_section.rst.jinja2").is_file()
    assert template_package.joinpath("feature_include.rst.jinja2").is_file()


def test_pyproject_package_data_lists_jinja2_assets() -> None:
    """Verify pyproject package data lists jinja2 assets."""
    pyproject = _load_pyproject()
    template_assets = pyproject["tool"]["setuptools"]["package-data"]["pytest_bdd.template"]

    assert "test.py.jinja2" in template_assets
    assert "features_index.rst.jinja2" in template_assets
    assert "features_section.rst.jinja2" in template_assets
    assert "feature_include.rst.jinja2" in template_assets
    assert "test.py.mak" not in template_assets


def test_pyproject_package_data_lists_message_schema_assets() -> None:
    """Verify pyproject package data lists message schema assets."""
    pyproject = _load_pyproject()
    package_data = pyproject["tool"]["setuptools"]["package-data"]

    assert package_data["pytest_bdd.model"] == ["message_jsonschema/*.json"]


def test_release_workflow_syncs_message_schemas_before_build() -> None:
    """Verify release workflow syncs message schemas before build."""
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "release.yaml").read_text(encoding="utf-8")

    sync_position = workflow.index("pytest_bdd.script.sync_messages_contract_schemas")
    build_position = workflow.index("python -m build")

    assert sync_position < build_position


def test_main_workflow_checks_generated_message_schemas_without_pre_commit() -> None:
    """Verify main workflow checks generated message schemas without pre commit."""
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "main.yml").read_text(encoding="utf-8")
    pre_commit_config = (PROJECT_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert "Generated messages schemas are up to date" in workflow
    assert "pytest_bdd.script.sync_messages_contract_schemas --check" in workflow
    assert "sync_messages_contract_schemas" not in pre_commit_config


def test_pyproject_declares_jinja2_and_removes_mako_runtime_dependency() -> None:
    """Verify pyproject declares jinja2 and removes mako runtime dependency."""
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"Jinja2"' in pyproject
    assert '"Mako"' not in pyproject


def test_pyproject_declares_gitpython_for_test_suite() -> None:
    """Verify pyproject declares gitpython for test suite."""
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"GitPython"' in pyproject
    assert '"GitRepo"' not in pyproject
