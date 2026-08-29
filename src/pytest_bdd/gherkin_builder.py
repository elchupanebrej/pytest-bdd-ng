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
    TableCell,
    TableRow,
    Tag,
)


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


def _build_step(step_dict: dict[str, Any]) -> Step:
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
        keyword=step_dict.get("keyword", ""),
        line=step_dict.get("location", {}).get("line", 0),
        id=step_dict.get("id"),
        type=step_dict.get("keywordType"),
        doc_string=doc_string,
        data_table=data_table,
    )


def _build_background(bg_dict: dict[str, Any]) -> Background:
    steps = tuple(_build_step(s) for s in bg_dict.get("steps", []))
    return Background(
        name=bg_dict.get("name", ""),
        keyword=bg_dict.get("keyword", "Background"),
        description=bg_dict.get("description", ""),
        line=bg_dict.get("location", {}).get("line", 0),
        id=bg_dict.get("id"),
        steps=steps,
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


def _build_scenario(sc_dict: dict[str, Any], background: Background | None = None) -> Scenario:
    steps = tuple(_build_step(s) for s in sc_dict.get("steps", []))
    examples = tuple(_build_examples(e) for e in sc_dict.get("examples", []))
    return Scenario(
        name=sc_dict.get("name", ""),
        keyword=sc_dict.get("keyword", "Scenario"),
        description=sc_dict.get("description", ""),
        line=sc_dict.get("location", {}).get("line", 0),
        id=sc_dict.get("id"),
        tags=_build_tags(sc_dict.get("tags")),
        steps=steps,
        examples=examples,
        background=background,
    )


def _build_rule(rule_dict: dict[str, Any], parent_background: Background | None = None) -> Rule:
    rule_background = None
    rule_scenarios = []
    for child in rule_dict.get("children", []):
        if "background" in child:
            rule_background = _build_background(child["background"])
        elif "scenario" in child:
            rule_scenarios.append(
                _build_scenario(
                    child["scenario"],
                    background=rule_background or parent_background,
                )
            )
    return Rule(
        name=rule_dict.get("name", ""),
        keyword=rule_dict.get("keyword", "Rule"),
        description=rule_dict.get("description", ""),
        line=rule_dict.get("location", {}).get("line", 0),
        id=rule_dict.get("id"),
        tags=_build_tags(rule_dict.get("tags")),
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
        description=feature_dict.get("description", ""),
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
