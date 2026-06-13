"""

Provide test hook helpers.
"""


def test_hook_execution_on_feature_tag_using_mark_hook(testdir):
    """
    Verify hook execution on feature tag using mark hook.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    testdir.makefile(
        ".ini",
        # language=ini
        pytest="""\
                [pytest]
                markers =
                    tag
                """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        same_name="""\
            @tag
            Feature: Feature with tag
                Scenario: Scenario with tag
                    When Do something
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest import fixture
        from pytest_bdd import when
        from pytest_bdd.hook import before_mark, after_mark, around_mark
        from pytest_bdd.compatibility.pytest import FixtureRequest
        from pytest_bdd.util.pytest_extra import inject_fixture


        @fixture(scope='session')
        def session_fixture():
            return 'session_fixture'

        @before_mark('tag')
        def inject_custom_fixture(request: FixtureRequest, session_fixture):
            inject_fixture(request, 'tag_fixture', True)
            assert session_fixture == 'session_fixture'

        @before_mark('tag')
        def inject_another_custom_fixture(request: FixtureRequest):
            inject_fixture(request, 'another_tag_fixture', True)

        @after_mark('tag')
        def check_step_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @around_mark('tag')
        def check_around_test_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert not hasattr(request.config, 'test_attr')
            yield
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @when("Do something")
        def do_something(
            tag_fixture,
            another_tag_fixture,
            request,
        ):
            assert tag_fixture
            assert another_tag_fixture
            inject_fixture(request, 'step_fixture', 'step_fixture')
            request.config.test_attr = 'test_attr'
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_hook_execution_on_feature_tag_using_tag_hook(testdir):
    """
    Verify hook execution on feature tag using tag hook.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    testdir.makefile(
        ".ini",
        # language=ini
        pytest="""\
                [pytest]
                markers =
                    tag
                """,
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        same_name="""\
            @tag
            Feature: Feature with tag
                Scenario: Scenario with tag
                    When Do something
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest import fixture
        from pytest_bdd import when
        from pytest_bdd.hook import before_tag, after_tag, around_tag
        from pytest_bdd.compatibility.pytest import FixtureRequest
        from pytest_bdd.util.pytest_extra import inject_fixture


        @fixture(scope='session')
        def session_fixture():
            return 'session_fixture'

        @before_tag('@tag')
        def inject_custom_fixture(request: FixtureRequest, session_fixture):
            inject_fixture(request, 'tag_fixture', True)
            assert session_fixture == 'session_fixture'

        @before_tag('@tag')
        def inject_another_custom_fixture(request: FixtureRequest):
            inject_fixture(request, 'another_tag_fixture', True)

        @after_tag('@tag')
        def check_step_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @around_tag('@tag')
        def check_around_test_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert not hasattr(request.config, 'test_attr')
            yield
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @when("Do something")
        def do_something(
            tag_fixture,
            another_tag_fixture,
            request,
        ):
            assert tag_fixture
            assert another_tag_fixture
            inject_fixture(request, 'step_fixture', 'step_fixture')
            request.config.test_attr = 'test_attr'
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_hook_execution_on_feature_no_tag_using_tag_hook(testdir):
    """
    Verify hook execution on feature no tag using tag hook.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    testdir.makefile(
        ".feature",
        # language=gherkin
        same_name="""\
            Feature: Feature without tag
                Scenario: Scenario without tag
                    When Do something
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest import fixture
        from pytest_bdd import when
        from pytest_bdd.hook import before_tag, after_tag, around_tag
        from pytest_bdd.compatibility.pytest import FixtureRequest
        from pytest_bdd.util.pytest_extra import inject_fixture


        @fixture(scope='session')
        def session_fixture():
            return 'session_fixture'

        @before_tag
        def inject_custom_fixture(request: FixtureRequest, session_fixture):
            inject_fixture(request, 'tag_fixture', True)
            assert session_fixture == 'session_fixture'

        @before_tag()
        def inject_another_custom_fixture(request: FixtureRequest):
            inject_fixture(request, 'another_tag_fixture', True)

        @after_tag()
        def check_step_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @around_tag
        def check_around_test_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert not hasattr(request.config, 'test_attr')
            yield
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @when("Do something")
        def do_something(
            tag_fixture,
            another_tag_fixture,
            request,
        ):
            assert tag_fixture
            assert another_tag_fixture
            inject_fixture(request, 'step_fixture', 'step_fixture')
            request.config.test_attr = 'test_attr'
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_hook_execution_on_feature_no_tag_using_mark_hook(testdir):
    """
    Verify hook execution on feature no tag using mark hook.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    testdir.makefile(
        ".feature",
        # language=gherkin
        same_name="""\
            Feature: Feature without tag
                Scenario: Scenario without tag
                    When Do something
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest import fixture
        from pytest_bdd import when
        from pytest_bdd.hook import before_mark, after_mark, around_mark
        from pytest_bdd.compatibility.pytest import FixtureRequest
        from pytest_bdd.util.pytest_extra import inject_fixture


        @fixture(scope='session')
        def session_fixture():
            return 'session_fixture'

        @before_mark
        def inject_custom_fixture(request: FixtureRequest, session_fixture):
            inject_fixture(request, 'tag_fixture', True)
            assert session_fixture == 'session_fixture'

        @before_mark()
        def inject_another_custom_fixture(request: FixtureRequest):
            inject_fixture(request, 'another_tag_fixture', True)

        @after_mark()
        def check_step_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @around_mark
        def check_around_test_fixture(request: FixtureRequest, session_fixture):
            # We can't rely on before/in test set fixtures because they could be already finished
            assert session_fixture == 'session_fixture'
            assert not hasattr(request.config, 'test_attr')
            yield
            assert session_fixture == 'session_fixture'
            assert request.config.test_attr == 'test_attr'

        @when("Do something")
        def do_something(
            tag_fixture,
            another_tag_fixture,
            request,
        ):
            assert tag_fixture
            assert another_tag_fixture
            inject_fixture(request, 'step_fixture', 'step_fixture')
            request.config.test_attr = 'test_attr'
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_message_hook_signature_uses_event_envelope_annotation():
    """
    Verify message hook signature uses event envelope annotation.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
    from pytest_bdd.model.message_extension import EventEnvelope
    from pytest_bdd.plugin.gherkin_message_reporter.hook import (
        GherkinMessageReporterHookSpec,
    )

    annotation = GherkinMessageReporterHookSpec.pytest_bdd_message.__annotations__["message"]
    assert annotation is EventEnvelope
