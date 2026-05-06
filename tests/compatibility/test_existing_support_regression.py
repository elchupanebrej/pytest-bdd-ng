from pathlib import Path

from pytest_bdd.compatibility.matrix import extract_factors_from_tox_ini


def test_eol_py39_and_pre70_pytest_factors_are_removed():
    py_factors, pytest_factors = extract_factors_from_tox_ini(Path("tox.ini"))

    assert "39" not in py_factors
    assert "60" not in pytest_factors
    assert "61" not in pytest_factors
    assert "62" not in pytest_factors
    assert "625" not in pytest_factors
    assert "310" in py_factors


def test_extract_factors_from_tox_ini_supports_brace_expansions(tmp_path):
    tox_ini = tmp_path / "tox.ini"
    tox_ini.write_text(
        "[tox]\nenv_list =\n    py{py311, py310}-pytest{latest,70}-coverage-lin\n",
        encoding="utf-8",
    )

    py_factors, pytest_factors = extract_factors_from_tox_ini(tox_ini)

    assert py_factors == ["310", "311"]
    assert pytest_factors == ["70", "latest"]


def test_makefile_renders_html_reports_from_tox_ndjson_artifacts():
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "render-tox-reports" in makefile
    assert "uv run render_cucumber_formatters --messages-ndjson" in makefile
    assert "messages-e2e-report" not in makefile
