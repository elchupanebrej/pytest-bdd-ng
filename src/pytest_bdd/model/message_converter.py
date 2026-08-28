from __future__ import annotations

from typing import TYPE_CHECKING

import messages
from pytest_bdd.model.message_extension import has_single_payload

if TYPE_CHECKING:
    from pytest_bdd.model.background import Background
    from pytest_bdd.model.doc_string import DocString
    from pytest_bdd.model.feature import Feature
    from pytest_bdd.model.rule import Rule
    from pytest_bdd.model.scenario import Scenario
    from pytest_bdd.model.step import Step
    from pytest_bdd.model.table import DataTable
    from pytest_bdd.model.tag import Tag


def make_location(line: int = 0, column: int | None = None) -> messages.Location:
    return messages.Location(line=line, column=column)


def tag_to_message(tag: Tag, default_id: str = "") -> messages.Tag:
    return messages.Tag(id=tag.id or default_id, name=tag.name, location=make_location(tag.line))


def doc_string_to_message(doc: DocString, default_id: str = "") -> messages.DocString:
    return messages.DocString(
        content=doc.content, delimiter='"""', media_type=doc.media_type, location=make_location(doc.line)
    )


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
    return messages.Scenario(
        id=sc_id,
        name=scenario.name,
        description=scenario.description,
        keyword=scenario.keyword,
        location=make_location(scenario.line),
        tags=tags,
        steps=steps,
        examples=[],
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


def rule_to_message(rule: Rule, default_id: str = "") -> messages.Rule:
    r_id = rule.id or default_id
    tags = [tag_to_message(t, f"{r_id}-tag-{i}") for i, t in enumerate(rule.tags)]
    children: list[messages.RuleChild] = []
    if rule.background:
        children.append(messages.RuleChild(background=background_to_message(rule.background, f"{r_id}-bg")))
    for i, sc in enumerate(rule.scenarios):
        children.append(messages.RuleChild(scenario=scenario_to_message(sc, f"{r_id}-sc-{i}")))
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
    tags = [tag_to_message(t, f"{f_id}-tag-{i}") for i, t in enumerate(feature.tags)]
    children: list[messages.FeatureChild] = []
    if feature.background:
        children.append(messages.FeatureChild(background=background_to_message(feature.background, f"{f_id}-bg")))
    for i, sc in enumerate(feature.scenarios):
        children.append(messages.FeatureChild(scenario=scenario_to_message(sc, f"{f_id}-sc-{i}")))
    for i, rl in enumerate(feature.rules):
        children.append(messages.FeatureChild(rule=rule_to_message(rl, f"{f_id}-rl-{i}")))

    msg_feat = messages.Feature(
        name=feature.name,
        description=feature.description,
        keyword=feature.keyword,
        language=feature.language,
        location=make_location(feature.line),
        tags=tags,
        children=children,
    )
    return messages.GherkinDocument(uri=uri or feature.uri or "", feature=msg_feat, comments=[])


def feature_to_envelope(feature: Feature, uri: str = "") -> messages.Envelope:
    return messages.Envelope(gherkin_document=feature_to_gherkin_document(feature, uri=uri))


def validate_envelope_shape(envelope: messages.Envelope) -> None:
    if not has_single_payload(envelope):
        msg = "Envelope must include exactly one payload field"
        raise TypeError(msg)


__all__ = [
    "background_to_message",
    "data_table_to_message",
    "doc_string_to_message",
    "feature_to_envelope",
    "feature_to_gherkin_document",
    "make_location",
    "rule_to_message",
    "scenario_to_message",
    "step_to_message",
    "tag_to_message",
    "validate_envelope_shape",
]
