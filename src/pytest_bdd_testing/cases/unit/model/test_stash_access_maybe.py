"""Stash Maybe contract tests — verify find_in_stash and get_optional return Maybe."""

from __future__ import annotations

from collections import UserDict

import pytest
from returns.maybe import Maybe, Nothing, Some

from pytest_bdd.model.stash_access import StashAccess, StashBound

pytestmark = [pytest.mark.unit]


class FakeStash(UserDict):
    """Minimal fake stash that supports dict-like access."""


class ExampleStashBound(StashBound):
    """Test subclass with a known STASH_KEY."""

    STASH_KEY = "example_stash_key"


def test_stash_bound_find_in_stash_returns_some_on_hit():
    """find_in_stash returns Some when the key exists."""
    stash = FakeStash()
    instance = ExampleStashBound()
    instance.set_in_stash(stash)

    result = ExampleStashBound.find_in_stash(stash)

    assert isinstance(result, Maybe)
    assert result == Some(instance)


def test_stash_bound_find_in_stash_returns_nothing_on_miss():
    """find_in_stash returns Nothing when the key is absent."""
    stash = FakeStash()

    result = ExampleStashBound.find_in_stash(stash)

    assert isinstance(result, Maybe)
    assert result == Nothing


def test_stash_bound_find_in_stash_value_or_none_at_boundary():
    """value_or(None) converts Maybe back to Optional at API boundaries."""
    stash = FakeStash()

    # Miss case
    result = ExampleStashBound.find_in_stash(stash)
    assert result.value_or(None) is None

    # Hit case
    instance = ExampleStashBound()
    instance.set_in_stash(stash)
    result = ExampleStashBound.find_in_stash(stash)
    assert result.value_or(None) is instance


def test_stash_access_get_optional_returns_some_on_hit():
    """get_optional returns Some when value exists and type matches."""
    stash = FakeStash()
    instance = ExampleStashBound()
    stash[ExampleStashBound.STASH_KEY] = instance

    result = StashAccess.get_optional(stash, ExampleStashBound)

    assert isinstance(result, Maybe)
    assert result == Some(instance)


def test_stash_access_get_optional_returns_nothing_on_miss():
    """get_optional returns Nothing when key is absent."""
    stash = FakeStash()

    result = StashAccess.get_optional(stash, ExampleStashBound)

    assert isinstance(result, Maybe)
    assert result == Nothing


def test_stash_access_get_optional_value_or_none_at_boundary():
    """value_or(None) converts Maybe back to Optional."""
    stash = FakeStash()

    # Miss
    result = StashAccess.get_optional(stash, ExampleStashBound)
    assert result.value_or(None) is None

    # Hit
    instance = ExampleStashBound()
    stash[ExampleStashBound.STASH_KEY] = instance
    result = StashAccess.get_optional(stash, ExampleStashBound)
    assert result.value_or(None) is instance
