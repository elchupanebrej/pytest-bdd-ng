"""
Provide stash access helpers.

Responsibility:
    Provide stash access helpers. It directly owns the observable contract, local decisions, and maintenance boundary
    for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.stash_access` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - _StringKeyStash: owns nested behavior below this boundary
    - StashAccess: owns nested behavior below this boundary
    - StashBound: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/collector_batch.py: imports or references `stash_access`
    - src/pytest_bdd/model/message_registry.py: imports or references `stash_access`
    - src/pytest_bdd/model/message_transport.py: imports or references `stash_access`
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `stash_access`
    - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `stash_access`

State and side effects:
    mutates candidate, T, string_stash, existing, STASH_KEY; depends on __future__.annotations, typing.TYPE_CHECKING,
    typing.ClassVar, typing.Protocol, typing.TypeVar.

Invariants:
    - `pytest_bdd.model.stash_access` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

Failure semantics:
    Raises or re-raises exceptions.PytestBDDStashTypeMismatchError, exceptions.PytestBDDStashLookupError,
    exceptions.PytestBDDStashAlreadyInitializedError; callers must treat these as boundary failures.

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

from typing import TYPE_CHECKING, ClassVar, Protocol, TypeVar, cast

from returns.maybe import Maybe, Nothing, Some
from typing_extensions import Self

import pytest_bdd.types.exception as exceptions

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_bdd.compatibility.pytest import Stash

T = TypeVar("T", bound="StashBound")


class _StringKeyStash(Protocol):
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.stash_access._StringKeyStash` owns documented class behavior.
        It directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.stash_access._StringKeyStash` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __getitem__: owns nested behavior below this boundary
        - __setitem__: owns nested behavior below this boundary
        - __contains__: owns nested behavior below this boundary
        - get: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `_StringKeyStash`
        - src/pytest_bdd/model/message_registry.py: imports or references `_StringKeyStash`
        - src/pytest_bdd/model/message_transport.py: imports or references `_StringKeyStash`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_StringKeyStash`
        - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `_StringKeyStash`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Invariants:
        - `pytest_bdd.model.stash_access._StringKeyStash` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    def __getitem__(self, key: str) -> object:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.model.stash_access._StringKeyStash.__getitem__` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access._StringKeyStash.__getitem__`
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
            - src/pytest_bdd/collector_batch.py: imports or references `__getitem__`
            - src/pytest_bdd/model/message_registry.py: imports or references `__getitem__`
            - src/pytest_bdd/model/message_transport.py: imports or references `__getitem__`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `__getitem__`
            - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `__getitem__`

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

    def __setitem__(self, key: str, value: object) -> None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.model.stash_access._StringKeyStash.__setitem__` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access._StringKeyStash.__setitem__`
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
            - src/pytest_bdd/collector_batch.py: imports or references `__setitem__`
            - src/pytest_bdd/model/message_registry.py: imports or references `__setitem__`
            - src/pytest_bdd/model/message_transport.py: imports or references `__setitem__`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `__setitem__`
            - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `__setitem__`

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

    def __contains__(self, key: str) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.model.stash_access._StringKeyStash.__contains__` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access._StringKeyStash.__contains__`
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
            - src/pytest_bdd/collector_batch.py: imports or references `__contains__`
            - src/pytest_bdd/model/message_registry.py: imports or references `__contains__`
            - src/pytest_bdd/model/message_transport.py: imports or references `__contains__`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `__contains__`
            - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `__contains__`

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

    def get(self, key: str, default: object | None = None) -> object | None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.model.stash_access._StringKeyStash.get` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access._StringKeyStash.get` because it
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
            - src/pytest_bdd/_gherkin_go/__init__.py: imports or references `get`
            - src/pytest_bdd/_gherkin_go/_bridge.py: imports or references `get`
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `get`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `get`
            - src/pytest_bdd/_pylint/checkers/responsibility_docs.py: imports or references `get`

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


class StashAccess:
    """
    Access pytest stash values across pytest versions.

    Responsibility:
        Access pytest stash values across pytest versions. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.stash_access.StashAccess` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _stash_get: owns nested behavior below this boundary
        - get_optional: owns nested behavior below this boundary
        - require: owns nested behavior below this boundary
        - set: owns nested behavior below this boundary
        - create_once: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `StashAccess`
        - src/pytest_bdd/model/message_registry.py: imports or references `StashAccess`
        - src/pytest_bdd/model/message_transport.py: imports or references `StashAccess`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `StashAccess`
        - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `StashAccess`

    State and side effects:
        mutates candidate, string_stash, existing.

    Invariants:
        - `pytest_bdd.model.stash_access.StashAccess` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises exceptions.PytestBDDStashTypeMismatchError, exceptions.PytestBDDStashLookupError,
        exceptions.PytestBDDStashAlreadyInitializedError; callers must treat these as boundary failures.

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

    @staticmethod
    def _stash_get(stash: Stash, key: str) -> object | None:
        """
        Responsibility:
            Responsibility: Responsibility: `pytest_bdd.model.stash_access.StashAccess._stash_get` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashAccess._stash_get` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - hasattr: collaborator call used by this boundary
            - string_stash.get: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `_stash_get`
            - src/pytest_bdd/model/message_registry.py: imports or references `_stash_get`
            - src/pytest_bdd/model/message_transport.py: imports or references `_stash_get`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_stash_get`
            - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `_stash_get`

        State and side effects:
            mutates string_stash.

        Invariants:
            - `pytest_bdd.model.stash_access.StashAccess._stash_get` keeps its documented import path, ownership
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
        string_stash = cast("_StringKeyStash", stash)
        if hasattr(string_stash, "get"):
            return string_stash.get(key, None)
        return string_stash[key] if key in string_stash else None  # noqa: SIM401

    @classmethod
    def get_optional(cls, stash: Stash, stash_type: type[T]) -> Maybe[T]:
        """
        Retrieve an instance of the specified type from the pytest stash if it exists.

        Returns:
            The instance stored in the stash matching the requested type, or Nothing if it has not been set.

        Raises:
            PytestBDDStashTypeMismatchError: If the value's type doesn't match expected.

        Responsibility:
            Retrieve an instance of the specified type from the pytest stash if it exists. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashAccess.get_optional` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls._stash_get: collaborator call used by this boundary
            - isinstance: collaborator call used by this boundary
            - Some: collaborator call used by this boundary
            - exceptions.PytestBDDStashTypeMismatchError: collaborator call used by this boundary
            - type: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `get_optional`
            - src/pytest_bdd/model/message_registry.py: imports or references `get_optional`
            - src/pytest_bdd/model/message_transport.py: imports or references `get_optional`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `get_optional`
            - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `get_optional`

        State and side effects:
            mutates candidate.

        Invariants:
            - `pytest_bdd.model.stash_access.StashAccess.get_optional` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises exceptions.PytestBDDStashTypeMismatchError; callers must treat these as boundary
            failures.

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
        candidate = cls._stash_get(stash, stash_type.STASH_KEY)
        if candidate is None:
            return Nothing
        if isinstance(candidate, stash_type):
            return Some(candidate)
        raise exceptions.PytestBDDStashTypeMismatchError(
            stash_key=stash_type.STASH_KEY,
            actual_type=type(candidate).__name__,
            expected_type=stash_type.__name__,
        )

    @classmethod
    def require(cls, stash: Stash, stash_type: type[T], *, missing_message: str) -> T:
        """
        Retrieve a required instance of the specified type from the pytest stash.

        Returns:
            The guaranteed instance of the requested type stored in the stash.

        Raises:
            PytestBDDStashLookupError: If the required instance is not found in the stash.

        Responsibility:
            Retrieve a required instance of the specified type from the pytest stash. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashAccess.require` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls.get_optional: collaborator call used by this boundary
            - candidate.value_or: collaborator call used by this boundary
            - exceptions.PytestBDDStashLookupError: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `require`
            - src/pytest_bdd/model/message_registry.py: imports or references `require`
            - src/pytest_bdd/model/message_transport.py: imports or references `require`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `require`
            - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `require`

        State and side effects:
            mutates candidate.

        Invariants:
            - `pytest_bdd.model.stash_access.StashAccess.require` keeps its documented import path, ownership boundary,
              and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises exceptions.PytestBDDStashLookupError; callers must treat these as boundary failures.

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
        candidate = cls.get_optional(stash, stash_type)
        if (value := candidate.value_or(None)) is not None:
            return value
        raise exceptions.PytestBDDStashLookupError(missing_message)

    @classmethod
    def set(cls, stash: Stash, value: T) -> T:
        """
        Store a type-bound value in the pytest stash using its designated class key.

        Returns:
            The newly stored value.

        Responsibility:
            Store a type-bound value in the pytest stash using its designated class key. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashAccess.set` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `set`
            - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `set`
            - src/pytest_bdd/collector_batch.py: imports or references `set`
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `set`
            - src/pytest_bdd/model/coverage/inventory.py: imports or references `set`

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
        cast("_StringKeyStash", stash)[value.STASH_KEY] = value
        return value

    @classmethod
    def create_once(
        cls,
        stash: Stash,
        stash_type: type[T],
        *,
        value_factory: Callable[[], T],
        duplicate_message: str,
    ) -> T:
        """
        Initialize and store a value in the pytest stash only if it doesn't already exist.

        Returns:
            The newly created and stored value.

        Raises:
            PytestBDDStashAlreadyInitializedError: If a value for the target type is already present in the stash.

        Responsibility:
            Initialize and store a value in the pytest stash only if it doesn't already exist. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashAccess.create_once` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls.get_optional: collaborator call used by this boundary
            - existing.value_or: collaborator call used by this boundary
            - exceptions.PytestBDDStashAlreadyInitializedError: collaborator call used by this boundary
            - cls.set: collaborator call used by this boundary
            - value_factory: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `create_once`
            - src/pytest_bdd/model/message_registry.py: imports or references `create_once`
            - src/pytest_bdd/model/message_transport.py: imports or references `create_once`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `create_once`
            - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `create_once`

        State and side effects:
            mutates existing.

        Invariants:
            - `pytest_bdd.model.stash_access.StashAccess.create_once` keeps its documented import path, ownership
              boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises exceptions.PytestBDDStashAlreadyInitializedError; callers must treat these as boundary
            failures.

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
        existing = cls.get_optional(stash, stash_type)
        if existing.value_or(None) is not None:
            raise exceptions.PytestBDDStashAlreadyInitializedError(duplicate_message)
        return cls.set(stash, value_factory())


