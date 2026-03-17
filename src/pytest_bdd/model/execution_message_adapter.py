from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

from attrs import frozen

from .message_converter import envelope_from_dict, envelope_to_dict
from .message_extension import EventEnvelope, PayloadKind, get_payload_kind
from .message_registry import EnvelopeRegistry, IdentifiableObjectRegistry
from .message_serialization import MessageSerializationProfile, normalize_envelope_dict_for_profile


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
    envelope: EventEnvelope
    payload_kind: PayloadKind
    payload: Any
    registry: IdentifiableObjectRegistry | None = None

    @property
    def payload_id(self) -> str | None:
        raw_id = getattr(self.payload, "id", None)
        if raw_id is None:
            return None
        return str(raw_id)

    def resolve(self, object_id: str) -> Any | None:
        if self.registry is None:
            return None
        return self.registry.resolve(str(object_id))


class ExecutionMessageAdapter:
    @staticmethod
    def _is_reference_key(key: str) -> bool:
        if key == "workerId":
            return False
        return key.endswith(("Id", "Ids", "_id", "_ids"))

    @classmethod
    def _transform_ids(
        cls,
        value: Any,
        *,
        transform: Any,
    ) -> Any:
        if isinstance(value, dict):
            transformed: dict[str, Any] = {}
            for key, item in value.items():
                if key == "id" and isinstance(item, str):
                    transformed[key] = transform(item)
                    continue
                if cls._is_reference_key(key):
                    if isinstance(item, str):
                        transformed[key] = transform(item)
                        continue
                    if isinstance(item, list):
                        transformed[key] = [
                            transform(candidate) if isinstance(candidate, str) else candidate for candidate in item
                        ]
                        continue
                transformed[key] = cls._transform_ids(item, transform=transform)
            return transformed
        if isinstance(value, list):
            return [cls._transform_ids(item, transform=transform) for item in value]
        return value

    @classmethod
    def namespace_dict_ids(cls, envelope_dict: dict[str, Any], *, namespace: str) -> dict[str, Any]:
        prefix = f"{namespace}:"

        def _namespace(value: str) -> str:
            return value if value.startswith(prefix) else f"{prefix}{value}"

        return cast(dict[str, Any], cls._transform_ids(deepcopy(envelope_dict), transform=_namespace))

    @classmethod
    def rewrite_dict_ids(cls, envelope_dict: dict[str, Any], remap: dict[str, str]) -> dict[str, Any]:
        if not remap:
            return cast(dict[str, Any], deepcopy(envelope_dict))
        return cast(
            dict[str, Any],
            cls._transform_ids(deepcopy(envelope_dict), transform=lambda value: remap.get(value, value)),
        )

    @staticmethod
    def serialize(
        envelope: EventEnvelope,
        *,
        profile: MessageSerializationProfile = MessageSerializationProfile.extended,
    ) -> EventEnvelope:
        ExecutionMessageAdapter.serialize_to_dict(envelope, profile=profile)
        return envelope

    @staticmethod
    def serialize_to_dict(
        envelope: EventEnvelope,
        *,
        profile: MessageSerializationProfile = MessageSerializationProfile.extended,
    ) -> dict[str, Any]:
        envelope_dict = envelope_to_dict(envelope)
        return normalize_envelope_dict_for_profile(envelope_dict, profile=profile)

    @classmethod
    def deserialize(
        cls,
        envelope: EventEnvelope,
        *,
        registry: EnvelopeRegistry | IdentifiableObjectRegistry | None = None,
    ) -> ExecutionProjection:
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
        payload: dict[str, Any],
        *,
        registry: EnvelopeRegistry | IdentifiableObjectRegistry | None = None,
    ) -> ExecutionProjection:
        return cls.deserialize(envelope_from_dict(payload), registry=registry)
