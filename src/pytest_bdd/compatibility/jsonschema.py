"""Provide jsonschema helpers."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


class ValidationError(Protocol):
    """Represent validation error failures."""

    message: str
    absolute_path: Sequence[object]
    absolute_schema_path: Sequence[object]
    validator: object | None


class SchemaValidator(Protocol):
    """Represent schema validator state."""

    def iter_errors(self, instance: object) -> Iterable[ValidationError]:
        """Yield errors."""
        ...


def build_validator(schema: object, *, registry: object | None = None) -> SchemaValidator:
    """Build validator."""
    validators = import_module("jsonschema.validators")
    validator_class = validators.validator_for(schema)
    validator_class.check_schema(schema)
    if registry is None:
        return cast(SchemaValidator, validator_class(schema))
    return cast(SchemaValidator, validator_class(schema, registry=registry))
