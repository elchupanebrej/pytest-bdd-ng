from __future__ import annotations

from contextlib import contextmanager, suppress
from dataclasses import dataclass
from functools import partial
from itertools import zip_longest
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Literal, cast

import pytest
from pytest import hookimpl

from pytest_cuke import exceptions
from pytest_cuke.compatibility.pytest import (
    Config,
    FixtureRequest,
    Item,
    call_fixture_func,
    inject_fixture,
)
from pytest_cuke.model.execution_steps import execution_steps
from pytest_cuke.model.run_access import get_run_context, set_scenario_run
from pytest_cuke.model.scenario_run import ScenarioRun
from pytest_cuke.model.session_run import RunContext
from pytest_cuke.steps.manager import StepDefinitionManager
from pytest_cuke.steps.matcher import Matcher
from pytest_cuke.steps.status_policy import resolve_tolerant_status, resolve_wip_status
from pytest_cuke.utils import DefaultMapping, get_args

if TYPE_CHECKING:
    from collections import deque
    from collections.abc import Callable, Iterator

    from pytest_cuke.model.feature import Feature
    from pytest_cuke.model.scenario import Scenario
    from pytest_cuke.model.step import Step
    from pytest_cuke.steps.definition import Definition


@dataclass(frozen=True, slots=True)
class _IgnoredStepFailure:
    exception: Exception


@dataclass(frozen=True, slots=True)
class _WipPassed:
    pass


class StepRunner:
    """Handles execution of individual steps in a scenario."""

    def match_to_step(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        previous_step: Step | None,
    ) -> Definition:
        __tracebackhide__ = True
        try:
            return cast(
                "Definition",
                request.config.hook.pytest_cuke_match_step_definition_to_step(
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    previous_step=previous_step,
                ),
            )
        except (Matcher.MatchNotFoundError, StepDefinitionManager.Matcher.MatchNotFoundError) as e:
            step_text = getattr(step, "name", getattr(step, "text", str(step)))
            step_kw = getattr(step, "keyword", "").strip()
            step_line = getattr(step, "line", getattr(step, "line_number", 0))
            scen_name = getattr(scenario, "name", "")
            feat_uri = getattr(feature, "uri", "")
            raise exceptions.StepDefinitionNotFoundError(
                f'Step definition is not found: "{step_text}". '
                f'Step keyword: "{step_kw}". '
                f"Line {step_line} "
                f'in scenario "{scen_name}" '
                f'in the feature "{feat_uri}"'
            ) from e

    def inject_step_parameters_as_fixtures(
        self,
        request: FixtureRequest,
        step_params: dict[str, Any] | None = None,
        params_fixtures_mapping: dict[str, str | None] | None = None,
    ) -> None:
        step_params = step_params or {}
        params_fixtures_mapping = (
            DefaultMapping.instantiate_from_collection_or_bool(
                params_fixtures_mapping or {}, warm_up_keys=step_params.keys()
            )
            or {}
        )

        for param, fixture_name in params_fixtures_mapping.items():
            if fixture_name is None or fixture_name is ...:
                continue
            inject_fixture(request, fixture_name, step_params[param])

    def get_step_function_kwargs(
        self, request: FixtureRequest, step: Step, step_definition: Definition, step_params: dict[str, Any]
    ) -> Iterator[tuple[str, Any]]:
        for param in get_args(step_definition.func):
            try:
                yield param, step_params[param]
            except KeyError:
                try:
                    yield param, {"step": step}[param]
                except KeyError:
                    yield param, request.getfixturevalue(param)

    def inject_target_fixtures(self, request: FixtureRequest, step_definition: Definition, step_result: Any) -> None:
        target_fixtures = getattr(step_definition, "target_fixtures", [])
        if len(target_fixtures) == 1:
            injectable_fixtures = [(target_fixtures[0], step_result)]
        elif step_result is not None and len(target_fixtures) != 0:
            injectable_fixtures = list(zip(target_fixtures, step_result, strict=False))
        else:
            injectable_fixtures = list(zip_longest(target_fixtures, []))

        for target_fixture, return_value in injectable_fixtures:
            inject_fixture(request, target_fixture, return_value)

    def run_step(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        previous_step: Step | None,
    ) -> Any:
        __tracebackhide__ = True
        hook_kwargs: dict[str, Any] = {
            "request": request,
            "feature": feature,
            "scenario": scenario,
            "step": step,
            "previous_step": previous_step,
            "step_func": None,
            "step_func_args": {},
        }

        try:
            step_definition = self.match_to_step(request, feature, scenario, step, previous_step)
        except exceptions.StepDefinitionNotFoundError as exception:
            hook_kwargs["exception"] = exception
            request.config.hook.pytest_cuke_step_func_lookup_error(**hook_kwargs)
            raise
        else:
            hook_kwargs["step_func"] = step_definition.func
            hook_kwargs["step_definition"] = step_definition

        if step_definition.not_implemented:
            wip_status = resolve_wip_status(request.config, request.node, scenario)
            if wip_status == "passed":
                request.config.hook.pytest_cuke_step_bypassed(
                    **hook_kwargs,
                    status=wip_status,
                    message=None,
                )
                return _WipPassed()
            if wip_status == "skipped":
                message = "Not-implemented step skipped by policy."
                request.config.hook.pytest_cuke_step_bypassed(
                    **hook_kwargs,
                    status=wip_status,
                    message=message,
                )
                pytest.skip(message)

        step_error_hook_called = False
        try:
            request.config.hook.pytest_cuke_before_step(**hook_kwargs)
            step_params = (
                step_definition.get_parameters(request, step) if hasattr(step_definition, "get_parameters") else {}
            )
            self.inject_step_parameters_as_fixtures(
                request,
                step_params=step_params,
                params_fixtures_mapping=getattr(step_definition, "params_fixtures_mapping", None),
            )

            step_function_kwargs = dict(self.get_step_function_kwargs(request, step, step_definition, step_params))
            hook_kwargs["step_func_args"] = step_function_kwargs

            request.config.hook.pytest_cuke_before_step_call(**hook_kwargs)

            step_caller = request.config.hook.pytest_cuke_get_step_caller(**hook_kwargs)
            if step_caller is None:
                step_caller = partial(
                    call_fixture_func,
                    fixturefunc=step_definition.func,
                    request=request,
                    kwargs=step_function_kwargs,
                )

            try:
                step_result = step_caller()
            except Exception as exception:
                outcome_exceptions = (pytest.skip.Exception, pytest.fail.Exception, pytest.xfail.Exception)
                if (
                    step_definition.tolerant
                    and not isinstance(exception, outcome_exceptions)
                    and resolve_tolerant_status(request.config, request.node, scenario) == "ignored"
                ):
                    hook_kwargs["exception"] = exception
                    hook_kwargs["tolerated"] = True
                    step_error_hook_called = True
                    request.config.hook.pytest_cuke_step_error(**hook_kwargs)
                    return _IgnoredStepFailure(exception)
                raise

            self.inject_target_fixtures(request, step_definition, step_result)
            request.config.hook.pytest_cuke_after_step(**hook_kwargs)
            return step_result
        except (Exception, pytest.skip.Exception, pytest.fail.Exception, pytest.xfail.Exception) as exception:
            if not step_error_hook_called:
                hook_kwargs["exception"] = exception
                request.config.hook.pytest_cuke_step_error(**hook_kwargs)
            raise


