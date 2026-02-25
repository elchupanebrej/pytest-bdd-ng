from __future__ import annotations

from typing import Any, cast

from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    Location,
    Pickle,
    PickleStep,
    Scenario,
    Step,
    TableRow,
)

from pytest_bdd.util.toolz_extra import deepattrgetter, itemgetter_


def get_linked_ast_nodes(registry: dict[str, Any], obj: Any) -> list[Any]:
    items = [
        *filter(
            lambda _: _ != "",
            ((obj.ast_node_id,) if hasattr(obj, "ast_node_id") else ()),
        ),
        *filter(lambda _: _ != "", getattr(obj, "ast_node_ids", ())),
    ]
    return list(itemgetter_(*items)(registry))


def get_pickle_ast_table_rows(registry: dict[str, Any], pickle: Pickle) -> list[TableRow]:
    return list(filter(lambda node: type(node) is TableRow, get_linked_ast_nodes(registry, pickle)))


def build_pickle_table_rows_breadcrumb(registry: dict[str, Any], pickle: Pickle) -> str:
    table_rows_lines = ",".join(
        (
            f"line: {deepattrgetter('location.line', default=-1)(row)[0]}"
            for row in get_pickle_ast_table_rows(registry, pickle)
        ),
    )
    return f"[table_rows:[{table_rows_lines}]]" if table_rows_lines else ""


def get_pickle_ast_scenario(registry: dict[str, Any], pickle: Pickle) -> Scenario:
    return cast(
        Scenario,
        next(
            filter(
                lambda node: type(node) is Scenario,
                get_linked_ast_nodes(registry, pickle),
            )
        ),
    )


def get_pickle_line_number(registry: dict[str, Any], pickle: Pickle) -> int:
    location = get_pickle_ast_scenario(registry, pickle).location
    return cast(Location, location).line if location is not None else -1


def get_pickle_step_model_step(registry: dict[str, Any], pickle_step: PickleStep) -> Step | None:
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


def get_step_keyword(registry: dict[str, Any], step: PickleStep) -> str | None:
    model_step = get_pickle_step_model_step(registry, step)
    if model_step is not None:
        keyword = getattr(model_step, "keyword", None)
        if isinstance(keyword, str):
            return keyword.strip()
    return None


def get_step_prefix(registry: dict[str, Any], step: PickleStep) -> str | None:
    keyword = get_step_keyword(registry, step)
    if keyword is not None:
        return keyword.lower()
    return None


def get_step_line_number(registry: dict[str, Any], step: PickleStep) -> int | None:
    model_step = get_pickle_step_model_step(registry, step)
    if model_step is not None:
        return model_step.location.line if model_step.location is not None else -1
    return None


def get_step_doc_string(registry: dict[str, Any], step: PickleStep) -> Any:
    return getattr(get_pickle_step_model_step(registry, step), "doc_string", None)


def get_step_data_table(registry: dict[str, Any], step: PickleStep) -> Any:
    return getattr(get_pickle_step_model_step(registry, step), "data_table", None)
