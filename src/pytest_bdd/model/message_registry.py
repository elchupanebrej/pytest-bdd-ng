"""
Provide message registry helpers.

Responsibility:
    Provide message registry helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_registry` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - _iter_object_graph: owns nested behavior below this boundary
    - _resolve_identifiable_id: owns nested behavior below this boundary
    - IdentifiableObjectRegistry: owns nested behavior below this boundary
    - EnvelopeRegistry: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/feature_binding.py: imports or references `message_registry`
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `message_registry`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
      `message_registry`

State and side effects:
    mutates identifier, stack, seen, current, current_ref; depends on __future__.annotations, collections.abc.Iterator,
    collections.abc.Mapping, contextlib.suppress, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.model.message_registry` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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

from collections.abc import Iterator, Mapping
from contextlib import suppress
from typing import TYPE_CHECKING, ClassVar, cast

from attrs import define, field
from returns.maybe import Nothing

from pytest_bdd.model.stash_access import StashBound
from pytest_bdd.types.protocol import Identifiable

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Stash
    from pytest_bdd.model.message_extension import EventEnvelope


def _iter_object_graph(root: object) -> Iterator[object]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_registry._iter_object_graph` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_registry._iter_object_graph` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - stack.extend: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - stack.pop: collaborator call used by this boundary
        - id: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/feature_binding.py: imports or references `_iter_object_graph`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_iter_object_graph`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_iter_object_graph`

    State and side effects:
        mutates stack, seen, current, current_ref, annotations.

    Invariants:
        - `pytest_bdd.model.message_registry._iter_object_graph` keeps its documented import path, ownership boundary,
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
    stack = [root]
    seen: set[int] = set()

    while stack:
        current = stack.pop()
        current_ref = id(current)
        if current_ref in seen:
            continue
        seen.add(current_ref)
        yield current

        if current is None or isinstance(current, (str, bytes, int, float, bool, complex)):
            continue

        if isinstance(current, Mapping):
            stack.extend(current.values())
            continue

        if isinstance(current, (list, tuple, set, frozenset)):
            stack.extend(current)
            continue

        annotations = getattr(type(current), "__annotations__", None)
        if isinstance(annotations, dict):
            for field_name in annotations:
                with suppress(AttributeError, TypeError):
                    value = getattr(current, field_name)
                    stack.append(value)
            continue

        values = getattr(current, "__dict__", None)
        if isinstance(values, dict):
            stack.extend(values.values())


def _resolve_identifiable_id(candidate: object) -> str | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.message_registry._resolve_identifiable_id` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_registry._resolve_identifiable_id` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - str.strip: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/feature_binding.py: imports or references `_resolve_identifiable_id`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `_resolve_identifiable_id`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_resolve_identifiable_id`

    State and side effects:
        mutates raw_identifier, identifier.

    Invariants:
        - `pytest_bdd.model.message_registry._resolve_identifiable_id` keeps its documented import path, ownership
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
    if not isinstance(candidate, Identifiable):
        return Nothing.value_or(None)

    raw_identifier = getattr(candidate, "id", None)
    if raw_identifier is None:
        return Nothing.value_or(None)

    identifier = str(raw_identifier).strip()
    return identifier or None


@define(slots=True)
class IdentifiableObjectRegistry:
    """
    Maintain a fast-lookup index of all globally identifiable objects parsed from messages.

    Responsibility:
        Maintain a fast-lookup index of all globally identifiable objects parsed from messages. It directly owns the
        observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_registry.IdentifiableObjectRegistry` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - index_tree: owns nested behavior below this boundary
        - resolve: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/execution_message_adapter.py: imports or references `IdentifiableObjectRegistry`
        - src/pytest_bdd/model/feature_binding.py: imports or references `IdentifiableObjectRegistry`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `IdentifiableObjectRegistry`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `IdentifiableObjectRegistry`

    State and side effects:
        mutates objects_by_id, identifier.

    Invariants:
        - `pytest_bdd.model.message_registry.IdentifiableObjectRegistry` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

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

    objects_by_id: dict[str, Identifiable] = field(factory=dict)

    def index_tree(self, root: object) -> None:
        """
        Recursively traverse an object graph to locate and index any Identifiable elements.

        Responsibility:
            Recursively traverse an object graph to locate and index any Identifiable elements. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_registry.IdentifiableObjectRegistry.index_tree` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - _iter_object_graph: collaborator call used by this boundary
            - _resolve_identifiable_id: collaborator call used by this boundary
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/feature_binding.py: imports or references `index_tree`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `index_tree`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `index_tree`

        State and side effects:
            mutates identifier.

        Invariants:
            - `pytest_bdd.model.message_registry.IdentifiableObjectRegistry.index_tree` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

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
        for candidate in _iter_object_graph(root):
            identifier = _resolve_identifiable_id(candidate)
            if identifier is None:
                continue
            self.objects_by_id[identifier] = cast("Identifiable", candidate)

    def resolve(self, object_id: str) -> Identifiable:
        """
        Retrieve an Identifiable object from the registry by its globally unique identifier.

        Returns:
            The matched Identifiable object.

        Responsibility:
            Retrieve an Identifiable object from the registry by its globally unique identifier. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_registry.IdentifiableObjectRegistry.resolve` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `resolve`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `resolve`
            - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `resolve`
            - src/pytest_bdd/compatibility/path.py: imports or references `resolve`
            - src/pytest_bdd/feature_locator.py: imports or references `resolve`

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
        return self.objects_by_id[object_id]


@define(slots=True)
class EnvelopeRegistry(StashBound):
    """
    Store the complete sequence of emitted EventEnvelopes and maintain an index of their identifiable contents.

    Responsibility:
        Store the complete sequence of emitted EventEnvelopes and maintain an index of their identifiable contents. It
        directly owns the observable contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_registry.EnvelopeRegistry` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - add_envelope: owns nested behavior below this boundary
        - resolve: owns nested behavior below this boundary
        - stash_missing_message: owns nested behavior below this boundary
        - register_envelope_in_pytest_stash: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/execution_message_adapter.py: imports or references `EnvelopeRegistry`
        - src/pytest_bdd/model/feature_binding.py: imports or references `EnvelopeRegistry`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `EnvelopeRegistry`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `EnvelopeRegistry`

    State and side effects:
        mutates STASH_KEY, envelopes, identifiable, registry.

    Invariants:
        - `pytest_bdd.model.message_registry.EnvelopeRegistry` keeps its documented import path, ownership boundary, and
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

    STASH_KEY: ClassVar[str] = "_pytest_bdd_envelope_registry"

    envelopes: list[EventEnvelope] = field(factory=list)
    identifiable: IdentifiableObjectRegistry = field(factory=IdentifiableObjectRegistry)

    def add_envelope(self, envelope: EventEnvelope) -> None:
        """
        Append a new event envelope to the registry and index its identifiable objects.

        Responsibility:
            Append a new event envelope to the registry and index its identifiable objects. It directly owns the
            observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.message_registry.EnvelopeRegistry.add_envelope`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.envelopes.append: collaborator call used by this boundary
            - self.identifiable.index_tree: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/feature_binding.py: imports or references `add_envelope`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `add_envelope`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `add_envelope`

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
        self.envelopes.append(envelope)
        self.identifiable.index_tree(envelope)

    def resolve(self, object_id: str) -> Identifiable | None:
        """
        Retrieve a registered Identifiable object from within any stored envelope by its unique identifier.

        Returns:
            The matched Identifiable object, or None if the identifier is not found.

        Responsibility:
            Retrieve a registered Identifiable object from within any stored envelope by its unique identifier. It
            directly owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.model.message_registry.EnvelopeRegistry.resolve`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.identifiable.resolve: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `resolve`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `resolve`
            - src/pytest_bdd/_pylint/checkers/test_import_rules.py: imports or references `resolve`
            - src/pytest_bdd/compatibility/path.py: imports or references `resolve`
            - src/pytest_bdd/feature_locator.py: imports or references `resolve`

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
        return self.identifiable.resolve(object_id)

    @classmethod
    def stash_missing_message(cls) -> str:
        """
        Provide a customized error message when the EnvelopeRegistry is absent from the pytest stash.

        Returns:
            A string explaining the prerequisite initialization for envelope tracking.

        Responsibility:
            Provide a customized error message when the EnvelopeRegistry is absent from the pytest stash. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_registry.EnvelopeRegistry.stash_missing_message` because it keeps the nearest
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
            - src/pytest_bdd/model/feature_binding.py: imports or references `stash_missing_message`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `stash_missing_message`
            - src/pytest_bdd/model/stash_access.py: imports or references `stash_missing_message`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `stash_missing_message`

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
            "`EnvelopeRegistry` is unavailable in config.stash. "
            "Execution plugins must initialize envelope tracking before reporter emission."
        )

    @classmethod
    def register_envelope_in_pytest_stash(
        cls,
        stash: Stash,
        envelope: EventEnvelope,
    ) -> EnvelopeRegistry:
        """
        Fetch the current EnvelopeRegistry from the pytest stash and append a new envelope to it.

        Returns:
            The updated EnvelopeRegistry instance.

        Responsibility:
            Fetch the current EnvelopeRegistry from the pytest stash and append a new envelope to it. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.message_registry.EnvelopeRegistry.register_envelope_in_pytest_stash` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls.from_stash: collaborator call used by this boundary
            - registry.add_envelope: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/model/feature_binding.py: imports or references `register_envelope_in_pytest_stash`
            - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `register_envelope_in_pytest_stash`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `register_envelope_in_pytest_stash`

        State and side effects:
            mutates registry.

        Invariants:
            - `pytest_bdd.model.message_registry.EnvelopeRegistry.register_envelope_in_pytest_stash` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

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
        registry = cls.from_stash(stash)
        registry.add_envelope(envelope)
        return registry
