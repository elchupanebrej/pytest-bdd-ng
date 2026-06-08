"""
Provide the string step parser.

Responsibility:
    Provide the string step parser. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parsers.string_parser` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - string: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/parsers/facade.py: imports or references `string_parser`
    - src/pytest_bdd/parsers/heuristic.py: imports or references `string_parser`

State and side effects:
    mutates type, self.name; depends on __future__.annotations, typing.TYPE_CHECKING,
    pytest_bdd.model.message_extension.StepDefinitionPatternType, pytest_bdd.util.other.StringRepresentable,
    pytest_bdd.util.other.normalize_to_string.

Invariants:
    - `pytest_bdd.parsers.string_parser` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.util.other import StringRepresentable, normalize_to_string

from .base import StepParser

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from pytest_bdd.compatibility.pytest import FixtureRequest


class string(StepParser):  # noqa: N801 intentional API
    """
    Exact string step parser.

    Responsibility:
        Exact string step parser. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.string_parser.string` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - parse_arguments: owns nested behavior below this boundary
        - arguments: owns nested behavior below this boundary
        - is_matching: owns nested behavior below this boundary
        - __str__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `string`
        - src/pytest_bdd/parsers/facade.py: imports or references `string`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `string`
        - src/pytest_bdd/plugin/code_generator/rendering.py: imports or references `string`
        - src/pytest_bdd/util/other.py: imports or references `string`

    State and side effects:
        mutates type, self.name.

    Invariants:
        - `pytest_bdd.parsers.string_parser.string` keeps its documented import path, ownership boundary, and observable
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
        #arch-eval:locational_stability=4
    """

    type = StepDefinitionPatternType.pytest_bdd_string_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    def __init__(self, name: StringRepresentable | str | bytes) -> None:
        """
        Initialize the string.

        Responsibility:
            Initialize the string. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.string_parser.string.__init__` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - normalize_to_string: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self.name.

        Invariants:
            - `pytest_bdd.parsers.string_parser.string.__init__` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self.name = normalize_to_string(name)

    def parse_arguments(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,  # noqa: ARG002 overload
        anonymous_group_names: Iterable[str] | None = None,  # noqa: ARG002 overload
    ) -> dict[str, object]:
        """
        Parse arguments - no parameters for string step.

        Returns:
            Empty dictionary.

        Responsibility:
            Parse arguments - no parameters for string step. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.string_parser.string.parse_arguments` because
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
            - src/pytest_bdd/parsers/facade.py: imports or references `parse_arguments`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `parse_arguments`
            - src/pytest_bdd/plugin/gherkin_message_reporter/step_catalog_runtime/_static_helpers.py: imports or
              references `parse_arguments`
            - src/pytest_bdd/steps/definition.py: imports or references `parse_arguments`

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
        return {}

    @property
    def arguments(self) -> Collection[str]:
        """
        Get argument names.

        Returns:
            Empty list for string parser.

        Responsibility:
            Get argument names. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.string_parser.string.arguments` because it
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
            - src/pytest_bdd/feature_locator.py: imports or references `arguments`
            - src/pytest_bdd/parsers/facade.py: imports or references `arguments`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `arguments`
            - src/pytest_bdd/plugin/cucumber_json/model.py: imports or references `arguments`
            - src/pytest_bdd/steps/definition.py: imports or references `arguments`

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
        return []

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
    ) -> bool:
        """
        Match given name with the step name.

        Returns:
            True if matches, False otherwise.

        Responsibility:
            Match given name with the step name. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.string_parser.string.is_matching` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - bool: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `is_matching`
            - src/pytest_bdd/parsers/facade.py: imports or references `is_matching`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `is_matching`
            - src/pytest_bdd/steps/matcher.py: imports or references `is_matching`

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
        return bool(self.name == name)

    def __str__(self) -> str:
        """
        Get the exact step name.

        Returns:
            Step name string.

        Responsibility:
            Get the exact step name. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.string_parser.string.__str__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/facade.py: imports or references `__str__`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `__str__`

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
        return self.name
