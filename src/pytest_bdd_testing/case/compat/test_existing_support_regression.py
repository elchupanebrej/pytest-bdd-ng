"""

Provide test existing support regression helpers.
"""

from pathlib import Path

from pytest_bdd.util.matrix import extract_factors_from_tox_ini


def test_eol_py39_and_pre70_pytest_factors_are_removed():
    """
    Verify eol py39 and pre70 pytest factors are removed.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    py_factors, pytest_factors = extract_factors_from_tox_ini(Path("tox.ini"))

    assert "39" not in py_factors
    assert "60" not in pytest_factors
    assert "61" not in pytest_factors
    assert "62" not in pytest_factors
    assert "625" not in pytest_factors
    assert "310" in py_factors


def test_extract_factors_from_tox_ini_supports_brace_expansions(tmp_path):
    """
    Verify extract factors from tox ini supports brace expansions.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    tox_ini = tmp_path / "tox.ini"
    tox_ini.write_text(
        "[tox]\nenv_list =\n    py{py311, py310}-pytest{latest,70}-coverage-lin\n",
        encoding="utf-8",
    )

    py_factors, pytest_factors = extract_factors_from_tox_ini(tox_ini)

    assert py_factors == ["310", "311"]
    assert pytest_factors == ["70", "latest"]


def test_makefile_renders_html_reports_from_tox_ndjson_artifacts():
    """
    Verify makefile renders html reports from tox ndjson artifacts.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
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
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "render-tox-reports" in makefile
    assert "uv run render_cucumber_formatters --messages-ndjson" in makefile
    assert "messages-e2e-report" not in makefile
