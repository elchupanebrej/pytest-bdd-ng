from collections.abc import Collection, Sequence
from contextlib import suppress
from functools import partial
from itertools import starmap
from operator import contains, methodcaller
from pathlib import Path
from types import ModuleType
from typing import Optional, Union
from unittest.mock import patch

import pytest

from messages import Pickle  # type:ignore[attr-defined, import-untyped]
from pytest_bdd.collector import FeatureFileModule as FeatureFileCollector
from pytest_bdd.collector import Module as ModuleCollector
from pytest_bdd.compatibility.pytest import (
    PYTEST7,
    Collector,
    Config,
    Mark,
    MarkDecorator,
    Metafunc,
)
from pytest_bdd.feature_locator import ScenarioLocatorBuilder
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model import Feature
from pytest_bdd.parser import GherkinParser, MarkdownGherkinParser
from pytest_bdd.plugin.scenario_test_collector.const import PYTEST_BDD_MARK, FeatureAutoLoad
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.util.npm_gherkin_checker import is_npm_gherkin_installed
from pytest_bdd.util.toolz_extra import chain_map


def _pytest_collect_file(parent: Collector, file_path=None):
    if not ScenarioTestCollector.is_enabled(parent.session.config):
        return None

    file_path = Path(file_path)
    config = parent.config
    hook = parent.config.hook

    if hook.pytest_bdd_is_collectible(config=config, path=Path(file_path)):
        return FeatureFileCollector.build(parent=parent, file_path=file_path)
    return None


def _pytest_pycollect_makemodule():
    with patch("_pytest.python.Module", new=ModuleCollector):
        yield


def _build_scenario_param(feature: Feature, pickle: Pickle, feature_data: str, config: Config):
    marks = []
    for tag in feature._get_pickle_tag_names(pickle):
        tag_marks = config.hook.pytest_bdd_convert_tag_to_marks(feature=feature, scenario=pickle, tag=tag)
        if tag_marks is not None:
            marks.extend(tag_marks)
    return pytest.param(
        feature,
        pickle,
        feature_data,
        id=f"{feature.uri}-{feature.name}-{pickle.name}{feature.build_pickle_table_rows_breadcrumb(pickle)}",
        marks=marks,
    )


class _ModernTestCollector:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_pycollect_makemodule(
        self,
        parent,  # noqa: ARG002 hookimpl
        module_path,  # noqa: ARG002 hookimpl
    ):
        yield from _pytest_pycollect_makemodule()

    @pytest.hookimpl
    def pytest_collect_file(self, parent: Collector, file_path):
        return _pytest_collect_file(parent=parent, file_path=file_path)


class _LegacyTestCollector:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_pycollect_makemodule(  # type:ignore[misc]
        self,
        path,  # noqa: ARG002 hookimpl
        parent,  # noqa: ARG002 hookimpl
    ):
        yield from _pytest_pycollect_makemodule()

    @pytest.hookimpl
    def pytest_collect_file(self, parent: Collector, path):  # type: ignore[misc]
        return _pytest_collect_file(parent=parent, file_path=path)


BaseCollector: type = _ModernTestCollector if PYTEST7 else _LegacyTestCollector


class ScenarioTestCollector(BaseCollector):
    @pytest.hookimpl(tryfirst=True)
    def pytest_plugin_registered(
        self,
        plugin,
        manager,  # noqa: ARG002 hookimpl
    ):
        if hasattr(plugin, "__file__") and isinstance(plugin, (type, ModuleType)):
            StepDefinitionManager.Registry.inject_registry_fixture_and_register_steps(plugin)

    @pytest.hookimpl
    def pytest_generate_tests(self, metafunc: Metafunc):
        config = metafunc.config

        # build marker locators
        marks: Sequence[Mark] = metafunc.definition.own_markers
        mark_names = [mark.name for mark in marks]
        if PYTEST_BDD_MARK in mark_names:
            scenario_marks = filter(lambda mark: mark.name == "scenarios", marks)
            locators = ScenarioLocatorBuilder(scenario_marks, config=config).build_locators()
            feature_scenario_feature_source = chain_map(methodcaller("resolve", config), locators)

            metafunc.parametrize(
                "feature, scenario, feature_source",
                starmap(
                    partial(_build_scenario_param, config=config),
                    feature_scenario_feature_source,
                ),
            )

    @pytest.hookimpl(trylast=True)
    def pytest_bdd_convert_tag_to_marks(
        self,
        feature,  # noqa: ARG002 hookimpl
        scenario,  # noqa: ARG002 hookimpl
        tag,
    ) -> Optional[Collection[Union[Mark, MarkDecorator]]]:
        return [getattr(pytest.mark, tag)]

    @pytest.hookimpl
    def pytest_bdd_match_step_definition_to_step(
        self, request, feature, scenario, step, previous_step
    ) -> StepDefinitionManager.Definition:
        step_registry: StepDefinitionManager.Registry = request.getfixturevalue("step_registry")
        step_matcher: StepDefinitionManager.Matcher = request.getfixturevalue("step_matcher")

        return step_matcher(request, feature, scenario, step, previous_step, step_registry)

    @pytest.hookimpl
    def pytest_bdd_get_mimetype(
        self,
        config: Config,  # noqa: ARG002 hookimpl
        path: Path,
    ):
        # TODO use mimetypes module
        if str(path).endswith(".gherkin") or str(path).endswith(".feature"):
            return Mimetype.gherkin_plain.value
        if (str(path).endswith(".gherkin.md") or str(path).endswith(".feature.md")) and is_npm_gherkin_installed:
            return Mimetype.markdown.value
        return None

    @pytest.hookimpl
    def pytest_bdd_get_parser(
        self,
        config: Config,  # noqa: ARG002 hookimpl
        mimetype: str,
    ):
        with suppress(KeyError, ValueError):
            return {
                Mimetype.gherkin_plain: GherkinParser,
                Mimetype.markdown: MarkdownGherkinParser,
            }.get(Mimetype(mimetype))

    @pytest.hookimpl
    def pytest_bdd_is_collectible(
        self,
        config: Config,  # noqa: ARG002 hookimpl
        path: Path,
    ):
        # TODO add more extensions
        if any(
            map(
                partial(contains, {".gherkin", ".feature", ".url", ".desktop", ".webloc"}),
                path.suffixes,
            )
        ):
            return True
        return None

    @staticmethod
    def is_enabled(config: Config):
        is_enabled = config.getoption(str(FeatureAutoLoad.Cli.DISABLE_OPTION))
        if is_enabled is None:
            is_enabled = not config.getini(str(FeatureAutoLoad.Ini.DISABLE_OPTION))
        return is_enabled
