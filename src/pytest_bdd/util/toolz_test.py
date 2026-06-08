"""
Provide toolz test helpers.

Responsibility:
    Provide toolz test helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.toolz_test` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - dump_obj: owns nested behavior below this boundary
    - collect_dumped_objects: owns nested behavior below this boundary
    - InstanceOfType: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates _DUMP_START, _DUMP_END, dump, encoded, stdout; depends on __future__.annotations, base64, pickle, re,
    typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.util.toolz_test` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

import base64
import pickle  # noqa:S403
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import RunResult

_DUMP_START = "_pytest_bdd_>>>"
_DUMP_END = "<<<_pytest_bdd_"


def dump_obj(*objects: object) -> None:
    """
    Dump objects to stdout so that they can be inspected by the test suite.

    Responsibility:
        Dump objects to stdout so that they can be inspected by the test suite. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_test.dump_obj` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - pickle.dumps: collaborator call used by this boundary
        - base64.b64encode.decode: collaborator call used by this boundary
        - base64.b64encode: collaborator call used by this boundary
        - print: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates dump, encoded.

    Invariants:
        - `pytest_bdd.util.toolz_test.dump_obj` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

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
    for obj in objects:
        dump = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        encoded = base64.b64encode(dump).decode("ascii")
        print(f"{_DUMP_START}{encoded}{_DUMP_END}")  # noqa: T201 intentional non-debug output


def collect_dumped_objects(result: RunResult) -> list[object]:
    """
    Parse all the objects dumped with `dump_object` from the result.

    Note: You must run the result with output to stdout enabled.
    For example, using ``testdir.runpytest("-s")``.

    Args:
        result: Pytest run result.

    Returns:
        List of unpickled objects.

    Responsibility:
        Parse all the objects dumped with `dump_object` from the result. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_test.collect_dumped_objects` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - result.stdout.str: collaborator call used by this boundary
        - re.findall: collaborator call used by this boundary
        - pickle.loads: collaborator call used by this boundary
        - base64.b64decode: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates stdout, payloads.

    Invariants:
        - `pytest_bdd.util.toolz_test.collect_dumped_objects` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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
    stdout = result.stdout.str()  # pytest < 6.2, otherwise we could just do str(result.stdout)
    payloads = re.findall(rf"{_DUMP_START}(.*?){_DUMP_END}", stdout)
    return [pickle.loads(base64.b64decode(payload)) for payload in payloads]  # noqa: S301


class InstanceOfType:
    """
    Helper for equality checks: returns True if.

    the other object is an instance of the given type
    (or always True if no type is specified).

    Responsibility:
        Helper for equality checks: returns True if. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.toolz_test.InstanceOfType` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - __eq__: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates self.type, __hash__.

    Invariants:
        - `pytest_bdd.util.toolz_test.InstanceOfType` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """

    def __init__(self, type_: type | None = None) -> None:
        """
        Initialize the instance of type.

        Responsibility:
            Initialize the instance of type. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.toolz_test.InstanceOfType.__init__` because it
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
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self.type.

        Invariants:
            - `pytest_bdd.util.toolz_test.InstanceOfType.__init__` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

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
        self.type = type_

    def __eq__(self, other: object) -> bool:
        """
        Return whether the other object matches the expected type.

        Args:
            other: Object to compare.

        Returns:
            True if matches expected type.

        Responsibility:
            Return whether the other object matches the expected type. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.util.toolz_test.InstanceOfType.__eq__` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary

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
        return isinstance(other, self.type) if self.type else True

    __hash__ = None  # type: ignore[assignment]  # type narrowing workaround for mypy
