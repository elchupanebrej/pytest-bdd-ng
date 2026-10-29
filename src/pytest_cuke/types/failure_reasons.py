from __future__ import annotations

import sys
from enum import Enum

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, Enum):
        pass


class StashFailure(StrEnum):
    NOT_FOUND = "not_found"
    TYPE_MISMATCH = "type_mismatch"
    ALREADY_INITIALIZED = "already_initialized"


class ScenarioRunFailure(StrEnum):
    FEATURE_NOT_BOUND = "feature_not_bound"
    STEP_NOT_FOUND = "step_not_found"
    INVALID_STAGE = "invalid_stage"
    BINDING_FAILED = "binding_failed"


class MessageValidationFailure(StrEnum):
    SCHEMA_LOAD_ERROR = "schema_load_error"
    VALIDATION_FAILED = "validation_failed"
    INVALID_ENVELOPE = "invalid_envelope"


class FeatureLocatorFailure(StrEnum):
    FILE_NOT_FOUND = "file_not_found"
    PARSE_FAILED = "parse_failed"
    RESOLUTION_FAILED = "resolution_failed"


class CollectorFailure(StrEnum):
    PARSE_FAILED = "parse_failed"
    READ_FAILED = "read_failed"
    BATCH_FAILED = "batch_failed"


class ParserFailure(StrEnum):
    SYNTAX_ERROR = "syntax_error"
    UNSUPPORTED_MIMETYPE = "unsupported_mimetype"


class GenericFailure(StrEnum):
    UNEXPECTED_ERROR = "unexpected_error"
