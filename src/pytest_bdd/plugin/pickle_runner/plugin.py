from __future__ import annotations

from contextlib import suppress
from functools import partial
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, cast

import pytest
from cucumber_messages import (
    GherkinDocument,  # type:ignore[attr-defined, import-untyped]
    Pickle,  # type:ignore[import-untyped]
    PickleStep,  # type:ignore[attr-defined, import-untyped]
)

import pytest_bdd.types.exception as exceptions
from pytest_bdd.compatibility.pytest import FixtureRequest, Item, call_fixture_func
from pytest_bdd.model.scenario_run import HookPhase, Run, RunStatus
from pytest_bdd.plugin.scenario_test_collector.const import PYTEST_BDD_MARK
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.util.inspect_extra import get_args
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.pytest_extra import inject_fixture
from pytest_bdd.util.toolz_extra import DefaultMapping

from .run_access import (
    resolve_feature_object,
    resolve_pickle_object,
    resolve_previous_step_object,
    resolve_scenario_description,
    resolve_step_object,
    resolve_step_runtime_enrichment,
)
from .run_transitions import apply_transition

if TYPE_CHECKING:
    from collections import deque


UNSET = object()


class PickleRunner:
    plugin_name = "pytest-bdd-scenario-runner-runtime"

    def __init__(self) -> None:
        self.request: FixtureRequest | None = None
        self.gherkin_document: GherkinDocument | None = None
        self.pickle: Pickle | None = None
        self.feature_source: Any | None = None

    @staticmethod
    def _resolve_runtime_params(item: Item) -> tuple[Any | None, Any | None, Any | None]:
        callspec = getattr(item, "callspec", None)
        params = getattr(callspec, "params", None)
        if isinstance(params, dict):
            gherkin_document = params.get("gherkin_document")
            pickle = params.get("pickle")
            feature_source = params.get("feature_source")
            if gherkin_document is not None and pickle is not None and feature_source is not None:
                return gherkin_document, pickle, feature_source
        return None, None, None

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionstart(self, session) -> None:
        run = Run.from_stash(session.config.stash)
        if run.reporting_state.run_started_id is None:
            run.reporting_state.run_started_id = next(IdGenerator.from_stash(session.config.stash))

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: Item) -> None:
        __tracebackhide__ = True
        mark_names = [mark.name for mark in item.iter_markers()]
        if PYTEST_BDD_MARK not in mark_names:
            return

        request = item._request
        gherkin_document, pickle, feature_source = self._resolve_runtime_params(item=item)
        if gherkin_document is None or pickle is None or feature_source is None:
            return

        run = Run.from_stash(request.config.stash)
        run.create_scenario_run(
            request,
            gherkin_document=gherkin_document,
            feature_source=feature_source,
            pickle=pickle,
        )

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_call(self, item: Item):
        __tracebackhide__ = True
        mark_names = [mark.name for mark in item.iter_markers()]
        if PYTEST_BDD_MARK not in mark_names:
            return

        self.request = item._request
        self.gherkin_document = self.request.getfixturevalue("gherkin_document")
        self.pickle = self.request.getfixturevalue("pickle")
        self.feature_source = self.request.getfixturevalue("feature_source")

        self._invoke_bdd_hook(
            hook_name="pytest_bdd_before_scenario",
            request=self.request,
            gherkin_document=self.gherkin_document,
            pickle=self.pickle,
        )
        try:
            self._invoke_bdd_hook(
                hook_name="pytest_bdd_run_scenario",
                request=self.request,
                gherkin_document=self.gherkin_document,
                pickle=self.pickle,
            )
        finally:
            self._invoke_bdd_hook(
                hook_name="pytest_bdd_after_scenario",
                request=self.request,
                gherkin_document=self.gherkin_document,
                pickle=self.pickle,
            )

        # Allow test function to use updated fixtures directly
        fixturenames = getattr(item, "fixturenames", [])
        for argname in fixturenames:
            item.funcargs[argname] = item._request.getfixturevalue(argname)  # type:ignore[attr-defined]

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_teardown(self, item: Item, nextitem: Item | None):  # noqa: ARG002
        __tracebackhide__ = True
        yield
        Run.pop_scenario_run(item._request)

    def _invoke_bdd_hook(
        self,
        *,
        hook_name: str,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        step: Any = UNSET,
        previous_step: Any = UNSET,
        status: RunStatus | None = None,
        **extra_kwargs: Any,
    ) -> Any:
        run = Run.from_stash(request.config.stash)
        scenario_run = run.active_scenario_run

        try:
            hook_phase = HookPhase(hook_name)
        except ValueError:
            pass
        else:
            if scenario_run is None:
                msg = (
                    f"Active scenario run is unavailable while invoking lifecycle hook {hook_name!r}. "
                    "Pickle-runner lifecycle state is corrupted or was not initialized."
                )
                raise RuntimeError(msg)
            apply_transition(
                scenario_run,
                hook_phase=hook_phase,
                gherkin_document=gherkin_document,
                pickle=pickle,
                step=None if step is UNSET else step,
                previous_step=None if previous_step is UNSET else previous_step,
                status=status,
            )

        hook_kwargs: dict[str, Any] = {
            "request": request,
            "run": run,
        }
        hook_kwargs.update(extra_kwargs)
        return getattr(request.config.hook, hook_name)(**hook_kwargs)

    def pytest_bdd_run_scenario(
        self,
        request: FixtureRequest,
        run: Run,
    ):
        """Execute scenarios via step dispatcher."""
        __tracebackhide__ = True
        gherkin_document = resolve_feature_object(run)
        pickle = resolve_pickle_object(run)
        if gherkin_document is None or pickle is None:
            return None
        steps: deque = request.getfixturevalue("steps_left")
        steps.extend(pickle.steps)
        step_dispatcher = request.config.hook.pytest_bdd_get_step_dispatcher(
            request=request,
            run=run,
        )
        return step_dispatcher(steps)

    @pytest.hookimpl(trylast=True)
    def pytest_bdd_get_step_dispatcher(
        self,
        request: FixtureRequest,
        run: Run,
    ):
        """Provide alternative approach to execute steps."""
        __tracebackhide__ = True

        def dispatcher(left_steps):
            __tracebackhide__ = True
            previous_step = None
            gherkin_document = resolve_feature_object(run)
            pickle = resolve_pickle_object(run)
            if gherkin_document is None or pickle is None:
                return
            while left_steps:
                step = left_steps.popleft()
                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_run_step",
                    request=request,
                    gherkin_document=gherkin_document,
                    pickle=pickle,
                    step=step,
                    previous_step=previous_step,
                )
                previous_step = step

        return dispatcher

    def pytest_bdd_run_step(
        self,
        request,
        run: Run,
    ):
        __tracebackhide__ = True
        gherkin_document = resolve_feature_object(run)
        pickle = resolve_pickle_object(run)
        step = resolve_step_object(run)
        previous_step = resolve_previous_step_object(run)
        if gherkin_document is None or pickle is None or step is None:
            return

        from pytest_bdd.model.scenario_run import StepRun

        scenario_run = run.active_scenario_run

        if scenario_run is not None:
            if isinstance(step, PickleStep):
                feature_binding = scenario_run.feature_binding()
                step_runtime_enrichment = resolve_step_runtime_enrichment(
                    step=step,
                    feature_binding=feature_binding,
                    scenario_run=scenario_run,
                )
                scenario_run.step_run = StepRun(
                    step=step,
                    keyword=step_runtime_enrichment.get("keyword"),
                    text=getattr(step, "text", ""),
                )

            scenario_description = resolve_scenario_description(
                pickle=pickle,
                feature_binding=scenario_run.feature_binding() if scenario_run is not None else None,
                scenario_run=scenario_run,
            )
            pickle.__dict__["description"] = scenario_description

        try:
            hook_kwargs = {
                "request": request,
                "run": run,
            }

            try:
                step_definition = self._match_to_step(run)
            except exceptions.StepDefinitionNotFoundError as exception:
                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_step_func_lookup_error",
                    request=request,
                    gherkin_document=gherkin_document,
                    pickle=pickle,
                    step=step,
                    previous_step=previous_step,
                    status=RunStatus.failed,
                    exception=exception,
                )
                raise
            else:
                hook_kwargs["step_func"] = step_definition.func
                hook_kwargs["step_definition"] = step_definition

            self._invoke_bdd_hook(
                hook_name="pytest_bdd_before_step",
                request=request,
                gherkin_document=gherkin_document,
                pickle=pickle,
                step=step,
                previous_step=previous_step,
                step_func=step_definition.func,
            )

            hook_kwargs["step_func_args"] = {}
            step_params = step_definition.get_parameters(request, step)

            if scenario_run is not None and scenario_run.step_run is not None:
                scenario_run.step_run.parameters = step_params

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
                    gherkin_document=gherkin_document,
                    pickle=pickle,
                    step=step,
                    previous_step=previous_step,
                    step_func=step_definition.func,
                    step_func_args=step_function_kwargs,
                    step_definition=step_definition,
                )

                step_caller = self._invoke_bdd_hook(
                    hook_name="pytest_bdd_get_step_caller",
                    request=request,
                    gherkin_document=gherkin_document,
                    pickle=pickle,
                    step=step,
                    previous_step=previous_step,
                    step_func=step_definition.func,
                    step_func_args=step_function_kwargs,
                    step_definition=step_definition,
                )
                step_result = step_caller()

                self._inject_target_fixtures(step_definition, step_result)
                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_after_step",
                    request=request,
                    gherkin_document=gherkin_document,
                    pickle=pickle,
                    step=step,
                    previous_step=previous_step,
                    step_func=step_definition.func,
                    step_func_args=step_function_kwargs,
                    step_definition=step_definition,
                )
            except Exception as exception:
                if scenario_run is not None and scenario_run.step_run is not None:
                    scenario_run.step_run.status = RunStatus.failed

                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_step_error",
                    request=request,
                    gherkin_document=gherkin_document,
                    pickle=pickle,
                    step=step,
                    previous_step=previous_step,
                    status=RunStatus.failed,
                    step_func=step_definition.func,
                    step_func_args=hook_kwargs["step_func_args"],
                    step_definition=step_definition,
                    exception=exception,
                )
                raise
        finally:
            pickle.__dict__["description"] = None

    @pytest.hookimpl(trylast=True)
    def pytest_bdd_get_step_caller(
        self,
        request,
        run,  # noqa: ARG002
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

    def _match_to_step(self, run: Run):
        step = resolve_step_object(run)
        if step is None:
            msg = "Execution context does not provide active step for matching"
            raise RuntimeError(msg)
        request = cast(FixtureRequest, self.request)
        try:
            return request.config.hook.pytest_bdd_match_step_definition_to_step(
                request=request,
                run=run,
            )
        except StepDefinitionManager.Matcher.MatchNotFoundError as exception:
            step_lookup_exception = exceptions.StepDefinitionNotFoundError(self.gherkin_document, self.pickle, step)
            with suppress(Exception):
                step_registry = request.getfixturevalue("step_registry")
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
