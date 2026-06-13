"""

Provide test group no duplicates helpers.
"""

from pathlib import Path

from pytest_bdd.util.matrix import build_migration_coverage_summary


def test_duplicate_user_facing_scenarios_are_detected(tmp_path: Path):
    """
    Verify duplicate user facing scenarios are detected.

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
    tests_feature_dir = tmp_path / "tests" / "feature"
    tests_feature_dir.mkdir(parents=True)
    (tests_feature_dir / "test_no_scenario.py").write_text("def test_x():\n    pass\n", encoding="utf-8")

    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "no-scenario.feature.md").write_text("Feature: no scenario\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.duplicates_in_tests == 1
    assert summary.threshold_met is False


def test_no_duplicates_when_user_facing_tests_removed(tmp_path: Path):
    """
    Verify no duplicates when user facing tests removed.

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
    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "only-doc.feature.md").write_text("Feature: only doc\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.duplicates_in_tests == 0
    assert summary.threshold_met is True


def test_inventory_keeps_non_removable_retained_and_deferred_tests():
    """
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
    inventory = Path("specs/002-e2e-test-conversion/e2e-migration-inventory.md").read_text(encoding="utf-8")

    assert "`tests/e2e/test_e2e.py`" in inventory
    assert "`tests/e2e/allure/test_e2e_allure.py`" in inventory
    assert "e2e_retain_technical" in inventory

    assert "`tests/feature/test_outline.py`" in inventory
    assert "`tests/feature/test_http.py`" in inventory
    assert "`tests/feature/test_steps.py`" in inventory
    assert "`tests/struct_bdd/test_steps.py`" in inventory
    assert "`tests/struct_bdd/test_deserialization.py`" in inventory
    assert "| Deferred conversion | 3 |" in inventory


def _iter_inventory_rows(inventory_text: str):
    for raw_line in inventory_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("| `tests/"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 11:
            continue
        yield cells


def test_fr_006b_restoration_required_rows_must_keep_source_until_parity_is_recorded():
    """
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
    inventory = Path("specs/002-e2e-test-conversion/e2e-migration-inventory.md").read_text(encoding="utf-8")

    restoration_rows = []
    for cells in _iter_inventory_rows(inventory):
        source_path = cells[0].strip("`")
        restoration_required = cells[7]
        if restoration_required.startswith("yes"):
            restoration_rows.append(source_path)
            assert Path(source_path).exists(), (
                f"{source_path} is marked restoration_required={restoration_required!r} "
                "but the pytest source file is missing"
            )


def test_e2e_doc_tests_do_not_count_as_migration_duplicates(tmp_path: Path):
    """
    Verify e2e doc tests do not count as migration duplicates.

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
    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "cucumber-formatter-reports.feature.md").write_text("Feature: report docs\n", encoding="utf-8")

    e2e_dir = tmp_path / "tests" / "e2e"
    e2e_dir.mkdir(parents=True)
    (e2e_dir / "test_report_doc_cucumber_formatters.py").write_text("def test_x():\n    pass\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.duplicates_in_tests == 0
