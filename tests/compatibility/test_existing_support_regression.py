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


def test_tox_pytest_envs_emit_named_ndjson_artifacts():
    tox_ini = Path("tox.ini").read_text(encoding="utf-8")

    assert "--messages-ndjson={tox_root}/.tox/{envname}.messages.ndjson" in tox_ini
    assert "GIT_PYTHON_GIT_EXECUTABLE = {env:GIT_PYTHON_GIT_EXECUTABLE:git}" in tox_ini
    assert "win: _PYTEST_WINDOWS_ARGS = -p no:cacheprovider" in tox_ini
    assert "{env:_PYTEST_WINDOWS_ARGS:}" in tox_ini
    assert (
        "tests/messages/test_messages_feature_suite.py -k html_report_renders_in_browser "
        "--messages-ndjson={tox_root}/.tox/{envname}.messages.ndjson -v"
    ) in tox_ini
    assert (
        "tests/e2e/test_xdist_remote_message_aggregation.py -k {env:PYTEST_REMOTE_MODE:{envname}} "
        "--messages-ndjson={tox_root}/.tox/{envname}.messages.ndjson -v"
    ) in tox_ini


def test_makefile_renders_html_reports_from_tox_ndjson_artifacts():
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "render-tox-reports" in makefile
    assert "uv run render_cucumber_formatters --messages-ndjson" in makefile
    assert "messages-e2e-report" not in makefile
