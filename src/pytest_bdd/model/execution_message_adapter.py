from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .message_converter import envelope_from_dict, envelope_to_dict
from .message_extension import EventEnvelope, PayloadKind, get_payload_kind
from .message_registry import EnvelopeRegistry, IdentifiableObjectRegistry


def _resolve_registry_index(
    registry: EnvelopeRegistry | IdentifiableObjectRegistry | None,
) -> IdentifiableObjectRegistry | None:
    if registry is None:
        return None
    if isinstance(registry, EnvelopeRegistry):
        return registry.identifiable
    return registry


@dataclass(frozen=True, slots=True)
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
    def serialize(envelope: EventEnvelope) -> EventEnvelope:
        envelope_to_dict(envelope)
        return envelope

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
