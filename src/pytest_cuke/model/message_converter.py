from __future__ import annotations

import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pytest_cuke.model import message_types as messages
from pytest_cuke.model.execution_steps import execution_steps
from pytest_cuke.model.message_extension import has_single_payload
from pytest_cuke.model.message_types import message_from_dict, message_to_dict

if TYPE_CHECKING:
    from pytest_cuke.exceptions import FeatureConcreteParseError
    from pytest_cuke.model.background import Background
    from pytest_cuke.model.doc_string import DocString
    from pytest_cuke.model.examples import Examples
    from pytest_cuke.model.feature import Feature
    from pytest_cuke.model.rule import Rule
    from pytest_cuke.model.scenario import Scenario
    from pytest_cuke.model.step import Step
    from pytest_cuke.model.table import DataTable, TableRow
    from pytest_cuke.model.tag import Tag


def make_location(line: int = 0, column: int | None = None) -> messages.Location:
    return messages.Location(line=line, column=column)


def make_timestamp(dt_or_seconds: float | int | datetime | None = None) -> messages.Timestamp:
    if dt_or_seconds is None:
        dt_or_seconds = time.time()
    if isinstance(dt_or_seconds, datetime):
        dt_or_seconds = dt_or_seconds.timestamp()
    sec = int(dt_or_seconds)
    nanos = int((dt_or_seconds - sec) * 1e9)
    return messages.Timestamp(seconds=sec, nanos=nanos)


def make_duration(seconds_float: float = 0.0) -> messages.Duration:
    sec = int(seconds_float)
    nanos = int((seconds_float - sec) * 1e9)
    return messages.Duration(seconds=sec, nanos=nanos)


def tag_to_message(tag: Tag, default_id: str = "") -> messages.Tag:
    return messages.Tag(id=tag.id or default_id, name=tag.name, location=make_location(tag.line))


def doc_string_to_message(doc: DocString, default_id: str = "") -> messages.DocString:
    return messages.DocString(
        content=doc.content, delimiter='"""', media_type=doc.media_type, location=make_location(doc.line)
    )


def scenario_message_id(scenario: Scenario, uri: str = "", default_id: str = "") -> str:
    """Return the scenario's AST identity, scoped to its Gherkin document."""
    if scenario.id:
        return scenario.id
    if default_id:
        return default_id
    return f"{uri or 'feature'}#scenario-{scenario.line}-{scenario.name}"


def scenario_pickle_id(scenario: Scenario, uri: str = "", default_id: str = "") -> str:
    """Return an execution identity distinct from document-local AST node IDs."""
    if default_id:
        return default_id
    if uri:
        return f"{uri}#{scenario_message_id(scenario)}"
    return scenario_message_id(scenario)


def data_table_to_message(table: DataTable, default_id: str = "") -> messages.DataTable:
    rows = [
        messages.TableRow(
            id=r.id or f"{default_id}-row-{i}",
            location=make_location(r.line),
            cells=[messages.TableCell(value=c.value, location=make_location(c.line)) for c in r.cells],
        )
        for i, r in enumerate(table.rows)
    ]
    return messages.DataTable(location=make_location(table.line), rows=rows)


def step_to_message(step: Step, default_id: str = "") -> messages.Step:
    st_id = step.id or default_id
    ds = doc_string_to_message(step.doc_string, f"{st_id}-ds") if step.doc_string else None
    dt = data_table_to_message(step.data_table, f"{st_id}-dt") if step.data_table else None
    return messages.Step(
        id=st_id, keyword=step.keyword, text=step.name, location=make_location(step.line), doc_string=ds, data_table=dt
    )


def scenario_to_message(scenario: Scenario, default_id: str = "") -> messages.Scenario:
    sc_id = scenario.id or default_id
    tags = [tag_to_message(t, f"{sc_id}-tag-{i}") for i, t in enumerate(scenario.tags)]
    steps = [step_to_message(s, f"{sc_id}-step-{i}") for i, s in enumerate(scenario.steps)]
    examples = [examples_to_message(item, f"{sc_id}-examples-{i}") for i, item in enumerate(scenario.examples)]
    return messages.Scenario(
        id=sc_id,
        name=scenario.name,
        description=scenario.description,
        keyword=scenario.keyword,
        location=make_location(scenario.line),
        tags=tags,
        steps=steps,
        examples=examples,
    )


