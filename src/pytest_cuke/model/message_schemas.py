"""Load vendored Cucumber Messages JSON schemas from the installed package."""

from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import cast

_SCHEMA_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")


def load_message_schema(name: str) -> dict[str, object]:
    """Load one bundled schema by its Cucumber Messages type name.

    ``name`` may be a bare type name (``"Envelope"``) or the matching JSON
    filename. Reading is deferred until this function is called so importing
    pytest-cuke never performs filesystem, network, or synchronization work.
    """
    schema_name = name.removesuffix(".schema.json").removesuffix(".json")
    if _SCHEMA_NAME.fullmatch(schema_name) is None:
        raise ValueError(f"invalid Cucumber Messages schema name: {name!r}")

    resource = (
        files("pytest_cuke")
        .joinpath("model")
        .joinpath("message_schemas")
        .joinpath(f"{schema_name}.schema.json")
    )
    try:
        schema_text = resource.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"pytest-cuke does not include the Cucumber Messages schema {schema_name!r}; "
            "reinstall the package or run `cuke sync messages schemas` in a source checkout"
        ) from error

    try:
        schema = json.loads(schema_text)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"bundled Cucumber Messages schema {schema_name!r} is not valid JSON") from error
    if not isinstance(schema, dict):
        raise ValueError(f"bundled Cucumber Messages schema {schema_name!r} must contain a JSON object")
    return cast("dict[str, object]", schema)


__all__ = ["load_message_schema"]
