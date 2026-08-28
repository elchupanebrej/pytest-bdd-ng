from __future__ import annotations

from pytest_bdd import utils


def test_utils_pure_facade() -> None:
    funcs = [utils.get_args, utils.data_table_to_dicts, utils.is_local_url, utils.prefer_posix_temp_root, utils.compose]
    assert all(callable(f) for f in funcs)
    assert utils.make_python_name("Some Name") == "some_name"
    assert utils.IdGenerator is not None
