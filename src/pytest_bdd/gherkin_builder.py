from __future__ import annotations

from typing import Any

from pytest_bdd.model import (
    Background,
    DataTable,
    DocString,
    Examples,
    Feature,
    Rule,
    Scenario,
    Step,
    StepType,
    TableCell,
    TableRow,
    Tag,
)

_KEYWORD_TYPE_TO_STEP_TYPE = {
    "Context": StepType.context,
    "Action": StepType.action,
    "Outcome": StepType.outcome,
    "Unknown": StepType.unknown,
}

_KEYWORD_TO_STEP_TYPE = {
    "given": StepType.context,
    "when": StepType.action,
    "then": StepType.outcome,
}


def _build_tags(tag_dicts: list[dict[str, Any]] | None) -> tuple[Tag, ...]:
    return tuple(
        Tag(
            name=t["name"],
            line=t.get("location", {}).get("line", 0),
            id=t.get("id"),
        )
        for t in (tag_dicts or [])
    )


def _build_table_row(row_dict: dict[str, Any]) -> TableRow:
    cells = tuple(
        TableCell(
            value=c.get("value", ""),
            line=c.get("location", {}).get("line", 0),
            id=c.get("id"),
        )
        for c in row_dict.get("cells", [])
    )
    return TableRow(
        cells=cells,
        line=row_dict.get("location", {}).get("line", 0),
        id=row_dict.get("id"),
    )


def _build_step(step_dict: dict[str, Any], step_type: StepType) -> Step:
    doc_string = None
    ds = step_dict.get("docString")
    if ds:
        doc_string = DocString(
            content=ds.get("content", ""),
            media_type=ds.get("mediaType"),
            line=ds.get("location", {}).get("line", 0),
            id=ds.get("id"),
        )
    data_table = None
    dt = step_dict.get("dataTable")
    if dt:
        rows = tuple(_build_table_row(r) for r in dt.get("rows", []))
        data_table = DataTable(
            rows=rows,
            line=dt.get("location", {}).get("line", 0),
            id=dt.get("id"),
        )
    return Step(
        name=step_dict.get("text", ""),
        keyword=step_dict.get("keyword", "").strip(),
        line=step_dict.get("location", {}).get("line", 0),
        id=step_dict.get("id"),
        type=step_type,
        doc_string=doc_string,
        data_table=data_table,
    )


def _resolve_step_type(step_dict: dict[str, Any], previous: StepType) -> StepType:
    keyword_type = str(step_dict.get("keywordType") or "")
    if keyword_type == "Conjunction":
        return previous
    if keyword_type:
        return _KEYWORD_TYPE_TO_STEP_TYPE.get(keyword_type, StepType.unknown)
    # The markdown token matcher does not emit keywordType: derive it from the keyword itself.
    prefix = str(step_dict.get("keyword") or "").strip().lower()
    if prefix in _KEYWORD_TO_STEP_TYPE:
        return _KEYWORD_TO_STEP_TYPE[prefix]
    if prefix in ("and", "but", "*"):
        return previous
    return StepType.unknown


def _build_steps(step_dicts: list[dict[str, Any]], previous: StepType) -> tuple[tuple[Step, ...], StepType]:
    steps: list[Step] = []
    for step_dict in step_dicts:
        previous = _resolve_step_type(step_dict, previous)
        steps.append(_build_step(step_dict, previous))
    return tuple(steps), previous


def _trailing_step_type(background: Background | None) -> StepType:
    if background is not None and background.steps and isinstance(background.steps[-1].type, StepType):
        return background.steps[-1].type
    return StepType.unknown


def _build_background(bg_dict: dict[str, Any]) -> Background:
    steps, _ = _build_steps(bg_dict.get("steps", []), StepType.unknown)
    return Background(
        name=bg_dict.get("name", ""),
        keyword=bg_dict.get("keyword", "Background"),
        description=bg_dict.get("description", ""),
        line=bg_dict.get("location", {}).get("line", 0),
        id=bg_dict.get("id"),
        steps=steps,
    )


