from pathlib import Path

from pytest_bdd.compatibility.importlib.resources import files

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_template_assets_are_available_through_package_resources() -> None:
    template_package = files("pytest_bdd.template")

    assert template_package.joinpath("test.py.jinja2").is_file()
    assert template_package.joinpath("features_section.rst.jinja2").is_file()
    assert template_package.joinpath("feature_include.rst.jinja2").is_file()


def test_setup_cfg_package_data_lists_jinja2_assets() -> None:
    setup_cfg = (PROJECT_ROOT / "setup.cfg").read_text(encoding="utf-8")

    assert "test.py.jinja2" in setup_cfg
    assert "features_section.rst.jinja2" in setup_cfg
    assert "feature_include.rst.jinja2" in setup_cfg
    assert "test.py.mak" not in setup_cfg


def test_pyproject_declares_jinja2_and_removes_mako_runtime_dependency() -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"Jinja2"' in pyproject
    assert '"Mako"' not in pyproject
