from __future__ import annotations

from pytest_bdd.const import ALPHA_REGEX, PYTHON_REPLACE_REGEX, TAG_PREFIX


def test_consts() -> None:
    assert TAG_PREFIX == "@"
    assert PYTHON_REPLACE_REGEX.sub("_", "a-b.c") == "a_b_c"
    assert ALPHA_REGEX.match("123_abc") is not None
    assert ALPHA_REGEX.match("abc") is None
