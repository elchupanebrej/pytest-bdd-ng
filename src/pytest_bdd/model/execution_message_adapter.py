"""Provide execution message adapter helpers."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, cast

from attrs import frozen

from pytest_bdd.types.json import JSONArray, JSONObject, JSONValue

from .message_converter import envelope_from_dict, envelope_to_dict
from .message_extension import EventEnvelope, PayloadKind, get_payload_kind
from .message_registry import EnvelopeRegistry, IdentifiableObjectRegistry
from .message_serialization import MessageSerializationProfile, normalize_envelope_dict_for_profile

if TYPE_CHECKING:
    from collections.abc import Callable


def _resolve_registry_index(
    registry: EnvelopeRegistry | IdentifiableObjectRegistry | None,
) -> IdentifiableObjectRegistry | None:
    if registry is None:
        return None
    if isinstance(registry, EnvelopeRegistry):
        return registry.identifiable
    return registry


@frozen
class ExecutionProjection:
    """Represent execution projection state."""

    envelope: EventEnvelope
    payload_kind: PayloadKind
    payload: object
    registry: IdentifiableObjectRegistry | None = None

    @property
    def payload_id(self) -> str | None:
        """Handle payload id."""
        raw_id = getattr(self.payload, "id", None)
        if raw_id is None:
            return None
        return str(raw_id)

    def resolve(self, object_id: str) -> object | None:
        """Resolve resolve."""
        if self.registry is None:
            return None
        return self.registry.resolve(str(object_id))


class ExecutionMessageAdapter:
    """Convert execution values into message payloads."""

    @staticmethod
    def _is_reference_key(key: str) -> bool:
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
                            JSONArray,
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
        """Handle namespace dict ids."""
        prefix = f"{namespace}:"

        def _namespace(value: str) -> str:
            return value if value.startswith(prefix) else f"{prefix}{value}"

        return cast(JSONObject, cls._transform_ids(deepcopy(envelope_dict), transform=_namespace))

    @classmethod
    def rewrite_dict_ids(cls, envelope_dict: JSONObject, remap: dict[str, str]) -> JSONObject:
        """Handle rewrite dict ids."""
        if not remap:
            return cast(JSONObject, deepcopy(envelope_dict))
        return cast(
            JSONObject,
            cls._transform_ids(deepcopy(envelope_dict), transform=lambda value: remap.get(value, value)),
        )

    @staticmethod
    def serialize(
        envelope: EventEnvelope,
        *,
        profile: MessageSerializationProfile = MessageSerializationProfile.extended,
    ) -> EventEnvelope:
        """Handle serialize."""
        ExecutionMessageAdapter.serialize_to_dict(envelope, profile=profile)
        return envelope

    @staticmethod
    def serialize_to_dict(
        envelope: EventEnvelope,
        *,
        profile: MessageSerializationProfile = MessageSerializationProfile.extended,
    ) -> JSONObject:
        """Handle serialize to dict."""
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
        Handle deserialize.

        Raises:
            TypeError: If the operation cannot be completed.

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
        """Handle deserialize dict."""
        return cls.deserialize(envelope_from_dict(payload), registry=registry)
