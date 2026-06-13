"""

Test IDE source binding cardinality diagnostics.
"""

from __future__ import annotations

import json

from contract.messages.test_messages import (
    list_filter_by_type,
    parse_and_unfold_messages,
    runpytest_with_message_reporter,
)
from cucumber_messages import Attachment

DIAGNOSTIC_MEDIA_TYPE = "application/vnd.pytest-bdd.diagnostic+json"


def test_binding_cardinality_diagnostics(testdir, tmp_path):
    """
    Verify that cardinality diagnostics warn on 0 or >1 hookups and are normal for 1 hookup.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
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
    # Scenario A: bound once (normal)
    # Scenario B: bound twice (warning: multiple hookups)
    # Scenario C: bound zero times (warning: zero hookups)
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        test="""
        Feature: Cardinality test
            Scenario: Bound Once Scenario
                Given a step
            Scenario: Bound Twice Scenario
                Given a step
            Scenario: Unbound Scenario
                Given a step
        """,
    )
    testdir.makeconftest(
        """
        from pytest_bdd import given
        @given("a step")
        def a_step():
            pass
        """,
    )
    testdir.makepyfile(
        test_one="""
        from pytest_bdd import scenario

        @scenario("test.feature", "Bound Once Scenario")
        def test_once():
            pass

        @scenario("test.feature", "Bound Twice Scenario")
        def test_twice_1():
            pass
        """,
        test_two="""
        from pytest_bdd import scenario

        @scenario("test.feature", "Bound Twice Scenario")
        def test_twice_2():
            pass
        """,
    )

    ndjson_path = tmp_path / "cardinality.ndjson"
    # Run pytest under mock run.
    result = runpytest_with_message_reporter(
        testdir,
        "--mock-run",
        "--messages-ndjson",
        str(ndjson_path),
    )
    result.assert_outcomes(passed=3)

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
    attachments = list_filter_by_type(Attachment, payloads)
    diagnostic_attachments = [
        a for a in attachments if getattr(a.media_type, "value", a.media_type) == DIAGNOSTIC_MEDIA_TYPE
    ]

    # We expect diagnostics for duplicate/zero bindings.
    diagnostics = [json.loads(a.body) for a in diagnostic_attachments]

    # Find the diagnostic for "Bound Twice Scenario"
    twice_diag = [d for d in diagnostics if d.get("kind") == "duplicate-bindings"]
    assert len(twice_diag) == 1, f"Expected exactly one duplicate-bindings diagnostic: {diagnostics}"
    assert twice_diag[0]["severity"] == "warning"
    assert len(twice_diag[0]["bindings"]) == 2
    # Verify that each binding has a nodeid and a testCaseId
    for b in twice_diag[0]["bindings"]:
        assert "nodeid" in b
        assert "testCaseId" in b

    # Find the diagnostic for "Unbound Scenario" (zero hookups)
    zero_diag = [d for d in diagnostics if d.get("kind") == "unbound-scenario"]
    assert len(zero_diag) == 1, f"Expected exactly one unbound-scenario diagnostic: {diagnostics}"
    assert zero_diag[0]["severity"] == "warning"
    assert "sourceIdentity" in zero_diag[0]

    # Ensure Bound Once Scenario has no warnings
    warning_diags = [d for d in diagnostics if d["severity"] == "warning"]
    assert len(warning_diags) == 2, f"Only expected warnings for duplicate/unbound scenarios: {warning_diags}"
