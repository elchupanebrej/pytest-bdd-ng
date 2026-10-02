from __future__ import annotations

import json
from enum import Enum
from typing import Any, TypeVar, cast

import attrs

from pytest_cuke.model.background import Background
from pytest_cuke.model.doc_string import DocString
from pytest_cuke.model.document import GherkinDocument
from pytest_cuke.model.examples import Example, Examples
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.rule import Rule
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.step import Step, StepType
from pytest_cuke.model.table import DataTable, TableCell, TableRow
from pytest_cuke.model.tag import Tag

T = TypeVar("T", bound=attrs.AttrsInstance)

_SCHEMA_MAPPING: dict[type, dict[str, Any]] = {
    Tag: {},
    DocString: {},
    TableCell: {},
    TableRow: {"cells": TableCell},
    DataTable: {"rows": TableRow},
    Example: {"row": TableRow, "tags": Tag},
    Examples: {"header": TableRow, "rows": TableRow, "tags": Tag},
    Step: {"doc_string": DocString, "data_table": DataTable, "type": StepType},
    Background: {"steps": Step},
    Scenario: {"tags": Tag, "steps": Step, "background": Background, "examples": Examples},
    Rule: {"tags": Tag, "background": Background, "scenarios": Scenario},
    Feature: {"tags": Tag, "background": Background, "scenarios": Scenario, "rules": Rule},
    GherkinDocument: {"feature": Feature},
}


def as_dict(inst: Any) -> Any:
    if not attrs.has(type(inst)):
        if isinstance(inst, dict):
            return {k: as_dict(v) for k, v in inst.items()}
        if isinstance(inst, list | tuple):
            return [as_dict(v) for v in inst]
        if isinstance(inst, Enum):
            return inst.value
        return inst
    return attrs.asdict(
        inst,
        recurse=True,
        value_serializer=lambda _inst, _field, value: value.value if isinstance(value, Enum) else value,
    )


def to_json(inst: Any, **kwargs: Any) -> str:
    return json.dumps(as_dict(inst), **kwargs)


def from_dict(cls: type[T], data: dict[str, Any]) -> T:
    if not isinstance(data, dict):
        return cast("T", data)
    schema = _SCHEMA_MAPPING.get(cls, {})
    kwargs: dict[str, Any] = {}
    field_names = {f.name for f in attrs.fields(cast("type[attrs.AttrsInstance]", cls))}
    for key, val in data.items():
        if key not in field_names:
            continue
        target_type = schema.get(key)
        if target_type is None:
            kwargs[key] = tuple(val) if isinstance(val, list) else val
        elif isinstance(target_type, type) and issubclass(target_type, Enum):
            kwargs[key] = target_type(val) if val is not None else None
        elif isinstance(val, list | tuple):
            kwargs[key] = tuple(from_dict(target_type, item) if isinstance(item, dict) else item for item in val)
        elif isinstance(val, dict):
            kwargs[key] = from_dict(target_type, val)
        else:
            kwargs[key] = val
    return cls(**kwargs)


def from_json(cls: type[T], json_str: str) -> T:
    return from_dict(cls, json.loads(json_str))


__all__ = ["as_dict", "from_dict", "from_json", "to_json"]
