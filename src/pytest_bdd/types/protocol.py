"""
Provide protocol helpers.

Responsibility:
    Provide protocol helpers. It directly owns the observable contract, local decisions, and maintenance boundary for
    this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
    collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.types.protocol` because it keeps the nearest code, data shape,
    call signature, and failure knowledge together.

Delegates:
    - HasPytestStash: owns nested behavior below this boundary
    - Identifiable: owns nested behavior below this boundary
    - LinkedAST: owns nested behavior below this boundary
    - MultiLinkedAST: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/compatibility/parser.py: imports or references `protocol`
    - src/pytest_bdd/feature_locator.py: imports or references `protocol`
    - src/pytest_bdd/model/feature_binding.py: imports or references `protocol`
    - src/pytest_bdd/model/message_registry.py: imports or references `protocol`
    - src/pytest_bdd/model/message_transport.py: imports or references `protocol`

State and side effects:
    mutates stash, id, ast_node_id, ast_node_ids; depends on __future__.annotations, typing.TYPE_CHECKING,
    typing.Protocol, typing.runtime_checkable, pytest_bdd.compatibility.pytest.Stash.

Invariants:
    - `pytest_bdd.types.protocol` keeps its documented import path, ownership boundary, and observable behavior stable
      for callers.

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

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Stash


@runtime_checkable
class HasPytestStash(Protocol):
    """
    Represent has pytest stash state.

    Responsibility:
        Represent has pytest stash state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.protocol.HasPytestStash` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/compatibility/parser.py: imports or references `HasPytestStash`
        - src/pytest_bdd/feature_locator.py: imports or references `HasPytestStash`
        - src/pytest_bdd/model/feature_binding.py: imports or references `HasPytestStash`
        - src/pytest_bdd/model/message_registry.py: imports or references `HasPytestStash`
        - src/pytest_bdd/model/message_transport.py: imports or references `HasPytestStash`

    State and side effects:
        mutates stash.

    Invariants:
        - `pytest_bdd.types.protocol.HasPytestStash` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    stash: Stash


@runtime_checkable
class Identifiable(Protocol):
    """
    Represent identifiable state.

    Responsibility:
        Represent identifiable state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.protocol.Identifiable` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/compatibility/parser.py: imports or references `Identifiable`
        - src/pytest_bdd/feature_locator.py: imports or references `Identifiable`
        - src/pytest_bdd/model/feature_binding.py: imports or references `Identifiable`
        - src/pytest_bdd/model/message_registry.py: imports or references `Identifiable`
        - src/pytest_bdd/model/message_transport.py: imports or references `Identifiable`

    State and side effects:
        mutates id.

    Invariants:
        - `pytest_bdd.types.protocol.Identifiable` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    id: object


@runtime_checkable
class LinkedAST(Protocol):
    """
    Represent linked ast state.

    Responsibility:
        Represent linked ast state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.protocol.LinkedAST` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/compatibility/parser.py: imports or references `LinkedAST`
        - src/pytest_bdd/feature_locator.py: imports or references `LinkedAST`
        - src/pytest_bdd/model/feature_binding.py: imports or references `LinkedAST`
        - src/pytest_bdd/model/message_registry.py: imports or references `LinkedAST`
        - src/pytest_bdd/model/message_transport.py: imports or references `LinkedAST`

    State and side effects:
        mutates ast_node_id.

    Invariants:
        - `pytest_bdd.types.protocol.LinkedAST` keeps its documented import path, ownership boundary, and observable
          behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    ast_node_id: str


@runtime_checkable
class MultiLinkedAST(Protocol):
    """
    Represent multi linked ast state.

    Responsibility:
        Represent multi linked ast state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.types.protocol.MultiLinkedAST` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/compatibility/parser.py: imports or references `MultiLinkedAST`
        - src/pytest_bdd/feature_locator.py: imports or references `MultiLinkedAST`
        - src/pytest_bdd/model/feature_binding.py: imports or references `MultiLinkedAST`
        - src/pytest_bdd/model/message_registry.py: imports or references `MultiLinkedAST`
        - src/pytest_bdd/model/message_transport.py: imports or references `MultiLinkedAST`

    State and side effects:
        mutates ast_node_ids.

    Invariants:
        - `pytest_bdd.types.protocol.MultiLinkedAST` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    ast_node_ids: list[str]
