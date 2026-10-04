from __future__ import annotations

from argparse import ArgumentTypeError
from collections import deque
from contextlib import suppress
from functools import lru_cache, partial
from inspect import signature
from itertools import chain
from operator import attrgetter, methodcaller
from os.path import normcase
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import patch

import pytest
from pathvalidate import is_valid_filepath

from pytest_cuke import cucumber_json, generation, gherkin_terminal_reporter, given, hooks, steps, then, when
from pytest_cuke.allure_conversion import AllureConversionError, convert_allure_messages
from pytest_cuke.allure_logging import AllurePytestBDD
from pytest_cuke.batch_collection import CollectionBatchService, get_batch_service
from pytest_cuke.collector import FeatureFileModule as FeatureFileCollector
from pytest_cuke.collector import Module as ModuleCollector
from pytest_cuke.compatibility.pytest import (
    PYTEST7,
    Config,
    FixtureRequest,
    Mark,
    MarkDecorator,
    Metafunc,
    Parser,
    PytestPluginManager,
)
from pytest_cuke.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_cuke.feature_sources import resolve_feature_sources
from pytest_cuke.message_plugin import MessagePlugin
from pytest_cuke.mimetypes import Mimetype
from pytest_cuke.npm_resource import check_npm, check_npm_package
from pytest_cuke.parser import GherkinParser, MarkdownGherkinParser, clear_parser_registrations
from pytest_cuke.parsers import cucumber_expression
from pytest_cuke.reporting import ScenarioReporterPlugin, ScenarioSummaryPlugin, add_summary_options
from pytest_cuke.runner import ScenarioRunner
from pytest_cuke.scenario import FeaturePathType, scenarios
from pytest_cuke.scenario import add_options as scenario_add_options
from pytest_cuke.scenario_locator import FileScenarioLocator, UrlScenarioLocator
from pytest_cuke.steps.matcher import Matcher
from pytest_cuke.steps.registry import Registry, StepRegistryProtocol
from pytest_cuke.test_groups.plugin import TestGroupPlugin, add_test_group_ini
from pytest_cuke.utils import IdGenerator, compose, getitemdefault, is_url_parsable, setdefaultattr

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Generator, Iterable, Sequence

    from _pytest.nodes import Collector
    from cucumber_messages import PickleStep as Step

    from pytest_cuke.model import Feature, Scenario
    from pytest_cuke.model.step import Step
    from pytest_cuke.steps.definition import Definition

if STRUCT_BDD_INSTALLED:
    from pytest_cuke.struct_bdd.plugin import StructBDDPlugin


@lru_cache(maxsize=1)
def _is_npm_gherkin_installed() -> bool:
    return check_npm() and (
        check_npm_package("@cucumber/gherkin", global_install=True) or check_npm_package("@cucumber/gherkin")
    )


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hooks."""
    pluginmanager.add_hookspecs(hooks)


@given("trace")
@when("trace")
@then("trace")
def trace() -> None:
    """Enter pytest's pdb trace."""
    pytest.set_trace()


__registry = Registry()


@pytest.fixture
def pytestbdd_step_runner() -> ScenarioRunner:
    """Fixture containing scenario step runner."""
    return ScenarioRunner()


@pytest.fixture
def pytestbdd_id_generator(pytestconfig: Config) -> IdGenerator:
    """Fixture containing ID generator."""
    if hasattr(pytestconfig, "stash"):
        return IdGenerator.from_stash(pytestconfig.stash)
    return getattr(pytestconfig, "pytest_cuke_id_generator", IdGenerator())


@pytest.fixture
def step_registry() -> Registry:
    """Fixture containing registry of all user-defined steps"""
    return __registry


step_registry.__pytest_cuke_step_registry__ = __registry  # type: ignore[attr-defined]  # The collector reads this dynamic marker from the fixture function.


@pytest.fixture
def step_matcher(pytestconfig: Config) -> Matcher:
    """Fixture containing matcher to help find step definition for selected step of scenario"""
    return Matcher(pytestconfig)


@pytest.fixture
def steps_left() -> deque[Step]:
    """Fixture containing steps which are left to be executed"""
    return deque()


@pytest.fixture
def parameter_type_registry() -> Any:
    """Fixture parameter type registry for Cucumber expressions"""
    return cucumber_expression.parameter_type_registry


