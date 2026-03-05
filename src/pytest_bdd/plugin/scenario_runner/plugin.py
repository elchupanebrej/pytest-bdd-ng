from __future__ import annotations

from contextlib import contextmanager, suppress
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
from pytest_bdd.model.scenario_run import RunStatus, Run, ScenarioRun
from pytest_bdd.plugin.scenario_test_collector.const import PYTEST_BDD_MARK
from pytest_bdd.steps import StepDefinitionManager
from pytest_bdd.types.protocol import HasPytestBDDIdGenerator
from pytest_bdd.util.inspect_extra import get_args
from pytest_bdd.util.pytest_extra import inject_fixture
from pytest_bdd.util.toolz_extra import DefaultMapping

from .run_access import (
    bind_hook_parameter_model,
    clear_hook_parameter_model,
    resolve_feature_object,
    resolve_pickle_object,
    resolve_previous_step_object,
    resolve_scenario_description,
    resolve_scenario_run,
    resolve_step_object,
    resolve_step_runtime_enrichment,
)
from .run_store import RunStore
from .run_transitions import apply_transition, phase_from_hook_name

if TYPE_CHECKING:
    from collections import deque


UNSET = object()


class ScenarioRunner:
    plugin_name = "pytest-bdd-scenario-runner-runtime"

    def __init__(self) -> None:
        self.request: FixtureRequest | None = None
        self.gherkin_document: GherkinDocument | None = None
        self.scenario: Pickle | None = None
        self.run_store = RunStore()

    @staticmethod
    def _resolve_gherkin_document_and_pickle(item: Item, request: FixtureRequest) -> tuple[Any | None, Any | None]:
        _ = request
        callspec = getattr(item, "callspec", None)
        params = getattr(callspec, "params", None)
        if isinstance(params, dict):
            gherkin_document = params.get("gherkin_document")
            pickle = params.get("scenario")
            if gherkin_document is not None and pickle is not None:
                return gherkin_document, pickle
        return None, None

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionstart(self, session) -> None:
        run_root = self.run_store.initialize_run(session=session)
        if run_root.reporting_state.run_started_id is None:
            config = cast(HasPytestBDDIdGenerator, session.config)
            run_root.reporting_state.run_started_id = config.pytest_bdd_id_generator.get_next_id()

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: Item) -> None:
        __tracebackhide__ = True
        mark_names = [mark.name for mark in item.iter_markers()]
        if PYTEST_BDD_MARK not in mark_names:
            return

        request = item._request
        gherkin_document, pickle = self._resolve_gherkin_document_and_pickle(item=item, request=request)
        if gherkin_document is None or pickle is None:
            return

        self.run_store.get_or_create(
            request,
            feature=gherkin_document,
            scenario=pickle,
        )

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_call(self, item: Item):
        __tracebackhide__ = True
        mark_names = [mark.name for mark in item.iter_markers()]
        if PYTEST_BDD_MARK not in mark_names:
            return

        self.request = item._request
        self.gherkin_document = self.request.getfixturevalue("gherkin_document")
        self.scenario = self.request.getfixturevalue("scenario")
        scenario_run = self.run_store.get_or_create(
            self.request,
            feature=self.gherkin_document,
            scenario=self.scenario,
        )

        self._invoke_bdd_hook(
            hook_name="pytest_bdd_before_scenario",
            request=self.request,
            gherkin_document=self.gherkin_document,
            pickle=self.scenario,
            scenario_run=scenario_run,
        )
        try:
            self._invoke_bdd_hook(
                hook_name="pytest_bdd_run_scenario",
                request=self.request,
                gherkin_document=self.gherkin_document,
                pickle=self.scenario,
                scenario_run=scenario_run,
            )
        finally:
            self._invoke_bdd_hook(
                hook_name="pytest_bdd_after_scenario",
                request=self.request,
                gherkin_document=self.gherkin_document,
                pickle=self.scenario,
                scenario_run=scenario_run,
            )
            self.run_store.pop(self.request)

        # Allow test function to use updated fixtures directly
        fixturenames = getattr(item, "fixturenames", [])
        for argname in fixturenames:
            item.funcargs[argname] = item._request.getfixturevalue(argname)  # type:ignore[attr-defined]

    def _invoke_bdd_hook(
        self,
        *,
        hook_name: str,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        scenario_run: ScenarioRun | None = None,
        step: Any = UNSET,
        previous_step: Any = UNSET,
        status: RunStatus | None = None,
        **extra_kwargs: Any,
    ) -> Any:
        context = scenario_run or resolve_scenario_run(
            request,
            run_store=self.run_store,
            feature=gherkin_document,
            scenario=pickle,
        )

        hook_phase = phase_from_hook_name(hook_name)
        if hook_phase is not None:
            apply_transition(
                context,
                hook_phase=hook_phase,
                run=request.session,
                feature=gherkin_document,
                scenario=pickle,
                step=None if step is UNSET else step,
                previous_step=None if previous_step is UNSET else previous_step,
                status=status,
            )

        parameter_model = bind_hook_parameter_model(
            request=request,
            scenario_run=context,
            feature=gherkin_document,
            scenario=pickle,
            step=None if step is UNSET else step,
            previous_step=None if previous_step is UNSET else previous_step,
        )
        run = context.run
        if run is None:
            run = self.run_store.ensure_run_for_session(config=request.config, session=request.session)
            context.run = run
        run.active_scenario_run = context

        hook_kwargs: dict[str, Any] = {
            "request": request,
            "run": run,
        }
        hook_kwargs.update(extra_kwargs)
        try:
            return getattr(request.config.hook, hook_name)(**hook_kwargs)
        finally:
            clear_hook_parameter_model(parameter_model)

    def pytest_bdd_run_scenario(
        self,
        request: FixtureRequest,
        run: Run,
    ):
        """Execute scenarios via step dispatcher."""
        __tracebackhide__ = True
        scenario_run = run.active_scenario_run
        if scenario_run is None:
            return None
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
            scenario_run = run.active_scenario_run
            if scenario_run is None:
                return
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

    @contextmanager
    def extended_step_context(self, run: Run):
        """Attach rich step metadata for hook consumers during step execution."""
        scenario_run = run.active_scenario_run
        if scenario_run is None:
            yield
            return
        gherkin_document = resolve_feature_object(run)
        pickle = resolve_pickle_object(run)
        step = resolve_step_object(run)
        if gherkin_document is None or pickle is None:
            yield
            return

        config = getattr(gherkin_document, "_pytest_bdd_config", None)
        if self.request is not None:
            config = getattr(self.request, "config", None)

        try:
            if isinstance(step, PickleStep):
                step_runtime_enrichment = resolve_step_runtime_enrichment(
                    feature=gherkin_document,
                    step=step,
                    scenario_run=scenario_run,
                    config=config,
                )
                step.__dict__["doc_string"] = step_runtime_enrichment["doc_string"]
                step.__dict__["data_table"] = step_runtime_enrichment["data_table"]
                step.__dict__["keyword"] = step_runtime_enrichment["keyword"]
                step.__dict__["line_number"] = step_runtime_enrichment["line_number"]

            scenario_description = (
                resolve_scenario_description(
                    feature=gherkin_document,
                    scenario=pickle,
                    scenario_run=scenario_run,
                    config=config,
                )
            )
            pickle.__dict__["description"] = scenario_description
            yield
        finally:
            if isinstance(step, PickleStep):
                step.__dict__.pop("doc_string", None)
                step.__dict__.pop("data_table", None)
                step.__dict__.pop("keyword", None)
                step.__dict__.pop("line_number", None)
            pickle.__dict__["description"] = None

    def pytest_bdd_run_step(
        self,
        request,
        run: Run,
    ):
        __tracebackhide__ = True
        context = run.active_scenario_run
        if context is None:
            return
        gherkin_document = resolve_feature_object(run)
        pickle = resolve_pickle_object(run)
        step = resolve_step_object(run)
        previous_step = resolve_previous_step_object(run)
        if gherkin_document is None or pickle is None or step is None:
            return

        with self.extended_step_context(run):
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
                    scenario_run=context,
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
                scenario_run=context,
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
                    gherkin_document=gherkin_document,
                    pickle=pickle,
                    step=step,
                    previous_step=previous_step,
                    scenario_run=context,
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
                    scenario_run=context,
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
                    scenario_run=context,
                    step_func=step_definition.func,
                    step_func_args=step_function_kwargs,
                    step_definition=step_definition,
                )
            except Exception as exception:
                self._invoke_bdd_hook(
                    hook_name="pytest_bdd_step_error",
                    request=request,
                    gherkin_document=gherkin_document,
                    pickle=pickle,
                    step=step,
                    previous_step=previous_step,
                    scenario_run=context,
                    status=RunStatus.failed,
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
        try:
            return self.request.config.hook.pytest_bdd_match_step_definition_to_step(
                request=self.request,
                run=run,
            )
        except StepDefinitionManager.Matcher.MatchNotFoundError as exception:
            step_lookup_exception = exceptions.StepDefinitionNotFoundError(self.gherkin_document, self.scenario, step)
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
