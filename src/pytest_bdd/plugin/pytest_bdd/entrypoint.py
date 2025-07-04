from collections import deque
from typing import Optional

import pytest

from messages import PickleStep as Step  # type:ignore[attr-defined]
from pytest_bdd import given, steps, then, when
from pytest_bdd.compatibility.pytest import (
    Config,
    FixtureRequest,
    Parser,
    PytestPluginManager,
)
from pytest_bdd.parsers import cucumber_expression
from pytest_bdd.runner import ScenarioRunner
from pytest_bdd.steps import StepHandler
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.toolz_extra import setdefaultattr


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hooks."""
    # TODO split hookspec per plugin
    from pytest_bdd.plugin.pytest_bdd.hook import PytestBDDHookSpec

    pluginmanager.add_hookspecs(PytestBDDHookSpec)


def pytest_addoption(parser: Parser) -> None:
    steps.add_options(parser)  # TestRunner


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    """Configure all subplugins."""
    config.pluginmanager.register(ScenarioRunner())
    # TODO Use DI here, don't pass value around plugins in such manner
    setdefaultattr(config, "pytest_bdd_id_generator", value_factory=IdGenerator)


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
