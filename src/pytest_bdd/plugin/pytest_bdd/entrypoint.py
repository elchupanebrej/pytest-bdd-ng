from collections import deque
from contextlib import suppress
from typing import Optional, Union

import pytest

from messages import PickleStep as Step  # type:ignore[attr-defined]
from pytest_bdd import feature_locator, given, steps, then, when
from pytest_bdd.compatibility.pytest import (
    Config,
    ExitCode,
    FixtureRequest,
    PytestPluginManager,
)
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.const import PYTEST_BDD_MARK
from pytest_bdd.parsers import cucumber_expression
from pytest_bdd.plugin.allure_logger import AllurePytestBDD
from pytest_bdd.plugin.gherkin_message_reporter import GherkinMessageReporter
from pytest_bdd.plugin.pytest_bdd import feature_autoload
from pytest_bdd.plugin.pytest_bdd.plugin import TestCollector
from pytest_bdd.runner import ScenarioRunner
from pytest_bdd.steps import StepHandler
from pytest_bdd.util import code_generation
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.toolz_extra import setdefaultattr

if STRUCT_BDD_INSTALLED:
    from pytest_bdd.struct_bdd.plugin import StructBDDPlugin

from pytest_bdd.compatibility.pytest import Parser


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hooks."""
    from pytest_bdd.plugin.pytest_bdd.hook import PytestBDDHookSpec

    pluginmanager.add_hookspecs(PytestBDDHookSpec)


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    feature_locator.add_options(parser)
    steps.add_options(parser)
    feature_autoload.add_options(parser)
    code_generation.add_options(parser)
    GherkinMessageReporter.add_options(parser)


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    """Configure all subplugins."""
    config.addinivalue_line("markers", f"{PYTEST_BDD_MARK}: marker to identify pytest_bdd tests")
    config.addinivalue_line("markers", "scenarios: marker to provide scenarios locator")
    config.pluginmanager.register(TestCollector())
    config.pluginmanager.register(ScenarioRunner())
    config.pluginmanager.register(GherkinMessageReporter(config=config), name="pytest_bdd_messages")  # type: ignore[call-arg]
    config.__allure_plugin__ = AllurePytestBDD.register_if_allure_accessible(config)  # type: ignore[attr-defined]
    setdefaultattr(config, "pytest_bdd_id_generator", value_factory=IdGenerator)
    if STRUCT_BDD_INSTALLED:
        config.pluginmanager.register(StructBDDPlugin())


@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config: Config) -> None:
    config.pluginmanager.unregister(name="pytest_bdd_messages")
    with suppress(AttributeError):
        config.__allure_plugin__.unregister(config)  # type: ignore[attr-defined]


# TODO Move to the separate plugin
@pytest.hookimpl
def pytest_cmdline_main(config: Config) -> Optional[Union[int, ExitCode]]:
    return code_generation.cmdline_main(config)


@given("trace")
@when("trace")
@then("trace")
def trace() -> None:
    """Enter pytest's pdb trace."""
    pytest.set_trace()


# Defining root step registry
_step_registry = StepHandler.Registry()


@pytest.fixture
def step_registry() -> StepHandler.Registry:
    """Fixture containing registry of all user-defined steps"""
    return _step_registry


step_registry.__pytest_bdd_step_definitions__ = _step_registry  # type: ignore[attr-defined]


@pytest.fixture
def step_matcher(pytestconfig) -> StepHandler.Matcher:
    """Fixture containing matcher to help find step definition for selected step of scenario"""
    return StepHandler.Matcher(pytestconfig)  # type: ignore[call-arg]


@pytest.fixture
def steps_left() -> deque[Step]:
    """Fixture containing steps which are left to be executed"""
    return deque()


@pytest.fixture
def parameter_type_registry():
    """Fixture parameter type registry for Cucumber expressions"""
    return cucumber_expression.parameter_type_registry


@pytest.fixture
def attach(request: FixtureRequest):
    """Fixture parameter type registry for Cucumber expressions"""

    def add_attachment(attachment, media_type: Optional[str] = None, file_name=None):
        request.config.hook.pytest_bdd_attach(
            request=request,
            attachment=attachment,
            media_type=media_type,
            file_name=file_name,
        )

    return add_attachment
