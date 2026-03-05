from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    Location,
    Pickle,
    PickleStep,
    Scenario,
    Step,
    TableRow,
)

from pytest_bdd.util.toolz_extra import deepattrgetter

if TYPE_CHECKING:
    from collections.abc import Mapping


def get_linked_ast_nodes(registry: Mapping[str, Any], obj: Any) -> list[Any]:
    items = [
        *filter(
            lambda _: _ != "",
            ((obj.ast_node_id,) if hasattr(obj, "ast_node_id") else ()),
        ),
        *filter(lambda _: _ != "", getattr(obj, "ast_node_ids", ())),
    ]
    linked_nodes: list[Any] = []
    for ast_node_id in items:
        try:
            linked_node = registry[ast_node_id]
        except KeyError:
            continue
        linked_nodes.append(linked_node)
    return linked_nodes


def get_pickle_ast_table_rows(registry: Mapping[str, Any], pickle: Pickle) -> list[TableRow]:
    return list(filter(lambda node: type(node) is TableRow, get_linked_ast_nodes(registry, pickle)))


def build_pickle_table_rows_breadcrumb(registry: Mapping[str, Any], pickle: Pickle) -> str:
    table_rows_lines = ",".join(
        (
            f"line: {deepattrgetter('location.line', default=-1)(row)[0]}"
            for row in get_pickle_ast_table_rows(registry, pickle)
        ),
    )
    return f"[table_rows:[{table_rows_lines}]]" if table_rows_lines else ""


def get_pickle_ast_scenario(registry: Mapping[str, Any], pickle: Pickle) -> Scenario | None:
    return cast(
        Scenario | None,
        next(
            filter(
                lambda node: type(node) is Scenario,
                get_linked_ast_nodes(registry, pickle),
            ),
            None,
        ),
    )


def get_pickle_line_number(registry: Mapping[str, Any], pickle: Pickle) -> int:
    scenario = get_pickle_ast_scenario(registry, pickle)
    if scenario is None:
        return -1
    location = scenario.location
    return cast(Location, location).line if location is not None else -1


def get_pickle_step_model_step(registry: Mapping[str, Any], pickle_step: PickleStep) -> Step | None:
    return cast(
        Step,
        next(
            filter(
                lambda node: type(node) is Step,
                get_linked_ast_nodes(registry, pickle_step),
            ),
            None,
        ),
    )


def get_step_keyword(registry: Mapping[str, Any], step: PickleStep) -> str | None:
    model_step = get_pickle_step_model_step(registry, step)
    if model_step is not None:
        keyword = getattr(model_step, "keyword", None)
        if isinstance(keyword, str):
            return keyword.strip()
    return None


def get_step_prefix(registry: Mapping[str, Any], step: PickleStep) -> str | None:
    keyword = get_step_keyword(registry, step)
    if keyword is not None:
        return keyword.lower()
    return None


def get_step_line_number(registry: Mapping[str, Any], step: PickleStep) -> int | None:
    model_step = get_pickle_step_model_step(registry, step)
    if model_step is not None:
        return model_step.location.line if model_step.location is not None else -1
    return None


def get_step_doc_string(registry: Mapping[str, Any], step: PickleStep) -> Any:
    return getattr(get_pickle_step_model_step(registry, step), "doc_string", None)


def get_step_data_table(registry: Mapping[str, Any], step: PickleStep) -> Any:
    return getattr(get_pickle_step_model_step(registry, step), "data_table", None)
