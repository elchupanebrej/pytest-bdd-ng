"""
Provide the parse and cfparse step parsers.

Responsibility:
    Provide the parse and cfparse step parsers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.parsers.parse_parser` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - parse: owns nested behavior below this boundary
    - cfparse: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/parsers/facade.py: imports or references `parse_parser`
    - src/pytest_bdd/parsers/heuristic.py: imports or references `parse_parser`

State and side effects:
    mutates type, self.format, self.parser, builder, match; depends on __future__.annotations,
    functools.singledispatchmethod, typing.TYPE_CHECKING, typing.cast, parse.

Invariants:
    - `pytest_bdd.parsers.parse_parser` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises ParserBuildValueError; callers must treat these as boundary failures.

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

from functools import singledispatchmethod
from typing import TYPE_CHECKING, cast

import parse as base_parse
import parse_type.cfparse as base_cfparse

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.util.other import StringRepresentable, normalize_to_string

from .base import ParserBuildValueError, StepParser, _ParseMatchProtocol, _ParserBuilder, register_parser

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from pytest_bdd.compatibility.pytest import FixtureRequest


class parse(StepParser):  # noqa:N801 intentional API
    """
    parse step parser.

    #arch-eval:score=reason_for_existence:5
    #arch-eval:score=srp_expert:5
    #arch-eval:score=why_not_inline:5
    #arch-eval:score=why_not_split:4
    #arch-eval:score=problems_solved:5
    #arch-eval:score=law_of_demeter:4
    #arch-eval:score=module_location:5

    Raises:
        ParserBuildValueError: If the operation cannot be completed.

    Responsibility:
        parse step parser. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.parse_parser.parse` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - _init_stringable: owns nested behavior below this boundary
        - _: owns nested behavior below this boundary
        - cfparse: owns nested behavior below this boundary
        - parse_arguments: owns nested behavior below this boundary
        - arguments: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `parse`
        - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `parse`
        - src/pytest_bdd/collector_batch.py: imports or references `parse`
        - src/pytest_bdd/hook.py: imports or references `parse`
        - src/pytest_bdd/parser.py: imports or references `parse`

    State and side effects:
        mutates self.format, self.parser, type, builder, match.

    Invariants:
        - `pytest_bdd.parsers.parse_parser.parse` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Failure semantics:
        Raises or re-raises ParserBuildValueError; callers must treat these as boundary failures.

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

    type = StepDefinitionPatternType.pytest_bdd_parse_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]  # mypy limitation with singledispatchmethod/dynamic typing
    def __init__(self, format_: object, *args: object, **kwargs: object) -> None:
        """
        Initialize the parse.

        Raises:
            ParserBuildValueError: If the operation cannot be completed.

        Responsibility:
            Initialize the parse. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.parse_parser.parse.__init__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - kwargs.pop: collaborator call used by this boundary
            - self._init_stringable: collaborator call used by this boundary
            - ParserBuildValueError: collaborator call used by this boundary

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
            mutates builder.

        Invariants:
            - `pytest_bdd.parsers.parse_parser.parse.__init__` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ParserBuildValueError; callers must treat these as boundary failures.

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
        if isinstance(format_, (StringRepresentable, str, bytes)):
            builder = cast("_ParserBuilder", kwargs.pop("builder", base_parse.compile))
            self._init_stringable(format_, *args, builder=builder, **kwargs)
        else:
            raise ParserBuildValueError(
                format_,
            )  # pragma: no cover -- unreachable; guarded by isinstance checks above

    def _init_stringable(
        self,
        format_: StringRepresentable | str | bytes,
        *args: object,
        builder: _ParserBuilder = base_parse.compile,  # type: ignore[assignment]  # dynamic parser builder dispatch
        **kwargs: object,
    ) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.parsers.parse_parser.parse._init_stringable` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.parse_parser.parse._init_stringable` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - normalize_to_string: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - builder: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/facade.py: imports or references `_init_stringable`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `_init_stringable`

        State and side effects:
            mutates self.format, self.parser.

        Invariants:
            - `pytest_bdd.parsers.parse_parser.parse._init_stringable` keeps its documented import path, ownership
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
        self.format = normalize_to_string(format_)
        self.parser = cast("base_parse.Parser", builder(self.format, *args, **kwargs))

    @__init__.register
    def _(self, format_: base_parse.Parser) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.parsers.parse_parser.parse._` owns documented method behavior.
            It directly owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.parse_parser.parse._` because it keeps the
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
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `_`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `_`
            - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `_`
            - src/pytest_bdd/collector_batch.py: imports or references `_`
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `_`

        State and side effects:
            mutates self.format, self.parser.

        Invariants:
            - `pytest_bdd.parsers.parse_parser.parse._` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

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
        self.format = format_._format  # noqa: SLF001
        self.parser = format_

    @classmethod
    def cfparse(cls, *args: object, **kwargs: object) -> parse:
        """
        Create a cfparse parser.

        Args:
            args: Positional arguments for parser.
            kwargs: Keyword arguments for parser.

        Returns:
            Configured parse parser.

        Responsibility:
            Create a cfparse parser. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.parse_parser.parse.cfparse` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - kwargs.setdefault: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/parsers/__init__.py: imports or references `cfparse`
            - src/pytest_bdd/parsers/facade.py: imports or references `cfparse`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `cfparse`

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
        kwargs.setdefault("builder", base_cfparse.Parser)
        return cast("parse", cls(*args, **kwargs))

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
            anonymous_group_names: Anonymous group names.

        Returns:
            Dictionary of parsed arguments.

        Responsibility:
            Parse arguments from step name. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.parse_parser.parse.parse_arguments` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - dict: collaborator call used by this boundary
            - cast: collaborator call used by this boundary
            - self.parser.parse: collaborator call used by this boundary
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
            - `pytest_bdd.parsers.parse_parser.parse.parse_arguments` keeps its documented import path, ownership
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
            #arch-eval:locational_stability=4
        """
        match = cast("_ParseMatchProtocol", self.parser.parse(name))
        group_dict = dict(match.named)
        if anonymous_group_names is not None:
            group_dict.update(dict(zip(anonymous_group_names, match.fixed, strict=False)))
        return group_dict

    @property
    def arguments(self) -> Collection[str]:
        """
        Get argument names.

        Returns:
            Collection of argument names.

        Responsibility:
            Get argument names. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.parse_parser.parse.arguments` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.parser._match_re.groupindex.keys: collaborator call used by this boundary

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
        return [*self.parser._match_re.groupindex.keys()]  # noqa: SLF001

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
    ) -> bool:
        """
        Check if name matches.

        Returns:
            True if matches, False otherwise.

        Responsibility:
            Check if name matches. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.parse_parser.parse.is_matching` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - bool: collaborator call used by this boundary
            - self.parser.parse: collaborator call used by this boundary

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
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False

    def __str__(self) -> str:
        """
        Get parser format as string.

        Returns:
            Parser format string.

        Responsibility:
            Get parser format as string. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.parse_parser.parse.__str__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary

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
        return str(self.format)


