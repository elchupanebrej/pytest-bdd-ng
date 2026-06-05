"""Integration coverage for compatibility shims."""

from __future__ import annotations

import pytest

from pytest_bdd.compatibility.enum import StrEnum

pytestmark = [pytest.mark.unit]


class CompatibilityEnum(StrEnum):
    A = "a"


def test_strenum_behaves_like_string() -> None:
    assert CompatibilityEnum.A == "a"
    assert CompatibilityEnum.A.value == "a"
    assert isinstance(CompatibilityEnum.A, str)
