"""

Step policy decorator tests.
"""

from __future__ import annotations

import pytest

from pytest_bdd import given, not_implemented, tolerant
from pytest_bdd.steps import Definition

pytestmark = [pytest.mark.unit]


def _single_definition(step_func):
    definitions = step_func.__pytest_bdd_step_definitions__
    assert len(definitions) == 1
    return next(iter(definitions))


def test_not_implemented_above_step_decorator_marks_definition():
    """
    Decorator updates definitions created before it runs.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
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

    @not_implemented
    @given("a pending step")
    def pending_step():
        raise NotImplementedError

    definition = _single_definition(pending_step)

    assert isinstance(definition, Definition)
    assert definition.not_implemented is True


def test_not_implemented_below_step_decorator_marks_definition():
    """
    Decorator stores pending metadata for later step decorators.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
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

    @given("another pending step")
    @not_implemented
    def pending_step():
        raise NotImplementedError

    definition = _single_definition(pending_step)

    assert isinstance(definition, Definition)
    assert definition.not_implemented is True


def test_plain_step_is_not_not_implemented():
    """
    Plain step definitions default to executable.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
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

    @given("a regular step")
    def regular_step():
        return "ok"

    definition = _single_definition(regular_step)

    assert definition.not_implemented is False


def test_tolerant_above_step_decorator_marks_definition():
    """
    Decorator updates definitions created before it runs.

    Test target:
        Allow step matching flexibility for user convenience without causing false positive failures.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Allow step matching flexibility for user convenience without
        causing false positive failures., then the expected outcome is produced.
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

    @tolerant
    @given("a tolerant step")
    def tolerant_step():
        raise AssertionError

    definition = _single_definition(tolerant_step)

    assert isinstance(definition, Definition)
    assert definition.tolerant is True


def test_tolerant_below_step_decorator_marks_definition():
    """
    Decorator stores tolerant metadata for later step decorators.

    Test target:
        Allow step matching flexibility for user convenience without causing false positive failures.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Allow step matching flexibility for user convenience without
        causing false positive failures., then the expected outcome is produced.
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

    @given("another tolerant step")
    @tolerant
    def tolerant_step():
        raise AssertionError

    definition = _single_definition(tolerant_step)

    assert isinstance(definition, Definition)
    assert definition.tolerant is True


def test_plain_step_is_not_tolerant():
    """
    Plain step definitions are strict by default.

    Test target:
        Allow step matching flexibility for user convenience without causing false positive failures.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Allow step matching flexibility for user convenience without
        causing false positive failures., then the expected outcome is produced.
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

    @given("a strict step")
    def strict_step():
        return "ok"

    definition = _single_definition(strict_step)

    assert definition.tolerant is False


def test_public_not_implemented_export():
    """
    Top-level pytest_bdd export exposes not_implemented.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
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
    import pytest_bdd

    assert pytest_bdd.not_implemented is not_implemented
    assert hasattr(pytest_bdd, "not_implemented")


def test_public_tolerant_export():
    """
    Top-level pytest_bdd export exposes tolerant.

    Test target:
        Allow step matching flexibility for user convenience without causing false positive failures.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Allow step matching flexibility for user convenience without
        causing false positive failures., then the expected outcome is produced.
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
    import pytest_bdd

    assert pytest_bdd.tolerant is tolerant
    assert hasattr(pytest_bdd, "tolerant")
