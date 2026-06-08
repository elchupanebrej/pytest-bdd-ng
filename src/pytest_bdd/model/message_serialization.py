"""
Provide message serialization helpers.

Responsibility:
    Provide message serialization helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.message_serialization` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - MessageSerializationProfile: owns nested behavior below this boundary
    - normalize_envelope_dict_for_profile: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `message_serialization`
    - src/pytest_bdd/model/message_schema_validation.py: imports or references `message_serialization`
    - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
      `message_serialization`
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
      `message_serialization`

State and side effects:
    mutates extended, schema_compatible, _SCHEMA_COMPATIBLE_STEP_DEFINITION_PATTERN_TYPES, normalized, payload; depends
    on __future__.annotations, copy.deepcopy, enum.Enum, typing.TYPE_CHECKING, pytest_bdd.types.json.JSONObject.

Invariants:
    - `pytest_bdd.model.message_serialization` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

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
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_bdd.types.json import JSONObject


class MessageSerializationProfile(str, Enum):
    """
    Enumerate the output serialization modes.

    Responsibility:
        Enumerate the output serialization modes. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.message_serialization.MessageSerializationProfile`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references `MessageSerializationProfile`
        - src/pytest_bdd/model/__init__.py: imports or references `MessageSerializationProfile`
        - src/pytest_bdd/model/execution_message_adapter.py: imports or references `MessageSerializationProfile`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `MessageSerializationProfile`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `MessageSerializationProfile`

    State and side effects:
        mutates extended, schema_compatible.

    Invariants:
        - `pytest_bdd.model.message_serialization.MessageSerializationProfile` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

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
    """
    Normalize an envelope dictionary based on the requested serialization profile.

    In 'schema_compatible' mode, pytest-bdd-specific step definition pattern types are downgraded to their canonical
    cucumber counterparts so the output passes strict upstream schema validation. In 'extended' mode the dictionary
    is returned unchanged, preserving pytest-bdd-specific type information for internal consumers.

    Returns:
        A normalized copy of the envelope dictionary conforming to the requested profile.

    Responsibility:
        Normalize an envelope dictionary based on the requested serialization profile. It directly owns the observable
        contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.model.message_serialization.normalize_envelope_dict_for_profile` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - deepcopy: collaborator call used by this boundary
        - normalized.get: collaborator call used by this boundary
        - payload.get: collaborator call used by this boundary
        - pattern.get: collaborator call used by this boundary
        - _SCHEMA_COMPATIBLE_STEP_DEFINITION_PATTERN_TYPES.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/message_stream_validation/pipeline.py: imports or references
          `normalize_envelope_dict_for_profile`
        - src/pytest_bdd/model/execution_message_adapter.py: imports or references `normalize_envelope_dict_for_profile`
        - src/pytest_bdd/model/message_schema_validation.py: imports or references `normalize_envelope_dict_for_profile`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `normalize_envelope_dict_for_profile`
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
          `normalize_envelope_dict_for_profile`

    State and side effects:
        mutates normalized, payload, pattern, raw_type.

    Invariants:
        - `pytest_bdd.model.message_serialization.normalize_envelope_dict_for_profile` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

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