def _merge_backgrounds(parent: Background | None, background: Background | None) -> Background | None:
    """Merge a parent (feature) background with a child (rule) background.

    Cucumber semantics run the feature background first, then the rule background
    (see gherkin/python/gherkin/pickles/compiler.py).
    """
    if parent is None or background is None:
        return background or parent
    return Background(
        name=background.name,
        keyword=background.keyword,
        description=background.description,
        line=background.line,
        id=background.id,
        steps=parent.steps + background.steps,
    )


def _build_examples(ex_dict: dict[str, Any]) -> Examples:
    header = None
    th = ex_dict.get("tableHeader")
    if th:
        header = _build_table_row(th)
    rows = tuple(_build_table_row(r) for r in ex_dict.get("tableBody", []))
    return Examples(
        name=ex_dict.get("name", ""),
        keyword=ex_dict.get("keyword", "Examples"),
        description=ex_dict.get("description", ""),
        line=ex_dict.get("location", {}).get("line", 0),
        id=ex_dict.get("id"),
        tags=_build_tags(ex_dict.get("tags")),
        header=header,
        rows=rows,
    )


def _build_scenario(
    sc_dict: dict[str, Any],
    background: Background | None = None,
    parent_tags: tuple[Tag, ...] = (),
) -> Scenario:
    steps, _ = _build_steps(sc_dict.get("steps", []), _trailing_step_type(background))
    examples = tuple(_build_examples(e) for e in sc_dict.get("examples", []))
    return Scenario(
        name=sc_dict.get("name", ""),
        keyword=sc_dict.get("keyword", "Scenario"),
        description=(sc_dict.get("description") or "").strip(),
        line=sc_dict.get("location", {}).get("line", 0),
        id=sc_dict.get("id"),
        tags=parent_tags + _build_tags(sc_dict.get("tags")),
        steps=steps,
        examples=examples,
        background=background,
    )


def _build_rule(rule_dict: dict[str, Any], parent_background: Background | None = None) -> Rule:
    rule_background = None
    rule_scenarios = []
    rule_tags = _build_tags(rule_dict.get("tags"))
    for child in rule_dict.get("children", []):
        if "background" in child:
            rule_background = _build_background(child["background"])
        elif "scenario" in child:
            rule_scenarios.append(
                _build_scenario(
                    child["scenario"],
                    background=_merge_backgrounds(parent_background, rule_background),
                    parent_tags=rule_tags,
                )
            )
    return Rule(
        name=rule_dict.get("name", ""),
        keyword=rule_dict.get("keyword", "Rule"),
        description=(rule_dict.get("description") or "").strip(),
        line=rule_dict.get("location", {}).get("line", 0),
        id=rule_dict.get("id"),
        tags=rule_tags,
        background=rule_background,
        scenarios=tuple(rule_scenarios),
    )


def build_feature_from_dict(raw_dict: dict[str, Any], uri: str = "", filename: str | None = None) -> Feature:
    feature_dict = raw_dict.get("feature", {})
    background = None
    scenarios: list[Scenario] = []
    rules: list[Rule] = []
    for child in feature_dict.get("children", []):
        if "background" in child:
            background = _build_background(child["background"])
        elif "scenario" in child:
            scenarios.append(_build_scenario(child["scenario"], background=background))
        elif "rule" in child:
            rules.append(_build_rule(child["rule"], parent_background=background))

    return Feature(
        name=feature_dict.get("name", ""),
        line=feature_dict.get("location", {}).get("line", 0),
        tags=_build_tags(feature_dict.get("tags")),
        description=(feature_dict.get("description") or "").strip(),
        background=background,
        scenarios=tuple(scenarios),
        rules=tuple(rules),
        uri=uri,
        filename=filename,
        id=feature_dict.get("id"),
        keyword=feature_dict.get("keyword", "Feature"),
        language=feature_dict.get("language", "en"),
    )


__all__ = ["build_feature_from_dict"]