class ScenarioRunner:
    def __init__(self, step_runner: StepRunner | None = None) -> None:
        self.step_runner = step_runner or StepRunner()

    @staticmethod
    def _is_scenario_item(item: Item) -> bool:
        return "pytest_cuke_scenario" in list(map(attrgetter("name"), item.iter_markers()))

    @staticmethod
    def _scenario_params(item: Item) -> tuple[Feature, Scenario] | None:
        callspec = getattr(item, "callspec", None)
        params = getattr(callspec, "params", {}) if callspec is not None else {}
        feature = params.get("feature")
        scenario = params.get("scenario")
        if feature is None or scenario is None:
            return None
        if not hasattr(feature, "uri") or not hasattr(scenario, "steps"):
            return None
        return cast("Feature", feature), cast("Scenario", scenario)

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_setup(self, item: Item) -> Iterator[None]:
        """Bind scenario state before fixture setup and retain setup failures for reporting."""
        if self._is_scenario_item(item):
            scenario_params = self._scenario_params(item)
            if scenario_params is not None:
                feature, scenario = scenario_params
                context = get_run_context(item.config) or RunContext.from_config(item.config)
                attempt = getattr(item, "execution_count", 0)
                scenario_run = context.start_scenario(
                    nodeid=item.nodeid,
                    feature=feature,
                    scenario=scenario,
                    attempt=attempt,
                )
                set_scenario_run(item, scenario_run)

        outcome = yield
        exc_info = getattr(outcome, "excinfo", None)
        if exc_info is not None:
            run_context = get_run_context(item.config)
            if run_context is not None:
                exception = cast("BaseException", exc_info[1])
                status = self._status_for_exception(exception)
                run_context.record_setup_error(status="failed" if status == "passed" else status, exception=exception)

    @hookimpl(tryfirst=True)
    def pytest_runtest_call(self, item: Item) -> None:
        __tracebackhide__ = True
        if self._is_scenario_item(item):
            request = item._request
            feature = request.getfixturevalue("feature")
            scenario = request.getfixturevalue("scenario")
            if feature is None or scenario is None:
                return
            if self._mock_run_enabled(request.config):
                self._verify_mock_run_bindings(item, request, feature, scenario)
                return
            context = get_run_context(request.config) or RunContext.from_config(request.config)
            scenario_run = context.get_scenario_run(item.nodeid)
            if scenario_run is None:
                scenario_run = context.start_scenario(
                    nodeid=item.nodeid,
                    feature=feature,
                    scenario=scenario,
                    attempt=getattr(item, "execution_count", 0),
                )
                set_scenario_run(item, scenario_run)
            context.transition(stage="running", hook_phase="pytest_cuke_before_scenario", status="running")
            error: BaseException | None = None
            try:
                request.config.hook.pytest_cuke_before_scenario(request=request, feature=feature, scenario=scenario)
                context.transition(stage="running", hook_phase="pytest_cuke_run_scenario", status="running")
                request.config.hook.pytest_cuke_run_scenario(request=request, feature=feature, scenario=scenario)
            except BaseException as exception:
                error = exception
                raise
            finally:
                status = self._status_for_exception(error) if error is not None else "passed"
                context.finish_active(status=status, exception=error)
                try:
                    request.config.hook.pytest_cuke_after_scenario(request=request, feature=feature, scenario=scenario)
                except BaseException as after_exception:
                    error = after_exception
                    context.finish_active(status=self._status_for_exception(error), exception=error)
                    raise

            self._refresh_test_function_fixtures(item, request)

    @staticmethod
    def _mock_run_enabled(config: Config) -> bool:
        option = getattr(getattr(config, "option", None), "cuke_mock_run", None)
        if option is not None:
            return bool(option)
        return bool(config.getini("cuke_mock_run"))

    @staticmethod
    def _refresh_test_function_fixtures(item: Item, request: FixtureRequest) -> None:
        """Keep late fixture values available to the ordinary pytest test function."""
        for argname in getattr(item, "fixturenames", []):
            item.funcargs[argname] = request.getfixturevalue(argname)  # type: ignore[attr-defined]  # Pytest populates this private request for late fixture injection.

    def _verify_mock_run_bindings(
        self,
        item: Item,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
    ) -> None:
        """Check every executable scenario step without entering BDD lifecycle hooks."""
        context = get_run_context(request.config) or RunContext.from_config(request.config)
        if context.get_scenario_run(item.nodeid) is None:
            scenario_run = context.start_scenario(
                nodeid=item.nodeid,
                feature=feature,
                scenario=scenario,
                attempt=getattr(item, "execution_count", 0),
            )
            set_scenario_run(item, scenario_run)

        missing: list[exceptions.StepDefinitionNotFoundError] = []
        previous_step: Step | None = None
        try:
            for step in execution_steps(feature, scenario):
                try:
                    self.step_runner.match_to_step(request, feature, scenario, step, previous_step)
                except exceptions.StepDefinitionNotFoundError as error:
                    missing.append(error)
                previous_step = step

            if missing:
                detail = "\n".join(f"- {error}" for error in missing)
                raise exceptions.StepDefinitionNotFoundError(
                    f"Scenario has steps without matching step definitions:\n{detail}"
                )

            self._refresh_test_function_fixtures(item, request)
        except BaseException as error:
            context.finish_active(
                status=self._status_for_exception(error),
                exception=error,
                hook_phase="pytest_runtest_call",
            )
            raise
        context.finish_active(status="passed", hook_phase="pytest_runtest_call")

    @staticmethod
    def _status_for_exception(
        exception: BaseException | None,
    ) -> Literal["passed", "failed", "skipped", "undefined"]:
        if exception is None:
            return "passed"
        if isinstance(exception, exceptions.StepDefinitionNotFoundError):
            return "undefined"
        if isinstance(exception, (pytest.skip.Exception, pytest.xfail.Exception)):
            return "skipped"
        return "failed"

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_teardown(self, item: Item, nextitem: Item | None) -> Iterator[None]:
        """Expose teardown state, retain its error, and always release active item references."""
        context = get_run_context(item.config)
        scenario_run = context.get_scenario_run(item.nodeid) if context is not None else None
        is_active_scenario = (
            scenario_run is not None and context is not None and context.active_scenario_run is scenario_run
        )
        if context is not None and is_active_scenario:
            context.enter_teardown()
        outcome = yield
        try:
            exc_info = getattr(outcome, "excinfo", None)
            if exc_info is not None and context is not None and is_active_scenario:
                context.record_teardown_error(cast("BaseException", exc_info[1]))
        finally:
            if context is not None and is_active_scenario:
                context.clear_active()
            stash = getattr(item, "stash", None)
            if stash is not None:
                with suppress(KeyError):
                    del stash[ScenarioRun.STASH_KEY]

    def pytest_cuke_run_scenario(self, request: FixtureRequest, feature: Feature, scenario: Scenario) -> Any:
        """Execute the scenario steps."""
        __tracebackhide__ = True
        steps: deque[Step] = request.getfixturevalue("steps_left")
        steps.extend(execution_steps(feature, scenario))
        step_dispatcher = request.config.hook.pytest_cuke_get_step_dispatcher(
            request=request, feature=feature, scenario=scenario
        )
        return step_dispatcher(steps)

    @hookimpl(trylast=True)
    def pytest_cuke_get_step_dispatcher(
        self, request: FixtureRequest, feature: Feature, scenario: Scenario
    ) -> Callable[[deque[Step]], None]:
        """Provide default step dispatcher."""
        __tracebackhide__ = True

        def dispatcher(left_steps: deque[Step]) -> None:
            __tracebackhide__ = True
            previous_step = None
            plugin_manager = cast("PluginManager", self.plugin_manager)
            while left_steps:
                step = left_steps.popleft()
                request.config.hook.pytest_cuke_run_step(
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    previous_step=previous_step,
                )
                previous_step = step

        return dispatcher

    @contextmanager
    def extended_step_context(self, feature: Feature, scenario: Scenario, step: Step) -> Iterator[None]:
        """Compatibility context manager; immutable parsed models need no transient mutation."""
        yield

    def pytest_cuke_run_step(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        previous_step: Step | None,
    ) -> Any:
        __tracebackhide__ = True
        context = get_run_context(request.config)
        scenario_run = context.active_scenario_run if context is not None else None
        if context is None or scenario_run is None or scenario_run.nodeid != getattr(request.node, "nodeid", ""):
            return self.step_runner.run_step(request, feature, scenario, step, previous_step)
        step_run = context.start_step(step)
        try:
            result = self.step_runner.run_step(request, feature, scenario, step, previous_step)
        except BaseException as exception:
            if isinstance(exception, exceptions.StepDefinitionNotFoundError):
                status: Literal["failed", "skipped", "undefined"] = "undefined"
            elif isinstance(exception, (pytest.skip.Exception, pytest.xfail.Exception)):
                status = "skipped"
            else:
                status = "failed"
            context.finish_step(
                step_run,
                status=status,
                exception=exception,
                failure_reason=type(exception).__name__,
            )
            raise
        if isinstance(result, _IgnoredStepFailure):
            context.finish_step(
                step_run,
                status="failed",
                exception=result.exception,
                failure_reason=type(result.exception).__name__,
            )
            return None
        if isinstance(result, _WipPassed):
            context.finish_step(step_run, status="passed")
            return None
        context.finish_step(step_run, result=result)
        return result

    def pytest_cuke_before_step_call(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        step_func: Any,
        step_func_args: dict[str, Any],
        step_definition: Definition,
    ) -> None:
        context = get_run_context(request.config)
        if context is not None and context.active_scenario_run is not None:
            context.transition(stage="step", hook_phase="pytest_cuke_step_call", status="running")

    def pytest_cuke_step_func_lookup_error(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Any,
        step: Step,
        exception: Exception,
    ) -> None:
        context = get_run_context(request.config)
        if context is not None and context.active_scenario_run is not None:
            context.transition(
                stage="step",
                hook_phase="pytest_cuke_step_func_lookup_error",
                status="undefined",
            )

    def pytest_cuke_step_error(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        step_func: Any,
        step_func_args: dict[str, Any],
        exception: BaseException,
        step_definition: Definition,
    ) -> None:
        context = get_run_context(request.config)
        if context is not None and context.active_scenario_run is not None:
            context.transition(stage="step", hook_phase="pytest_cuke_step_error", status="failed")

    def pytest_cuke_after_step(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        step_func: Any,
        step_func_args: dict[str, Any],
        step_definition: Definition,
    ) -> None:
        context = get_run_context(request.config)
        if context is not None and context.active_scenario_run is not None:
            context.transition(stage="step", hook_phase="pytest_cuke_after_step", status="running")

    @hookimpl(trylast=True)
    def pytest_cuke_get_step_caller(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        step_func: Any,
        step_func_args: dict[str, Any],
        step_definition: Definition,
    ) -> Callable[[], Any]:
        return partial(call_fixture_func, fixturefunc=step_definition.func, request=request, kwargs=step_func_args)
