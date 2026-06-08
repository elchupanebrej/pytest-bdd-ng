"""
Provide runtime contract helpers.

Responsibility:
    Provide runtime contract helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.runtime_contract` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - ReporterLifecycleContract: owns nested behavior below this boundary
    - FormatterRenderingContract: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references `runtime_contract`

State and side effects:
    mutates QuietTerminalRestorer, QuietTerminalReplacer, plugin_name; depends on __future__.annotations,
    collections.abc.Callable, typing.TYPE_CHECKING, typing.Protocol, typing.runtime_checkable.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.runtime_contract` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

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

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pytest_bdd.compatibility.pytest import Config, PytestPluginManager

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_bdd.model.message_extension import EventEnvelope
    from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRenderResult

QuietTerminalRestorer = Callable[[], None] | None
QuietTerminalReplacer = Callable[[Config], QuietTerminalRestorer]


@runtime_checkable
class ReporterLifecycleContract(Protocol):
    """
    Represent reporter lifecycle contract state.

    Responsibility:
        Represent reporter lifecycle contract state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_contract.ReporterLifecycleContract` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - configure: owns nested behavior below this boundary
        - unconfigure: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `ReporterLifecycleContract`

    State and side effects:
        mutates plugin_name.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.runtime_contract.ReporterLifecycleContract` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

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

    plugin_name: str

    def configure(
        self,
        *,
        pluginmanager: PytestPluginManager,
        quiet_terminal_replacer: QuietTerminalReplacer,
    ) -> None:
        """
        Configure configure.

        Responsibility:
            Configure configure. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.runtime_contract.ReporterLifecycleContract.configure` because it
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
            - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references `configure`

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
            #arch-eval:locational_stability=3
        """
        ...

    def unconfigure(self, *, pluginmanager: PytestPluginManager) -> None:
        """
        Handle unconfigure.

        Responsibility:
            Handle unconfigure. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.runtime_contract.ReporterLifecycleContract.unconfigure` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references `unconfigure`

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
            #arch-eval:locational_stability=3
        """
        ...


@runtime_checkable
class FormatterRenderingContract(Protocol):
    """
    Handle formatter rendering contract.

    Responsibility:
        Handle formatter rendering contract. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.runtime_contract.FormatterRenderingContract` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - read_envelopes_from_path: owns nested behavior below this boundary
        - render_requested_cucumber_formatters_from_path: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `FormatterRenderingContract`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.runtime_contract.FormatterRenderingContract` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    def read_envelopes_from_path(self, messages_file_path: Path) -> list[EventEnvelope]:
        """
        Read envelopes from path.

        Responsibility:
            Read envelopes from path. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.runtime_contract.FormatterRenderingContract.read_envelopes_from_path`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
              `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/standalone_renderer.py: imports or references
              `read_envelopes_from_path`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `read_envelopes_from_path`

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
        ...

    def render_requested_cucumber_formatters_from_path(
        self,
        messages_file_path: Path,
    ) -> CucumberFormatterRenderResult:
        """
        Render requested cucumber formatters from path.

        Responsibility:
            Render requested cucumber formatters from path. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.runtime_contract.FormatterRenderingContract.render_requested_cucumber_formatters_from_path`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
              `render_requested_cucumber_formatters_from_path`

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
            #arch-eval:locational_stability=3
        """
        ...
