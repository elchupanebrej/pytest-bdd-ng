from __future__ import annotations

import os
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
from warnings import catch_warnings, simplefilter

import pytest
from ordered_set import OrderedSet
from pathvalidate import is_valid_filepath

from pytest_cuke import cucumber_json, generation, given, hooks, steps, then, when
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
from pytest_cuke.cucumber_pretty import selected_pretty_formatter_requests
from pytest_cuke.cucumber_progress import add_options as add_cucumber_progress_options
from pytest_cuke.cucumber_progress import progress_formatter_selected, selected_progress_formatter_requests
from pytest_cuke.cucumber_progress_bar import add_options as add_cucumber_progress_bar_options
from pytest_cuke.cucumber_progress_bar import progress_bar_formatter_selected, selected_progress_bar_formatter_requests
from pytest_cuke.cucumber_snippets import add_options as add_cucumber_snippets_options
from pytest_cuke.cucumber_snippets import selected_snippets_formatter_requests
from pytest_cuke.cucumber_summary import add_options as add_cucumber_summary_options
from pytest_cuke.cucumber_summary import selected_summary_formatter_requests
from pytest_cuke.cucumber_usage import add_options as add_cucumber_usage_options
from pytest_cuke.cucumber_usage import selected_usage_formatter_requests
from pytest_cuke.cucumber_usage_json import add_options as add_cucumber_usage_json_options
from pytest_cuke.cucumber_usage_json import selected_usage_json_formatter_requests
from pytest_cuke.debug_mcp.options import DebugMcpOptions
from pytest_cuke.debug_mcp.options import add_options as add_debug_mcp_options
from pytest_cuke.debug_mcp.plugin import DebugMcpPlugin
from pytest_cuke.feature_sources import resolve_feature_sources
from pytest_cuke.message_plugin import MessagePlugin, MessageSessionFinishHookAdapter, message_session_finish_hook
from pytest_cuke.mimetypes import Mimetype
from pytest_cuke.model import Feature, Scenario
from pytest_cuke.model.execution_steps import execution_steps
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.native_allure import NativeAllureDependencyError, NativeAllureReporter
from pytest_cuke.native_allure_worker import NativeAllureWorkerBridge, NativeAllureWorkerDependencyError
from pytest_cuke.npm_resource import check_npm, check_npm_package
from pytest_cuke.parser import GherkinParser, MarkdownGherkinParser, clear_parser_registrations
from pytest_cuke.parsers import cucumber_expression
from pytest_cuke.reporting import ScenarioReporterPlugin
from pytest_cuke.runner import ScenarioRunner
from pytest_cuke.scenario import FeaturePathType, scenarios
from pytest_cuke.scenario import add_options as scenario_add_options
from pytest_cuke.scenario_locator import FileScenarioLocator, UrlScenarioLocator
from pytest_cuke.steps.matcher import Matcher
from pytest_cuke.steps.registry import Registry, StepRegistryProtocol
from pytest_cuke.steps.status_policy import configured_tolerant_status, configured_wip_status
from pytest_cuke.test_groups.plugin import TestGroupPlugin, add_test_group_ini
from pytest_cuke.utils import IdGenerator, compose, getitemdefault, is_url_parsable, setdefaultattr
from pytest_cuke.warning_types import PytestBDDStepDefinitionWarning

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Generator, Iterable, Sequence

    from _pytest.nodes import Collector
    from cucumber_messages import PickleStep as Step

    from pytest_cuke.formatter_api import FormatterRequest
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


def pytest_cuke_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Return built-in live formatter requests selected through pytest-cuke options."""
    return (
        *selected_pretty_formatter_requests(config),
        *selected_progress_formatter_requests(config),
        *selected_progress_bar_formatter_requests(config),
        *selected_snippets_formatter_requests(config),
        *selected_summary_formatter_requests(config),
        *selected_usage_formatter_requests(config),
        *selected_usage_json_formatter_requests(config),
    )


@pytest.hookimpl(tryfirst=True)
def pytest_report_teststatus(report: Any, config: Config) -> tuple[str, str, str] | None:
    """Keep pytest's per-test glyphs from overwriting selected Cucumber progress output."""
    if (
        not (progress_formatter_selected(config) or progress_bar_formatter_selected(config))
        or report.when != "call"
        or not hasattr(report, "scenario")
    ):
        return None
    return report.outcome, "", ""


