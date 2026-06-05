"""Typed failure reasons for Result-based pytest-bdd operations."""

from __future__ import annotations

from pytest_bdd.compatibility.enum import StrEnum


class StashFailure(StrEnum):
    """Failure reasons for stash access operations."""

    NOT_FOUND = "not_found"
    TYPE_MISMATCH = "type_mismatch"
    ALREADY_INITIALIZED = "already_initialized"


class ScenarioRunFailure(StrEnum):
    """Failure reasons for scenario run operations."""

    FEATURE_NOT_BOUND = "feature_not_bound"
    STEP_NOT_FOUND = "step_not_found"
    INVALID_STAGE = "invalid_stage"
    BINDING_FAILED = "binding_failed"


class MessageValidationFailure(StrEnum):
    """Failure reasons for message validation operations."""

    SCHEMA_LOAD_ERROR = "schema_load_error"
    VALIDATION_FAILED = "validation_failed"
    INVALID_ENVELOPE = "invalid_envelope"


class FeatureLocatorFailure(StrEnum):
    """Failure reasons for feature locator operations."""

    FILE_NOT_FOUND = "file_not_found"
    PARSE_FAILED = "parse_failed"
    RESOLUTION_FAILED = "resolution_failed"


class CollectorFailure(StrEnum):
    """Failure reasons for collection operations."""

    PARSE_FAILED = "parse_failed"
    READ_FAILED = "read_failed"
    BATCH_FAILED = "batch_failed"


class ParserFailure(StrEnum):
    """Failure reasons for parser operations."""

    SYNTAX_ERROR = "syntax_error"
    UNSUPPORTED_MIMETYPE = "unsupported_mimetype"


class GenericFailure(StrEnum):
    """Failure reasons for uncategorized operations."""

    UNEXPECTED_ERROR = "unexpected_error"
