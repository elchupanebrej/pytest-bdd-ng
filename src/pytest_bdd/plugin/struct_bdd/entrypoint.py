import pytest

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED

if STRUCT_BDD_INSTALLED:
    from pytest_bdd.plugin.struct_bdd.plugin import StructBDDPlugin

if STRUCT_BDD_INSTALLED:

    @pytest.hookimpl(trylast=True)
    def pytest_configure(config: Config) -> None:
        config.pluginmanager.register(StructBDDPlugin())