@given("trace")
@when("trace")
@then("trace")
def trace() -> None:
    """Enter pytest's pdb trace."""
    pytest.set_trace()


__registry = Registry()


@pytest.fixture
def pytestbdd_step_runner(pytestconfig: Config | None = None) -> ScenarioRunner:
    """Fixture containing scenario step runner."""
    if pytestconfig is None:
        return ScenarioRunner()
    runner = pytestconfig.pluginmanager.get_plugin("pytest_cuke_scenario_runner")
    return cast("ScenarioRunner", runner) if runner is not None else ScenarioRunner()


@pytest.fixture(scope="session")
def run_context(pytestconfig: Config) -> RunContext:
    """Return the authoritative mutable runtime root for this pytest session."""
    return RunContext.from_config(pytestconfig)


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
            request=request,
            run=RunContext.from_config(request.config),
            attachment=attachment,
            media_type=media_type,
            file_name=file_name,
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
        "--cuke-mock-run",
        action="store_true",
        dest="cuke_mock_run",
        default=None,
        help="validate scenario step bindings without running BDD hooks or step bodies",
    )
    feature_group.addoption(
        "--cuke-allow-empty-scenarios",
        action="store_true",
        dest="cuke_allow_empty_scenarios",
        default=None,
        help="skip explicit scenarios when none of their steps match a step definition",
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
    tolerant_group = parser.getgroup("cuke", "Tolerant steps")
    tolerant_group.addoption(
        "--cuke-tolerant-status",
        action="store",
        dest="cuke_tolerant_status",
        metavar="STATUS",
        choices=("failed", "ignored"),
        default=None,
        help="status of a failed @tolerant step; overrides cuke_tolerant_status",
    )
    wip_group = parser.getgroup("cuke", "Not-implemented steps")
    wip_group.addoption(
        "--cuke-wip-status",
        action="store",
        dest="cuke_wip_status",
        metavar="STATUS",
        choices=("passed", "skipped", "failed"),
        default=None,
        help="status of a @not_implemented step; overrides cuke_wip_status",
    )
    steps.add_options(parser)
    scenario_add_options(parser)
    cucumber_json.add_options(parser)
    generation.add_options(parser)
    add_cucumber_progress_options(parser)
    add_cucumber_progress_bar_options(parser)
    add_cucumber_snippets_options(parser)
    MessagePlugin.add_options(parser)
    add_cucumber_summary_options(parser)
    add_cucumber_usage_options(parser)
    add_cucumber_usage_json_options(parser)
    add_debug_mcp_options(parser)


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
    parser.addini(
        "cuke_mock_run",
        "Validate scenario step bindings without running BDD hooks or step bodies.",
        default=False,
        type="bool",
    )
    parser.addini(
        "cuke_allow_empty_scenarios",
        "Skip explicitly bound non-empty scenarios when none of their steps match a step definition.",
        default=False,
        type="bool",
    )
    parser.addini(
        "cuke_tolerant_status",
        "Status policy for ordinary exceptions in @tolerant steps: failed or ignored.",
        default="failed",
        type="string",
    )
    parser.addini(
        "cuke_wip_status",
        "Status policy for @not_implemented steps: passed, skipped, or failed.",
        default="failed",
        type="string",
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


def _allow_empty_scenarios_enabled(config: Config) -> bool:
    option = getattr(getattr(config, "option", None), "cuke_allow_empty_scenarios", None)
    if option is not None:
        return bool(option)
    return bool(config.getini("cuke_allow_empty_scenarios"))


def _generation_mode_enabled(config: Config) -> bool:
    for name in ("cuke_generate_missing", "cuke_generate"):
        option = getattr(getattr(config, "option", None), name, None)
        if option is None:
            try:
                option = config.getini(name)
            except (KeyError, ValueError):
                option = False
        if option:
            return True
    return False


def _item_fixture_definitions(item: Any, name: str) -> Any:
    """Return applicable fixture definitions without setting up the fixture."""
    fixture_manager = getattr(getattr(item, "session", None), "_fixturemanager", None)
    get_fixture_definitions = getattr(fixture_manager, "getfixturedefs", None)
    if get_fixture_definitions is None:
        return ()
    return get_fixture_definitions(name, item) or ()


def _collection_step_registry(item: Any) -> Registry:
    """Build the item's applicable step registry without setting up fixtures."""

    registries: list[Registry] = []
    module_registry = getattr(getattr(item, "module", None), "__pytest_cuke_step_registry__", None)
    if isinstance(module_registry, Registry):
        registries.append(module_registry)

    for fixture_definition in reversed(_item_fixture_definitions(item, "step_registry")):
        fixture_function = getattr(fixture_definition, "func", None)
        registry = getattr(fixture_function, "__pytest_cuke_step_registry__", None)
        if isinstance(registry, Registry) and all(registry is not existing for existing in registries):
            registries.append(registry)

    definitions: OrderedSet[Any] = OrderedSet()
    for registry in registries:
        definitions.update(registry.registry)
    return Registry(definitions=definitions)


class _CollectionMatchRequest:
    """Expose only safe collection-time dependencies to the ordinary matcher."""

    def __init__(self, config: Config, *, custom_parameter_registry: bool) -> None:
        self.config = config
        self.custom_parameter_registry = custom_parameter_registry

    def getfixturevalue(self, name: str) -> Any:
        if name == "parameter_type_registry":
            return cucumber_expression.parameter_type_registry
        raise LookupError(f"fixture {name!r} is unavailable during scenario collection validation")


def _has_custom_parameter_type_registry(item: Any) -> bool:
    return any(
        getattr(fixture_definition, "func", None) is not parameter_type_registry
        for fixture_definition in _item_fixture_definitions(item, "parameter_type_registry")
    )


def _scenario_has_matching_step(config: Config, item: Any, feature: Feature, scenario: Scenario) -> bool:
    """Return whether any executable step matches, without running a user fixture."""
    steps_to_check = execution_steps(feature, scenario)
    if not steps_to_check:
        return False

    matcher = Matcher(config)
    request = _CollectionMatchRequest(
        config,
        custom_parameter_registry=_has_custom_parameter_type_registry(item),
    )
    registry = _collection_step_registry(item)
    previous_step = None
    for step in steps_to_check:
        try:
            with catch_warnings():
                simplefilter("ignore", PytestBDDStepDefinitionWarning)
                matcher(request, feature, scenario, step, previous_step, registry)  # type: ignore[arg-type]  # The collection request deliberately exposes no fixture setup API.
        except Matcher.MatchNotFoundError:
            if request.custom_parameter_registry and matcher._undefined_parameter_types:
                # Unknown custom expression types require their fixture value, which collection must not execute.
                return True
            pass
        except LookupError:
            # A parser may need a user fixture. Leave that case to normal runtime matching.
            return True
        else:
            return True
        finally:
            previous_step = step
    return False


def _bound_scenario(item: Any) -> tuple[Feature, Scenario] | None:
    if item.get_closest_marker("pytest_cuke_scenario") is None:
        return None
    callspec = getattr(item, "callspec", None)
    params = getattr(callspec, "params", {})
    feature, scenario = params.get("feature"), params.get("scenario")
    if isinstance(feature, Feature) and isinstance(scenario, Scenario):
        return feature, scenario
    return None


def _is_feature_autoload_item(item: Any) -> bool:
    parent = getattr(item, "parent", None)
    while parent is not None:
        if isinstance(parent, FeatureFileCollector):
            return True
        parent = getattr(parent, "parent", None)
    return False


def _zero_match_scenario_detail(feature: Feature, scenario: Scenario) -> str:
    source = feature.filename or feature.uri or feature.rel_filename or "<unknown feature>"
    location = f"{source}:{scenario.line}" if scenario.line else source
    heading = f"{scenario.keyword} {scenario.name}"
    details = [f"  {source}:{step.line}: {step.keyword}{step.name}" for step in execution_steps(feature, scenario)]
    return "\n".join((f"{location}: {heading} has no matching step definitions.", "  Scenario steps:", *details))


def _zero_match_skip_reason(feature: Feature, scenario: Scenario) -> str:
    source = feature.filename or feature.uri or feature.rel_filename or "<unknown feature>"
    location = f"{source}:{scenario.line}" if scenario.line else source
    return (
        f"No scenario step matched a step definition at {location} ({scenario.keyword} {scenario.name}); "
        "allowed by --cuke-allow-empty-scenarios."
    )


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config: Config, items: list[Any]) -> Generator[Any, Any, None]:
    """Validate explicit bindings after pytest has applied item selection."""
    outcome = yield
    if outcome.excinfo is not None:
        return

    if (
        _generation_mode_enabled(config)
        or bool(getattr(config.option, "keyword", None))
        or bool(getattr(config.option, "markexpr", None))
        or ScenarioRunner._mock_run_enabled(config)
    ):
        return

    allow_empty = _allow_empty_scenarios_enabled(config)
    invalid: list[str] = []
    for item in items:
        if _is_feature_autoload_item(item):
            continue
        binding = _bound_scenario(item)
        if binding is None:
            continue
        feature, scenario = binding
        if not execution_steps(feature, scenario) or _scenario_has_matching_step(config, item, feature, scenario):
            continue
        if allow_empty:
            item.add_marker(pytest.mark.skip(reason=_zero_match_skip_reason(feature, scenario)))
        else:
            invalid.append(_zero_match_scenario_detail(feature, scenario))

    if invalid:
        raise pytest.UsageError(
            "Explicit scenarios with steps but no matching step definitions were found:\n\n" + "\n\n".join(invalid)
        )


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
    namespace = getattr(config, "known_args_namespace", None)
    if namespace is None:
        namespace = getattr(config, "option", None)
    option = getattr(namespace, "cuke_allure", None)
    if option is not None:
        return option if isinstance(option, str) else None
    ini_value = config.getini("cuke_allure")
    return ini_value if isinstance(ini_value, str) and ini_value else None


def _allure_adapter_output_path(config: Config) -> str | None:
    namespace = getattr(config, "known_args_namespace", None)
    if namespace is None:
        namespace = getattr(config, "option", None)
    option = getattr(namespace, "allure_report_dir", None)
    return option if isinstance(option, str) and option else None


def _same_output_directory(first: str, second: str) -> bool:
    def resolved(path: str) -> Path:
        expanded = os.path.expandvars(os.path.expanduser(path))
        return Path(expanded).resolve()

    first_path = resolved(first)
    second_path = resolved(second)
    try:
        if first_path.exists() and second_path.exists() and os.path.samefile(first_path, second_path):
            return True
    except OSError:
        pass
    return normcase(str(first_path)) == normcase(str(second_path))


def _validate_allure_output_paths(config: Config) -> None:
    native_output = _allure_output_path(config)
    adapter_output = _allure_adapter_output_path(config)
    if (
        native_output is not None
        and adapter_output is not None
        and _same_output_directory(native_output, adapter_output)
    ):
        raise pytest.UsageError(
            "--cuke-allure and --alluredir must use different directories when both reporting modes are enabled"
        )


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config: Config) -> None:
    """Keep saved-stream conversion independent from consumer conftest files."""
    _validate_allure_output_paths(early_config)
    if _allure_messages_input(early_config) is not None:
        early_config.known_args_namespace.noconftest = True
        return
    early_config.pluginmanager.register(
        message_session_finish_hook(),
        name="pytest_cuke_messages_session_finish",
    )


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    """Configure all subplugins."""
    try:
        debug_mcp_options = DebugMcpOptions.from_config(config)
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error

    if _allure_messages_input(config) is not None:
        if _allure_output_path(config) is None:
            raise pytest.UsageError("--cuke-allure-messages-in requires --cuke-allure")
        return

    try:
        configured_tolerant_status(config)
        configured_wip_status(config)
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error

    try:
        resolve_feature_sources(config)
    except ValueError as error:
        raise pytest.UsageError(str(error)) from error

    config.addinivalue_line("markers", "pytest_cuke_scenario: marker to identify pytest_cuke tests")
    config.addinivalue_line("markers", "scenarios: marker to provide scenarios locator")
    config.addinivalue_line("markers", "tolerant_status(value): override the tolerant step status for this scenario")
    config.addinivalue_line("markers", "tolerant-status-ignored: ignore ordinary failures in @tolerant steps")
    config.addinivalue_line("markers", "tolerant-status-failed: report ordinary failures in @tolerant steps")
    config.addinivalue_line("markers", "wip_status(value): override the not-implemented step status for this scenario")
    config.addinivalue_line("markers", "wip-status-passed: mark not-implemented steps as passed without execution")
    config.addinivalue_line("markers", "wip-status-skipped: skip scenarios at not-implemented steps")
    config.addinivalue_line("markers", "wip-status-failed: execute not-implemented steps normally")
    run_context = RunContext.from_config(config)
    cucumber_json.configure(config)
    config.pluginmanager.register(ScenarioReporterPlugin())
    config.pluginmanager.register(ScenarioRunner(), name="pytest_cuke_scenario_runner")
    message_plugin = MessagePlugin(config=config)
    config.pluginmanager.register(message_plugin, name="pytest_cuke_messages")
    allure_output_path = _allure_output_path(config)
    if allure_output_path is not None:
        if isinstance(getattr(config, "workerinput", None), dict):
            try:
                native_allure_worker = NativeAllureWorkerBridge(config)
                native_allure_worker.start()
            except NativeAllureWorkerDependencyError as error:
                raise pytest.UsageError(str(error)) from error
            config.pluginmanager.register(native_allure_worker, name="pytest_cuke_native_allure_worker")
        else:
            try:
                native_allure_reporter = NativeAllureReporter(Path(allure_output_path))
                native_allure_reporter.start()
            except NativeAllureDependencyError as error:
                raise pytest.UsageError(str(error)) from error
            except OSError as error:
                raise pytest.UsageError(f"cannot initialize native Allure reporting: {error}") from error
            config.pluginmanager.register(native_allure_reporter, name="pytest_cuke_native_allure")
    session_finish_hook = config.pluginmanager.get_plugin("pytest_cuke_messages_session_finish")
    if isinstance(session_finish_hook, MessageSessionFinishHookAdapter):
        session_finish_hook.bind(message_plugin)
    else:
        config.pluginmanager.register(
            message_session_finish_hook(message_plugin),
            name="pytest_cuke_messages_session_finish",
        )
    vars(config)["__allure_plugin__"] = (
        None if _allure_output_path(config) is not None else AllurePytestBDD.register_if_allure_accessible(config)
    )
    id_generator = IdGenerator.from_stash(config.stash) if hasattr(config, "stash") else IdGenerator()
    id_generator.set_namespace(run_context.run_id)
    setdefaultattr(config, "pytest_cuke_id_generator", value=id_generator)
    if STRUCT_BDD_INSTALLED:
        config.pluginmanager.register(StructBDDPlugin())
    if config.getini("cuke_test_group_order"):
        config.pluginmanager.register(TestGroupPlugin(config), name="pytest_cuke_test_groups")
    if debug_mcp_options.enabled:
        config.pluginmanager.register(
            DebugMcpPlugin(config, debug_mcp_options),
            name="pytest_cuke_debug_mcp",
        )
    config.pluginmanager.register(
        _SessionFinishOrderingHookAdapter(),
        name="pytest_cuke_session_finish_ordering",
    )


