"""

Provide test features repository heading baseline helpers.
"""

from __future__ import annotations

from pathlib import Path

from pytest_bdd.script.validate_feature_headings import build_baseline_audit


def test_repository_feature_documents_have_no_empty_parsed_headings() -> None:
    """
    Verify repository feature documents have no empty parsed headings.

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
    repository_root = Path(__file__).resolve().parents[5]
    features_root = repository_root / "features"

    baseline = build_baseline_audit(features_root)

    assert baseline.compliant
    assert baseline.violations_count == 0
