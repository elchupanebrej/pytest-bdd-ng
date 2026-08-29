from __future__ import annotations

from pytest_bdd.model.examples import Examples
from pytest_bdd.model.scenario import Scenario
from pytest_bdd.model.table import TableCell, TableRow
from pytest_bdd.util.matrix import (
    build_parametrization,
    build_scenario_parametrization,
    expand_example_rows,
    expand_examples,
    expand_parameter_matrix,
    substitute_parameters,
)


def test_substitute_parameters() -> None:
    text = "Given <user> has <count> apples in <city>"
    params = {"user": "Alice", "count": 5}
    res = substitute_parameters(text, params)
    assert res == "Given Alice has 5 apples in <city>"


def test_expand_example_rows() -> None:
    headers = ["name", "age"]
    rows = [["Alice", 30], ["Bob", 25]]
    dicts = expand_example_rows(headers, rows)
    assert dicts == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    assert expand_example_rows([], []) == []


def test_expand_parameter_matrix() -> None:
    matrix = {"a": [1, 2], "b": ["x", "y"]}
    combos = expand_parameter_matrix(matrix)
    assert combos == [
        {"a": 1, "b": "x"},
        {"a": 1, "b": "y"},
        {"a": 2, "b": "x"},
        {"a": 2, "b": "y"},
    ]
    assert expand_parameter_matrix({}) == []


def test_expand_examples_model() -> None:
    header = TableRow(cells=(TableCell(value="item"), TableCell(value="qty")))
    row1 = TableRow(cells=(TableCell(value="apple"), TableCell(value="3")))
    row2 = TableRow(cells=(TableCell(value="banana"), TableCell(value="5")))
    examples = Examples(header=header, rows=(row1, row2))

    res = expand_examples([examples])
    assert res == [{"item": "apple", "qty": "3"}, {"item": "banana", "qty": "5"}]


def test_build_parametrization_and_scenario_parametrization() -> None:
    names, values = build_parametrization(["col1", "col2"], [["a", "b"], ["c", "d"]])
    assert names == ("col1", "col2")
    assert values == [("a", "b"), ("c", "d")]

    header = TableRow(cells=(TableCell(value="col1"), TableCell(value="col2")))
    row1 = TableRow(cells=(TableCell(value="v1"), TableCell(value="v2")))
    examples = Examples(header=header, rows=(row1,))
    scenario = Scenario(name="Outline Scenario", examples=(examples,))

    s_names, s_values, s_ids = build_scenario_parametrization(scenario)
    assert s_names == ("col1", "col2")
    assert s_values == [("v1", "v2")]
    assert len(s_ids) == 1

    assert build_scenario_parametrization(Scenario(name="No Examples")) == ((), [], [])
