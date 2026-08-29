from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from ordered_set import OrderedSet

from pytest_bdd.model.step import Step, StepType
from pytest_bdd.parsers.string_parser import string
from pytest_bdd.plugin import (
    _build_scenario_locators_from_mark,
    pytest_configure,
    pytest_unconfigure,
)
from pytest_bdd.scenario_locator import FileScenarioLocator
from pytest_bdd.steps import Matcher, Registry, given
from pytest_bdd.utils import IdGenerator


def test_seam6_liberal_steps_configuration_contract() -> None:
    config = MagicMock()
    config.option.liberal_steps = True
    config.getini.return_value = False

    @given(string("I do a step"))
    def given_step() -> str:
        return "ok"

    defn = next(iter(given_step.__pytest_bdd_step_definitions__))
    reg = Registry(definitions=OrderedSet([defn]))
    matcher = Matcher(config)

    step_item = Step(name="I do a step", keyword="When", type=StepType.action)
    matched = matcher(None, None, None, step_item, None, reg)
    assert matched.func is given_step


def test_seam6_features_base_dir_configuration_contract() -> None:
    config = MagicMock()
    config.rootpath = Path("/workspace")
    config.getini.return_value = "/custom/features/dir"

    mark = MagicMock()
    mark.args = ("test.feature",)
    mark.kwargs = {}

    locators = list(_build_scenario_locators_from_mark(mark, config))
    file_locators = [loc for loc in locators if isinstance(loc, FileScenarioLocator)]
    assert len(file_locators) == 1
    assert str(file_locators[0].features_base_dir) == "/custom/features/dir"


def test_seam6_plugin_lifecycle_and_stash_contract() -> None:
    config = MagicMock()
    config.stash = {}
    config.pluginmanager = MagicMock()
    config.option.cucumber_json_path = None
    config.option.gherkin_terminal_reporter = None

    pytest_configure(config)

    id_gen = config.stash[IdGenerator.pytest_bdd_id_generator]
    assert isinstance(id_gen, IdGenerator)
    assert id_gen.get_next_id() == "0"

    pytest_unconfigure(config)
