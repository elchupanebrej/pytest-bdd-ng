from __future__ import annotations

from pytest_cuke.compatibility.struct_bdd import STRUCT_BDD_INSTALLED


def test_struct_bdd_installed_flag() -> None:
    assert isinstance(STRUCT_BDD_INSTALLED, bool)