@pytest.fixture
def attach(request: FixtureRequest) -> Callable[..., None]:
    """Fixture parameter type registry for Cucumber expressions"""

    def add_attachment(attachment: Any, media_type: str | None = None, file_name: str | None = None) -> None:
        request.config.hook.pytest_cuke_attach(
            request=request, attachment=attachment, media_type=media_type, file_name=file_name
        )

    return add_attachment


def pytest_addoption(parser: Parser) -> None:
    """Add the canonical pytest-cuke configuration and CLI surface."""
    add_bdd_ini(parser)
    feature_group = parser.getgroup("cuke", "Feature collection")
    feature_group.addoption(
        "--cuke-features-dir",
        action="store",
        dest="cuke_features_dir",
        metavar="DIR",
        type=_non_empty_path,
        default=None,
        help=(
            "select the local feature root (cuke_features_dir); precedence is binding, CLI, then ini; "
            "relative to pytest root"
        ),
    )
    feature_group.addoption(
        "--cuke-features-base-url",
        action="store",
        dest="cuke_features_base_url",
        metavar="URL",
        default=None,
        help=(
            "select the URL base for URL-backed bindings (cuke_features_base_url); precedence is binding, CLI, then ini"
        ),
    )
    feature_group.addoption(
        "--cuke-strict",
        action="store_true",
        dest="cuke_strict",
        default=None,
        help="reject empty parsed Feature and Scenario titles during collection",
    )
    feature_group.addoption(
        "--cuke-parser",
        action="store",
        dest="cuke_parser",
        metavar="MODE",
        default=None,
        help="select the Gherkin parser backend: python, auto, or go",
    )
    feature_group.addoption(
        "--cuke-batch-threshold",
        action="store",
        dest="cuke_batch_threshold",
        metavar="COUNT",
        type=_positive_integer,
        default=None,
        help="feature count at which collection switches to spawn-based batch parsing",
    )
    steps.add_options(parser)
    scenario_add_options(parser)
    cucumber_json.add_options(parser)
    generation.add_options(parser)
    gherkin_terminal_reporter.add_options(parser)
    MessagePlugin.add_options(parser)
    add_summary_options(parser)


def add_bdd_ini(parser: Parser) -> None:
    parser.addini("cuke_features_dir", "Base features directory.", default="features", type="string")
    parser.addini("cuke_features_base_url", "Base features URL.", default="", type="string")
    parser.addini("cuke_parser", "Gherkin parser backend: python, auto, or go.", default="auto", type="string")
    parser.addini(
        "cuke_batch_threshold",
        "Feature count at which collection switches to spawn-based batch parsing.",
        default=None,
        type="int",
    )
    parser.addini(
        "cuke_strict", "Reject empty parsed Feature and Scenario titles during collection.", default=False, type="bool"
    )
    add_test_group_ini(parser)


def _non_empty_path(value: str) -> str:
    if not value.strip():
        raise ArgumentTypeError("feature directory must not be empty")
    return value


def _positive_integer(value: str) -> int:
    try:
        threshold = int(value)
    except ValueError as error:
        raise ArgumentTypeError("batch threshold must be a positive integer") from error
    if threshold < 1:
        raise ArgumentTypeError("batch threshold must be a positive integer")
    return threshold


def _allure_messages_input(config: Config) -> str | None:
    namespace = getattr(config, "known_args_namespace", None)
    if namespace is None:
        namespace = getattr(config, "option", None)
    option = getattr(namespace, "cuke_allure_messages_in", None)
    if option is not None:
        return option if isinstance(option, str) else None
    ini_value = config.getini("cuke_allure_messages_in")
    return ini_value if isinstance(ini_value, str) and ini_value else None


