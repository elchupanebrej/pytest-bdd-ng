"""Provide plugin helpers."""

import mimetypes
from collections.abc import Collection, Iterator, Sequence
from contextlib import suppress
from functools import partial
from itertools import starmap
from operator import contains
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast
from unittest.mock import patch

import pytest
from attrs import define
from cucumber_messages import GherkinDocument, Pickle, Source  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.collector import FeatureFileModule as FeatureFileCollector
from pytest_bdd.collector import Module as ModuleCollector
from pytest_bdd.compatibility.pytest import (
    Collector,
    Config,
    FixtureRequest,
    Mark,
    MarkDecorator,
    Metafunc,
)
from pytest_bdd.feature_locator import ScenarioLocatorBuilder
from pytest_bdd.mimetype import Mimetype, gherkin_suffixes, link_suffixes
from pytest_bdd.model.scenario_run import Run
from pytest_bdd.parser import GherkinParser, MarkdownGherkinParser, ParserProtocol
from pytest_bdd.plugin.pickle_runner.run_access import (
    require_feature_object,
    require_pickle_object,
    require_step_object,
    resolve_previous_step_object,
)
from pytest_bdd.plugin.scenario_test_collector.const import PYTEST_BDD_MARK, FeatureAutoLoad
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.util.toolz_extra import chain_map


def _pytest_collect_file(parent: Collector, file_path: Path | str | None = None) -> Collector | None:
    if not ScenarioTestCollector.is_enabled(parent.session.config):
        return None
    if file_path is None:
        return None

    file_path = Path(file_path)
    config = parent.config
    hook = parent.config.hook

    if hook.pytest_bdd_is_collectible(config=config, path=Path(file_path)):
        return FeatureFileCollector.build(parent=parent, file_path=file_path)
    return None


def _pytest_pycollect_makemodule() -> Iterator[None]:
    with patch("_pytest.python.Module", new=ModuleCollector):
        yield


def _build_pickle_param(
    gherkin_document: GherkinDocument,
    pickle: Pickle,
    feature_source: Source,
    config: Config,
) -> object:
    binding = Run.from_stash(config.stash).ensure_feature_binding(
        gherkin_document=gherkin_document,
        source=feature_source,
    )
    marks = []
    for tag in sorted(tag.name.lstrip("@") for tag in pickle.tags):
        tag_marks = config.hook.pytest_bdd_convert_tag_to_marks(
            gherkin_document=gherkin_document,
            pickle=pickle,
            tag=tag,
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


@define(kw_only=True)
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


class _ScenarioLocatorProtocol(Protocol):
    def resolve(
        self,
        config: Config,
        *,
        observer: _ScenarioCollectionReadObserver,
    ) -> Iterator[tuple[GherkinDocument, Pickle, Source]]: ...


def _iter_resolved_feature_scenarios(
    config: Config,
    locators: Collection[_ScenarioLocatorProtocol],
) -> Iterator[tuple[GherkinDocument, Pickle, Source]]:
    observer = _ScenarioCollectionReadObserver(config=config)
    for locator in locators:
        yield from locator.resolve(config, observer=observer)


class _ModernTestCollector:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_pycollect_makemodule(
        self,
        parent: Collector,  # noqa: ARG002 hookimpl
        module_path: Path,  # noqa: ARG002 hookimpl
    ) -> Iterator[None]:
        yield from _pytest_pycollect_makemodule()

    @pytest.hookimpl
    def pytest_collect_file(self, parent: Collector, file_path: Path) -> Collector | None:
        return _pytest_collect_file(parent=parent, file_path=file_path)


class ScenarioTestCollector(_ModernTestCollector):
    """Collect scenario-backed pytest items from feature files."""

    @pytest.hookimpl(tryfirst=True)
    def pytest_plugin_registered(
        self,
        plugin: object,
        manager: object,  # noqa: ARG002 hookimpl
    ) -> None:
        """Handle plugin registered."""
        if hasattr(plugin, "__file__") and isinstance(plugin, (type, ModuleType)):
            StepDefinitionManager.Registry.inject_registry_fixture_and_register_steps(
                cast(StepDefinitionManager.NamespaceStepRegistryProtocol, plugin),
            )

    @pytest.hookimpl
    def pytest_generate_tests(self, metafunc: Metafunc) -> None:
        """Handle generate tests."""
        config = metafunc.config

        # build marker locators
        marks: Sequence[Mark] = metafunc.definition.own_markers
        mark_names = [mark.name for mark in marks]
        if PYTEST_BDD_MARK in mark_names:
            scenario_marks = filter(lambda mark: mark.name == "scenarios", marks)
            locator_builder = ScenarioLocatorBuilder(config=config)
            locators = cast(
                Collection[_ScenarioLocatorProtocol],
                chain_map(locator_builder.build_for_pytest_mark, scenario_marks),
            )
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
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        tag: str,
    ) -> Collection[Mark | MarkDecorator] | None:
        """
        Convert tag to pytest marks.

        Returns:
            Collection of marks or None.

        """
        _ = gherkin_document
        _ = pickle
        return [getattr(pytest.mark, tag)]

    @pytest.hookimpl
    def pytest_bdd_match_step_definition_to_step(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> StepDefinitionManager.Definition:
        """
        Match step definition to step.

        Returns:
            Step definition.

        """
        gherkin_document = require_feature_object(run, hook_name="pytest_bdd_match_step_definition_to_step")
        pickle = require_pickle_object(run, hook_name="pytest_bdd_match_step_definition_to_step")
        step = require_step_object(run, hook_name="pytest_bdd_match_step_definition_to_step")
        previous_step = resolve_previous_step_object(run)
        step_registry: StepDefinitionManager.Registry = request.getfixturevalue("step_registry")
        step_matcher: StepDefinitionManager.Matcher = request.getfixturevalue("step_matcher")

        return step_matcher(request, gherkin_document, pickle, step, previous_step, step_registry)

    @pytest.hookimpl
    def pytest_bdd_get_mimetype(
        self,
        config: Config,  # noqa: ARG002 hookimpl
        path: Path,
    ) -> Mimetype | None:
        """
        Get mimetype for file path.

        Returns:
            Mimetype or None.

        """
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
    ) -> type[ParserProtocol] | None:
        """
        Get parser for mimetype.

        Returns:
            Parser class or None.

        """
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
    ) -> bool | None:
        """
        Check if path is collectible.

        Returns:
            True if collectible, False or None otherwise.

        """
        return (
            any(
                map(
                    partial(
                        contains,
                        gherkin_suffixes.union(link_suffixes),
                    ),
                    path.suffixes,
                ),
            )
            or None
        )

    @staticmethod
    def is_enabled(config: Config) -> bool:
        """
        Check if collector is enabled.

        Returns:
            True if enabled, False otherwise.

        """
        is_enabled = config.getoption(str(FeatureAutoLoad.Cli.DISABLE_OPTION))
        if is_enabled is None:
            is_enabled = not config.getini(str(FeatureAutoLoad.Ini.DISABLE_OPTION))
        return bool(is_enabled)