def examples_to_message(examples: Examples, default_id: str = "") -> messages.Examples:
    """Convert Examples rows while marking generated external row locations as unspecified."""
    source = examples.external_source

    def row_to_message(row: TableRow, index: int) -> messages.TableRow:
        line = 0 if source else row.line
        cells = [
            messages.TableCell(value=cell.value, location=make_location(0 if source else cell.line))
            for cell in row.cells
        ]
        return messages.TableRow(id=row.id or f"{default_id}-row-{index}", location=make_location(line), cells=cells)

    header = row_to_message(examples.header, 0) if examples.header else None
    rows = [row_to_message(row, i + 1) for i, row in enumerate(examples.rows)]
    description = examples.description
    if source is not None:
        row_map = ", ".join(f"{index}:line {line}" for index, line in enumerate(source.row_lines, start=1))
        provenance = (
            f"External Examples source: {source.path}; section {source.section_index}; "
            f"feature marker line {source.marker_line}; "
            f"header source line {source.header_line}; data rows {row_map}."
        )
        description = "\n".join(part for part in (description, provenance) if part)

    return messages.Examples(
        id=examples.id or default_id,
        tags=[tag_to_message(tag, f"{default_id}-tag-{i}") for i, tag in enumerate(examples.tags)],
        location=make_location(examples.line),
        keyword=examples.keyword,
        name=examples.name,
        description=description,
        table_header=header,
        table_body=rows,
    )


def background_to_message(bg: Background, default_id: str = "") -> messages.Background:
    bg_id = bg.id or default_id
    steps = [step_to_message(s, f"{bg_id}-step-{i}") for i, s in enumerate(bg.steps)]
    return messages.Background(
        id=bg_id,
        name=bg.name,
        description=bg.description,
        keyword=bg.keyword,
        location=make_location(bg.line),
        steps=steps,
    )


def rule_to_message(rule: Rule, default_id: str = "", uri: str = "") -> messages.Rule:
    r_id = rule.id or default_id
    tags = [tag_to_message(t, f"{r_id}-tag-{i}") for i, t in enumerate(rule.tags)]
    children: list[messages.RuleChild] = []
    if rule.background:
        children.append(messages.RuleChild(background=background_to_message(rule.background, f"{r_id}-bg")))
    for sc in rule.scenarios:
        scenario_id = scenario_message_id(sc, uri=uri)
        children.append(messages.RuleChild(scenario=scenario_to_message(sc, scenario_id)))
    return messages.Rule(
        id=r_id,
        name=rule.name,
        description=rule.description,
        keyword=rule.keyword,
        location=make_location(rule.line),
        tags=tags,
        children=children,
    )


def feature_to_gherkin_document(feature: Feature, uri: str = "") -> messages.GherkinDocument:
    f_id = feature.id or "feature-1"
    feature_uri = uri or feature.uri or ""
    tags = [tag_to_message(t, f"{f_id}-tag-{i}") for i, t in enumerate(feature.tags)]
    children: list[messages.FeatureChild] = []
    if feature.background:
        children.append(messages.FeatureChild(background=background_to_message(feature.background, f"{f_id}-bg")))
    for sc in feature.scenarios:
        scenario_id = scenario_message_id(sc, uri=feature_uri)
        children.append(messages.FeatureChild(scenario=scenario_to_message(sc, scenario_id)))
    for i, rl in enumerate(feature.rules):
        children.append(messages.FeatureChild(rule=rule_to_message(rl, f"{f_id}-rl-{i}", uri=feature_uri)))

    comments: list[messages.Comment] = []
    scenarios = [*feature.scenarios, *(scenario for rule in feature.rules for scenario in rule.scenarios)]
    for scenario in scenarios:
        for example in scenario.examples:
            source = example.external_source
            if source is not None:
                row_map = ", ".join(f"{index}:line {line}" for index, line in enumerate(source.row_lines, start=1))
                comments.append(
                    messages.Comment(
                        location=make_location(source.marker_line),
                        text=(
                            f"External Examples source: {source.path}; section {source.section_index}; "
                            f"header source line {source.header_line}; "
                            f"data rows {row_map}."
                        ),
                    )
                )

    msg_feat = messages.Feature(
        name=feature.name,
        description=feature.description,
        keyword=feature.keyword,
        language=feature.language,
        location=make_location(feature.line),
        tags=tags,
        children=children,
    )
    return messages.GherkinDocument(uri=feature_uri, feature=msg_feat, comments=comments)


def feature_to_envelope(feature: Feature, uri: str = "") -> messages.Envelope:
    return messages.Envelope(gherkin_document=feature_to_gherkin_document(feature, uri=uri))


