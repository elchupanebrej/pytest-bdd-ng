from __future__ import annotations

from pytest_bdd.compatibility.sys import get_frame


def test_get_frame() -> None:
    frame = get_frame()
    assert frame is not None
    assert frame.f_code.co_name == "test_get_frame"
