"""
Defines recursive JSON type aliases (JSONPrimitive, JSONValue, JSONObject, JSONArray) used for
type-annotating JSON s.

Responsibility:
    Defines recursive JSON type aliases (JSONPrimitive, JSONValue, JSONObject, JSONArray) used for
    type-annotating JSON serialization boundaries throughout the Cucumber message conversion and
    formatter subsystems of pytest-bdd.

Reason for existence:
    The recursive JSONValue type requires forward references and cannot be expressed as a simple
    alias. Centralizing it here prevents duplication and ensures all JSON-handling code uses
    consistent type annotations for static analysis tools like mypy across the codebase.

Delegates:
    - `typing.TypeAlias`: provides the type alias annotation mechanism

Cohesion:
    All four TypeAlias definitions build on each other forming a single recursive JSON type
    hierarchy.

Separation:
    - `pytest_bdd.types.protocol`: protocol defines behavioral contracts while json provides data shape aliases.

Main consumers:
    - `pytest_bdd.model.message_converter`: uses JSON types for message serialization annotations

State and side effects:
    None, TypeAlias definitions have zero runtime footprint and keep no state.

Invariants:
    - JSONValue correctly models the recursive nature of JSON where values can contain nested objects and arrays.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=5
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=5
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

from typing import TypeAlias

JSONPrimitive: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONPrimitive | dict[str, "JSONValue"] | list["JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]
JSONArray: TypeAlias = list[JSONValue]