def _allure_output_path(config: Config) -> str | None:
    option = getattr(config.option, "cuke_allure", None)
    if option is not None:
        return option if isinstance(option, str) else None
    ini_value = config.getini("cuke_allure")
    return ini_value if isinstance(ini_value, str) and ini_value else None


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config: Config) -> None:
    """Keep saved-stream conversion independent from consumer conftest files."""
    if _allure_messages_input(early_config) is not None:
        early_config.known_args_namespace.noconftest = True


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    """Configure all subplugins."""
    if _allure_messages_input(config) is not None:
        if _allure_output_path(config) is None:
            raise pytest.UsageError("--cuke-allure-messages-in requires --cuke-allure")
        return

    try:
        resolve_feature_sources(config)
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error

    config.addinivalue_line("markers", "pytest_cuke_scenario: marker to identify pytest_cuke tests")
    config.addinivalue_line("markers", "scenarios: marker to provide scenarios locator")
    cucumber_json.configure(config)
    gherkin_terminal_reporter.configure(config)
    config.pluginmanager.register(ScenarioReporterPlugin())
    config.pluginmanager.register(ScenarioRunner())
    config.pluginmanager.register(MessagePlugin(config=config), name="pytest_cuke_messages")
    summary_enabled = config.option.cuke_summary
    if summary_enabled is None:
        summary_enabled = config.getini("cuke_summary")
    if summary_enabled:
        config.pluginmanager.register(ScenarioSummaryPlugin(), name="pytest_cuke_summary")
    setattr(
        config,
        "__allure_plugin__",
        None if _allure_output_path(config) is not None else AllurePytestBDD.register_if_allure_accessible(config),
    )
    if hasattr(config, "stash"):
        IdGenerator.from_stash(config.stash)
    setdefaultattr(config, "pytest_cuke_id_generator", value_factory=IdGenerator)
    if STRUCT_BDD_INSTALLED:
        config.pluginmanager.register(StructBDDPlugin())
    if config.getini("cuke_test_group_order"):
        config.pluginmanager.register(TestGroupPlugin(config), name="pytest_cuke_test_groups")


def pytest_sessionstart(session: Any) -> None:
    """Create the batch cache for the current collection session."""
    CollectionBatchService.for_session(session, session.config)


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """Release the session cache once collection and execution are complete."""
    service = get_batch_service(session.config)
    if service is not None:
        service.close()


@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config: Config) -> None:
    service = get_batch_service(config)
    if service is not None:
        service.close()
    clear_parser_registrations(config)
    config.pluginmanager.unregister(name="pytest_cuke_messages")
    config.pluginmanager.unregister(name="pytest_cuke_summary")
    with suppress(AttributeError):
        config.__allure_plugin__.unregister(config)  # type: ignore[attr-defined]  # Allure is attached dynamically during configuration.
    cucumber_json.unconfigure(config)


def _pytest_pycollect_makemodule() -> Generator[Any, None, None]:
    with patch("_pytest.python.Module", new=ModuleCollector):
        yield


def _pytest_pycollect_makemodule_pytest7(parent: Collector, module_path: Path) -> Generator[Any, None, None]:
    yield from _pytest_pycollect_makemodule()


def _pytest_pycollect_makemodule_legacy(path: Path, parent: Collector) -> Generator[Any, None, None]:
    yield from _pytest_pycollect_makemodule()


pytest_pycollect_makemodule: Any
if PYTEST7:
    pytest_pycollect_makemodule = pytest.hookimpl(hookwrapper=True)(_pytest_pycollect_makemodule_pytest7)
else:
    pytest_pycollect_makemodule = pytest.hookimpl(hookwrapper=True)(_pytest_pycollect_makemodule_legacy)


@pytest.hookimpl(tryfirst=True)
def pytest_plugin_registered(plugin: object, manager: PytestPluginManager) -> None:
    if hasattr(plugin, "__file__") and isinstance(plugin, type | ModuleType):
        Registry.inject_registry_fixture(cast("StepRegistryProtocol", plugin))


def _build_filter(filter_: Any) -> Callable[..., bool] | None:
    if callable(filter_):
        updated_filter = cast("Callable[..., bool]", filter_)
    elif filter_ is None:
        updated_filter = None
    else:
        filter_str = str(filter_)

        def updated_filter(config: Config, feature: Feature, scenario: Scenario) -> bool:
            return scenario.name == filter_str or scenario.name.startswith(f"{filter_str}[")

    return updated_filter


