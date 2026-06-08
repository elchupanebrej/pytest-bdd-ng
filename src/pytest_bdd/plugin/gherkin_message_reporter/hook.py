"""
Provide hook helpers.

Responsibility:
    Provide hook helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.hook` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - GherkinMessageReporterHookSpec: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/hook.py: imports or references `hook`
    - src/pytest_bdd/plugin/code_generator/collection.py: imports or references `hook`
    - src/pytest_bdd/plugin/code_generator/plugin.py: imports or references `hook`
    - src/pytest_bdd/plugin/debug_mcp/artifacts.py: imports or references `hook`
    - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `hook`

State and side effects:
    depends on collections.abc.Callable, pathlib.Path, typing.TYPE_CHECKING, pytest,
    pytest_bdd.compatibility.pytest.Config.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.hook` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.model.message_extension import EventEnvelope

if TYPE_CHECKING:
    from pytest_bdd.plugin.gherkin_message_reporter.session import CucumberFormatterRequest


class GherkinMessageReporterHookSpec:
    """
    Declare hooks used by the gherkin message reporter.

    Responsibility:
        Declare hooks used by the gherkin message reporter. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.hook.GherkinMessageReporterHookSpec` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_bdd_message: owns nested behavior below this boundary
        - pytest_bdd_xdist_message_batch: owns nested behavior below this boundary
        - pytest_bdd_cucumber_formatter_request: owns nested behavior below this boundary
        - pytest_bdd_cucumber_formatter_runtime_assets: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/entrypoint.py: imports or references
          `GherkinMessageReporterHookSpec`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.hook.GherkinMessageReporterHookSpec` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

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

    @pytest.hookspec
    def pytest_bdd_message(self, config: Config, message: EventEnvelope) -> None:
        """
        Implement cucumber message protocol <https://github.com/cucumber/messages>.

        Responsibility:
            Implement cucumber message protocol <https://github.com/cucumber/messages>. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.hook.GherkinMessageReporterHookSpec.pytest_bdd_message` because
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
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `pytest_bdd_message`

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

    @pytest.hookspec
    def pytest_bdd_xdist_message_batch(self, config: Config, node: object, batch: dict[str, object]) -> None:
        """
        Record reporter-specific xdist batch events received on the controller side.

        Responsibility:
            Record reporter-specific xdist batch events received on the controller side. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.hook.GherkinMessageReporterHookSpec.pytest_bdd_xdist_message_batch`
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
            - src/pytest_bdd/plugin/gherkin_message_reporter/message_stream.py: imports or references
              `pytest_bdd_xdist_message_batch`

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

    @pytest.hookspec
    def pytest_bdd_cucumber_formatter_request(
        self,
        config: Config,
        resolve_output_path: Callable[[str], Path],
    ) -> "CucumberFormatterRequest | None":
        """
        Build one formatter runtime request from the current pytest configuration.

        Responsibility:
            Build one formatter runtime request from the current pytest configuration. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.hook.GherkinMessageReporterHookSpec.pytest_bdd_cucumber_formatter_request`
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
            - src/pytest_bdd/plugin/gherkin_message_reporter/session.py: imports or references
              `pytest_bdd_cucumber_formatter_request`

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

    @pytest.hookspec
    def pytest_bdd_cucumber_formatter_runtime_assets(
        self,
        formatter_request: "CucumberFormatterRequest",
        formatter_requests: tuple["CucumberFormatterRequest", ...],
    ) -> dict[str, str] | None:
        """
        Render formatter-specific runtime assets required by the live formatter bridge.

        Responsibility:
            Render formatter-specific runtime assets required by the live formatter bridge. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.hook.GherkinMessageReporterHookSpec.pytest_bdd_cucumber_formatter_runtime_assets`
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
            - src/pytest_bdd/plugin/gherkin_message_reporter/session.py: imports or references
              `pytest_bdd_cucumber_formatter_runtime_assets`

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
