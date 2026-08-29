from __future__ import annotations

import pytest

from pytest_bdd.exceptions import PytestBDDStashLookupError
from pytest_bdd.model.run_access import (
    bind_scenario_run,
    get_execution_context,
    get_scenario_run,
    require_execution_context,
    require_scenario_run,
    set_scenario_run,
)
from pytest_bdd.model.scenario_run import ScenarioRun
from pytest_bdd.model.stash_access import ItemStash, SimpleStash


def test_run_access_with_simple_stash() -> None:
    stash = SimpleStash()
    assert get_scenario_run(stash) is None
    assert get_execution_context(stash) is None

    with pytest.raises(PytestBDDStashLookupError):
        require_scenario_run(stash)

    with pytest.raises(PytestBDDStashLookupError):
        require_execution_context(stash)

    sc_run = ScenarioRun(run_id="run-42")
    sc_run.context.set_param("foo", "bar")

    set_scenario_run(stash, sc_run)
    assert get_scenario_run(stash) is sc_run
    assert require_scenario_run(stash) is sc_run
    assert get_execution_context(stash) is sc_run.context
    assert require_execution_context(stash) is sc_run.context
    assert require_execution_context(stash).get_param("foo") == "bar"


def test_run_access_with_item_and_binding() -> None:
    class DummyItem:
        pass

    item = DummyItem()
    item_stash = ItemStash.from_item(item)
    sc_run = ScenarioRun(run_id="item-run-1")

    bind_scenario_run(item, sc_run)
    assert get_scenario_run(item) is sc_run
    assert get_scenario_run(item_stash) is sc_run
    assert require_execution_context(item) is sc_run.context
