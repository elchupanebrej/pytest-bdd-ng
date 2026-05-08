"""Provide entrypoint helpers."""

from collections import deque
from io import BufferedIOBase, TextIOBase
from typing import TYPE_CHECKING, Protocol

import pytest
from cucumber_messages import PickleStep as Step  # type:ignore[import-untyped]

from pytest_bdd import given, then, when
from pytest_bdd.compatibility.pytest import (
    Config,
    FixtureRequest,
    Parser,
    PytestPluginManager,
)
from pytest_bdd.model.scenario_run import Run
from pytest_bdd.parsers import cucumber_expression
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.util.other import IdGenerator

from .const import Steps
from .plugin import PickleRunner

if TYPE_CHECKING:
    from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry


class AttachmentCallable(Protocol):
    """Represent attachment callable state."""

    def __call__(
        self,
        attachment: str | bytes | bytearray | BufferedIOBase | TextIOBase | object,
        media_type: str | None = None,
        file_name: str | None = None,
        *,
        source_data: str | None = None,
        source_media_type: str | None = None,
        source_uri: str | None = None,
        url: str | None = None,
        as_external: bool = False,
        test_run_hook_started_id: str | None = None,
        test_run_started_id: str | None = None,
    ) -> None:
        """Handle call."""
        ...


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hooks."""
    from .hook import PickleRunnerHookSpec

    pluginmanager.add_hookspecs(PickleRunnerHookSpec)


def pytest_addoption(parser: Parser) -> None:
    """Handle addoption."""
    group = parser.getgroup("bdd", "Steps")
    help_ = "Allow use different keywords with same step definition"
    group.addoption(
        "--liberal-steps",
        action="store_true",
        dest=str(Steps.Cli.LIBERAL_OPTION),
        default=None,
        help=help_,
    )
    parser.addini(
        str(Steps.Ini.LIBERAL_OPTION),
        default=False,
        type="bool",
        help=help_,
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    """Configure all subplugins."""
    runner = PickleRunner()
    config.pluginmanager.register(runner, runner.plugin_name)
    Run.initialize_for_config(stash=config.stash, config=config)
    IdGenerator().initialize_in_stash(config.stash)


@given("trace")
@when("trace")
@then("trace")
def trace() -> None:
    """Enter pytest's pdb trace."""
    pytest.set_trace()


# Defining root step registry
_step_registry = StepDefinitionManager.Registry()


@pytest.fixture
def step_registry() -> StepDefinitionManager.Registry:
    """
    Fixture containing registry of all user-defined steps.

    Returns:
        Step definition registry.

    """
    return _step_registry


step_registry.__pytest_bdd_step_definitions__ = _step_registry  # type: ignore[attr-defined]


@pytest.fixture
def step_matcher(pytestconfig: Config) -> StepDefinitionManager.Matcher:
    """
    Fixture containing matcher to help find step definition for selected step of scenario.

    Returns:
        Step definition matcher.

    """
    return StepDefinitionManager.Matcher(pytestconfig)  # type: ignore[call-arg]


@pytest.fixture
def steps_left() -> deque[Step]:
    """
    Fixture containing steps which are left to be executed.

    Returns:
        Empty deque of steps.

    """
    return deque()


@pytest.fixture
def parameter_type_registry() -> "ParameterTypeRegistry":
    """
    Fixture parameter type registry for Cucumber expressions.

    Returns:
        Parameter type registry.

    """
    return cucumber_expression.parameter_type_registry


@pytest.fixture
def attach(request: FixtureRequest) -> AttachmentCallable:
    """
    Fixture to attach data to test report.

    Returns:
        Attachment callable.

    """

    def add_attachment(
        attachment: str | bytes | bytearray | BufferedIOBase | TextIOBase | object,
        media_type: str | None = None,
        file_name: str | None = None,
        *,
        source_data: str | None = None,
        source_media_type: str | None = None,
        source_uri: str | None = None,
        url: str | None = None,
        as_external: bool = False,
        test_run_hook_started_id: str | None = None,
        test_run_started_id: str | None = None,
    ) -> None:
        request.config.hook.pytest_bdd_attach(
            request=request,
            attachment=attachment,
            media_type=media_type,
            file_name=file_name,
            source_data=source_data,
            source_media_type=source_media_type,
            source_uri=source_uri,
            url=url,
            as_external=as_external,
            test_run_hook_started_id=test_run_hook_started_id,
            test_run_started_id=test_run_started_id,
        )

    return add_attachment


@pytest.fixture(scope="session")
def run_context(request: FixtureRequest) -> Run:
    """
    Session-scoped fixture exposing canonical Run.

    Returns:
        Run instance.

    """
    return Run.from_stash(request.config.stash)
