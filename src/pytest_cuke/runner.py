from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from itertools import zip_longest
from operator import attrgetter
from typing import TYPE_CHECKING, Any, cast

from pytest import hookimpl

from pytest_cuke import exceptions
from pytest_cuke.compatibility.pytest import (
    FixtureRequest,
    Item,
    call_fixture_func,
    inject_fixture,
)
from pytest_cuke.steps.manager import StepDefinitionManager
from pytest_cuke.steps.matcher import Matcher
from pytest_cuke.utils import DefaultMapping, get_args

if TYPE_CHECKING:
    from collections import deque
    from collections.abc import Callable, Iterator

    from pytest_cuke.model.feature import Feature
    from pytest_cuke.model.scenario import Scenario
    from pytest_cuke.model.step import Step
    from pytest_cuke.steps.definition import Definition


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

        request.config.hook.pytest_cuke_before_step(**hook_kwargs)

        step_params = (
            step_definition.get_parameters(request, step) if hasattr(step_definition, "get_parameters") else {}
        )
        try:
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

            step_result = step_caller()

            self.inject_target_fixtures(request, step_definition, step_result)
            request.config.hook.pytest_cuke_after_step(**hook_kwargs)
            return step_result
        except Exception as exception:
            hook_kwargs["exception"] = exception
            request.config.hook.pytest_cuke_step_error(**hook_kwargs)
            raise


class ScenarioRunner:
    def __init__(self, step_runner: StepRunner | None = None) -> None:
        self.step_runner = step_runner or StepRunner()
        self.request: FixtureRequest | None = None
        self.feature: Feature | None = None
        self.scenario: Scenario | None = None
        self.plugin_manager: Any = None

    @hookimpl(tryfirst=True)
    def pytest_runtest_call(self, item: Item) -> None:
        __tracebackhide__ = True
        if "pytest_cuke_scenario" in list(map(attrgetter("name"), item.iter_markers())):
            self.request = item._request
            self.feature = self.request.getfixturevalue("feature")
            self.scenario = self.request.getfixturevalue("scenario")
            if self.feature is None or self.scenario is None:
                return
            self.plugin_manager = self.request.config.hook
            self.plugin_manager.pytest_cuke_before_scenario(
                request=self.request, feature=self.feature, scenario=self.scenario
            )
            try:
                self.plugin_manager.pytest_cuke_run_scenario(
                    request=self.request,
                    feature=self.feature,
                    scenario=self.scenario,
                )
            finally:
                self.plugin_manager.pytest_cuke_after_scenario(
                    request=self.request, feature=self.feature, scenario=self.scenario
                )

            # Allow test function to use updated fixtures directly
            fixturenames = getattr(item, "fixturenames", [])
            for argname in fixturenames:
                item.funcargs[argname] = item._request.getfixturevalue(argname)  # type: ignore[attr-defined]  # Pytest populates this private request for late fixture injection.

    def pytest_cuke_run_scenario(self, request: FixtureRequest, feature: Feature, scenario: Scenario) -> Any:
        """Execute the scenario steps."""
        __tracebackhide__ = True
        steps: deque[Step] = request.getfixturevalue("steps_left")
        scenario_background = scenario.background
        if scenario_background is not None:
            bg_steps = scenario_background.steps
        else:
            feature_background = feature.background
            bg_steps = feature_background.steps if feature_background is not None else ()
        all_steps = tuple(bg_steps) + tuple(getattr(scenario, "steps", ()))
        steps.extend(all_steps)
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
            while left_steps:
                step = left_steps.popleft()
                self.plugin_manager.pytest_cuke_run_step(
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
        try:
            if hasattr(step, "__dict__"):
                if hasattr(feature, "_get_step_doc_string"):
                    step.__dict__["doc_string"] = feature._get_step_doc_string(step)
                if hasattr(feature, "_get_step_data_table"):
                    step.__dict__["data_table"] = feature._get_step_data_table(step)
                if hasattr(feature, "_get_step_keyword"):
                    step.__dict__["keyword"] = feature._get_step_keyword(step)
                if hasattr(feature, "_get_step_line_number"):
                    step.__dict__["line_number"] = feature._get_step_line_number(step)
            registry = getattr(feature, "registry", None)
            ast_node_ids = getattr(scenario, "ast_node_ids", None)
            if registry is not None and ast_node_ids and hasattr(scenario, "__dict__"):
                scenario.__dict__["description"] = registry[ast_node_ids[0]].description
            yield
        finally:
            if hasattr(step, "__dict__"):
                step.__dict__.pop("doc_string", None)
                step.__dict__.pop("data_table", None)
                step.__dict__.pop("keyword", None)
                step.__dict__.pop("line_number", None)
            if hasattr(scenario, "__dict__"):
                scenario.__dict__["description"] = None

    def pytest_cuke_run_step(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        previous_step: Step | None,
    ) -> Any:
        __tracebackhide__ = True
        with self.extended_step_context(feature, scenario, step):
            return self.step_runner.run_step(request, feature, scenario, step, previous_step)

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

    def _inject_step_parameters_as_fixtures(
        self,
        step_params: dict[str, Any] | None = None,
        params_fixtures_mapping: dict[str, str | None] | None = None,
    ) -> None:
        return self.step_runner.inject_step_parameters_as_fixtures(
            cast("FixtureRequest", self.request), step_params, params_fixtures_mapping
        )

    def _get_step_function_kwargs(
        self, step: Step, step_definition: Definition, step_params: dict[str, Any]
    ) -> Iterator[tuple[str, Any]]:
        return self.step_runner.get_step_function_kwargs(
            cast("FixtureRequest", self.request), step, step_definition, step_params
        )

    def _inject_target_fixtures(self, step_definition: Definition, step_result: Any) -> None:
        return self.step_runner.inject_target_fixtures(
            cast("FixtureRequest", self.request), step_definition, step_result
        )

    def _match_to_step(self, step: Step, previous_step: Step | None) -> Definition:
        if self.feature is None or self.scenario is None:
            raise RuntimeError("ScenarioRunner has no active feature and scenario.")
        return self.step_runner.match_to_step(
            cast("FixtureRequest", self.request), self.feature, self.scenario, step, previous_step
        )