def parse_error_to_envelope(error: FeatureConcreteParseError) -> messages.Envelope:
    """Convert a parser failure to the official Cucumber ParseError payload."""
    if error.line < 1 or not error.source_uri:
        raise ValueError("a Cucumber ParseError requires a positive source line and non-empty URI")
    column = error.column if error.column > 0 else 1
    return messages.Envelope(
        parse_error=messages.ParseError(
            source=messages.SourceReference(
                uri=error.source_uri,
                location=make_location(error.line, column),
            ),
            message=error.parse_message,
        )
    )


def step_to_pickle_step(
    step: Step,
    default_id: str = "",
    *,
    force_generated_id: bool = False,
    ast_node_id: str | None = None,
) -> messages.PickleStep:
    st_id = default_id if force_generated_id else (step.id or default_id)
    arg: messages.PickleStepArgument | None = None
    if step.doc_string:
        arg = messages.PickleStepArgument(
            doc_string=messages.PickleDocString(
                content=step.doc_string.content,
                media_type=step.doc_string.media_type,
            )
        )
    elif step.data_table:
        arg = messages.PickleStepArgument(
            data_table=messages.PickleTable(
                rows=[
                    messages.PickleTableRow(cells=[messages.PickleTableCell(value=c.value) for c in r.cells])
                    for r in step.data_table.rows
                ]
            )
        )
    return messages.PickleStep(
        id=st_id,
        text=step.name,
        ast_node_ids=[step.id or ast_node_id] if step.id or ast_node_id else [],
        argument=arg,
    )


def _execution_step_ast_node_ids(feature: Feature | None, scenario: Scenario, uri: str) -> tuple[str | None, ...]:
    """Match executed steps to the IDs emitted for their Gherkin AST nodes."""
    scenario_id = scenario_message_id(scenario, uri=uri)
    feature_id = feature.id or "feature-1" if feature is not None else "feature-1"
    backgrounds: list[tuple[Background, str]] = []
    seen_background_ids: set[str] = set()

    for background in (feature.background if feature is not None else None, scenario.background):
        if background is None:
            continue
        if any(background is seen for seen, _ in backgrounds):
            continue
        if background.id is not None and background.id in seen_background_ids:
            continue

        background_id = background.id
        if background_id is None and feature is not None and background is feature.background:
            background_id = f"{feature_id}-bg"
        if background_id is None and feature is not None:
            for index, rule in enumerate(feature.rules):
                if rule.background is not background or not any(item is scenario for item in rule.scenarios):
                    continue
                rule_id = rule.id or f"{feature_id}-rl-{index}"
                background_id = f"{rule_id}-bg"
                break
        if background_id is None:
            background_id = f"{scenario_id}-background"

        backgrounds.append((background, background_id))
        if background.id is not None:
            seen_background_ids.add(background.id)

    ast_node_ids = [
        step.id or f"{background_id}-step-{index}"
        for background, background_id in backgrounds
        for index, step in enumerate(background.steps)
    ]
    ast_node_ids.extend(step.id or f"{scenario_id}-step-{index}" for index, step in enumerate(scenario.steps))
    return tuple(ast_node_ids)


def scenario_to_pickle(
    scenario: Scenario,
    uri: str = "",
    default_id: str = "",
    *,
    feature: Feature | None = None,
) -> messages.Pickle:
    sc_id = scenario_pickle_id(scenario, uri=uri, default_id=default_id)
    execution = execution_steps(feature, scenario) if feature is not None else scenario.all_steps
    ast_node_ids = _execution_step_ast_node_ids(feature, scenario, uri)
    steps = [
        step_to_pickle_step(
            step,
            f"{sc_id}-step-{index}",
            force_generated_id=True,
            ast_node_id=ast_node_ids[index] if index < len(ast_node_ids) else None,
        )
        for index, step in enumerate(execution)
    ]
    tags = [messages.PickleTag(name=t.name, ast_node_id=t.id or "") for t in scenario.tags]
    scenario_ast_node_ids = list(scenario.source_ast_node_ids) or [scenario_message_id(scenario, uri=uri)]
    external_row_id = scenario.external_example_source.row_id if scenario.external_example_source else None
    if external_row_id and external_row_id not in scenario_ast_node_ids:
        scenario_ast_node_ids.append(external_row_id)
    return messages.Pickle(
        id=sc_id,
        uri=uri,
        name=scenario.name,
        language="en",
        steps=steps,
        tags=tags,
        ast_node_ids=scenario_ast_node_ids,
    )


def pickle_to_envelope(pickle: messages.Pickle) -> messages.Envelope:
    return messages.Envelope(pickle=pickle)