class _SessionFinishOrderingHookAdapter:
    def __init__(self) -> None:
        self._session_started = False

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_sessionstart(self, session: Any) -> Generator[None, Any, Any]:
        """Initialize runtime state, then order finish hooks after session startup completes."""
        CollectionBatchService.for_session(session, session.config)
        RunContext.from_config(session.config).begin_collection()
        yield
        self._session_started = True
        _place_session_finish_adapter(session.config)

    @pytest.hookimpl(optionalhook=True)
    def pytest_plugin_registered(
        self,
        plugin: Any,
        manager: PytestPluginManager,
    ) -> None:
        """Reorder finish hooks when new implementations register after session startup."""
        if not self._session_started or plugin is self:
            return
        session_finish_hook = manager.get_plugin("pytest_cuke_messages_session_finish")
        if plugin is session_finish_hook:
            return
        if not any(hookimpl.plugin is plugin for hookimpl in manager.hook.pytest_sessionfinish.get_hookimpls()):
            return
        config = manager.get_plugin("pytestconfig")
        if isinstance(config, Config):
            _place_session_finish_adapter(config)


def _place_session_finish_adapter(config: Config) -> None:
    """Place the Messages finish wrapper outside conftests and inside xdist's worker wrapper."""
    plugin_manager = config.pluginmanager
    session_finish_hook = plugin_manager.get_plugin("pytest_cuke_messages_session_finish")
    if not isinstance(session_finish_hook, MessageSessionFinishHookAdapter):
        return

    message_plugin = plugin_manager.get_plugin("pytest_cuke_messages")
    if not isinstance(message_plugin, MessagePlugin) or message_plugin.is_disabled:
        return

    plugin_manager.unregister(name="pytest_cuke_messages_session_finish")
    plugin_manager.register(session_finish_hook, name="pytest_cuke_messages_session_finish")

    if not hasattr(config, "workerinput"):
        return

    session_finish = plugin_manager.hook.pytest_sessionfinish
    hookimpls = getattr(session_finish, "_hookimpls", None)
    wrappers = getattr(session_finish, "_wrappers", None)
    nonwrappers = getattr(session_finish, "_nonwrappers", None)
    if isinstance(hookimpls, list):
        ordered_hookimpls = hookimpls
        orderable_impls = hookimpls
    elif isinstance(wrappers, list) and isinstance(nonwrappers, list):
        ordered_hookimpls = [*nonwrappers, *wrappers]
        orderable_impls = wrappers
    else:
        raise pytest.UsageError(
            "pytest-cuke cannot order session-finish reporting in this pytest-xdist worker "
            "with the installed Pluggy version."
        )
    adapter_impl = next((impl for impl in ordered_hookimpls if impl.plugin is session_finish_hook), None)
    worker_impl = next(
        (
            impl
            for impl in ordered_hookimpls
            if impl.hookwrapper
            and type(impl.plugin).__name__ == "WorkerInteractor"
            and impl.function.__name__ == "pytest_sessionfinish"
        ),
        None,
    )
    if (
        adapter_impl is None
        or worker_impl is None
        or adapter_impl not in orderable_impls
        or worker_impl not in orderable_impls
    ):
        error_message = (
            "pytest-cuke cannot find pytest-xdist's worker-finish wrapper while ordering Cucumber Messages reporting."
        )
        raise pytest.UsageError(error_message)

    # Pluggy has no public ordering API for placing a wrapper between xdist and
    # consumer wrappers. Its HookCaller runs wrappers in reverse registration order.
    # Keep workerfinished outside this adapter so workeroutput includes the manifest,
    # while this adapter still wraps external tryfirst finish hooks.
    call_order = list(reversed(orderable_impls))
    call_order.remove(worker_impl)
    call_order.remove(adapter_impl)
    orderable_impls[:] = reversed([worker_impl, adapter_impl, *call_order])


