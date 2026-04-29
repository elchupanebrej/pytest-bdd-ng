from pathlib import Path

from pytest_bdd.compatibility.tomllib import loads
from pytest_bdd.compatibility.importlib.resources import files

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_pyproject() -> dict:
    return loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_template_assets_are_available_through_package_resources() -> None:
    template_package = files("pytest_bdd.template")

    assert template_package.joinpath("test.py.jinja2").is_file()
    assert template_package.joinpath("features_index.rst.jinja2").is_file()
    assert template_package.joinpath("features_section.rst.jinja2").is_file()
    assert template_package.joinpath("feature_include.rst.jinja2").is_file()


def test_pyproject_package_data_lists_jinja2_assets() -> None:
    pyproject = _load_pyproject()
    template_assets = pyproject["tool"]["setuptools"]["package-data"]["pytest_bdd.template"]

    assert "test.py.jinja2" in template_assets
    assert "features_index.rst.jinja2" in template_assets
    assert "features_section.rst.jinja2" in template_assets
    assert "feature_include.rst.jinja2" in template_assets
    assert "test.py.mak" not in template_assets


def test_pyproject_declares_jinja2_and_removes_mako_runtime_dependency() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"Jinja2"' in pyproject
    assert '"Mako"' not in pyproject


def test_pyproject_declares_gitpython_for_test_suite() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"GitPython"' in pyproject
    assert '"GitRepo"' not in pyproject
