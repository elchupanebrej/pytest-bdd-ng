import pytest
from pluggy import HookimplMarker

from pytest_bdd.compatibility.allure import ALLURE_INSTALLED
from pytest_bdd.compatibility.pytest import (
    PYTEST81,
    Config,
)
from pytest_bdd.plugin.allure_logger.plugin import AllureLogger

if ALLURE_INSTALLED:
    from allure_commons import plugin_manager as allure_plugin_manager
    from allure_pytest.listener import AllureListener
else:
    hookimpl = HookimplMarker("allure")


def _check_allure_accessible(config: Config):
    return config.pluginmanager.hasplugin("allure_pytest") and config.option.allure_report_dir


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    pluginmanager = config.pluginmanager
    if _check_allure_accessible(config) and not PYTEST81:
        allure_plugin_manager.get_plugins()

        listener = next(
            filter(
                lambda plugin: isinstance(plugin, AllureListener),
                allure_plugin_manager.get_plugins(),
            ),
        )

        allure_logger = AllureLogger(listener.allure_logger, listener._cache)
        allure_logger.allure_plugin_name = allure_plugin_manager.register(allure_logger)
        allure_logger.pytest_plugin_name = pluginmanager.register(allure_logger, name=AllureLogger.plugin_name)


@pytest.mark.trylast
def pytest_unconfigure(config: Config) -> None:
    if _check_allure_accessible(config) and not PYTEST81:
        config.pluginmanager.unregister(AllureLogger.plugin_name)
