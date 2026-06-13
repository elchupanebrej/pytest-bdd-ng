"""
Defines structural typing Protocols (HasPytestStash, Identifiable, LinkedAST, MultiLinkedAST)
that enable duck-typing.

Responsibility:
    Defines structural typing Protocols (HasPytestStash, Identifiable, LinkedAST, MultiLinkedAST)
    that enable duck-typing across pytest-bdd runtime objects without requiring concrete class
    inheritance, supporting both first-party and third-party pytest plugin extension points.

Reason for existence:
    Protocols enable the runtime to accept any object satisfying a structural contract (e.g.,
    having a `stash` attribute or `id` field) rather than coupling to specific implementation
    classes. This is critical for pytest plugin interoperability where objects originate from
    different sources.

Delegates:
    - `typing.Protocol`: provides the structural subtyping mechanism via @runtime_checkable

Cohesion:
    All four Protocols define structural typing contracts for runtime objects; no logic, only shape
    definitions.

Separation:
    - `pytest_bdd.types.exception`: exception defines error classes while protocol defines interface contracts.

Main consumers:
    - `pytest_bdd.model.stash_access`: uses HasPytestStash and Identifiable protocols for runtime type checking

State and side effects:
    None, Protocols are pure type definitions with zero runtime behavior or state footprint.

Invariants:
    - Each Protocol declares exactly the minimal attribute set required for its structural contract.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Stash


@runtime_checkable
class HasPytestStash(Protocol):
    """
    Defines a structural typing contract requiring conforming objects to expose specific
    attributes, enabling duck-typing.

    Responsibility:
        Defines a structural typing contract requiring conforming objects to expose specific
        attributes, enabling duck-typing across pytest-bdd runtime objects without mandating concrete
        class inheritance for pytest plugin interoperability.

    Reason for existence:
        This Protocol exists as a named type so runtime code can use isinstance() checks and static
        type annotations against a documented contract rather than relying on ad-hoc hasattr() calls
        spread across the codebase.

    Delegates:
        - Protocol: HasPytestStash specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate HasPytestStash for error handling and type checking

    State and side effects:
        Pure type definition with zero runtime behavior or state.

    Invariants:
        - The Protocol declares only the attributes essential to its contract.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    stash: Stash


@runtime_checkable
class Identifiable(Protocol):
    """
    Defines a structural typing contract requiring conforming objects to expose specific
    attributes, enabling duck-typing.

    Responsibility:
        Defines a structural typing contract requiring conforming objects to expose specific
        attributes, enabling duck-typing across pytest-bdd runtime objects without mandating concrete
        class inheritance for pytest plugin interoperability.

    Reason for existence:
        This Protocol exists as a named type so runtime code can use isinstance() checks and static
        type annotations against a documented contract rather than relying on ad-hoc hasattr() calls
        spread across the codebase.

    Delegates:
        - Protocol: Identifiable specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate Identifiable for error handling and type checking

    State and side effects:
        Pure type definition with zero runtime behavior or state.

    Invariants:
        - The Protocol declares only the attributes essential to its contract.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    id: object


@runtime_checkable
class LinkedAST(Protocol):
    """
    Defines a structural typing contract requiring conforming objects to expose specific
    attributes, enabling duck-typing.

    Responsibility:
        Defines a structural typing contract requiring conforming objects to expose specific
        attributes, enabling duck-typing across pytest-bdd runtime objects without mandating concrete
        class inheritance for pytest plugin interoperability.

    Reason for existence:
        This Protocol exists as a named type so runtime code can use isinstance() checks and static
        type annotations against a documented contract rather than relying on ad-hoc hasattr() calls
        spread across the codebase.

    Delegates:
        - Protocol: LinkedAST specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate LinkedAST for error handling and type checking

    State and side effects:
        Pure type definition with zero runtime behavior or state.

    Invariants:
        - The Protocol declares only the attributes essential to its contract.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    ast_node_id: str


@runtime_checkable
class MultiLinkedAST(Protocol):
    """
    Defines a structural typing contract requiring conforming objects to expose specific
    attributes, enabling duck-typing.

    Responsibility:
        Defines a structural typing contract requiring conforming objects to expose specific
        attributes, enabling duck-typing across pytest-bdd runtime objects without mandating concrete
        class inheritance for pytest plugin interoperability.

    Reason for existence:
        This Protocol exists as a named type so runtime code can use isinstance() checks and static
        type annotations against a documented contract rather than relying on ad-hoc hasattr() calls
        spread across the codebase.

    Delegates:
        - Protocol: MultiLinkedAST specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        Declares exactly the minimal attribute set required for its structural contract.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate MultiLinkedAST for error handling and type checking

    State and side effects:
        Pure type definition with zero runtime behavior or state.

    Invariants:
        - The Protocol declares only the attributes essential to its contract.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """

    ast_node_ids: list[str]
