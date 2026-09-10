"""Unit tests for collection-time scenario precondition ordering."""

from types import SimpleNamespace

import pytest

from pytest_bdd.model.scenario_preconditions import (
    MissingScenarioPreconditionError,
    ScenarioPreconditionCycleError,
    order_scenario_items,
    parse_precondition_tag,
)

pytestmark = [pytest.mark.unit]


def _pickle(name: str, *tags: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, tags=[SimpleNamespace(name=tag) for tag in tags])


def _item(uri: str, name: str, *tags: str) -> SimpleNamespace:
    return SimpleNamespace(
        callspec=SimpleNamespace(
            params={
                "pickle": _pickle(name, *tags),
                "feature_source": SimpleNamespace(uri=uri),
            },
        ),
        name=name,
    )


def test_parse_precondition_resolves_relative_feature() -> None:
    declaration = parse_precondition_tag(
        "@precondition(setup.feature: Creates an account)",
        source_uri="/suite/features/main.feature",
        scenario_name="Uses an account",
    )

    assert declaration is not None
    assert declaration.target.name == "Creates an account"
    assert declaration.target.uri.endswith("/suite/features/setup.feature")


def test_order_scenario_items_puts_precondition_first() -> None:
    setup = _item("/suite/features/main.feature", "Creates an account")
    dependent = _item(
        "/suite/features/main.feature",
        "Uses an account",
        "@precondition(Creates an account)",
    )

    assert order_scenario_items([dependent, setup]) == [setup, dependent]


def test_order_scenario_items_reports_missing_target() -> None:
    dependent = _item(
        "/suite/features/main.feature",
        "Uses an account",
        "@precondition(Missing setup)",
    )

    with pytest.raises(MissingScenarioPreconditionError, match="missing precondition"):
        order_scenario_items([dependent])


def test_order_scenario_items_reports_cycles() -> None:
    first = _item("/suite/features/main.feature", "First", "@precondition(Second)")
    second = _item("/suite/features/main.feature", "Second", "@precondition(First)")

    with pytest.raises(ScenarioPreconditionCycleError, match="Circular"):
        order_scenario_items([first, second])
