from collections import deque
from collections.abc import Collection, Sequence
from contextlib import suppress
from functools import partial
from itertools import starmap
from operator import contains, methodcaller
from pathlib import Path
from types import ModuleType
from typing import Deque, Optional, Union
from unittest.mock import patch

import pytest
from _pytest.nodes import Collector

from messages import Pickle  # type:ignore[attr-defined, import-untyped]
from messages import PickleStep as Step  # type:ignore[attr-defined]
from pytest_bdd import feature_locator, given, steps, then, when
from pytest_bdd.collector import FeatureFileModule as FeatureFileCollector
from pytest_bdd.collector import Module as ModuleCollector
from pytest_bdd.compatibility.pytest import (
    PYTEST7,
    Config,
    FixtureRequest,
    Mark,
    MarkDecorator,
    Metafunc,
    PytestPluginManager,
)
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.const import PYTEST_BDD_MARK
from pytest_bdd.feature_locator import ScenarioLocatorBuilder
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.model import Feature
from pytest_bdd.parser import GherkinParser, MarkdownGherkinParser
from pytest_bdd.parsers import cucumber_expression
from pytest_bdd.plugin import cucumber_json, gherkin_terminal_reporter
from pytest_bdd.plugin.allure_logger import AllurePytestBDD
from pytest_bdd.plugin.gherkin_message_reporter import GherkinMessageReporter
from pytest_bdd.plugin.pytest_bdd import feature_autoload
from pytest_bdd.plugin.reporter import ScenarioReporterPlugin
from pytest_bdd.runner import ScenarioRunner
from pytest_bdd.steps import StepHandler
from pytest_bdd.util import code_generation
from pytest_bdd.util.npm_gherkin_checker import is_npm_gherkin_installed
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.toolz_extra import chain_map, setdefaultattr

if STRUCT_BDD_INSTALLED:
    from pytest_bdd.struct_bdd.plugin import StructBDDPlugin

from pytest_bdd.compatibility.pytest import Parser


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hooks."""
    from pytest_bdd.plugin.pytest_bdd.hook import PytestBDDHookSpec

    pluginmanager.add_hookspecs(PytestBDDHookSpec)


@given("trace")
@when("trace")
@then("trace")
def trace() -> None:
    """Enter pytest's pdb trace."""
    pytest.set_trace()


# Defining root step registry
_step_registry = StepHandler.Registry()


@pytest.fixture
def step_registry() -> StepHandler.Registry:
    """Fixture containing registry of all user-defined steps"""
    return _step_registry


step_registry.__pytest_bdd_step_definitions__ = _step_registry  # type: ignore[attr-defined]


@pytest.fixture
def step_matcher(pytestconfig) -> StepHandler.Matcher:
    """Fixture containing matcher to help find step definition for selected step of scenario"""
    return StepHandler.Matcher(pytestconfig)  # type: ignore[call-arg]


@pytest.fixture
def steps_left() -> Deque[Step]:
    """Fixture containing steps which are left to be executed"""
    return deque()


@pytest.fixture
def parameter_type_registry():
    """Fixture parameter type registry for Cucumber expressions"""
    return cucumber_expression.parameter_type_registry


@pytest.fixture
def attach(request: FixtureRequest):
    """Fixture parameter type registry for Cucumber expressions"""

    def add_attachment(attachment, media_type: Optional[str] = None, file_name=None):
        request.config.hook.pytest_bdd_attach(
            request=request,
            attachment=attachment,
            media_type=media_type,
            file_name=file_name,
        )

    return add_attachment


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    feature_locator.add_options(parser)
    steps.add_options(parser)
    feature_autoload.add_options(parser)
    cucumber_json.add_options(parser)
    code_generation.add_options(parser)
    gherkin_terminal_reporter.add_options(parser)
    GherkinMessageReporter.add_options(parser)


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    """Configure all subplugins."""
    config.addinivalue_line("markers", f"{PYTEST_BDD_MARK}: marker to identify pytest_bdd tests")
    config.addinivalue_line("markers", "scenarios: marker to provide scenarios locator")
    cucumber_json.configure(config)
    gherkin_terminal_reporter.configure(config)
    config.pluginmanager.register(ScenarioReporterPlugin())
    config.pluginmanager.register(ScenarioRunner())
    config.pluginmanager.register(GherkinMessageReporter(config=config), name="pytest_bdd_messages")  # type: ignore[call-arg]
    config.__allure_plugin__ = AllurePytestBDD.register_if_allure_accessible(config)  # type: ignore[attr-defined]
    setdefaultattr(config, "pytest_bdd_id_generator", value_factory=IdGenerator)
    if STRUCT_BDD_INSTALLED:
        config.pluginmanager.register(StructBDDPlugin())


