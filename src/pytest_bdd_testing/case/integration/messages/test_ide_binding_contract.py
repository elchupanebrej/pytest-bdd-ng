"""

Test IDE binding contract and launch nodeids.
"""

from __future__ import annotations

import json
from pathlib import Path

from contract.messages.test_messages import (
    list_filter_by_type,
    parse_and_unfold_messages,
    runpytest_with_message_reporter,
)
from cucumber_messages import (
    Attachment,
    GherkinDocument,
    Pickle,
    Source,
    StepDefinition,
)
from cucumber_messages import TestCase as _TestCase

LAUNCH_MEDIA_TYPE = "application/vnd.pytest-bdd.launch+json"


def test_ide_bootstrap_messages_and_probes(testdir, tmp_path):
    """
    Verify that mock-run writes cucumber-messages and launch attachments without executing probes.

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
        Feature: Mock run test
            Scenario: Simple Scenario
                Given a step definition
        """,
    )
    testdir.makeconftest(
        """
        import pytest
        from pytest_bdd import given

        @pytest.fixture
        def my_fixture():
            with open("probes.txt", "a") as f:
                f.write("fixture_body\\n")
            return 42

        @given("a step definition")
        def a_step(my_fixture):
            with open("probes.txt", "a") as f:
                f.write("step_body\\n")

        def pytest_bdd_before_scenario(request, run):
            with open("probes.txt", "a") as f:
                f.write("before_scenario_hook\\n")

        def pytest_bdd_after_scenario(request, run):
            with open("probes.txt", "a") as f:
                f.write("after_scenario_hook\\n")

        def pytest_bdd_before_step(request, run, step_func):
            with open("probes.txt", "a") as f:
                f.write("before_step_hook\\n")

        def pytest_bdd_after_step(request, run, step_func, step_func_args, step_definition):
            with open("probes.txt", "a") as f:
                f.write("after_step_hook\\n")
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Simple Scenario")
        def test_simple():
            pass
        """,
    )

    ndjson_path = tmp_path / "mock_run.ndjson"
    result = runpytest_with_message_reporter(
        testdir,
        "--mock-run",
        "--messages-ndjson",
        str(ndjson_path),
    )
    # Under mock-run, the tests should still pass/succeed but not execute bodies.
    result.assert_outcomes(passed=1)

    # Verify probe file does not exist (meaning no hook/fixture/step bodies executed)
    probe_file = Path(testdir.tmpdir) / "probes.txt"
    assert not probe_file.exists(), f"Probes executed: {probe_file.read_text() if probe_file.exists() else ''}"

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())

    # Check that required message types exist
    assert list_filter_by_type(Source, payloads)
    assert list_filter_by_type(GherkinDocument, payloads)
    assert list_filter_by_type(Pickle, payloads)
    assert list_filter_by_type(StepDefinition, payloads)
    assert list_filter_by_type(_TestCase, payloads)

    # Check for launch attachments
    attachments = list_filter_by_type(Attachment, payloads)
    launch_attachments = [a for a in attachments if getattr(a.media_type, "value", a.media_type) == LAUNCH_MEDIA_TYPE]
    assert len(launch_attachments) == 1

    launch_data = json.loads(launch_attachments[0].body)
    assert "testCaseId" in launch_data
    assert "pickleId" in launch_data
    assert "nodeid" in launch_data
    assert "sourceIdentity" in launch_data


def test_runnable_launch_mapping(testdir, tmp_path):
    """
    Verify launch attachment contains nodeid that can be executed directly.

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
        Feature: Launch test
            Scenario: Run me
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
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Run me")
        def test_run_me():
            pass
        """,
    )

    ndjson_path = tmp_path / "launch.ndjson"
    result = runpytest_with_message_reporter(
        testdir,
        "--mock-run",
        "--messages-ndjson",
        str(ndjson_path),
    )
    result.assert_outcomes(passed=1)

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
    attachments = list_filter_by_type(Attachment, payloads)
    launch_attachments = [a for a in attachments if getattr(a.media_type, "value", a.media_type) == LAUNCH_MEDIA_TYPE]
    assert len(launch_attachments) == 1

    launch_data = json.loads(launch_attachments[0].body)
    nodeid = launch_data["nodeid"]

    # Invoking pytest with this nodeid should run exactly that scenario
    result2 = testdir.runpytest(nodeid)
    result2.assert_outcomes(passed=1)


def test_examples_row_launch_mapping(testdir, tmp_path):
    """
    Verify outline scenarios with multiple Examples rows emit distinct row-specific nodeids and sourceIdentities.

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
        Feature: Scenario Outline Launch
            Scenario Outline: Outline scenario
                Given <value> step
                Examples:
                    | value |
                    | one   |
                    | two   |
        """,
    )
    testdir.makeconftest(
        """
        from pytest_bdd import given
        @given("one step")
        def step_one():
            pass
        @given("two step")
        def step_two():
            pass
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenarios
        test_scenarios = scenarios("test.feature")
        """,
    )

    ndjson_path = tmp_path / "outline.ndjson"
    result = runpytest_with_message_reporter(
        testdir,
        "--mock-run",
        "--messages-ndjson",
        str(ndjson_path),
    )
    result.assert_outcomes(passed=2)

    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
    attachments = list_filter_by_type(Attachment, payloads)
    launch_attachments = [a for a in attachments if getattr(a.media_type, "value", a.media_type) == LAUNCH_MEDIA_TYPE]
    assert len(launch_attachments) == 2

    launch_data_list = [json.loads(a.body) for a in launch_attachments]

    nodeids = [d["nodeid"] for d in launch_data_list]
    source_identities = [d["sourceIdentity"] for d in launch_data_list]

    assert len(set(nodeids)) == 2
    assert len({json.dumps(si) for si in source_identities}) == 2

    # Asserting that running each nodeid runs exactly one item
    for nodeid in nodeids:
        res = testdir.runpytest(nodeid)
        res.assert_outcomes(passed=1)


def test_launch_metadata_isolation(testdir, tmp_path):
    """
    Verify launch metadata remains isolated from tag filtering (-m) and user tags.

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
        @user_tag
        Feature: Metadata Isolation
            Scenario: Tagged scenario
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
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Tagged scenario")
        def test_tagged():
            pass
        """,
    )

    ndjson_path = tmp_path / "isolation.ndjson"

    # Verify standard tag selection works with --messages-ndjson enabled
    result_tagged = runpytest_with_message_reporter(
        testdir,
        "-m",
        "user_tag",
        "--mock-run",
        "--messages-ndjson",
        str(ndjson_path),
    )
    result_tagged.assert_outcomes(passed=1)

    # Verify filtering with non-existent tag skips it
    result_skipped = runpytest_with_message_reporter(
        testdir,
        "-m",
        "not_a_tag",
        "--mock-run",
        "--messages-ndjson",
        str(ndjson_path),
    )
    result_skipped.assert_outcomes(passed=0)

    # The pickle tags must only contain user_tag, no launch metadata
    payloads = parse_and_unfold_messages(ndjson_path.read_text(encoding="utf-8").splitlines())
    pickles = list_filter_by_type(Pickle, payloads)
    assert len(pickles) == 1
    pickle_tags = [t.name for t in pickles[0].tags]
    assert "@user_tag" in pickle_tags
    assert not any("launch" in tag or "nodeid" in tag for tag in pickle_tags)
