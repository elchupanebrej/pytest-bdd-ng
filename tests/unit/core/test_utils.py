from __future__ import annotations

import pytest
from pytest_bdd import utils

from pytest import mark

pytestmark = mark.unit


def test_utils_pure_facade() -> None:
    funcs = [utils.get_args, utils.data_table_to_dicts, utils.is_local_url, utils.prefer_posix_temp_root, utils.compose]
    assert all(callable(f) for f in funcs)
    assert utils.make_python_name("Some Name") == "some_name"
    assert utils.IdGenerator is not None


def test_caller_module_helpers_report_the_calling_frame() -> None:
    probe = "probe"
    assert utils.get_caller_module_locals(1)["probe"] == probe
    assert utils.get_caller_module_path(1).endswith("test_utils.py")


def test_default_mapping_intercessors() -> None:
    skipped = utils.DefaultMapping.instantiate_from_collection_or_bool(False)
    with pytest.raises(KeyError):
        skipped["missing"]

    upper = utils.DefaultMapping({...: lambda key: key.upper()})
    assert upper["name"] == "NAME"

    constant = utils.DefaultMapping({...: "constant"})
    assert constant["anything"] == "constant"

    identity = utils.DefaultMapping({...: ...})
    assert identity["echo"] == "echo"


def test_getitemdefault_paths() -> None:
    with pytest.raises(ValueError, match="Both 'default' and 'default_factory'"):
        utils.getitemdefault({}, "key", default="value", default_factory=list)

    assert utils.getitemdefault({}, "key", default_factory=lambda: "fallback") == "fallback"
    assert utils.getitemdefault({"key": "value"}, "key") == "value"

    with pytest.raises(KeyError):
        utils.getitemdefault({}, "key")

    with pytest.raises(KeyError):
        utils.getitemdefault({"key": utils.Empty.empty}, "key")


def test_id_generator_from_stash() -> None:
    stash: dict[str, utils.IdGenerator] = {}
    generator = utils.IdGenerator.from_stash(stash)
    assert stash[utils.IdGenerator.pytest_bdd_id_generator] is generator
    assert next(generator) == "0"
    assert utils.IdGenerator.from_stash(stash) is generator

    stateless = utils.IdGenerator.from_stash(object())
    assert next(stateless) == "0"


def test_url_helpers_reject_unparsable_input() -> None:
    assert utils.is_local_url(123) is False
    assert utils.is_local_url("features/example.feature") is True
    assert utils.is_url_parsable("http://[invalid-ipv6") is False
    assert utils.is_url_parsable("https://example.com") is True
