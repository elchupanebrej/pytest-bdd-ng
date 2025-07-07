import pytest
from pluggy import HookimplMarker

from pytest_bdd.compatibility.allure import ALLURE_INSTALLED
from pytest_bdd.compatibility.pytest import Config

# from pytest_bdd.util.toolz_extra import flip
# from .plugin import AllureLogger, PatchedAllureListener

if ALLURE_INSTALLED:
    pass
else:
    hookimpl = HookimplMarker("allure")


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    allure_accessible = config.pluginmanager.hasplugin("allure_pytest") and config.option.allure_report_dir
    if not allure_accessible:
        return

    # TODO refactor/reimplement Allure plugin
    # listener = next(
    #     filter(
    #         partial(flip(isinstance), AllureListener),
    #         allure_plugin_manager.get_plugins(),
    #     ), None
    # )
    # if listener is None:
    #     return
    #
    # allure_listener = PatchedAllureListener(listener)
    # allure_plugin_manager.register(allure_listener)
    #
    # allure_logger = AllureLogger(allure_listener)
    # config.pluginmanager.register(allure_logger, name=AllureLogger.plugin_name)
