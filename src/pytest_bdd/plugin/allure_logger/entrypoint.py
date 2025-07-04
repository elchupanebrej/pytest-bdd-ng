from functools import partial
from operator import ge

import pytest
from pluggy import HookimplMarker

from pytest_bdd.compatibility.allure import ALLURE_INSTALLED
from pytest_bdd.compatibility.pytest import PYTEST81, Config
from pytest_bdd.plugin.allure_logger.plugin import AllureLogger, PatchedAllureListener
from pytest_bdd.util.packaging import compare_distribution_version
from pytest_bdd.util.toolz_extra import flip

if ALLURE_INSTALLED:
    from allure_commons import plugin_manager as allure_plugin_manager
    from allure_pytest.listener import AllureListener
else:
    hookimpl = HookimplMarker("allure")


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    allure_accessible = config.pluginmanager.hasplugin("allure_pytest") and config.option.allure_report_dir
    if PYTEST81 or not allure_accessible:
        return

    listener = next(
        filter(
            partial(flip(isinstance), AllureListener),
            allure_plugin_manager.get_plugins(),
        ),
    )

    if compare_distribution_version("allure-python-commons", "2.14.2", ge):
        allure_listener = listener
    else:
        allure_listener = PatchedAllureListener(listener)
        allure_plugin_manager.register(allure_listener)

    allure_logger = AllureLogger(allure_listener)
    config.pluginmanager.register(allure_logger, name=AllureLogger.plugin_name)
