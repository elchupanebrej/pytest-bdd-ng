from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ElementType(Enum):
    background = "background"
    scenario = "scenario"


class Argument(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    value: Optional[str] = None
    offset: Optional[float] = None


class Status(Enum):
    passed = "passed"
    failed = "failed"
    skipped = "skipped"
    undefined = "undefined"
    pending = "pending"
    unknown = "unknown"


class DocString(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    line: Optional[float] = None
    value: Optional[str] = None
    content_type: Optional[str] = None


class DataTableRow(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    cells: list[str]


class Tag(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    name: str
    line: Optional[float] = None


class Match(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    location: Optional[str] = None
    arguments: Optional[list["Argument"]] = None


class Result(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    duration: Optional[float] = None
    status: "Status"
    error_message: Optional[str] = None


class Step(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    keyword: Optional[str] = None
    line: Optional[float] = None
    match: Optional["Match"] = None
    name: Optional[str] = None
    result: Optional["Result"] = None
    doc_string: Optional["DocString"] = None
    rows: Optional[list["DataTableRow"]] = None


class Hook(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    match: Optional["Match"] = None
    result: "Result"


class Element(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    start_timestamp: Optional[str] = None
    line: Optional[float] = None
    id: Optional[str] = None
    type: Optional["ElementType"] = None
    keyword: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    before: Optional[list["Hook"]] = None
    steps: Optional[list["Step"]] = None
    after: Optional[list["Hook"]] = None
    tags: Optional[list["Tag"]] = None


class Feature(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    uri: Optional[str] = None
    id: Optional[str] = None
    line: Optional[float] = None
    keyword: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    elements: Optional[list["Element"]] = None
    tags: Optional[list["Tag"]] = None


class CucumberJson(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    implementation: Optional[str] = None
    features: Optional[list["Feature"]] = None