def _build_scenario_locators_from_mark(mark: Mark, config: Config) -> Iterable[Any]:
    raw_mark_arguments = signature(scenarios).bind(*mark.args, **mark.kwargs)
    raw_mark_arguments.apply_defaults()
    mark_arguments = raw_mark_arguments.arguments

    locators_iterables = [mark_arguments["locators"]]

    filter_ = _build_filter(getitemdefault(mark_arguments, "filter_", default=None))

    feature_sources = resolve_feature_sources(
        config,
        features_base_dir=mark.kwargs.get("features_base_dir"),
        features_base_url=mark.kwargs.get("features_base_url"),
    )
    features_base_dir = feature_sources.features_base_dir
    features_base_url = feature_sources.features_base_url

    features_path_type = mark_arguments["features_path_type"]
    if features_path_type is None:
        features_path_type = FeaturePathType.UNDEFINED
    elif isinstance(features_path_type, str):
        features_path_type = FeaturePathType(features_path_type)
    elif isinstance(features_path_type, FeaturePathType):
        pass
    else:
        raise ValueError("Unknown feature path type")

    feature_paths = list(mark_arguments["feature_paths"] or [])

    if features_path_type is FeaturePathType.PATH:
        file_locator_feature_paths = feature_paths
    elif features_path_type is FeaturePathType.UNDEFINED:
        file_locator_feature_paths = [*filter(lambda p: is_valid_filepath(Path(p), platform="auto"), feature_paths)]
    else:
        file_locator_feature_paths = []

    path_locator = FileScenarioLocator(
        feature_paths=file_locator_feature_paths,
        filter_=filter_,
        encoding=mark_arguments["encoding"],
        features_base_dir=features_base_dir,
        mimetype=mark_arguments["features_mimetype"],
        parser_type=mark_arguments["parser_type"],
        parse_args=mark_arguments["parse_args"],
    )

    locators_iterables.append([path_locator])

    if features_path_type is FeaturePathType.URL:
        url_locator_feature_paths = feature_paths
    elif features_path_type is FeaturePathType.UNDEFINED:
        url_locator_feature_paths = [*filter(is_url_parsable, feature_paths)]
    else:
        url_locator_feature_paths = []

    url_locator = UrlScenarioLocator(
        url_paths=url_locator_feature_paths,
        filter_=mark_arguments["filter_"],
        encoding=mark_arguments["encoding"],
        features_base_url=features_base_url,
        mimetype=mark_arguments["features_mimetype"],
        parser_type=mark_arguments["parser_type"],
        parse_args=mark_arguments["parse_args"],
    )

    locators_iterables.append([url_locator])
    return chain(*locators_iterables)


def _build_scenario_param(feature: Feature, scenario: Scenario, config: Config) -> Any:
    marks: list[Mark | MarkDecorator] = []
    feature_tags = getattr(feature, "tag_names", ()) or ()
    scenario_tags = getattr(scenario, "tag_names", ()) or ()
    all_tags = set(feature_tags).union(scenario_tags)
    for tag in all_tags:
        tag_marks = config.hook.pytest_cuke_convert_tag_to_marks(feature=feature, scenario=scenario, tag=tag)
        if tag_marks is not None:
            marks.extend(tag_marks)
    return pytest.param(
        feature,
        scenario,
        id=f"{feature.uri or feature.filename or 'feature'}-{feature.name}-{scenario.name}",
        marks=marks,
    )


def _feature_scenario_identity(feature: Feature, scenario: Scenario) -> tuple[Any, ...] | None:
    """Build a stable identity for duplicate locator results with a known source."""
    if feature.filename:
        source: tuple[str, str] = ("path", normcase(str(Path(feature.filename).resolve())))
    elif feature.uri:
        source = ("uri", feature.uri)
    else:
        return None

    scenario_identity = (
        scenario.id or scenario.name,
        scenario.line,
        tuple((step.keyword, step.name, step.line) for step in scenario.steps),
        scenario.tag_names,
    )
    return (*source, *scenario_identity)


def _deduplicate_feature_scenarios(
    feature_scenarios: Iterable[tuple[Feature, Scenario]],
) -> list[tuple[Feature, Scenario]]:
    """Drop duplicate source/scenario pairs while preserving locator order."""
    seen: set[tuple[Any, ...]] = set()
    unique: list[tuple[Feature, Scenario]] = []
    for feature, scenario in feature_scenarios:
        identity = _feature_scenario_identity(feature, scenario)
        if identity is not None and identity in seen:
            continue
        if identity is not None:
            seen.add(identity)
        unique.append((feature, scenario))
    return unique


chain_map = compose(chain.from_iterable, map)


