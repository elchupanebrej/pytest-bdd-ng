from __future__ import annotations

from contextlib import contextmanager, suppress
from functools import partial
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, cast

import pytest
from cucumber_messages import Pickle as Scenario  # type:ignore[import-untyped]
from cucumber_messages import PickleStep  # type:ignore[attr-defined, import-untyped]

import pytest_bdd.types.exception as exceptions
from pytest_bdd.compatibility.pytest import FixtureRequest, Item, call_fixture_func
from pytest_bdd.model.execution_context import ExecutionContext, ExecutionStatus
from pytest_bdd.plugin.scenario_test_collector.const import PYTEST_BDD_MARK
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.util.inspect_extra import get_args
from pytest_bdd.util.pytest_extra import inject_fixture
from pytest_bdd.util.toolz_extra import DefaultMapping

from .context_access import bind_hook_parameter_model, clear_hook_parameter_model, resolve_execution_context
from .context_store import ExecutionContextStore
from .context_transitions import apply_transition, phase_from_hook_name

if TYPE_CHECKING:
    from collections import deque

    from pytest_bdd.model.gherkin_document import Feature


UNSET = object()


class ScenarioRunner:
    plugin_name = "pytest-bdd-scenario-runner-runtime"

    def __init__(self) -> None:
        self.request: FixtureRequest | None = None
        self.feature: Feature | None = None
        self.scenario: Scenario | None = None
        self.context_store = ExecutionContextStore()

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionstart(self, session) -> None:
        self.context_store.initialize_session_root(session=session)

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_call(self, item: Item):
        __tracebackhide__ = True
        mark_names = [mark.name for mark in item.iter_markers()]
        if PYTEST_BDD_MARK not in mark_names:
            return

        self.request = item._request
        self.feature = self.request.getfixturevalue("feature")
        self.scenario = self.request.getfixturevalue("scenario")
        execution_context = self.context_store.get_or_create(
            self.request,
            feature=self.feature,
            scenario=self.scenario,
        )

        self._invoke_bdd_hook(
            hook_name="pytest_bdd_before_scenario",
            request=self.request,
            feature=self.feature,
            scenario=self.scenario,
            execution_context=execution_context,
        )
        try:
            self._invoke_bdd_hook(
                hook_name="pytest_bdd_run_scenario",
                request=self.request,
                feature=self.feature,
                scenario=self.scenario,
                execution_context=execution_context,
            )
        finally:
            self._invoke_bdd_hook(
                hook_name="pytest_bdd_after_scenario",
                request=self.request,
                feature=self.feature,
                scenario=self.scenario,
                execution_context=execution_context,
            )
            self.context_store.pop(self.request)

        # Allow test function to use updated fixtures directly
        fixturenames = getattr(item, "fixturenames", [])
        for argname in fixturenames:
            item.funcargs[argname] = item._request.getfixturevalue(argname)  # type:ignore[attr-defined]

    def _invoke_bdd_hook(
        self,
        *,
        hook_name: str,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        execution_context: ExecutionContext | None = None,
        step: Any = UNSET,
        previous_step: Any = UNSET,
        status: ExecutionStatus | None = None,
        **extra_kwargs: Any,
    ) -> Any:
        context = execution_context or resolve_execution_context(
            request,
            context_store=self.context_store,
            feature=feature,
            scenario=scenario,
        )

        hook_phase = phase_from_hook_name(hook_name)
        if hook_phase is not None:
            apply_transition(
                context,
                hook_phase=hook_phase,
                run=request.session,
                feature=feature,
                scenario=scenario,
                step=None if step is UNSET else step,
                previous_step=None if previous_step is UNSET else previous_step,
                status=status,
            )

        parameter_model = bind_hook_parameter_model(
            request=request,
            execution_context=context,
            feature=feature,
            scenario=scenario,
            step=None if step is UNSET else step,
            previous_step=None if previous_step is UNSET else previous_step,
        )

        hook_kwargs: dict[str, Any] = {
            "request": request,
            "feature": feature,
            "scenario": scenario,
        }
        if step is not UNSET:
            hook_kwargs["step"] = step
        if previous_step is not UNSET:
            hook_kwargs["previous_step"] = previous_step
        hook_kwargs.update(extra_kwargs)
        try:
            return getattr(request.config.hook, hook_name)(**hook_kwargs)
        finally:
            clear_hook_parameter_model(parameter_model)

    def pytest_bdd_run_scenario(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
    ):
        """Execute scenarios via step dispatcher."""
        __tracebackhide__ = True
        steps: deque = request.getfixturevalue("steps_left")
        steps.extend(scenario.steps)
        step_dispatcher = request.config.hook.pytest_bdd_get_step_dispatcher(
            request=request,
            feature=feature,
            scenario=scenario,
        )
        return step_dispatcher(steps)

    @pytest.hookimpl(trylast=True)
    def pytest_bdd_get_step_dispatcher(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
    ):
        """Provide alternative approach to execute steps."""
        __tracebackhide__ = True

        def dispatcher(left_steps):
            __tracebackhide__ = True
            previous_step = None
            while left_steps:
                step = left_steps.popleft()
                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_run_step",
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    previous_step=previous_step,
                )
                previous_step = step

        return dispatcher

    @contextmanager
    def extended_step_context(self, feature: Feature, scenario, step):
        """Attach rich step metadata for hook consumers during step execution."""
        try:
            if isinstance(step, PickleStep):
                step.__dict__["doc_string"] = feature._get_step_doc_string(step)
                step.__dict__["data_table"] = feature._get_step_data_table(step)
                step.__dict__["keyword"] = feature._get_step_keyword(step)
                step.__dict__["line_number"] = feature._get_step_line_number(step)
            scenario.__dict__["description"] = feature.registry[scenario.ast_node_ids[0]].description
            yield
        finally:
            if isinstance(step, PickleStep):
                step.__dict__.pop("doc_string", None)
                step.__dict__.pop("data_table", None)
                step.__dict__.pop("keyword", None)
                step.__dict__.pop("line_number", None)
            scenario.__dict__["description"] = None

    def pytest_bdd_run_step(
        self,
        request,
        feature: Feature,
        scenario,
        step,
        previous_step,
    ):
        __tracebackhide__ = True
        context = resolve_execution_context(
            request,
            context_store=self.context_store,
            feature=feature,
            scenario=scenario,
        )

        with self.extended_step_context(feature, scenario, step):
            hook_kwargs = {
                "request": request,
                "feature": feature,
                "scenario": scenario,
                "step": step,
                "previous_step": previous_step,
                "execution_context": context,
            }

            try:
                step_definition = self._match_to_step(step, previous_step)
            except exceptions.StepDefinitionNotFoundError as exception:
                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_step_func_lookup_error",
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    execution_context=context,
                    status=ExecutionStatus.failed,
                    exception=exception,
                )
                raise
            else:
                hook_kwargs["step_func"] = step_definition.func
                hook_kwargs["step_definition"] = step_definition

            self._invoke_bdd_hook(
                hook_name="pytest_bdd_before_step",
                request=request,
                feature=feature,
                scenario=scenario,
                step=step,
                execution_context=context,
                step_func=step_definition.func,
            )

            hook_kwargs["step_func_args"] = {}
            step_params = step_definition.get_parameters(request, step)
            try:
                self._inject_step_parameters_as_fixtures(
                    step_params=step_params,
                    params_fixtures_mapping=step_definition.params_fixtures_mapping,
                )

                step_function_kwargs = dict(self._get_step_function_kwargs(step, step_definition, step_params))
                hook_kwargs["step_func_args"] = step_function_kwargs

                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_before_step_call",
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    execution_context=context,
                    step_func=step_definition.func,
                    step_func_args=step_function_kwargs,
                    step_definition=step_definition,
                )

                step_caller = self._invoke_bdd_hook(
                    hook_name="pytest_bdd_get_step_caller",
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    execution_context=context,
                    step_func=step_definition.func,
                    step_func_args=step_function_kwargs,
                    step_definition=step_definition,
                )
                step_result = step_caller()

                self._inject_target_fixtures(step_definition, step_result)
                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_after_step",
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    execution_context=context,
                    step_func=step_definition.func,
                    step_func_args=step_function_kwargs,
                    step_definition=step_definition,
                )
            except Exception as exception:
                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_step_error",
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    execution_context=context,
                    status=ExecutionStatus.failed,
                    step_func=step_definition.func,
                    step_func_args=hook_kwargs["step_func_args"],
                    step_definition=step_definition,
                    exception=exception,
                )
                raise

    @pytest.hookimpl(trylast=True)
    def pytest_bdd_get_step_caller(
        self,
        request,
        feature,  # noqa: ARG002
        scenario,  # noqa: ARG002
        step,  # noqa: ARG002
        step_func,  # noqa: ARG002
        step_func_args,
        step_definition,
    ):
        # Execute the step as if it was a fixture to support generator fixtures.
        return partial(
            call_fixture_func,
            fixturefunc=step_definition.func,
            request=request,
            kwargs=step_func_args,
        )

    def _inject_step_parameters_as_fixtures(
        self,
        step_params: dict | None = None,
        params_fixtures_mapping: dict | None = None,
    ):
        step_params = step_params or {}
        params_fixtures_mapping = (
            DefaultMapping.instantiate_from_collection_or_bool(
                params_fixtures_mapping or {},
                warm_up_keys=step_params.keys(),
            )
            or {}
        )

        for param, fixture_name in params_fixtures_mapping.items():
            if fixture_name is None or fixture_name is ...:
                continue
            inject_fixture(cast(FixtureRequest, self.request), fixture_name, step_params[param])

    def _get_step_function_kwargs(self, step, step_definition, step_params):
        for param in get_args(step_definition.func):
            try:
                yield param, step_params[param]
            except KeyError:  # noqa: PERF203
                try:
                    yield param, {"step": step}[param]
                except KeyError:
                    yield param, self.request.getfixturevalue(param)

    def _inject_target_fixtures(self, step_definition, step_result):
        if len(step_definition.target_fixtures) == 1:
            injectable_fixtures = [(step_definition.target_fixtures[0], step_result)]
        elif step_result is not None and len(step_definition.target_fixtures) != 0:
            injectable_fixtures = zip(step_definition.target_fixtures, step_result, strict=False)
        else:
            injectable_fixtures = zip_longest(step_definition.target_fixtures, [])

        for target_fixture, return_value in injectable_fixtures:
            inject_fixture(self.request, target_fixture, return_value)

    def _match_to_step(
        self,
        step,
        previous_step,
    ):
        try:
            return self.request.config.hook.pytest_bdd_match_step_definition_to_step(
                request=self.request,
                feature=self.feature,
                scenario=self.scenario,
                step=step,
                previous_step=previous_step,
            )
        except StepDefinitionManager.Matcher.MatchNotFoundError as exception:
            step_lookup_exception = exceptions.StepDefinitionNotFoundError(self.feature, self.scenario, step)
            with suppress(Exception):
                step_registry = self.request.getfixturevalue("step_registry")
                undefined_info = None
                while step_registry is not None:
                    for step_definition in step_registry:
                        candidate = getattr(step_definition.parser, "last_undefined_parameter_type", None)
                        if isinstance(candidate, tuple) and len(candidate) == 2 and candidate[1]:
                            undefined_info = (str(candidate[0]), str(candidate[1]))
                            break
                    if undefined_info is not None:
                        break
                    step_registry = step_registry.parent
                if undefined_info is not None:
                    step_lookup_exception.undefined_parameter_type = undefined_info
            raise step_lookup_exception from exception
