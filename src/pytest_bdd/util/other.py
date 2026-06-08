"""
Provide other helpers.

Responsibility:
    Provide other helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.other` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - format_as_python_identifier: owns nested behavior below this boundary
    - format_as_simplified_python_identifier: owns nested behavior below this boundary
    - StringRepresentable: owns nested behavior below this boundary
    - normalize_to_string: owns nested behavior below this boundary
    - IdGenerator: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector.py: imports or references `other`
    - src/pytest_bdd/compatibility/parser.py: imports or references `other`
    - src/pytest_bdd/feature_locator.py: imports or references `other`
    - src/pytest_bdd/parsers/heuristic.py: imports or references `other`
    - src/pytest_bdd/parsers/parse_parser.py: imports or references `other`

State and side effects:
    mutates self._id_counter, s1, s2, s3, s4; depends on __future__.annotations, re, typing.ClassVar, typing.Protocol,
    typing.runtime_checkable.

Invariants:
    - `pytest_bdd.util.other` keeps its documented import path, ownership boundary, and observable behavior stable for
      callers.

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

from __future__ import annotations

import re
from typing import ClassVar, Protocol, runtime_checkable

from gherkin.stream.id_generator import IdGenerator as BaseIdGenerator

from pytest_bdd.const import ALPHA_REGEX, PYTHON_REPLACE_REGEX
from pytest_bdd.model.stash_access import StashBound


def format_as_python_identifier(s: object) -> str:
    """
    Format an object as a valid Python identifier.

    Args:
        s: Object to format.

    Returns:
        Valid Python identifier string.

    Responsibility:
        Format an object as a valid Python identifier. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.other.format_as_python_identifier` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - re.sub: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - s3.strip: collaborator call used by this boundary
        - re.match: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `format_as_python_identifier`
        - src/pytest_bdd/compatibility/parser.py: imports or references `format_as_python_identifier`
        - src/pytest_bdd/feature_locator.py: imports or references `format_as_python_identifier`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `format_as_python_identifier`
        - src/pytest_bdd/parsers/parse_parser.py: imports or references `format_as_python_identifier`

    State and side effects:
        mutates s1, s2, s3, s4.

    Invariants:
        - `pytest_bdd.util.other.format_as_python_identifier` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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
    s1: str = str(s)
    s2 = re.sub(r"[^.a-zA-Z0-9]", "_", s1)
    s3 = re.sub(r"_+", "_", s2)
    s4 = s3.strip("_")
    return f"_{s4}" if re.match(r"\d.*", s4) else s4


def format_as_simplified_python_identifier(string: str) -> str:
    """
    Format a string as a simplified Python identifier.

    Args:
        string: String to format.

    Returns:
        Simplified identifier string.

    Responsibility:
        Format a string as a simplified Python identifier. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.other.format_as_simplified_python_identifier` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - re.sub: collaborator call used by this boundary
        - string.replace: collaborator call used by this boundary
        - re.sub.lower: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `format_as_simplified_python_identifier`
        - src/pytest_bdd/compatibility/parser.py: imports or references `format_as_simplified_python_identifier`
        - src/pytest_bdd/feature_locator.py: imports or references `format_as_simplified_python_identifier`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `format_as_simplified_python_identifier`
        - src/pytest_bdd/parsers/parse_parser.py: imports or references `format_as_simplified_python_identifier`

    State and side effects:
        mutates string.

    Invariants:
        - `pytest_bdd.util.other.format_as_simplified_python_identifier` keeps its documented import path, ownership
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
    string = re.sub(PYTHON_REPLACE_REGEX, "", string.replace(" ", "_"))
    return re.sub(ALPHA_REGEX, "", string).lower()


@runtime_checkable
class StringRepresentable(Protocol):
    """
    Represent string representable state.

    Responsibility:
        Represent string representable state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.other.StringRepresentable` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __str__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `StringRepresentable`
        - src/pytest_bdd/compatibility/parser.py: imports or references `StringRepresentable`
        - src/pytest_bdd/feature_locator.py: imports or references `StringRepresentable`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `StringRepresentable`
        - src/pytest_bdd/parsers/parse_parser.py: imports or references `StringRepresentable`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.util.other.StringRepresentable` keeps its documented import path, ownership boundary, and
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

    def __str__(self) -> str:
        """
        Return the value as a string.

        Responsibility:
            Return the value as a string. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.other.StringRepresentable.__str__` because it
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
            - src/pytest_bdd/collector.py: imports or references `__str__`
            - src/pytest_bdd/compatibility/parser.py: imports or references `__str__`
            - src/pytest_bdd/feature_locator.py: imports or references `__str__`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `__str__`
            - src/pytest_bdd/parsers/parse_parser.py: imports or references `__str__`

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
        ...  # pragma: no cover


def normalize_to_string(value: StringRepresentable | str | bytes) -> str:
    """
    Normalize a value to a string.

    Args:
        value: Value to normalize.

    Returns:
        Normalized string.

    Responsibility:
        Normalize a value to a string. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.other.normalize_to_string` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `normalize_to_string`
        - src/pytest_bdd/compatibility/parser.py: imports or references `normalize_to_string`
        - src/pytest_bdd/feature_locator.py: imports or references `normalize_to_string`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `normalize_to_string`
        - src/pytest_bdd/parsers/parse_parser.py: imports or references `normalize_to_string`

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
    return str(value, **({"encoding": "utf-8"} if isinstance(value, bytes) else {}))


