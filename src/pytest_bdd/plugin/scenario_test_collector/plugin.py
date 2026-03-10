import mimetypes
from collections.abc import Collection, Sequence
from contextlib import suppress
from dataclasses import dataclass
from functools import partial
from itertools import starmap
from operator import contains
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest
from cucumber_messages import GherkinDocument, Pickle, Source  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.collector import FeatureFileModule as FeatureFileCollector
from pytest_bdd.collector import Module as ModuleCollector
from pytest_bdd.compatibility.pytest import (
    Collector,
    Config,
    Mark,
    MarkDecorator,
    Metafunc,
)
from pytest_bdd.feature_locator import ScenarioLocatorBuilder
from pytest_bdd.mimetype import Mimetype, gherkin_suffixes, link_suffixes
from pytest_bdd.model.scenario_run import Run
from pytest_bdd.parser import GherkinParser, MarkdownGherkinParser
from pytest_bdd.plugin.pickle_runner.run_access import (
    resolve_feature_object,
    resolve_pickle_object,
    resolve_previous_step_object,
    resolve_step_object,
)
from pytest_bdd.plugin.scenario_test_collector.const import PYTEST_BDD_MARK, FeatureAutoLoad
from pytest_bdd.steps import StepDefinitionManager
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


def _build_pickle_param(gherkin_document: GherkinDocument, pickle: Pickle, feature_source: Source, config: Config):
    binding = Run.from_stash(config.stash).ensure_feature_binding(
        gherkin_document=gherkin_document,
        source=feature_source,
    )
    marks = []
    for tag in sorted(tag.name.lstrip("@") for tag in pickle.tags):
        tag_marks = config.hook.pytest_bdd_convert_tag_to_marks(
            gherkin_document=gherkin_document, pickle=pickle, tag=tag
        )
        if tag_marks is not None:
            marks.extend(tag_marks)
    table_rows_breadcrumb = binding.pickle_table_rows_breadcrumb(pickle)
    return pytest.param(
        gherkin_document,
        pickle,
        feature_source,
        id=f"{binding.uri}-{binding.name}-{pickle.name}{table_rows_breadcrumb}",
        marks=marks,
    )


@dataclass(kw_only=True)
class _ScenarioCollectionReadObserver:
    config: Config

    def on_source_loaded(self, gherkin_document: GherkinDocument, source: Source) -> None:
        self.config.hook.pytest_bdd_source_read(
            config=self.config,
            gherkin_document=gherkin_document,
            source=source,
        )

    def on_feature_loaded(self, gherkin_document: GherkinDocument) -> None:
        self.config.hook.pytest_bdd_feature_read(config=self.config, gherkin_document=gherkin_document)

    def on_pickle_loaded(self, gherkin_document: GherkinDocument, pickle: Pickle) -> None:
        self.config.hook.pytest_bdd_pickle_read(
            config=self.config,
            gherkin_document=gherkin_document,
            pickle=pickle,
        )


def _iter_resolved_feature_scenarios(config: Config, locators):
    observer = _ScenarioCollectionReadObserver(config=config)
    for locator in locators:
        yield from locator.resolve(config, observer=observer)


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


class ScenarioTestCollector(_ModernTestCollector):
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
            locator_builder = ScenarioLocatorBuilder(config=config)
            locators = chain_map(locator_builder.build_for_pytest_mark, scenario_marks)
            feature_scenario_feature_source = _iter_resolved_feature_scenarios(config, locators)

            metafunc.parametrize(
                "gherkin_document, pickle, feature_source",
                starmap(
                    partial(_build_pickle_param, config=config),
                    feature_scenario_feature_source,
                ),
            )

    @pytest.hookimpl(trylast=True)
    def pytest_bdd_convert_tag_to_marks(
        self,
        gherkin_document,
        pickle,
        tag,
    ) -> Collection[Mark | MarkDecorator] | None:
        _ = gherkin_document
        _ = pickle
        return [getattr(pytest.mark, tag)]

    @pytest.hookimpl
    def pytest_bdd_match_step_definition_to_step(
        self,
        request,
        run,
    ) -> StepDefinitionManager.Definition:
        gherkin_document = resolve_feature_object(run)
        pickle = resolve_pickle_object(run)
        step = resolve_step_object(run)
        previous_step = resolve_previous_step_object(run)
        if gherkin_document is None or pickle is None or step is None:
            msg = "Execution context does not provide required objects for step matching"
            raise RuntimeError(msg)
        step_registry: StepDefinitionManager.Registry = request.getfixturevalue("step_registry")
        step_matcher: StepDefinitionManager.Matcher = request.getfixturevalue("step_matcher")

        return step_matcher(request, gherkin_document, pickle, step, previous_step, step_registry)

    @pytest.hookimpl
    def pytest_bdd_get_mimetype(
        self,
        config: Config,  # noqa: ARG002 hookimpl
        path: Path,
    ):
        mimetype_string, _encoding = mimetypes.guess_type(path)
        if mimetype_string is None:
            return None
        try:
            mimetype = Mimetype(mimetype_string)
        except ValueError:
            return None
        if mimetype is Mimetype.gherkin_plain:
            return mimetype
        if mimetype is Mimetype.markdown and any(map(partial(contains, gherkin_suffixes), path.suffixes)):
            return Mimetype.gherkin_markdown
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
                Mimetype.gherkin_markdown: MarkdownGherkinParser,
            }[Mimetype(mimetype)]
        return None

    @pytest.hookimpl
    def pytest_bdd_is_collectible(
        self,
        config: Config,  # noqa: ARG002 hookimpl
        path: Path,
    ):
        return (
            any(
                map(
                    partial(
                        contains,
                        gherkin_suffixes.union(link_suffixes),
                    ),
                    path.suffixes,
                )
            )
            or None
        )

    @staticmethod
    def is_enabled(config: Config):
        is_enabled = config.getoption(str(FeatureAutoLoad.Cli.DISABLE_OPTION))
        if is_enabled is None:
            is_enabled = not config.getini(str(FeatureAutoLoad.Ini.DISABLE_OPTION))
        return is_enabled
