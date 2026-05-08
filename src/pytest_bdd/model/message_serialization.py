"""Provide message serialization helpers."""

from __future__ import annotations

from copy import deepcopy
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject


class MessageSerializationProfile(str, Enum):
    """Represent message serialization profile state."""

    extended = "extended"
    schema_compatible = "schema_compatible"


_SCHEMA_COMPATIBLE_STEP_DEFINITION_PATTERN_TYPES: dict[str, str] = {
    "PYTEST_BDD_HEURISTIC_EXPRESSION": "REGULAR_EXPRESSION",
    "PYTEST_BDD_STRING_EXPRESSION": "REGULAR_EXPRESSION",
    "PYTEST_BDD_REGULAR_EXPRESSION": "REGULAR_EXPRESSION",
    "PYTEST_BDD_PARSE_EXPRESSION": "REGULAR_EXPRESSION",
    "PYTEST_BDD_CFPARSE_EXPRESSION": "REGULAR_EXPRESSION",
    "PYTEST_BDD_OTHER_EXPRESSION": "REGULAR_EXPRESSION",
}


def normalize_envelope_dict_for_profile(
    envelope_dict: JSONObject,
    *,
    profile: MessageSerializationProfile,
) -> JSONObject:
    """Normalize envelope dict for profile."""
    if profile is MessageSerializationProfile.extended:
        return envelope_dict

    normalized = deepcopy(envelope_dict)
    for payload_key in ("stepDefinition", "step_definition"):
        payload = normalized.get(payload_key)
        if not isinstance(payload, dict):
            continue
        pattern = payload.get("pattern")
        if not isinstance(pattern, dict):
            continue
        raw_type = pattern.get("type")
        if isinstance(raw_type, str):
            pattern["type"] = _SCHEMA_COMPATIBLE_STEP_DEFINITION_PATTERN_TYPES.get(raw_type, raw_type)
        break

    return normalized
