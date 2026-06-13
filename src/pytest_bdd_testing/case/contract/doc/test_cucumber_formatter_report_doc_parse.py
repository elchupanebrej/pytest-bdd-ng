"""

Provide test cucumber formatter report doc parse helpers.
"""

from pathlib import Path

from pytest_bdd.script.validate_feature_headings import parse_gherkin_document


def test_cucumber_formatter_report_doc_is_parseable() -> None:
    """
    Verify cucumber formatter report doc is parseable.

    Test target:
        Enforce Gherkin specification compliance during parsing.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce Gherkin specification compliance during parsing., then
        the expected outcome is produced.
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
    feature_path = (
        Path(__file__).resolve().parents[5] / "features" / "07 Report" / "09 Cucumber formatter reports.feature.md"
    )

    parsed_document = parse_gherkin_document(feature_path)

    assert parsed_document["feature"]["name"] == "Cucumber formatter reports"
    assert parsed_document["feature"]["children"]


def test_cucumber_formatter_report_doc_mentions_live_stream_and_controller_ownership() -> None:
    """
    Verify cucumber formatter report doc mentions live stream and controller ownership.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
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
    feature_path = (
        Path(__file__).resolve().parents[5] / "features" / "07 Report" / "09 Cucumber formatter reports.feature.md"
    )

    contents = feature_path.read_text(encoding="utf-8")

    assert "live incremental message stream" in contents
    assert "workers forward messages to the controller/main process" in contents
    assert "authority renders formatter output" in contents


def test_cucumber_formatter_report_doc_does_not_require_manual_capture_flags() -> None:
    """
    Verify cucumber formatter report doc does not require manual capture flags.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
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
    feature_path = (
        Path(__file__).resolve().parents[5] / "features" / "07 Report" / "09 Cucumber formatter reports.feature.md"
    )

    contents = feature_path.read_text(encoding="utf-8")

    assert "--capture=no" not in contents
    assert " -s" not in contents
