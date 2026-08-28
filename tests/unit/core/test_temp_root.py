from __future__ import annotations

from pytest_bdd.util.temp_root import prefer_posix_temp_root
from pytest_bdd.util.toolz_extra import compose, flip


def test_temp_root_and_toolz() -> None:
    assert isinstance(prefer_posix_temp_root(), bool)
    fn = compose(lambda x: x * 2, lambda x: x + 1)
    assert fn(3) == 8
    flipped = flip(lambda a, b: f"{a}-{b}")
    assert flipped("x", "y") == "y-x"
