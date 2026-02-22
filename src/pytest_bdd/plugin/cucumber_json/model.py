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
    value: str | None = None
    offset: float | None = None


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
    line: float | None = None
    value: str | None = None
    content_type: str | None = None


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
    line: float | None = None


class Match(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    location: str | None = None
    arguments: list["Argument"] | None = None


class Result(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    duration: float | None = None
    status: "Status"
    error_message: str | None = None


class Step(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    keyword: str | None = None
    line: float | None = None
    match: Optional["Match"] = None
    name: str | None = None
    result: Optional["Result"] = None
    doc_string: Optional["DocString"] = None
    rows: list["DataTableRow"] | None = None


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
    start_timestamp: str | None = None
    line: float | None = None
    id: str | None = None
    type: Optional["ElementType"] = None
    keyword: str | None = None
    name: str | None = None
    description: str | None = None
    before: list["Hook"] | None = None
    steps: list["Step"] | None = None
    after: list["Hook"] | None = None
    tags: list["Tag"] | None = None


class Feature(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    uri: str | None = None
    id: str | None = None
    line: float | None = None
    keyword: str | None = None
    name: str | None = None
    description: str | None = None
    elements: list["Element"] | None = None
    tags: list["Tag"] | None = None


class CucumberJson(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    implementation: str | None = None
    features: list["Feature"] | None = None
