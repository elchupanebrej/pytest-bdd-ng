"""Validation for individual Cucumber Messages envelopes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, cast
from urllib.parse import urljoin

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from pytest_cuke.message_schema_sync import SchemaSyncError, UpstreamRelease, resolve_upstream_release
from pytest_cuke.model import message_types as messages
from pytest_cuke.model.message_extension import PAYLOAD_KINDS, get_payload_kind
from pytest_cuke.model.message_types import message_to_dict

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from pytest_cuke.model import message_types as messages


MessageValidationCode: TypeAlias = Literal[
    "INVALID_PAYLOAD_SHAPE",
    "SCHEMA_VALIDATION_ERROR",
    "UNSUPPORTED_PROTOCOL_VERSION",
    "DUPLICATE_LIFECYCLE_ID",
    "ORPHAN_REFERENCE",
    "OUT_OF_ORDER_LIFECYCLE",
    "INCOMPLETE_LIFECYCLE",
    "SINK_FAILURE",
    "FINAL_STREAM_VALIDATION_ERROR",
    "missing_worker_manifest",
    "missing_worker_fragment",
    "interrupted_worker_transfer",
    "partial_stream",
    "duplicate_worker_batch",
    "duplicate_worker_manifest",
    "worker_manifest_mismatch",
]
MessageValidationSeverity: TypeAlias = Literal["error", "warning"]
JsonPathComponent: TypeAlias = str | int

_SCHEMA_BASE_URI = "https://pytest-cuke.invalid/cucumber/messages/"


@dataclass(frozen=True, slots=True)
class MessageValidationDiagnostic:
    """A stable, serializable description of one message validation problem."""

    code: MessageValidationCode
    severity: MessageValidationSeverity
    position: int
    payload_kind: str | None
    message: str
    offending_ids: tuple[str, ...] = ()
    instance_path: tuple[JsonPathComponent, ...] | None = None


class MessageValidationError(ValueError):
    """Raised when a validator rejects an envelope or a terminal stream action."""

    def __init__(self, diagnostics: Iterable[MessageValidationDiagnostic]) -> None:
        self.diagnostics = tuple(diagnostics)
        super().__init__("; ".join(diagnostic.message for diagnostic in self.diagnostics))


def message_diagnostic_to_dict(diagnostic: MessageValidationDiagnostic) -> dict[str, object]:
    """Serialize one diagnostic with its stable machine-readable field names."""
    instance_path = diagnostic.instance_path
    path_string = (
        None
        if instance_path is None
        else "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in instance_path)
    )
    return {
        "code": diagnostic.code,
        "severity": diagnostic.severity,
        "position": diagnostic.position,
        "payload_kind": diagnostic.payload_kind,
        "message": diagnostic.message,
        "offending_ids": list(diagnostic.offending_ids),
        "instance_path": path_string,
    }


def integration_diagnostic(
    code: MessageValidationCode,
    *,
    position: int,
    payload_kind: str | None,
    message: str,
    offending_ids: Iterable[str] = (),
    instance_path: tuple[JsonPathComponent, ...] | None = None,
) -> MessageValidationDiagnostic:
    """Build a standard diagnostic for failures raised outside envelope validation."""
    return MessageValidationDiagnostic(
        code=code,
        severity="error",
        position=position,
        payload_kind=payload_kind,
        message=message,
        offending_ids=tuple(offending_ids),
        instance_path=instance_path,
    )


@lru_cache(maxsize=1)
def _installed_release() -> tuple[str, UpstreamRelease]:
    return resolve_upstream_release()


@lru_cache(maxsize=1)
def _schema_registry() -> tuple[dict[str, dict[str, object]], Registry]:
    _, release = _installed_release()
    schema_dir = resources.files("pytest_cuke.model").joinpath("message_schemas")
    schemas: dict[str, dict[str, object]] = {}
    resources_by_uri: list[tuple[str, Resource[dict[str, object]]]] = []

    for schema_path in sorted(schema_dir.iterdir(), key=lambda item: item.name):
        if not schema_path.name.endswith(".schema.json"):
            continue
        schema_name = schema_path.name.removesuffix(".schema.json") + ".json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if not isinstance(schema, dict):
            continue
        schema_uri = urljoin(f"{_SCHEMA_BASE_URI}{release.tag}/", schema_name)
        schema["$id"] = schema_uri
        schemas[schema_name] = schema
        resources_by_uri.append((schema_uri, Resource.from_contents(schema)))

    def reject_remote_retrieval(uri: str) -> Resource[dict[str, object]]:
        raise NoSuchResource(uri)

    registry = Registry(retrieve=reject_remote_retrieval).with_resources(  # type: ignore[call-arg]
        resources_by_uri
    )
    return schemas, registry


def _supported_protocol_version() -> str | None:
    try:
        _, release = _installed_release()
    except SchemaSyncError:
        return None
    return release.protocol_version


def _diagnostic(
    *,
    code: MessageValidationCode,
    position: int,
    payload_kind: str | None,
    message: str,
    offending_ids: Iterable[str] = (),
    instance_path: tuple[JsonPathComponent, ...] | None = None,
) -> MessageValidationDiagnostic:
    return MessageValidationDiagnostic(
        code=code,
        severity="error",
        position=position,
        payload_kind=payload_kind,
        message=message,
        offending_ids=tuple(offending_ids),
        instance_path=instance_path,
    )


def _snake_to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in tail)


def _validate_envelope_instance(
    instance: dict[str, Any],
    *,
    payload_kind: str | None,
    position: int,
) -> tuple[MessageValidationDiagnostic, ...]:
    try:
        expected_version = _supported_protocol_version()
        schemas, registry = _schema_registry()
    except SchemaSyncError as error:
        return (
            _diagnostic(
                code="UNSUPPORTED_PROTOCOL_VERSION",
                position=position,
                payload_kind=payload_kind,
                message=str(error),
            ),
        )

    schema = schemas.get("Envelope.json")
    if schema is None:
        return (
            _diagnostic(
                code="SCHEMA_VALIDATION_ERROR",
                position=position,
                payload_kind=payload_kind,
                message="The vendored Envelope JSON Schema is unavailable",
            ),
        )

    errors: list[MessageValidationDiagnostic] = []
    validator = Draft202012Validator(schema, registry=registry)
    for schema_error in sorted(
        validator.iter_errors(instance),
        key=lambda item: (tuple(str(part) for part in item.absolute_path), item.message),
    ):
        errors.append(
            _diagnostic(
                code="SCHEMA_VALIDATION_ERROR",
                position=position,
                payload_kind=payload_kind,
                message=schema_error.message,
                instance_path=tuple(schema_error.absolute_path),
            )
        )

    if payload_kind == "meta":
        wire_meta_data = instance.get("meta")
        wire_meta = cast("dict[str, Any]", wire_meta_data) if isinstance(wire_meta_data, dict) else None
        protocol_version = wire_meta.get("protocolVersion") if wire_meta is not None else None
        if isinstance(protocol_version, str) and (expected_version is None or protocol_version != expected_version):
            expected = expected_version if expected_version is not None else "a version supported by this installation"
            errors.append(
                _diagnostic(
                    code="UNSUPPORTED_PROTOCOL_VERSION",
                    position=position,
                    payload_kind=payload_kind,
                    message=(f"Meta protocolVersion {protocol_version!r} is unsupported; expected {expected!r}"),
                    instance_path=("meta", "protocolVersion"),
                )
            )

    return tuple(errors)


def validate_envelope_data(
    envelope_data: Mapping[str, object],
    *,
    position: int = 0,
) -> tuple[MessageValidationDiagnostic, ...]:
    """Validate raw wire data before a model converter can discard unknown fields."""
    payload_kinds = {_snake_to_camel(kind): kind for kind in PAYLOAD_KINDS}
    found_kinds = [kind for wire_name, kind in payload_kinds.items() if wire_name in envelope_data]
    payload_kind = found_kinds[0] if len(found_kinds) == 1 else None
    errors: list[MessageValidationDiagnostic] = []
    if len(found_kinds) != 1:
        errors.append(
            _diagnostic(
                code="INVALID_PAYLOAD_SHAPE",
                position=position,
                payload_kind=payload_kind,
                message=f"Envelope must contain exactly one payload; found {len(found_kinds)}",
            )
        )
    errors.extend(_validate_envelope_instance(dict(envelope_data), payload_kind=payload_kind, position=position))
    return tuple(errors)


def validate_envelope(
    envelope: messages.Envelope,
    *,
    position: int = 0,
) -> tuple[MessageValidationDiagnostic, ...]:
    """Validate payload cardinality and one envelope against its official v28 schema."""
    payload_kind = get_payload_kind(envelope)
    payload_count = sum(getattr(envelope, name, None) is not None for name in PAYLOAD_KINDS)
    if payload_count != 1 or payload_kind is None:
        return (
            _diagnostic(
                code="INVALID_PAYLOAD_SHAPE",
                position=position,
                payload_kind=None,
                message=f"Envelope must contain exactly one payload; found {payload_count}",
            ),
        )

    try:
        instance = message_to_dict(envelope)
    except Exception as serialization_error:  # defensive against model_construct() callers
        return (
            _diagnostic(
                code="SCHEMA_VALIDATION_ERROR",
                position=position,
                payload_kind=payload_kind,
                message=f"Envelope could not be serialized for schema validation: {serialization_error}",
            ),
        )

    return validate_envelope_data(instance, position=position)


__all__ = [
    "JsonPathComponent",
    "MessageValidationCode",
    "MessageValidationDiagnostic",
    "MessageValidationError",
    "MessageValidationSeverity",
    "integration_diagnostic",
    "validate_envelope",
    "validate_envelope_data",
]
