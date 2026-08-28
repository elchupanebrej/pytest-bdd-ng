from __future__ import annotations

from pytest_bdd.compatibility.enum import StrEnum


def test_str_enum() -> None:
    class Color(StrEnum):
        RED = "red"
        BLUE = "blue"

    assert Color.RED == "red"
    assert str(Color.RED) == "red"
    assert Color("red") is Color.RED
