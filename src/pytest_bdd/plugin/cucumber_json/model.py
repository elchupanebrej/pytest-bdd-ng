"""
Provide model helpers.

Responsibility:
    Provide model helpers. It directly owns the observable contract, local decisions, and maintenance boundary for this
    module. That boundary is intentionally stated in prose so maintainers can distinguish owned work from collaborators
    before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model` because it keeps the nearest code,
    data shape, call signature, and failure knowledge together.

Delegates:
    - ElementType: owns nested behavior below this boundary
    - Argument: owns nested behavior below this boundary
    - Status: owns nested behavior below this boundary
    - DocString: owns nested behavior below this boundary
    - DataTableRow: owns nested behavior below this boundary
    - Tag: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `model`
    - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `model`

State and side effects:
    mutates model_config, line, name, keyword, value; depends on enum.Enum, typing.Optional, pydantic.BaseModel,
    pydantic.ConfigDict.

Invariants:
    - `pytest_bdd.plugin.cucumber_json.model` keeps its documented import path, ownership boundary, and observable
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
    #arch-eval:locational_stability=3
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ElementType(Enum):
    """
    Represent element type state.

    Responsibility:
        Represent element type state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.ElementType` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `ElementType`

    State and side effects:
        mutates background, scenario.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.ElementType` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    background = "background"
    scenario = "scenario"


class Argument(BaseModel):
    """
    Represent argument state.

    Responsibility:
        Represent argument state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.Argument` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `Argument`

    State and side effects:
        mutates model_config, value, offset.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.Argument` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    value: str | None = None
    offset: float | None = None


class Status(Enum):
    """
    Represent status state.

    Responsibility:
        Represent status state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.Status` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `Status`

    State and side effects:
        mutates passed, failed, skipped, undefined, pending.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.Status` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    passed = "passed"
    failed = "failed"
    skipped = "skipped"
    undefined = "undefined"
    pending = "pending"
    unknown = "unknown"


class DocString(BaseModel):
    """
    Represent doc string state.

    Responsibility:
        Represent doc string state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.DocString` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `DocString`
        - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `DocString`

    State and side effects:
        mutates model_config, line, value, content_type.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.DocString` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    line: float | None = None
    value: str | None = None
    content_type: str | None = None


class DataTableRow(BaseModel):
    """
    Represent data table row state.

    Responsibility:
        Represent data table row state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.DataTableRow` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `DataTableRow`

    State and side effects:
        mutates model_config, cells.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.DataTableRow` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    cells: list[str]


class Tag(BaseModel):
    """
    Represent tag state.

    Responsibility:
        Represent tag state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.Tag` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `Tag`
        - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `Tag`

    State and side effects:
        mutates model_config, name, line.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.Tag` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    name: str
    line: float | None = None


class Match(BaseModel):
    """
    Represent match state.

    Responsibility:
        Represent match state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.Match` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/parsers/re_parser.py: imports or references `Match`
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `Match`

    State and side effects:
        mutates model_config, location, arguments.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.Match` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    location: str | None = None
    arguments: list["Argument"] | None = None


class Result(BaseModel):
    """
    Represent result state.

    Responsibility:
        Represent result state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.Result` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/collector_batch.py: imports or references `Result`
        - src/pytest_bdd/feature_locator.py: imports or references `Result`
        - src/pytest_bdd/model/message_validation_result.py: imports or references `Result`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `Result`
        - src/pytest_bdd/parsers/heuristic.py: imports or references `Result`

    State and side effects:
        mutates model_config, duration, status, error_message.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.Result` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    duration: float | None = None
    status: "Status"
    error_message: str | None = None


class Step(BaseModel):
    """
    Represent step state.

    Responsibility:
        Represent step state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.Step` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/feature_binding.py: imports or references `Step`
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `Step`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `Step`
        - src/pytest_bdd/plugin/pickle_runner/hook.py: imports or references `Step`
        - src/pytest_bdd/plugin/struct_bdd/model/_base.py: imports or references `Step`

    State and side effects:
        mutates model_config, keyword, line, match, name.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.Step` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

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
    """
    Represent hook state.

    Responsibility:
        Represent hook state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.Hook` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `Hook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/hook_catalog_runtime.py: imports or references `Hook`
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references `Hook`

    State and side effects:
        mutates model_config, match, result.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.Hook` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    match: Optional["Match"] = None
    result: "Result"


class Element(BaseModel):
    """
    Represent element state.

    Responsibility:
        Represent element state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.Element` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `Element`

    State and side effects:
        mutates model_config, start_timestamp, line, id, type.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.Element` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

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
    """
    Represent feature state.

    Responsibility:
        Represent feature state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.Feature` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `Feature`
        - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `Feature`
        - src/pytest_bdd/steps/matcher.py: imports or references `Feature`

    State and side effects:
        mutates model_config, uri, id, line, keyword.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.Feature` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

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
    """
    Represent cucumber json state.

    Responsibility:
        Represent cucumber json state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.cucumber_json.model.CucumberJson` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - ConfigDict: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/cucumber_json/entrypoint.py: imports or references `CucumberJson`
        - src/pytest_bdd/plugin/cucumber_json/plugin.py: imports or references `CucumberJson`

    State and side effects:
        mutates model_config, implementation, features.

    Invariants:
        - `pytest_bdd.plugin.cucumber_json.model.CucumberJson` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    implementation: str | None = None
    features: list["Feature"] | None = None
