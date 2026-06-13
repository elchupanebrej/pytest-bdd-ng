"""

Test IDE step bindings and step-scoped diagnostics.
"""

from __future__ import annotations

import json

from contract.messages.test_messages import (
    list_filter_by_type,
    parse_and_unfold_messages,
    runpytest_with_message_reporter,
)
from cucumber_messages import Attachment

BINDING_MEDIA_TYPE = "application/vnd.pytest-bdd.step-binding+json"
DIAGNOSTIC_MEDIA_TYPE = "application/vnd.pytest-bdd.diagnostic+json"


def test_matched_step_bindings(testdir, tmp_path):
    """
    Verify that matched steps (string, parse, regex, cfparse) emit explicit binding attachments.

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
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        test="""
        Feature: Step Matching
            Scenario: Match kinds
                Given normal string step
                When parse step 42
                Then regex step foo
                And cfparse step bar
        """,
    )
    testdir.makeconftest(
        """
        import re
        from pytest_bdd import given, when, then, parsers

        @given("normal string step")
        def step_string():
            pass

        @when(parsers.parse("parse step {num:d}"))
        def step_parse(num):
            pass

        @then(parsers.re(r"regex step (?P<val>\\w+)"))
        def step_re(val):
            pass

        @then(parsers.parse("cfparse step {val:w}"))
        def step_cf(val):
            pass
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario
        @scenario("test.feature", "Match kinds")
        def test_kinds():
            pass
        """,
    )

    ndjson_path = tmp_path / "matched_steps.ndjson"
    result = runpytest_with_message_reporter(
        testdir,
        "--mock-run",
        "--messages-ndjson",
        str(ndjson_path),
    )
    result.assert_outcomes(passed=1)

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
    attachments = list_filter_by_type(Attachment, payloads)
    binding_attachments = [a for a in attachments if getattr(a.media_type, "value", a.media_type) == BINDING_MEDIA_TYPE]
    # We should have 4 step binding attachments
    assert len(binding_attachments) == 4

    bindings = [json.loads(a.body) for a in binding_attachments]

    for b in bindings:
        assert "testCaseId" in b
        assert "pickleStepId" in b
        assert "stepDefinitionId" in b
        assert "sourceReference" in b
        assert "matchArguments" in b

        sr = b["sourceReference"]
        assert "uri" in sr
        assert "line" in sr
        assert isinstance(sr["line"], int)
        assert sr["line"] > 0


def test_missing_step_diagnostics(testdir, tmp_path):
    """
    Verify that a missing step emits a diagnostic warning with available step definitions.

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
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        test="""
        Feature: Missing Step
            Scenario: Scen
                Given this is missing
        """,
    )
    testdir.makeconftest(
        """
        from pytest_bdd import given
        @given("other available step")
        def other_step():
            pass
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario
        @scenario("test.feature", "Scen")
        def test_scen():
            pass
        """,
    )

    ndjson_path = tmp_path / "missing.ndjson"
    result = runpytest_with_message_reporter(
        testdir,
        "--mock-run",
        "--messages-ndjson",
        str(ndjson_path),
    )
    # A missing step under mock-run still fails the test suite!
    assert result.ret != 0

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
    attachments = list_filter_by_type(Attachment, payloads)
    diagnostic_attachments = [
        a for a in attachments if getattr(a.media_type, "value", a.media_type) == DIAGNOSTIC_MEDIA_TYPE
    ]

    diagnostics = [json.loads(a.body) for a in diagnostic_attachments]
    missing_diags = [d for d in diagnostics if d.get("kind") == "missing-step"]
    assert len(missing_diags) == 1

    diag = missing_diags[0]
    assert diag["severity"] == "warning"
    assert "testCaseId" in diag
    assert "pickleStepId" in diag
    assert "unmatchedStepText" in diag
    assert diag["unmatchedStepText"] == "this is missing"

    # Scoped available definitions should be listed
    assert "availableStepDefinitions" in diag
    available = diag["availableStepDefinitions"]
    assert len(available) >= 1
    assert any("other available step" in item.get("pattern", "") for item in available)
    for step_def in available:
        assert "id" in step_def
        assert "pattern" in step_def
        assert "sourceReference" in step_def


def test_ambiguous_step_diagnostics(testdir, tmp_path):
    """
    Verify that an ambiguous step emits a diagnostic warning with matched candidates.

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
    testdir.makeini("[pytest]\ndisable_feature_autoload = true\n")
    testdir.makefile(
        ".feature",
        test="""
        Feature: Ambiguous Step
            Scenario: Scen
                Given ambiguous step
        """,
    )
    testdir.makeconftest(
        """
        from pytest_bdd import given
        @given("ambiguous step")
        def step1():
            pass

        @given("ambiguous step")
        def step2():
            pass
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario
        @scenario("test.feature", "Scen")
        def test_scen():
            pass
        """,
    )

    ndjson_path = tmp_path / "ambiguous.ndjson"
    result = runpytest_with_message_reporter(
        testdir,
        "--mock-run",
        "--messages-ndjson",
        str(ndjson_path),
    )
    result.assert_outcomes(passed=1)

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
    attachments = list_filter_by_type(Attachment, payloads)
    diagnostic_attachments = [
        a for a in attachments if getattr(a.media_type, "value", a.media_type) == DIAGNOSTIC_MEDIA_TYPE
    ]

    diagnostics = [json.loads(a.body) for a in diagnostic_attachments]
    ambig_diags = [d for d in diagnostics if d.get("kind") == "ambiguous-step"]
    assert len(ambig_diags) == 1

    diag = ambig_diags[0]
    assert diag["severity"] == "warning"
    assert "testCaseId" in diag
    assert "pickleStepId" in diag
    assert "candidates" in diag
    candidates = diag["candidates"]
    assert len(candidates) == 2
    for cand in candidates:
        assert "stepDefinitionId" in cand
        assert "pattern" in cand
        assert "sourceReference" in cand
        assert cand["pattern"] == "ambiguous step"
