"""Step policy decorator tests."""

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
    """Decorator updates definitions created before it runs."""

    @not_implemented
    @given("a pending step")
    def pending_step():
        raise NotImplementedError

    definition = _single_definition(pending_step)

    assert isinstance(definition, Definition)
    assert definition.not_implemented is True


def test_not_implemented_below_step_decorator_marks_definition():
    """Decorator stores pending metadata for later step decorators."""

    @given("another pending step")
    @not_implemented
    def pending_step():
        raise NotImplementedError

    definition = _single_definition(pending_step)

    assert isinstance(definition, Definition)
    assert definition.not_implemented is True


def test_plain_step_is_not_not_implemented():
    """Plain step definitions default to executable."""

    @given("a regular step")
    def regular_step():
        return "ok"

    definition = _single_definition(regular_step)

    assert definition.not_implemented is False


def test_tolerant_above_step_decorator_marks_definition():
    """Decorator updates definitions created before it runs."""

    @tolerant
    @given("a tolerant step")
    def tolerant_step():
        raise AssertionError

    definition = _single_definition(tolerant_step)

    assert isinstance(definition, Definition)
    assert definition.tolerant is True


def test_tolerant_below_step_decorator_marks_definition():
    """Decorator stores tolerant metadata for later step decorators."""

    @given("another tolerant step")
    @tolerant
    def tolerant_step():
        raise AssertionError

    definition = _single_definition(tolerant_step)

    assert isinstance(definition, Definition)
    assert definition.tolerant is True


def test_plain_step_is_not_tolerant():
    """Plain step definitions are strict by default."""

    @given("a strict step")
    def strict_step():
        return "ok"

    definition = _single_definition(strict_step)

    assert definition.tolerant is False


def test_public_not_implemented_export():
    """Top-level pytest_bdd export exposes not_implemented."""
    import pytest_bdd

    assert pytest_bdd.not_implemented is not_implemented
    assert hasattr(pytest_bdd, "not_implemented")


def test_public_tolerant_export():
    """Top-level pytest_bdd export exposes tolerant."""
    import pytest_bdd

    assert pytest_bdd.tolerant is tolerant
    assert hasattr(pytest_bdd, "tolerant")
