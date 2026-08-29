from __future__ import annotations

import pytest

from pytest_bdd.exceptions import (
    PytestBDDStashAlreadyInitializedError,
    PytestBDDStashLookupError,
    PytestBDDStashTypeMismatchError,
)
from pytest_bdd.model.stash_access import (
    ConfigStash,
    ItemStash,
    SessionStash,
    SimpleStash,
    StashAccess,
    StashBound,
    StashKey,
)


class DummyBound(StashBound):
    STASH_KEY = "dummy_bound_key"


def test_stash_key_and_simple_stash() -> None:
    key: StashKey[str] = StashKey("my_key", "sample key")
    assert repr(key) == "<StashKey 'my_key'>"
    stash = SimpleStash({"initial": 1})
    assert len(stash) == 1 and "initial" in stash and stash["initial"] == 1
    stash["other"] = 2
    assert stash.get("other") == 2
    assert stash.setdefault("other", 99) == 2 and stash.setdefault("new_key", 100) == 100
    del stash["initial"]
    assert "initial" not in stash
    stash.clear()
    assert len(stash) == 0


def test_stash_access_and_stash_bound_lifecycle() -> None:
    stash = SimpleStash()
    bound = DummyBound()
    assert DummyBound.find_in_stash(stash) is None
    with pytest.raises(PytestBDDStashLookupError):
        DummyBound.from_stash(stash)

    bound.set_in_stash(stash)
    assert DummyBound.find_in_stash(stash) is bound
    assert DummyBound.from_stash(stash) is bound

    with pytest.raises(PytestBDDStashAlreadyInitializedError):
        bound.initialize_in_stash(stash)

    stash[DummyBound.STASH_KEY] = "not_a_dummy_bound"
    with pytest.raises(PytestBDDStashTypeMismatchError):
        DummyBound.find_in_stash(stash)
    assert StashAccess.get_optional(stash, "missing_key") is None


def test_proxy_stashes() -> None:
    class Dummy:
        pass

    item, config, session = Dummy(), Dummy(), Dummy()
    item_stash = ItemStash.from_item(item)
    item_stash["k1"] = "v1"
    assert "k1" in item_stash and item_stash.get("k1") == "v1" and item_stash["k1"] == "v1"

    cfg_stash = ConfigStash.from_config(config)
    cfg_stash["k2"] = "v2"
    assert cfg_stash.get("k2") == "v2"

    sess_stash = SessionStash.from_session(session)
    sess_stash["k3"] = "v3"
    assert sess_stash.get("k3") == "v3"