class IdGenerator(BaseIdGenerator, StashBound):
    """
    Represent id generator state.

    Responsibility:
        Represent id generator state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.other.IdGenerator` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - __next__: owns nested behavior below this boundary
        - stash_missing_message: owns nested behavior below this boundary
        - stash_duplicate_message: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector.py: imports or references `IdGenerator`
        - src/pytest_bdd/compatibility/parser.py: imports or references `IdGenerator`
        - src/pytest_bdd/feature_locator.py: imports or references `IdGenerator`
        - src/pytest_bdd/model/feature_binding.py: imports or references `IdGenerator`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `IdGenerator`

    State and side effects:
        mutates self._id_counter, STASH_KEY, get_next_id.

    Invariants:
        - `pytest_bdd.util.other.IdGenerator` keeps its documented import path, ownership boundary, and observable
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

    STASH_KEY: ClassVar[str] = "_pytest_bdd_id_generator"

    def __init__(self) -> None:
        """
        Initialize the id generator.

        Responsibility:
            Initialize the id generator. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.other.IdGenerator.__init__` because it keeps the
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
            - src/pytest_bdd/collector.py: imports or references `__init__`

        State and side effects:
            mutates self._id_counter.

        Invariants:
            - `pytest_bdd.util.other.IdGenerator.__init__` keeps its documented import path, ownership boundary, and
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
        self._id_counter = 0

    def __next__(self) -> str:
        """
        Return the next generated ID.

        Returns:
            String representation of the next ID.

        Responsibility:
            Return the next generated ID. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.other.IdGenerator.__next__` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `__next__`
            - src/pytest_bdd/compatibility/parser.py: imports or references `__next__`
            - src/pytest_bdd/feature_locator.py: imports or references `__next__`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `__next__`
            - src/pytest_bdd/parsers/parse_parser.py: imports or references `__next__`

        State and side effects:
            mutates self._id_counter.

        Invariants:
            - `pytest_bdd.util.other.IdGenerator.__next__` keeps its documented import path, ownership boundary, and
              observable behavior stable for callers.

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
            return str(self._id_counter)
        finally:
            self._id_counter += 1

    get_next_id = __next__

    @classmethod
    def stash_missing_message(cls) -> str:
        """
        Return error message for missing stash.

        Returns:
            Error message string.

        Responsibility:
            Return error message for missing stash. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.other.IdGenerator.stash_missing_message` because
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
            - src/pytest_bdd/collector.py: imports or references `stash_missing_message`
            - src/pytest_bdd/compatibility/parser.py: imports or references `stash_missing_message`
            - src/pytest_bdd/feature_locator.py: imports or references `stash_missing_message`
            - src/pytest_bdd/model/stash_access.py: imports or references `stash_missing_message`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `stash_missing_message`

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
        return (
            "`pytest_bdd_id_generator` is unavailable in config.stash. "
            "Execution and collection plugins must initialize stash-backed runtime services before use."
        )

    @classmethod
    def stash_duplicate_message(cls) -> str:
        """
        Return error message for duplicate stash.

        Returns:
            Error message string.

        Responsibility:
            Return error message for duplicate stash. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.other.IdGenerator.stash_duplicate_message`
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
            - src/pytest_bdd/collector.py: imports or references `stash_duplicate_message`
            - src/pytest_bdd/compatibility/parser.py: imports or references `stash_duplicate_message`
            - src/pytest_bdd/feature_locator.py: imports or references `stash_duplicate_message`
            - src/pytest_bdd/model/stash_access.py: imports or references `stash_duplicate_message`
            - src/pytest_bdd/parsers/heuristic.py: imports or references `stash_duplicate_message`

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
        return (
            "`pytest_bdd_id_generator` is already initialized in config.stash. "
            "Framework bootstrap must initialize it exactly once."
        )