@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config: Config) -> None:
    config.pluginmanager.unregister(name="pytest_bdd_messages")
    with suppress(AttributeError):
        config.__allure_plugin__.unregister(config)  # type: ignore[attr-defined]
    cucumber_json.unconfigure(config)


def _pytest_pycollect_makemodule():
    with patch("_pytest.python.Module", new=ModuleCollector):
        yield


if PYTEST7:

    @pytest.hookimpl(hookwrapper=True)
    def pytest_pycollect_makemodule(parent, module_path):
        yield from _pytest_pycollect_makemodule()

else:

    @pytest.hookimpl(hookwrapper=True)
    def pytest_pycollect_makemodule(path, parent):  # type:ignore[misc]
        yield from _pytest_pycollect_makemodule()


@pytest.hookimpl(tryfirst=True)
def pytest_plugin_registered(plugin, manager):
    if hasattr(plugin, "__file__") and isinstance(plugin, (type, ModuleType)):
        StepHandler.Registry.inject_registry_fixture_and_register_steps(plugin)


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


def pytest_generate_tests(metafunc: Metafunc):
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


def pytest_cmdline_main(config: Config) -> Optional[int]:
    return code_generation.cmdline_main(config)


def _pytest_collect_file(parent: Collector, file_path=None):
    if not feature_autoload.is_enabled(parent.session.config):
        return None

    file_path = Path(file_path)
    config = parent.config
    hook = parent.config.hook

    if hook.pytest_bdd_is_collectible(config=config, path=Path(file_path)):
        return FeatureFileCollector.build(parent=parent, file_path=file_path)


if PYTEST7:  # Done intentionally because of API change

    def pytest_collect_file(parent: Collector, file_path):
        return _pytest_collect_file(parent=parent, file_path=file_path)

else:

    def pytest_collect_file(parent: Collector, path):  # type: ignore[misc]
        return _pytest_collect_file(parent=parent, file_path=path)


@pytest.mark.trylast
def pytest_bdd_convert_tag_to_marks(feature, scenario, tag) -> Optional[Collection[Union[Mark, MarkDecorator]]]:
    return [getattr(pytest.mark, tag)]


def pytest_bdd_match_step_definition_to_step(request, feature, scenario, step, previous_step) -> StepHandler.Definition:
    step_registry: StepHandler.Registry = request.getfixturevalue("step_registry")
    step_matcher: StepHandler.Matcher = request.getfixturevalue("step_matcher")

    return step_matcher(request, feature, scenario, step, previous_step, step_registry)


def pytest_bdd_get_mimetype(config: Config, path: Path):
    # TODO use mimetypes module
    if str(path).endswith(".gherkin") or str(path).endswith(".feature"):
        return Mimetype.gherkin_plain.value
    if (str(path).endswith(".gherkin.md") or str(path).endswith(".feature.md")) and is_npm_gherkin_installed:
        return Mimetype.markdown.value


def pytest_bdd_get_parser(config: Config, mimetype: str):
    with suppress(KeyError, ValueError):
        return {
            Mimetype.gherkin_plain: GherkinParser,
            Mimetype.markdown: MarkdownGherkinParser,
        }.get(Mimetype(mimetype))


def pytest_bdd_is_collectible(config: Config, path: Path):
    # TODO add more extensions
    if any(
        map(
            partial(contains, {".gherkin", ".feature", ".url", ".desktop", ".webloc"}),
            path.suffixes,
        )
    ):
        return True
