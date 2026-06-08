"""
Provide entrypoint helpers.

Responsibility:
    Provide entrypoint helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_terminal_reporter.entrypoint` because it keeps
    the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - pytest_addoption: owns nested behavior below this boundary
    - pytest_configure: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/cucumber_formatter_support/registry.py: imports or references `entrypoint`

State and side effects:
    mutates group, current_reporter, gherkin_reporter, msg; depends on pytest, pytest_bdd.compatibility.pytest.Config,
    pytest_bdd.compatibility.pytest.Parser, pytest_bdd.compatibility.pytest.TerminalReporter,
    exception.IncompatiblePluginConfigurationError.

Invariants:
    - `pytest_bdd.plugin.gherkin_terminal_reporter.entrypoint` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises IncompatiblePluginError, IncompatiblePluginConfigurationError; callers must treat these as
    boundary failures.

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

import pytest

from pytest_bdd.compatibility.pytest import Config, Parser, TerminalReporter

from .exception import IncompatiblePluginConfigurationError, IncompatiblePluginError
from .plugin import GherkinTerminalReporterPlugin


def pytest_addoption(parser: Parser) -> None:
    """
    Handle addoption.

    Responsibility:
        Handle addoption. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_terminal_reporter.entrypoint.pytest_addoption` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - parser.getgroup: collaborator call used by this boundary
        - group._addoption: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `pytest_addoption`

    State and side effects:
        mutates group.

    Invariants:
        - `pytest_bdd.plugin.gherkin_terminal_reporter.entrypoint.pytest_addoption` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
    group = parser.getgroup("terminal reporting", "reporting", after="general")  # type: ignore[call-arg]  # pytest Parser.getgroup after kwarg
    group._addoption(  # noqa: SLF001
        "--gherkin-terminal-reporter",
        action="store_true",
        dest="gherkin_terminal_reporter",
        default=False,
        help="enable gherkin output",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    """
    Handle configure.

    Raises:
        IncompatiblePluginError: If the operation cannot be completed.
        IncompatiblePluginConfigurationError: If the operation cannot be completed.

    Responsibility:
        Handle configure. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_terminal_reporter.entrypoint.pytest_configure` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - config.pluginmanager.getplugin: collaborator call used by this boundary
        - IncompatiblePluginError: collaborator call used by this boundary
        - GherkinTerminalReporterPlugin: collaborator call used by this boundary
        - config.pluginmanager.unregister: collaborator call used by this boundary
        - config.pluginmanager.register: collaborator call used by this boundary
        - IncompatiblePluginConfigurationError: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates current_reporter, gherkin_reporter, msg.

    Invariants:
        - `pytest_bdd.plugin.gherkin_terminal_reporter.entrypoint.pytest_configure` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises IncompatiblePluginError, IncompatiblePluginConfigurationError; callers must treat these as
        boundary failures.

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
    if config.option.gherkin_terminal_reporter:
        # Get the standard terminal reporter plugin and replace it with our
        current_reporter = config.pluginmanager.getplugin("terminalreporter")
        if current_reporter.__class__ != TerminalReporter:
            raise IncompatiblePluginError(current_reporter)
        gherkin_reporter = GherkinTerminalReporterPlugin(config)
        config.pluginmanager.unregister(current_reporter)
        config.pluginmanager.register(gherkin_reporter, "terminalreporter")
        if config.pluginmanager.getplugin("dsession"):
            msg = "xdist"
            raise IncompatiblePluginConfigurationError(msg)
