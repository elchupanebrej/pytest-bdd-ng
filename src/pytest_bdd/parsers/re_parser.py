"""
Provide the re step parser.

Responsibility:
    Provide the re step parser. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parsers.re_parser` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - re: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/parsers/facade.py: imports or references `re_parser`
    - src/pytest_bdd/parsers/heuristic.py: imports or references `re_parser`

State and side effects:
    mutates self.pattern, self.regex, type, match, group_dict; depends on __future__.annotations, functools.partial,
    functools.singledispatchmethod, itertools.filterfalse, operator.contains.

Invariants:
    - `pytest_bdd.parsers.re_parser` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

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

from functools import partial, singledispatchmethod
from itertools import filterfalse
from operator import contains
from re import Match
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import TYPE_CHECKING, cast

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.util.other import normalize_to_string

from .base import StepParser, _RegexCompiler, register_parser

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from pytest_bdd.compatibility.pytest import FixtureRequest


class re(StepParser):  # noqa:N801 intentional API
    """
    Regex step parser.

    #arch-eval:score=reason_for_existence:5
    #arch-eval:score=srp_expert:5
    #arch-eval:score=why_not_inline:5
    #arch-eval:score=why_not_split:5
    #arch-eval:score=problems_solved:5
    #arch-eval:score=law_of_demeter:4
    #arch-eval:score=module_location:5

    Responsibility:
        Regex step parser. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.re_parser.re` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _: owns nested behavior below this boundary
        - _: owns nested behavior below this boundary
        - parse_arguments: owns nested behavior below this boundary
        - arguments: owns nested behavior below this boundary
        - is_matching: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_pylint/checkers/noqa_rules.py: imports or references `re`
        - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `re`
        - src/pytest_bdd/_pylint/checkers/typing_rules.py: imports or references `re`
        - src/pytest_bdd/const.py: imports or references `re`
        - src/pytest_bdd/parsers/__init__.py: imports or references `re`

    State and side effects:
        mutates self.pattern, self.regex, type, match, group_dict.

    Invariants:
        - `pytest_bdd.parsers.re_parser.re` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Failure semantics:
        Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

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

    type = StepDefinitionPatternType.pytest_bdd_regular_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]  # mypy limitation with singledispatchmethod/dynamic typing
    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Initialize the re.

        Raises:
            NotImplementedError: If the operation cannot be completed.

        Responsibility:
            Initialize the re. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.re_parser.re.__init__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

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
            keeps no local persistent state beyond call-local values.

        Failure semantics:
            Raises or re-raises NotImplementedError; callers must treat these as boundary failures.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        raise NotImplementedError  # pragma: no cover -- abstract subclass hook

    @__init__.register
    def _(self, pattern: str, *args: object, **kwargs: object) -> None:
        """
        Compile regex.

        Responsibility:
            Compile regex. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.re_parser.re._` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `_`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `_`
            - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `_`
            - src/pytest_bdd/collector_batch.py: imports or references `_`
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `_`

        State and side effects:
            mutates self.pattern, self.regex.

        Invariants:
            - `pytest_bdd.parsers.re_parser.re._` keeps its documented import path, ownership boundary, and observable
              behavior stable for callers.

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
        self.pattern = pattern
        self.regex = cast("_RegexCompiler", re_compile)(self.pattern, *args, **kwargs)

    @__init__.register
    def _(self, pattern: _RePattern) -> None:  # type: ignore[type-arg]  # re.Pattern[str] not a class at runtime
        """
        Compile regex.

        Responsibility:
            Compile regex. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.re_parser.re._` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `_`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `_`
            - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `_`
            - src/pytest_bdd/collector_batch.py: imports or references `_`
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `_`

        State and side effects:
            mutates self.pattern, self.regex.

        Invariants:
            - `pytest_bdd.parsers.re_parser.re._` keeps its documented import path, ownership boundary, and observable
              behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        self.pattern = pattern.pattern
        self.regex = pattern

    def parse_arguments(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object]:
        """
        Parse arguments from step name.

        Args:
            request: Pytest fixture request.
            name: Step name to parse.
            anonymous_group_names: Names for anonymous groups.

        Returns:
            Dictionary of parsed arguments.

        Responsibility:
            Parse arguments from step name. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.re_parser.re.parse_arguments` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - map: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - self.regex.fullmatch: collaborator call used by this boundary
            - match.groupdict: collaborator call used by this boundary
            - group_dict.update: collaborator call used by this boundary
            - zip: collaborator call used by this boundary

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
            mutates match, group_dict.

        Invariants:
            - `pytest_bdd.parsers.re_parser.re.parse_arguments` keeps its documented import path, ownership boundary,
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
        match = cast("Match[str]", self.regex.fullmatch(name))
        group_dict = match.groupdict()
        if anonymous_group_names is not None:
            group_dict.update(
                zip(
                    anonymous_group_names,
                    (
                        name[slice(*span)]
                        for span in filterfalse(
                            partial(contains, [*map(match.span, group_dict.keys())]),
                            map(match.span, range(1, len(match.groups()) + 1)),
                        )
                    ),
                    strict=False,
                ),
            )

        return {k: v for k, v in group_dict.items() if v is not None}

    @property
    def arguments(self) -> Collection[str]:
        """
        Get argument names from the parser.

        Returns:
            Collection of argument names.

        Responsibility:
            Get argument names from the parser. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.re_parser.re.arguments` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.regex.groupindex.keys: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
        return [*self.regex.groupindex.keys()]

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
    ) -> bool:
        """
        Check if name matches the pattern.

        Returns:
            True if matches, False otherwise.

        Responsibility:
            Check if name matches the pattern. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.re_parser.re.is_matching` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - bool: collaborator call used by this boundary
            - self.regex.fullmatch: collaborator call used by this boundary

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
        return bool(self.regex.fullmatch(name))

    def __str__(self) -> str:
        """
        Get parser pattern as string.

        Returns:
            Parser pattern string.

        Responsibility:
            Get parser pattern as string. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.re_parser.re.__str__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - normalize_to_string: collaborator call used by this boundary

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
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        return normalize_to_string(self.pattern)


register_parser(lambda parserlike: isinstance(parserlike, _RePattern), re)
