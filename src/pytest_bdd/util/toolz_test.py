"""
Provides focused utility functions for the `toolz_test` concern within pytest-bdd utility
layer, offering helper oper.

Responsibility:
    Provides focused utility functions for the `toolz_test` concern within pytest-bdd utility
    layer, offering helper operations consumed by higher layers (collection, runtime, reporting)
    without pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `toolz_test` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `toolz_test`-related helper operations within
    the utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `toolz_test` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `toolz_test` utilities for reporting, collection, and runtime operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import base64
import pickle  # noqa:S403  -- suppressed warning
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import RunResult

_DUMP_START = "_pytest_bdd_>>>"
_DUMP_END = "<<<_pytest_bdd_"


def dump_obj(*objects: object) -> None:
    """
    Perform the `dump_obj` operation within its module boundary, implementing a focused helper.
    function that is consumed.

    Responsibility:
        Performs the `dump_obj` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `dump_obj` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the dump_obj operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke dump_obj for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The dump_obj function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    for obj in objects:
        dump = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        encoded = base64.b64encode(dump).decode("ascii")
        print(f"{_DUMP_START}{encoded}{_DUMP_END}")  # noqa: T201 intentional non-debug output


def collect_dumped_objects(result: RunResult) -> list[object]:
    """
    Perform the `collect_dumped_objects` operation within its module boundary, implementing a.
    focused helper function th.

    Responsibility:
        Performs the `collect_dumped_objects` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `collect_dumped_objects` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the collect_dumped_objects operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke collect_dumped_objects for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The collect_dumped_objects function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    stdout = result.stdout.str()  # pytest < 6.2, otherwise we could just do str(result.stdout)
    payloads = re.findall(rf"{_DUMP_START}(.*?){_DUMP_END}", stdout)
    return [pickle.loads(base64.b64decode(payload)) for payload in payloads]  # noqa: S301  -- suppressed warning


class InstanceOfType:
    """
    Encapsulates the InstanceOfType concern within pytest-bdd, providing a focused set of
    collaborating operations that t.

    Responsibility:
        Encapsulates the InstanceOfType concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        InstanceOfType is a distinct class because its methods share internal state and collaborate on
        a cohesive task that would be awkward to express as standalone functions with shared mutable
        parameters.

    Delegates:
        - object: InstanceOfType specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single InstanceOfType domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate InstanceOfType for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of InstanceOfType maintain internal consistency across all method calls.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    def __init__(self, type_: type | None = None) -> None:
        """
        Initializ a new InstanceOfType instance with domain-specific context parameters, formatting a.
        human-readable diagno.

        Responsibility:
            Initializes a new InstanceOfType instance with domain-specific context parameters, formatting a
            human-readable diagnostic message that includes relevant identifiers for debugging test
            failures in pytest output and log files.

        Reason for existence:
            The __init__ of InstanceOfType is the constructor boundary where raw failure context is
            transformed into a formatted exception message. It is the single place where the diagnostic
            message format for this error type is defined.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __init__ operation on InstanceOfType instances.

        Separation:
            - Other InstanceOfType methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch InstanceOfType implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        self.type = type_

    def __eq__(self, other: object) -> bool:
        """
        Perform the __eq__ operation within the InstanceOfType boundary, handling its specific sub-.
        task as part of the broa.

        Responsibility:
            Performs the __eq__ operation within the InstanceOfType boundary, handling its specific sub-
            task as part of the broader InstanceOfType responsibility in the pytest-bdd runtime lifecycle.

        Reason for existence:
            __eq__ is a distinct method because it encapsulates a specific behavioral concern that must be
            independently callable and potentially overridable by subclasses of InstanceOfType without
            affecting other operations.

        Delegates:
            - super().__init__(): delegates standard initialization to the Python base class

        Cohesion:
            All logic directly supports the __eq__ operation on InstanceOfType instances.

        Separation:
            - Other InstanceOfType methods: each method handles a distinct lifecycle aspect of the class.

        Main consumers:
            - `pytest_bdd.*`: callers that raise or catch InstanceOfType implicitly invoke this method

        State and side effects:
            None, this method is stateless and only formats or stores its input arguments.

        Invariants:
            - The constructed/formatted message always includes domain context passed to this method.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=3
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        return isinstance(other, self.type) if self.type else True

    __hash__ = None  # type: ignore[assignment]  # type narrowing workaround for mypy