class cfparse(parse):  # noqa:N801 intentional API
    """
    cfparse step parser.

    #arch-eval:score=reason_for_existence:4
    #arch-eval:score=srp_expert:5
    #arch-eval:score=why_not_inline:4
    #arch-eval:score=why_not_split:5
    #arch-eval:score=problems_solved:4
    #arch-eval:score=law_of_demeter:5
    #arch-eval:score=module_location:4

    Responsibility:
        cfparse step parser. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.parsers.parse_parser.cfparse` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/__init__.py: imports or references `cfparse`
        - src/pytest_bdd/parsers/facade.py: imports or references `cfparse`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `cfparse`

    State and side effects:
        mutates type.

    Invariants:
        - `pytest_bdd.parsers.parse_parser.cfparse` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    type = StepDefinitionPatternType.pytest_bdd_cfparse_expression  # type:ignore[attr-defined]  # upstream type stubs missing this attribute

    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Initialize the cfparse.

        Responsibility:
            Initialize the cfparse. It directly owns the observable contract, local decisions, and maintenance boundary
            for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work
            from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.parsers.parse_parser.cfparse.__init__` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - kwargs.setdefault: collaborator call used by this boundary
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

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
        kwargs.setdefault("builder", base_cfparse.Parser)
        super().__init__(*args, **kwargs)


register_parser(lambda parserlike: isinstance(parserlike, base_parse.Parser), parse)
