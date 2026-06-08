"""
Provide execution message adapter helpers.

Responsibility:
    Provide execution message adapter helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.execution_message_adapter` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - _resolve_registry_index: owns nested behavior below this boundary
    - ExecutionProjection: owns nested behavior below this boundary
    - ExecutionMessageAdapter: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `execution_message_adapter`
    - src/pytest_bdd/model/message_schema_validation.py: imports or references `execution_message_adapter`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
      `execution_message_adapter`
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
      `execution_message_adapter`

State and side effects:
    mutates payload_kind, payload, envelope, registry, raw_id; depends on __future__.annotations, copy.deepcopy,
    typing.TYPE_CHECKING, typing.cast, attrs.frozen.

Invariants:
    - `pytest_bdd.model.execution_message_adapter` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Failure semantics:
    Raises or re-raises TypeError; callers must treat these as boundary failures.

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

from copy import deepcopy
from typing import TYPE_CHECKING, cast

from attrs import frozen
from returns.maybe import Nothing

from .message_converter import envelope_from_dict, envelope_to_dict
from .message_extension import EventEnvelope, PayloadKind, get_payload_kind
from .message_registry import EnvelopeRegistry, IdentifiableObjectRegistry
from .message_serialization import MessageSerializationProfile, normalize_envelope_dict_for_profile

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_bdd.types.json import JSONArray, JSONObject, JSONValue


def _resolve_registry_index(
    registry: EnvelopeRegistry | IdentifiableObjectRegistry | None,
) -> IdentifiableObjectRegistry | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.model.execution_message_adapter._resolve_registry_index` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.execution_message_adapter._resolve_registry_index`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_resolve_registry_index`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `_resolve_registry_index`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_resolve_registry_index`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `_resolve_registry_index`

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
    if registry is None:
        return Nothing.value_or(None)
    if isinstance(registry, EnvelopeRegistry):
        return registry.identifiable
    return registry


@frozen
class ExecutionProjection:
    """
    Wrap an event envelope with payload kind, payload, and registry access.

    Responsibility:
        Wrap an event envelope with payload kind, payload, and registry access. It directly owns the observable
        contract, local decisions, and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.execution_message_adapter.ExecutionProjection`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - payload_id: owns nested behavior below this boundary
        - resolve: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `ExecutionProjection`
        - src/pytest_bdd/model/__init__.py: imports or references `ExecutionProjection`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `ExecutionProjection`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `ExecutionProjection`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `ExecutionProjection`

    State and side effects:
        mutates envelope, payload_kind, payload, registry, raw_id.

    Invariants:
        - `pytest_bdd.model.execution_message_adapter.ExecutionProjection` keeps its documented import path, ownership
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

    envelope: EventEnvelope
    payload_kind: PayloadKind
    payload: object
    registry: IdentifiableObjectRegistry | None = None

    @property
    def payload_id(self) -> str | None:
        """
        Extract the string-based identifier from the current payload, if one exists.

        Returns:
            The payload ID string, or None if the payload lacks an ID.

        Responsibility:
            Extract the string-based identifier from the current payload, if one exists. It directly owns the observable
            contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.execution_message_adapter.ExecutionProjection.payload_id` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - Nothing.value_or: collaborator call used by this boundary
            - str: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `payload_id`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `payload_id`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `payload_id`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `payload_id`

        State and side effects:
            mutates raw_id.

        Invariants:
            - `pytest_bdd.model.execution_message_adapter.ExecutionProjection.payload_id` keeps its documented import
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
        raw_id = getattr(self.payload, "id", None)
        if raw_id is None:
            return Nothing.value_or(None)
        return str(raw_id)

    def resolve(self, object_id: str) -> object | None:
        """
        Retrieve a registered identifiable object using its string ID via the associated registry.

        Returns:
            The resolved object if found, or None if the registry is unavailable or the object is unknown.

        Responsibility:
            Retrieve a registered identifiable object using its string ID via the associated registry. It directly owns
            the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.execution_message_adapter.ExecutionProjection.resolve` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - Nothing.value_or: collaborator call used by this boundary
            - self.registry.resolve: collaborator call used by this boundary
            - str: collaborator call used by this boundary

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
        if self.registry is None:
            return Nothing.value_or(None)
        return self.registry.resolve(str(object_id))


class ExecutionMessageAdapter:
    """
    Convert execution values into message payloads.

    Responsibility:
        Convert execution values into message payloads. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _is_reference_key: owns nested behavior below this boundary
        - _transform_ids: owns nested behavior below this boundary
        - namespace_dict_ids: owns nested behavior below this boundary
        - rewrite_dict_ids: owns nested behavior below this boundary
        - serialize: owns nested behavior below this boundary
        - serialize_to_dict: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `ExecutionMessageAdapter`
        - src/pytest_bdd/model/__init__.py: imports or references `ExecutionMessageAdapter`
        - src/pytest_bdd/model/message_consolidation.py: imports or references `ExecutionMessageAdapter`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `ExecutionMessageAdapter`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `ExecutionMessageAdapter`

    State and side effects:
        mutates transformed, prefix, envelope_dict, normalized_envelope, payload_kind.

    Invariants:
        - `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TypeError; callers must treat these as boundary failures.

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
    def _is_reference_key(key: str) -> bool:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter._is_reference_key` owns documented
            method behavior. It directly owns the observable contract, local decisions, and maintenance boundary for
            this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter._is_reference_key` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - key.endswith: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_is_reference_key`
            - src/pytest_bdd/model/message_consolidation.py: imports or references `_is_reference_key`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `_is_reference_key`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_is_reference_key`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_is_reference_key`

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
        if key == "workerId":
            return False
        return key.endswith(("Id", "Ids", "_id", "_ids"))

    @classmethod
    def _transform_ids(
        cls,
        value: JSONValue,
        *,
        transform: Callable[[str], str],
    ) -> JSONValue:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter._transform_ids` owns documented method
            behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter._transform_ids` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - transform: collaborator call used by this boundary
            - cls._transform_ids: collaborator call used by this boundary
            - value.items: collaborator call used by this boundary
            - cls._is_reference_key: collaborator call used by this boundary
            - cast: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_transform_ids`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `_transform_ids`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_transform_ids`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_transform_ids`

        State and side effects:
            mutates transformed.

        Invariants:
            - `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter._transform_ids` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

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
        if isinstance(value, dict):
            transformed: JSONObject = {}
            for key, item in value.items():
                if key == "id" and isinstance(item, str):
                    transformed[key] = transform(item)
                    continue
                if cls._is_reference_key(key):
                    if isinstance(item, str):
                        transformed[key] = transform(item)
                        continue
                    if isinstance(item, list):
                        transformed[key] = cast(
                            "JSONArray",
                            [transform(candidate) if isinstance(candidate, str) else candidate for candidate in item],
                        )
                        continue
                transformed[key] = cls._transform_ids(item, transform=transform)
            return transformed
        if isinstance(value, list):
            return [cls._transform_ids(item, transform=transform) for item in value]
        return value

    @classmethod
    def namespace_dict_ids(cls, envelope_dict: JSONObject, *, namespace: str) -> JSONObject:
        """
        Prefix all identified reference strings within an envelope dictionary with a given namespace.

        Returns:
            A new dictionary with namespaced IDs.

        Responsibility:
            Prefix all identified reference strings within an envelope dictionary with a given namespace. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.namespace_dict_ids` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - _namespace: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `namespace_dict_ids`
            - src/pytest_bdd/model/message_consolidation.py: imports or references `namespace_dict_ids`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `namespace_dict_ids`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `namespace_dict_ids`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `namespace_dict_ids`

        State and side effects:
            mutates prefix.

        Invariants:
            - `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.namespace_dict_ids` keeps its
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
        prefix = f"{namespace}:"

        def _namespace(value: str) -> str:
            """
            Responsibility:
                Responsibility: Responsibility:
                `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.namespace_dict_ids._namespace` owns
                documented method behavior. It directly owns the observable contract, local decisions, and maintenance
                boundary for this method.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.namespace_dict_ids._namespace`
                because it keeps the nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - value.startswith: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `_namespace`
                - src/pytest_bdd/model/message_schema_validation.py: imports or references `_namespace`
                - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
                  `_namespace`
                - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
                  `_namespace`

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
            return value if value.startswith(prefix) else f"{prefix}{value}"

        return cast("JSONObject", cls._transform_ids(deepcopy(envelope_dict), transform=_namespace))

    @classmethod
    def rewrite_dict_ids(cls, envelope_dict: JSONObject, remap: dict[str, str]) -> JSONObject:
        """
        Map reference strings in an envelope dictionary to new values using a provided mapping dictionary.

        Returns:
            A new dictionary reflecting the remapped IDs.

        Responsibility:
            Map reference strings in an envelope dictionary to new values using a provided mapping dictionary. It
            directly owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.rewrite_dict_ids` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - deepcopy: collaborator call used by this boundary
            - cls._transform_ids: collaborator call used by this boundary
            - remap.get: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `rewrite_dict_ids`
            - src/pytest_bdd/model/message_consolidation.py: imports or references `rewrite_dict_ids`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `rewrite_dict_ids`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `rewrite_dict_ids`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `rewrite_dict_ids`

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
        if not remap:
            return deepcopy(envelope_dict)
        return cls._transform_ids(deepcopy(envelope_dict), transform=lambda value: remap.get(value, value))  # type: ignore[return-value]  # JSONValue union variant

    @staticmethod
    def serialize(
        envelope: EventEnvelope,
        *,
        profile: MessageSerializationProfile = MessageSerializationProfile.extended,
    ) -> EventEnvelope:
        """
        Normalize an EventEnvelope based on a specified serialization profile without mutating its class type.

        Returns:
            The processed EventEnvelope instance.

        Responsibility:
            Normalize an EventEnvelope based on a specified serialization profile without mutating its class type. It
            directly owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.serialize` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - ExecutionMessageAdapter.serialize_to_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `serialize`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `serialize`
            - src/pytest_bdd/model/scenario_report.py: imports or references `serialize`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `serialize`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `serialize`

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
        ExecutionMessageAdapter.serialize_to_dict(envelope, profile=profile)
        return envelope

    @staticmethod
    def serialize_to_dict(
        envelope: EventEnvelope,
        *,
        profile: MessageSerializationProfile = MessageSerializationProfile.extended,
    ) -> JSONObject:
        """
        Convert envelope to JSON dict, stripping internal fields.

        Returns:
            A JSON-compatible dictionary representation of the envelope.

        Responsibility:
            Convert envelope to JSON dict, stripping internal fields. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.serialize_to_dict` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - envelope_to_dict: collaborator call used by this boundary
            - normalize_envelope_dict_for_profile: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `serialize_to_dict`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `serialize_to_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `serialize_to_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `serialize_to_dict`

        State and side effects:
            mutates envelope_dict.

        Invariants:
            - `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.serialize_to_dict` keeps its
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
        envelope_dict = envelope_to_dict(envelope)
        return normalize_envelope_dict_for_profile(envelope_dict, profile=profile)

    @classmethod
    def deserialize(
        cls,
        envelope: EventEnvelope,
        *,
        registry: EnvelopeRegistry | IdentifiableObjectRegistry | None = None,
    ) -> ExecutionProjection:
        """
        Normalize an incoming EventEnvelope and extract its internal projection state (payload, kind).

        Returns:
            An ExecutionProjection representing the normalized envelope.

        Raises:
            TypeError: If the envelope fails payload shape validation (e.g., missing or multiple payloads).

        Responsibility:
            Normalize an incoming EventEnvelope and extract its internal projection state (payload, kind). It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.deserialize` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls.serialize: collaborator call used by this boundary
            - get_payload_kind: collaborator call used by this boundary
            - TypeError: collaborator call used by this boundary
            - getattr: collaborator call used by this boundary
            - ExecutionProjection: collaborator call used by this boundary
            - _resolve_registry_index: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `deserialize`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `deserialize`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `deserialize`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `deserialize`

        State and side effects:
            mutates normalized_envelope, payload_kind, msg, payload.

        Invariants:
            - `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.deserialize` keeps its documented
              import path, ownership boundary, and observable behavior stable for callers.

        Failure semantics:
            Raises or re-raises TypeError; callers must treat these as boundary failures.

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
        normalized_envelope = cls.serialize(envelope)
        payload_kind = get_payload_kind(normalized_envelope)
        if payload_kind is None:
            msg = "Envelope must include exactly one payload field"
            raise TypeError(msg)
        payload = getattr(normalized_envelope, payload_kind)
        return ExecutionProjection(
            envelope=normalized_envelope,
            payload_kind=payload_kind,
            payload=payload,
            registry=_resolve_registry_index(registry),
        )

    @classmethod
    def deserialize_dict(
        cls,
        payload: JSONObject,
        *,
        registry: EnvelopeRegistry | IdentifiableObjectRegistry | None = None,
    ) -> ExecutionProjection:
        """
        Instantiate an EventEnvelope from a dictionary and immediately extract its projection state.

        Returns:
            An ExecutionProjection derived from the parsed dictionary.

        Responsibility:
            Instantiate an EventEnvelope from a dictionary and immediately extract its projection state. It directly
            owns the observable contract, local decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.model.execution_message_adapter.ExecutionMessageAdapter.deserialize_dict` because it keeps the
            nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - cls.deserialize: collaborator call used by this boundary
            - envelope_from_dict: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `deserialize_dict`
            - src/pytest_bdd/model/message_consolidation.py: imports or references `deserialize_dict`
            - src/pytest_bdd/model/message_schema_validation.py: imports or references `deserialize_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `deserialize_dict`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `deserialize_dict`

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
        return cls.deserialize(envelope_from_dict(payload), registry=registry)
