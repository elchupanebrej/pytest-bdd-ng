"""
Provide hook helpers.

Responsibility:
    Provide hook helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.scenario_test_collector.hook` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - ScenarioTestCollectorHookSpec: owns nested behavior below this boundary

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
    depends on collections.abc.Iterable, pathlib.Path, pytest, cucumber_messages.GherkinDocument,
    cucumber_messages.Pickle.

Invariants:
    - `pytest_bdd.plugin.scenario_test_collector.hook` keeps its documented import path, ownership boundary, and
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

from collections.abc import Iterable
from pathlib import Path

import pytest
from cucumber_messages import (  # upstream library missing type stubs
    GherkinDocument,
    Pickle,
    Source,
)

from pytest_bdd.compatibility.pytest import Config, Mark
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.parser import ParserProtocol  # type: ignore[attr-defined]  # re-exported from compatibility module


class ScenarioTestCollectorHookSpec:
    """
    Declare hooks used by the scenario test collector.

    Responsibility:
        Declare hooks used by the scenario test collector. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.scenario_test_collector.hook.ScenarioTestCollectorHookSpec` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pytest_bdd_is_collectible: owns nested behavior below this boundary
        - pytest_bdd_get_parser: owns nested behavior below this boundary
        - pytest_bdd_get_mimetype: owns nested behavior below this boundary
        - pytest_bdd_convert_tag_to_marks: owns nested behavior below this boundary
        - pytest_bdd_source_read: owns nested behavior below this boundary
        - pytest_bdd_feature_read: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py: imports or references
          `ScenarioTestCollectorHookSpec`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.plugin.scenario_test_collector.hook.ScenarioTestCollectorHookSpec` keeps its documented import
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

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_is_collectible(self, config: Config, path: Path) -> bool | None:
        """
        Verify if path could be collected by pytest_bdd.

        Responsibility:
            Verify if path could be collected by pytest_bdd. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.hook.ScenarioTestCollectorHookSpec.pytest_bdd_is_collectible`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - pytest.hookspec: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `pytest_bdd_is_collectible`

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

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_parser(self, config: Config, mimetype: str) -> type[ParserProtocol] | None:
        """
        Get parser for specific file path.

        Responsibility:
            Get parser for specific file path. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.hook.ScenarioTestCollectorHookSpec.pytest_bdd_get_parser` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - pytest.hookspec: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `pytest_bdd_get_parser`
            - src/pytest_bdd/scenario_locator/url_locator.py: imports or references `pytest_bdd_get_parser`

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

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_mimetype(self, config: Config, path: Path) -> Mimetype | None:
        """
        Get parser for specific file path.

        Responsibility:
            Get parser for specific file path. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.hook.ScenarioTestCollectorHookSpec.pytest_bdd_get_mimetype`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - pytest.hookspec: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/scenario_locator/file_locator.py: imports or references `pytest_bdd_get_mimetype`

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

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_convert_tag_to_marks(
        self,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        tag: str,
    ) -> Iterable[Mark] | None:
        """
        Apply a tag (from a ``.feature`` file) to the given test item.

        The default implementation does the equivalent of
        ``getattr(pytest.mark, tag)(function)``, but you can override this hook and
        return ``True`` to do more sophisticated handling of tags.

        Responsibility:
            Apply a tag (from a ``.feature`` file) to the given test item. It directly owns the observable contract,
            local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.hook.ScenarioTestCollectorHookSpec.pytest_bdd_convert_tag_to_marks`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - pytest.hookspec: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/scenario_test_collector/_helpers.py: imports or references
              `pytest_bdd_convert_tag_to_marks`

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

    def pytest_bdd_source_read(self, config: Config, gherkin_document: GherkinDocument, source: Source) -> None:
        """
        Notify plugins that source payload for feature was read during collection.

        Responsibility:
            Notify plugins that source payload for feature was read during collection. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.hook.ScenarioTestCollectorHookSpec.pytest_bdd_source_read`
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
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `pytest_bdd_source_read`

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

    def pytest_bdd_feature_read(self, config: Config, gherkin_document: GherkinDocument) -> None:
        """
        Notify plugins that gherkin document payload for feature was read during collection.

        Responsibility:
            Notify plugins that gherkin document payload for feature was read during collection. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.hook.ScenarioTestCollectorHookSpec.pytest_bdd_feature_read`
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
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `pytest_bdd_feature_read`

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

    def pytest_bdd_pickle_read(self, config: Config, gherkin_document: GherkinDocument, pickle: Pickle) -> None:
        """
        Notify plugins that pickle payload was materialized during collection.

        Responsibility:
            Notify plugins that pickle payload was materialized during collection. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.scenario_test_collector.hook.ScenarioTestCollectorHookSpec.pytest_bdd_pickle_read`
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
            - src/pytest_bdd/plugin/scenario_test_collector/plugin.py: imports or references `pytest_bdd_pickle_read`

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
