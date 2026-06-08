"""
Provide tag expression helpers.

Responsibility:
    Provide tag expression helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.tag_expression` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - TagExpression: owns nested behavior below this boundary
    - _ModernTagExpression: owns nested behavior below this boundary
    - _EnhancedMarksTagExpression: owns nested behavior below this boundary
    - _MarksTagExpression: owns nested behavior below this boundary
    - GherkinTagExpression: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/hook.py: imports or references `tag_expression`
    - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `tag_expression`
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_payload.py: imports or references `tag_expression`

State and side effects:
    mutates expression, msg, MarksTagExpression, TagExpressionType; depends on operator.attrgetter, typing.Protocol,
    typing.runtime_checkable, attrs.define, attrs.field.

Invariants:
    - `pytest_bdd.tag_expression` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Failure semantics:
    Raises or re-raises NotImplementedError, ValueError; callers must treat these as boundary failures.

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

from operator import attrgetter
from typing import Protocol, runtime_checkable

from attrs import define, field
from cucumber_tag_expressions import TagExpressionError, TagExpressionParser
from typing_extensions import Self

from pytest_bdd.compatibility.pytest import PYTEST83, Expression, Mark, MarkMatcher, ParseError


@runtime_checkable
class TagExpression(Protocol):
    """
    Evaluate cucumber tag expressions against pytest marks.

    Responsibility:
        Evaluate cucumber tag expressions against pytest marks. It directly owns the observable contract, local
        decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.tag_expression.TagExpression` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parse: owns nested behavior below this boundary
        - evaluate: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `TagExpression`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `TagExpression`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.tag_expression.TagExpression` keeps its documented import path, ownership boundary, and observable
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
        #arch-eval:locational_stability=3
    """

    @classmethod
    def parse(cls, expression: str) -> Self:
        """
        Parse parse.

        Raises:
            NotImplementedError: If the operation cannot be completed.

        Responsibility:
            Parse parse. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.tag_expression.TagExpression.parse` because it keeps
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
            - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `parse`
            - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `parse`
            - src/pytest_bdd/collector_batch.py: imports or references `parse`
            - src/pytest_bdd/hook.py: imports or references `parse`
            - src/pytest_bdd/parser.py: imports or references `parse`

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
        raise NotImplementedError  # pragma: no cover

    def evaluate(self, marks: list[Mark]) -> bool:
        """
        Handle evaluate.

        Raises:
            NotImplementedError: If the operation cannot be completed.

        Responsibility:
            Handle evaluate. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.tag_expression.TagExpression.evaluate` because it
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
            - src/pytest_bdd/hook.py: imports or references `evaluate`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `evaluate`

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
            #arch-eval:locational_stability=3

        """
        raise NotImplementedError  # pragma: no cover


@define
class _ModernTagExpression(TagExpression):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.tag_expression._ModernTagExpression` owns documented class behavior.
        It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.tag_expression._ModernTagExpression` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parse: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `_ModernTagExpression`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `_ModernTagExpression`

    State and side effects:
        mutates expression, msg.

    Invariants:
        - `pytest_bdd.tag_expression._ModernTagExpression` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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

    expression: Expression | None = field()

    @classmethod
    def parse(cls, expression: str) -> Self:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.tag_expression._ModernTagExpression.parse` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.tag_expression._ModernTagExpression.parse` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls: collaborator call used by this boundary
            - Expression.compile: collaborator call used by this boundary
            - ValueError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `parse`
            - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `parse`
            - src/pytest_bdd/collector_batch.py: imports or references `parse`
            - src/pytest_bdd/hook.py: imports or references `parse`
            - src/pytest_bdd/parser.py: imports or references `parse`

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.tag_expression._ModernTagExpression.parse` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError; callers must treat these as boundary failures.

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
        try:
            return cls(expression=Expression.compile(expression) if expression else None)
        except ParseError as e:
            msg = f"Unable parse mark expression: {expression}: {e}"
            raise ValueError(msg) from e


@define
class _EnhancedMarksTagExpression(_ModernTagExpression):
    """
    Used for 8.3<=pytest.

    Responsibility:
        Used for 8.3<=pytest. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.tag_expression._EnhancedMarksTagExpression` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - evaluate: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `_EnhancedMarksTagExpression`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `_EnhancedMarksTagExpression`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.tag_expression._EnhancedMarksTagExpression` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """

    def evaluate(self, marks: list[Mark]) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.tag_expression._EnhancedMarksTagExpression.evaluate` owns
            documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.tag_expression._EnhancedMarksTagExpression.evaluate`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.expression.evaluate: collaborator call used by this boundary
            - MarkMatcher.from_markers: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `evaluate`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `evaluate`

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
        return self.expression.evaluate(MarkMatcher.from_markers(marks)) if self.expression is not None else True  # type: ignore[arg-type]  # pytest Expression.evaluate is untyped


@define
class _MarksTagExpression(_ModernTagExpression):
    """
    Used for 6.0<=pytest<8.3.

    Responsibility:
        Used for 6.0<=pytest<8.3. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.tag_expression._MarksTagExpression` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - evaluate: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `_MarksTagExpression`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `_MarksTagExpression`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.tag_expression._MarksTagExpression` keeps its documented import path, ownership boundary, and
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
        #arch-eval:locational_stability=3
    """

    def evaluate(self, marks: list[Mark]) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.tag_expression._MarksTagExpression.evaluate` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.tag_expression._MarksTagExpression.evaluate` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.expression.evaluate: collaborator call used by this boundary
            - MarkMatcher: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `evaluate`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `evaluate`

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
        return (
            self.expression.evaluate(MarkMatcher({mark.name: [mark] for mark in marks}))  # type: ignore[arg-type, call-arg]  # pytest Expression.evaluate/MarkMatcher are untyped
            if self.expression is not None
            else True
        )


MarksTagExpression: type[_EnhancedMarksTagExpression | _MarksTagExpression]
MarksTagExpression = _EnhancedMarksTagExpression if PYTEST83 else _MarksTagExpression


@define
class GherkinTagExpression(TagExpression):
    """
    Represent gherkin tag expression state.

    Raises:
        ValueError: If the operation cannot be completed.

    Responsibility:
        Represent gherkin tag expression state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.tag_expression.GherkinTagExpression` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - parse: owns nested behavior below this boundary
        - evaluate: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/hook.py: imports or references `GherkinTagExpression`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references
          `GherkinTagExpression`

    State and side effects:
        mutates expression, msg.

    Invariants:
        - `pytest_bdd.tag_expression.GherkinTagExpression` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises ValueError; callers must treat these as boundary failures.

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

    expression: TagExpressionParser = field()

    @classmethod
    def parse(cls, expression: str) -> Self:
        """
        Parse a tag expression string.

        Args:
            expression: Tag expression string.

        Returns:
            Parsed tag expression object.

        Raises:
            ValueError: If the expression is invalid.

        Responsibility:
            Parse a tag expression string. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.tag_expression.GherkinTagExpression.parse` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls: collaborator call used by this boundary
            - TagExpressionParser.parse: collaborator call used by this boundary
            - ValueError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `parse`
            - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `parse`
            - src/pytest_bdd/collector_batch.py: imports or references `parse`
            - src/pytest_bdd/hook.py: imports or references `parse`
            - src/pytest_bdd/parser.py: imports or references `parse`

        State and side effects:
            mutates msg.

        Invariants:
            - `pytest_bdd.tag_expression.GherkinTagExpression.parse` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises ValueError; callers must treat these as boundary failures.

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
        try:
            return cls(expression=TagExpressionParser.parse(expression))
        except TagExpressionError as e:
            msg = f"Unable parse tag expression: {expression}: {e}"
            raise ValueError(msg) from e

    def evaluate(self, marks: list[Mark]) -> bool:
        """
        Evaluate tag expression against pytest marks.

        Args:
            marks: List of pytest marks.

        Returns:
            True if expression matches.

        Responsibility:
            Evaluate tag expression against pytest marks. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.tag_expression.GherkinTagExpression.evaluate` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - bool: collaborator call used by this boundary
            - self.expression.evaluate: collaborator call used by this boundary
            - list: collaborator call used by this boundary
            - map: collaborator call used by this boundary
            - attrgetter: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/hook.py: imports or references `evaluate`
            - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `evaluate`

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
        return bool(self.expression.evaluate(list(map(attrgetter("name"), marks))))


TagExpressionType = _EnhancedMarksTagExpression | _MarksTagExpression | GherkinTagExpression