class StashBound:
    """
    A generic base class that automatically bounds its subclasses to specific keys within the pytest stash.

    Responsibility:
        A generic base class that automatically bounds its subclasses to specific keys within the pytest stash. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.stash_access.StashBound` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - stash_missing_message: owns nested behavior below this boundary
        - stash_duplicate_message: owns nested behavior below this boundary
        - find_in_stash: owns nested behavior below this boundary
        - from_stash: owns nested behavior below this boundary
        - set_in_stash: owns nested behavior below this boundary
        - initialize_in_stash: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `StashBound`
        - src/pytest_bdd/model/message_registry.py: imports or references `StashBound`
        - src/pytest_bdd/model/message_transport.py: imports or references `StashBound`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `StashBound`
        - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `StashBound`

    State and side effects:
        mutates STASH_KEY.

    Invariants:
        - `pytest_bdd.model.stash_access.StashBound` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

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

    STASH_KEY: ClassVar[str]

    @classmethod
    def stash_missing_message(cls) -> str:
        """
        Construct a default error message for when the bound type is missing from the stash.

        Returns:
            A formatted string explaining that the bound class is unavailable in the current stash.

        Responsibility:
            Construct a default error message for when the bound type is missing from the stash. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashBound.stash_missing_message`
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
            - src/pytest_bdd/collector_batch.py: imports or references `stash_missing_message`
            - src/pytest_bdd/model/message_registry.py: imports or references `stash_missing_message`
            - src/pytest_bdd/model/message_transport.py: imports or references `stash_missing_message`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `stash_missing_message`
            - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `stash_missing_message`

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
        return f"`{cls.__name__}` is unavailable in config.stash."

    @classmethod
    def stash_duplicate_message(cls) -> str:
        """
        Construct a default error message for when the bound type already exists in the stash.

        Returns:
            A formatted string explaining that the bound class has already been initialized in the stash.

        Responsibility:
            Construct a default error message for when the bound type already exists in the stash. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashBound.stash_duplicate_message`
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
            - src/pytest_bdd/collector_batch.py: imports or references `stash_duplicate_message`
            - src/pytest_bdd/model/message_registry.py: imports or references `stash_duplicate_message`
            - src/pytest_bdd/model/message_transport.py: imports or references `stash_duplicate_message`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `stash_duplicate_message`
            - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `stash_duplicate_message`

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
        return f"`{cls.__name__}` is already initialized in config.stash."

    @classmethod
    def find_in_stash(cls, stash: Stash) -> Maybe[Self]:
        """
        Look up the bound type in the provided pytest stash.

        Returns:
            The stored instance of the bound type, or Nothing if not found.

        Responsibility:
            Look up the bound type in the provided pytest stash. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashBound.find_in_stash` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - StashAccess.get_optional: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector.py: imports or references `find_in_stash`
            - src/pytest_bdd/collector_batch.py: imports or references `find_in_stash`
            - src/pytest_bdd/model/message_registry.py: imports or references `find_in_stash`
            - src/pytest_bdd/model/message_transport.py: imports or references `find_in_stash`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `find_in_stash`

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
        return StashAccess.get_optional(stash, cls)

    @classmethod
    def from_stash(cls, stash: Stash) -> Self:
        """
        Retrieve the bound type from the provided pytest stash, enforcing its existence.

        Returns:
            The guaranteed instance of the bound type stored in the stash.

        Responsibility:
            Retrieve the bound type from the provided pytest stash, enforcing its existence. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashBound.from_stash` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - StashAccess.require: collaborator call used by this boundary
            - cls.stash_missing_message: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `from_stash`
            - src/pytest_bdd/hook.py: imports or references `from_stash`
            - src/pytest_bdd/model/message_registry.py: imports or references `from_stash`
            - src/pytest_bdd/model/message_transport.py: imports or references `from_stash`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `from_stash`

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
        return StashAccess.require(stash, cls, missing_message=cls.stash_missing_message())

    def set_in_stash(self, stash: Stash) -> Self:
        """
        Store the current instance within the provided pytest stash.

        Returns:
            The instance that was successfully stored.

        Responsibility:
            Store the current instance within the provided pytest stash. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashBound.set_in_stash` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - StashAccess.set: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `set_in_stash`
            - src/pytest_bdd/model/message_registry.py: imports or references `set_in_stash`
            - src/pytest_bdd/model/message_transport.py: imports or references `set_in_stash`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `set_in_stash`
            - src/pytest_bdd/plugin/debug_mcp/state.py: imports or references `set_in_stash`

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
        return StashAccess.set(stash, self)

    def initialize_in_stash(self, stash: Stash) -> Self:
        """
        Safely initialize the current instance within the pytest stash, ensuring no duplication.

        Returns:
            The instance that was successfully stored.

        Responsibility:
            Safely initialize the current instance within the pytest stash, ensuring no duplication. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.stash_access.StashBound.initialize_in_stash`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - type: collaborator call used by this boundary
            - StashAccess.create_once: collaborator call used by this boundary
            - type.stash_duplicate_message: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/collector_batch.py: imports or references `initialize_in_stash`
            - src/pytest_bdd/model/message_registry.py: imports or references `initialize_in_stash`
            - src/pytest_bdd/model/message_transport.py: imports or references `initialize_in_stash`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `initialize_in_stash`
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `initialize_in_stash`

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
        return StashAccess.create_once(
            stash,
            type(self),
            value_factory=lambda: self,
            duplicate_message=type(self).stash_duplicate_message(),
        )
