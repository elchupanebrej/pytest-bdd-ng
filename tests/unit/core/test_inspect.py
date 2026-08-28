from __future__ import annotations

from pytest_bdd.util.inspect_extra import (
    get_args,
    get_caller_module_locals,
    get_caller_module_path,
    get_first_source_line,
)


def sample_func(a: int, b: str = "x") -> None:
    pass


def test_inspect_helpers() -> None:
    local_val = 42
    assert list(get_args(sample_func)) == ["a", "b"]
    assert get_first_source_line(sample_func) > 0
    assert get_caller_module_locals(1)["local_val"] == local_val
    assert get_caller_module_path(1).endswith("test_inspect.py")
