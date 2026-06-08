"""
Provide entrypoint helpers.

Responsibility:
    Provide entrypoint helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - AttachmentCallable: owns nested behavior below this boundary
    - pytest_addhooks: owns nested behavior below this boundary
    - pytest_addoption: owns nested behavior below this boundary
    - pytest_configure: owns nested behavior below this boundary
    - trace: owns nested behavior below this boundary
    - step_registry: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `entrypoint`

State and side effects:
    mutates group, help_, runner, _step_registry, step_registry.__pytest_bdd_step_registry__; depends on
    collections.deque, io.BufferedIOBase, io.TextIOBase, typing.TYPE_CHECKING, typing.Protocol.

Invariants:
    - `pytest_bdd.plugin.pickle_runner.entrypoint` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

from collections import deque
from io import BufferedIOBase, TextIOBase
from typing import TYPE_CHECKING, Protocol, cast

import pytest
from cucumber_messages import PickleStep as Step  # library has no type stubs

from pytest_bdd import given, then, when
from pytest_bdd.compatibility.pytest import (
    Config,
    FixtureRequest,
    Parser,
    PytestPluginManager,
)
from pytest_bdd.model.run import Run
from pytest_bdd.parsers import cucumber_expression
from pytest_bdd.steps import Matcher, Registry, StepDefinitionManager
from pytest_bdd.util.other import IdGenerator

from .const import Steps
from .hook import PickleRunnerHookSpec
from .plugin import PickleRunnerPlugin

if TYPE_CHECKING:
    from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry


class AttachmentCallable(Protocol):
    """
    Represent attachment callable state.

    Responsibility:
        Represent attachment callable state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.AttachmentCallable`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __call__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.entrypoint.AttachmentCallable` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=2
    """

    def __call__(  # noqa: PLR0913
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
        """
        Handle call.

        Responsibility:
            Handle call. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.pickle_runner.entrypoint.AttachmentCallable.__call__` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=2
        """
        ...


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """
    Register plugin hooks.

    Responsibility:
        Register plugin hooks. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.pytest_addhooks` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pluginmanager.add_hookspecs: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_addhooks`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    pluginmanager.add_hookspecs(PickleRunnerHookSpec)


def pytest_addoption(parser: Parser) -> None:
    """
    Handle addoption.

    Responsibility:
        Handle addoption. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.pytest_addoption` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - group.addoption: collaborator call used by this boundary
        - parser.getgroup: collaborator call used by this boundary
        - parser.addini: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_addoption`

    State and side effects:
        mutates group, help_.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.entrypoint.pytest_addoption` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    group = parser.getgroup("bdd", "Steps")
    help_ = "Allow use different keywords with same step definition"
    group.addoption(
        "--liberal-steps",
        action="store_true",
        dest=str(Steps.Cli.LIBERAL_OPTION),
        default=None,
        help=help_,
    )
    group.addoption(
        "--mock-run",
        action="store_true",
        dest=str(Steps.Cli.MOCK_RUN),
        default=False,
        help="Verify BDD scenario collection and binding without executing scenario or step lifecycle.",
    )
    group.addoption(
        "--wip-status",
        action="store",
        choices=["passed", "skipped", "failed"],
        dest=str(Steps.Cli.WIP_STATUS),
        default="failed",
        help="Status for @not_implemented steps.",
    )
    group.addoption(
        "--tolerant-status",
        action="store",
        choices=["failed", "ignored"],
        dest=str(Steps.Cli.TOLERANT_STATUS),
        default="failed",
        help="Status for @tolerant step failures.",
    )
    parser.addini(
        str(Steps.Ini.LIBERAL_OPTION),
        default=False,
        type="bool",
        help=help_,
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    """
    Configure all subplugins.

    Responsibility:
        Configure all subplugins. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.pytest_configure` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - config.addinivalue_line: collaborator call used by this boundary
        - PickleRunnerPlugin: collaborator call used by this boundary
        - config.pluginmanager.register: collaborator call used by this boundary
        - Run.initialize_for_config: collaborator call used by this boundary
        - IdGenerator.initialize_in_stash: collaborator call used by this boundary
        - IdGenerator: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates runner.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.entrypoint.pytest_configure` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    config.addinivalue_line("markers", "wip_status(status): override @not_implemented step status")
    config.addinivalue_line("markers", "wip-status-passed: mark WIP steps as passed")
    config.addinivalue_line("markers", "wip-status-skipped: mark WIP steps as skipped")
    config.addinivalue_line("markers", "wip-status-failed: mark WIP steps as failed")
    config.addinivalue_line("markers", "tolerant_status(status): override @tolerant step status")
    config.addinivalue_line("markers", "tolerant-status-ignored: mark tolerant step failures as ignored")
    config.addinivalue_line("markers", "tolerant-status-failed: mark tolerant step failures as failed")
    runner = PickleRunnerPlugin()
    config.pluginmanager.register(runner, runner.plugin_name)
    Run.initialize_for_config(stash=config.stash, config=config)
    IdGenerator().initialize_in_stash(config.stash)


@given("trace")
@when("trace")
@then("trace")
def trace() -> None:
    """
    Enter pytest's pdb trace.

    Responsibility:
        Enter pytest's pdb trace. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.trace` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest.set_trace: collaborator call used by this boundary
        - given: collaborator call used by this boundary
        - when: collaborator call used by this boundary
        - then: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    pytest.set_trace()


# Defining root step registry
import sys

_step_registry = StepDefinitionManager.Registry(sys.modules[__name__])


@pytest.fixture
def step_registry() -> Registry:
    """
    Fixture containing registry of all user-defined steps.

    Returns:
        Step definition registry.

    Responsibility:
        Fixture containing registry of all user-defined steps. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.step_registry` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_core.py: imports or references
          `step_registry`
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `step_registry`
        - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references `step_registry`
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `step_registry`
        - src/pytest_bdd/steps/matcher.py: imports or references `step_registry`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4

    """
    return _step_registry


step_registry.__pytest_bdd_step_registry__ = _step_registry  # upstream type stubs missing this attribute


@pytest.fixture
def step_matcher(pytestconfig: Config) -> Matcher:
    """
    Fixture containing matcher to help find step definition for selected step of scenario.

    Returns:
        Step definition matcher.

    Responsibility:
        Fixture containing matcher to help find step definition for selected step of scenario. It directly owns the
        observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.step_matcher` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - StepDefinitionManager.Matcher: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `step_matcher`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    return StepDefinitionManager.Matcher(pytestconfig)  # pydantic v1 compatibility in pydantic v2


@pytest.fixture
def steps_left() -> deque[Step]:
    """
    Fixture containing steps which are left to be executed.

    Returns:
        Empty deque of steps.

    Responsibility:
        Fixture containing steps which are left to be executed. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.steps_left` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - deque: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    return deque()


@pytest.fixture
def parameter_type_registry() -> "ParameterTypeRegistry":
    """
    Fixture parameter type registry for Cucumber expressions.

    Returns:
        Parameter type registry.

    Responsibility:
        Fixture parameter type registry for Cucumber expressions. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.parameter_type_registry`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/cucumber_expression.py: imports or references `parameter_type_registry`
        - src/pytest_bdd/parsers/cucumber_regex.py: imports or references `parameter_type_registry`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `parameter_type_registry`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `parameter_type_registry`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
          `parameter_type_registry`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    return cast("ParameterTypeRegistry", cucumber_expression.parameter_type_registry)


@pytest.fixture
def attach(request: FixtureRequest) -> AttachmentCallable:
    """
    Fixture to attach data to test report.

    Returns:
        Attachment callable.

    Responsibility:
        Fixture to attach data to test report. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.attach` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - add_attachment: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """

    def add_attachment(  # noqa: PLR0913
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
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.entrypoint.attach.add_attachment` owns
            documented function behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this function.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.attach.add_attachment`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - request.config.hook.pytest_bdd_attach: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - None found by static import/name scan; verify dynamic use before refactor

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=2
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=2
        """
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


@pytest.fixture(scope="session")  # type: ignore[untyped-decorator]  # pytest fixture returns untyped Callable
def run_context(request: FixtureRequest) -> Run:
    """
    Session-scoped fixture exposing canonical Run.

    Returns:
        Run instance.

    Responsibility:
        Session-scoped fixture exposing canonical Run. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.entrypoint.run_context` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Run.from_stash: collaborator call used by this boundary
        - pytest.fixture: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    return Run.from_stash(request.config.stash)