def pytest_generate_tests(metafunc: Metafunc) -> None:
    config = metafunc.config

    # build marker locators
    marks: Sequence[Mark] = metafunc.definition.own_markers
    mark_names = list(map(attrgetter("name"), marks))
    if "pytest_cuke_scenario" in mark_names:
        scenario_marks = filter(lambda mark: mark.name == "scenarios", marks)
        locators = chain_map(partial(_build_scenario_locators_from_mark, config=config), scenario_marks)
        feature_scenarios = _deduplicate_feature_scenarios(chain_map(methodcaller("resolve", config), locators))

        if not feature_scenarios:
            metafunc.parametrize(
                ("feature", "scenario"),
                [pytest.param(None, None, marks=pytest.mark.skip(reason="No scenarios found"))],
            )
        else:
            metafunc.parametrize(
                ("feature", "scenario"),
                [_build_scenario_param(feat, sc, config=config) for feat, sc in feature_scenarios],
            )


@pytest.hookimpl(tryfirst=True)
def pytest_cmdline_main(config: Config) -> int | None:
    """Convert a saved stream before test collection, or run pytest-cuke's generator."""
    messages_path = _allure_messages_input(config)
    if messages_path is not None:
        output_path = _allure_output_path(config)
        if output_path is None:
            raise pytest.UsageError("--cuke-allure-messages-in requires --cuke-allure")
        try:
            convert_allure_messages(Path(messages_path), Path(output_path))
        except AllureConversionError as error:
            raise pytest.UsageError(f"cannot convert Cucumber Messages input: {error}") from error
        return pytest.ExitCode.OK
    return generation.cmdline_main(config)


def _pytest_collect_file(parent: Collector, file_path: Any = None) -> FeatureFileCollector | None:
    file_path = Path(file_path)
    config = parent.session.config
    is_enabled_feature_autoload = config.getoption("cuke_autoload")
    if is_enabled_feature_autoload is None:
        is_enabled_feature_autoload = config.getini("cuke_autoload")
    if not is_enabled_feature_autoload:
        return None

    feature_root = resolve_feature_sources(config).features_base_dir
    if not feature_root.is_dir():
        raise pytest.UsageError(
            f"Feature root {str(feature_root)!r}, selected by --cuke-features-dir or cuke_features_dir, does not exist."
        )
    try:
        file_path.resolve().relative_to(feature_root.resolve())
    except ValueError:
        return None

    config = parent.config
    hook = parent.config.hook

    if hook.pytest_cuke_is_collectible(config=config, path=Path(file_path)):
        return cast("FeatureFileCollector", FeatureFileCollector.build(parent=parent, file_path=file_path))
    return None


def _pytest_collect_file_pytest7(parent: Collector, file_path: Path) -> FeatureFileCollector | None:
    return _pytest_collect_file(parent=parent, file_path=file_path)


def _pytest_collect_file_legacy(parent: Collector, path: Any) -> FeatureFileCollector | None:
    return _pytest_collect_file(parent=parent, file_path=path)


pytest_collect_file: Any
# The two pytest collector APIs intentionally have version-specific signatures.
pytest_collect_file = _pytest_collect_file_pytest7 if PYTEST7 else _pytest_collect_file_legacy


@pytest.mark.trylast
def pytest_cuke_convert_tag_to_marks(
    feature: Feature, scenario: Scenario, tag: str
) -> Collection[Mark | MarkDecorator] | None:
    tag_clean = tag.lstrip("@")
    return [getattr(pytest.mark, tag_clean)]


def pytest_cuke_match_step_definition_to_step(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, previous_step: Step | None
) -> Definition:
    step_registry: Registry = request.getfixturevalue("step_registry")
    step_matcher: Matcher = request.getfixturevalue("step_matcher")

    return step_matcher(request, feature, scenario, step, previous_step, step_registry)


def pytest_cuke_get_mimetype(config: Config, path: Path) -> str | None:
    name = path.name.casefold()
    if name.endswith((".gherkin", ".feature")):
        return Mimetype.gherkin_plain.value
    if name.endswith((".gherkin.md", ".feature.md")) and _is_npm_gherkin_installed():
        return Mimetype.markdown.value
    return None


def pytest_cuke_get_parser(config: Config, mimetype: str) -> Any:
    return {
        Mimetype.gherkin_plain.value: GherkinParser,
        Mimetype.markdown.value: MarkdownGherkinParser,
    }.get(mimetype)


def pytest_cuke_is_collectible(config: Config, path: Path) -> bool | None:
    suffixes = {".gherkin", ".feature", ".url", ".desktop", ".webloc"}
    if any(suffix.casefold() in suffixes for suffix in path.suffixes):
        return True
    return None