def scenario_to_test_case(
    scenario: Scenario,
    pickle_id: str | None = None,
    default_id: str = "",
    *,
    feature: Feature | None = None,
) -> messages.TestCase:
    tc_id = scenario_message_id(scenario, default_id=default_id)
    p_id = pickle_id or scenario_message_id(scenario, default_id=default_id)
    test_steps = [
        messages.TestStep(
            id=f"{tc_id}-step-{i}",
            pickle_step_id=f"{p_id}-step-{i}",
        )
        for i, _step in enumerate(execution_steps(feature, scenario) if feature is not None else scenario.all_steps)
    ]
    return messages.TestCase(id=tc_id, pickle_id=p_id, test_steps=test_steps)


def test_case_to_envelope(test_case: messages.TestCase) -> messages.Envelope:
    return messages.Envelope(test_case=test_case)


def make_test_run_started(timestamp: float | int | datetime | None = None) -> messages.Envelope:
    return messages.Envelope(test_run_started=messages.TestRunStarted(timestamp=make_timestamp(timestamp)))


def make_test_run_finished(
    timestamp: float | int | datetime | None = None, success: bool = True, message: str | None = None
) -> messages.Envelope:
    payload = messages.TestRunFinished(timestamp=make_timestamp(timestamp), success=success, message=message)
    return messages.Envelope(test_run_finished=payload)


def make_test_case_started(
    test_case_id: str,
    id: str | None = None,
    attempt: int = 0,
    timestamp: float | int | datetime | None = None,
    worker_id: str | None = None,
) -> messages.Envelope:
    payload = messages.TestCaseStarted(
        id=id or f"tcs-{test_case_id}",
        test_case_id=test_case_id,
        attempt=attempt,
        timestamp=make_timestamp(timestamp),
        worker_id=worker_id,
    )
    return messages.Envelope(test_case_started=payload)


def make_test_case_finished(
    test_case_started_id: str, timestamp: float | int | datetime | None = None, will_be_retried: bool = False
) -> messages.Envelope:
    payload = messages.TestCaseFinished(
        test_case_started_id=test_case_started_id, timestamp=make_timestamp(timestamp), will_be_retried=will_be_retried
    )
    return messages.Envelope(test_case_finished=payload)


def make_test_step_started(
    test_case_started_id: str, test_step_id: str, timestamp: float | int | datetime | None = None
) -> messages.Envelope:
    payload = messages.TestStepStarted(
        test_case_started_id=test_case_started_id, test_step_id=test_step_id, timestamp=make_timestamp(timestamp)
    )
    return messages.Envelope(test_step_started=payload)


def make_test_step_finished(
    test_case_started_id: str,
    test_step_id: str,
    *,
    status: messages.Status | str = messages.Status.passed,
    duration: float = 0.0,
    message: str | None = None,
    timestamp: float | int | datetime | None = None,
) -> messages.Envelope:
    if isinstance(status, str):
        status = messages.Status(status.upper())
    result = messages.TestStepResult(status=status, duration=make_duration(duration), message=message)
    payload = messages.TestStepFinished(
        test_case_started_id=test_case_started_id,
        test_step_id=test_step_id,
        test_step_result=result,
        timestamp=make_timestamp(timestamp),
    )
    return messages.Envelope(test_step_finished=payload)


def envelope_to_dict(message: messages.Envelope) -> dict[str, Any]:
    validate_envelope_shape(message)
    return message_to_dict(message)


def envelope_from_dict(payload: dict[str, Any]) -> messages.Envelope:
    env = message_from_dict(payload, messages.Envelope)
    validate_envelope_shape(env)
    return env


def validate_envelope_shape(envelope: messages.Envelope) -> None:
    if not has_single_payload(envelope):
        msg = "Envelope must include exactly one payload field"
        raise TypeError(msg)


__all__ = [
    "background_to_message",
    "data_table_to_message",
    "doc_string_to_message",
    "envelope_from_dict",
    "envelope_to_dict",
    "examples_to_message",
    "feature_to_envelope",
    "feature_to_gherkin_document",
    "make_duration",
    "make_location",
    "make_test_case_finished",
    "make_test_case_started",
    "make_test_run_finished",
    "make_test_run_started",
    "make_test_step_finished",
    "make_test_step_started",
    "make_timestamp",
    "pickle_to_envelope",
    "rule_to_message",
    "scenario_message_id",
    "scenario_pickle_id",
    "scenario_to_message",
    "scenario_to_pickle",
    "scenario_to_test_case",
    "step_to_message",
    "step_to_pickle_step",
    "tag_to_message",
    "test_case_to_envelope",
    "validate_envelope_shape",
]