def pytest_collection_finish(session: Any) -> None:
    """Return the runtime root to its explicit inactive state after collection."""
    run_context = RunContext.find_in_config(session.config)
    if run_context is not None:
        run_context.clear_active()


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    """Release the session cache once collection and execution are complete."""
    service = get_batch_service(session.config)
    if service is not None:
        service.close()
    run_context = RunContext.find_in_config(session.config)
    if run_context is not None:
        run_context.clear_active()


@pytest.hookimpl(tryfirst=True)
def pytest_unconfigure(config: Config) -> None:
    service = get_batch_service(config)
    if service is not None:
        service.close()
    run_context = RunContext.find_in_config(config)
    if run_context is not None:
        run_context.clear_active()
    clear_parser_registrations(config)
    formatter_session = config.pluginmanager.get_plugin("pytest_cuke_formatter_session")
    if formatter_session is not None:
        formatter_session.abort()
        config.pluginmanager.unregister(name="pytest_cuke_formatter_session")
    config.pluginmanager.unregister(name="pytest_cuke_messages_session_finish")
    config.pluginmanager.unregister(name="pytest_cuke_messages")
    native_allure_reporter = config.pluginmanager.get_plugin("pytest_cuke_native_allure")
    if native_allure_reporter is not None:
        stop = getattr(native_allure_reporter, "stop", None)
        if callable(stop):
            stop()
        config.pluginmanager.unregister(name="pytest_cuke_native_allure")
    native_allure_worker = config.pluginmanager.get_plugin("pytest_cuke_native_allure_worker")
    if native_allure_worker is not None:
        stop = getattr(native_allure_worker, "stop", None)
        if callable(stop):
            stop()
        config.pluginmanager.unregister(name="pytest_cuke_native_allure_worker")
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
            run_context = RunContext.find_in_config(config)
            if run_context is not None:
                for feature, scenario in feature_scenarios:
                    run_context.bind_feature(feature).register_scenario(scenario)
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


@pytest.hookimpl(trylast=True)
def pytest_cuke_match_step_definition_to_step(request: FixtureRequest, run: RunContext) -> Definition:
    feature = run.require_feature("pytest_cuke_match_step_definition_to_step")
    scenario = run.require_scenario("pytest_cuke_match_step_definition_to_step")
    step = run.require_step("pytest_cuke_match_step_definition_to_step")
    step_registry: Registry = request.getfixturevalue("step_registry")
    step_matcher: Matcher = request.getfixturevalue("step_matcher")

    return step_matcher(request, feature, scenario, step, run.previous_step, step_registry)


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
