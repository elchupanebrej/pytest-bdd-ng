"""Provide hook helpers."""

from collections import deque
from collections.abc import Callable

import pytest

from pytest_bdd.compatibility.pytest import FixtureRequest
from pytest_bdd.model.run import Run
from pytest_bdd.steps import Step, StepDefinitionManager, StepFunc


class PickleRunnerHookSpec:
    """Represent pickle runner hook spec state."""

    def pytest_bdd_before_scenario(self, request: FixtureRequest, run: Run) -> None:
        """Call before scenario is executed."""

    def pytest_bdd_run_scenario(self, request: FixtureRequest, run: Run) -> object:
        """Execute scenario protocol."""

    def pytest_bdd_after_scenario(self, request: FixtureRequest, run: Run) -> None:
        """Call after scenario is executed."""

    def pytest_bdd_run_step(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> None:
        """Execute run step protocol."""

    def pytest_bdd_before_step(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: StepFunc,
    ) -> None:
        """Call before step function is set up."""

    def pytest_bdd_before_step_call(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: StepFunc,
        step_func_args: dict[str, object],
        step_definition: StepDefinitionManager.Definition,
    ) -> None:
        """Call before step function is executed."""

    def pytest_bdd_after_step(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: StepFunc,
        step_func_args: dict[str, object],
        step_definition: StepDefinitionManager.Definition,
    ) -> None:
        """Call after step function is successfully executed."""

    def pytest_bdd_step_error(  # noqa: PLR0913, PLR0917
        self,
        request: FixtureRequest,
        run: Run,
        step_func: StepFunc,
        step_func_args: dict[str, object],
        exception: Exception,
        step_definition: StepDefinitionManager.Definition,
    ) -> None:
        """Call when step function failed to execute."""

    def pytest_bdd_step_func_lookup_error(
        self,
        request: FixtureRequest,
        run: Run,
        exception: Exception,
    ) -> None:
        """Call when step lookup failed."""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_match_step_definition_to_step(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> StepDefinitionManager.Definition | None:
        """Find match between scenario step and user defined step function."""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_step_caller(
        self,
        request: FixtureRequest,
        run: Run,
        step_func: StepFunc,
        step_func_args: dict[str, object],
        step_definition: StepDefinitionManager.Definition,
    ) -> Callable[[], object] | None:
        """Provide alternative approach to execute step."""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_step_dispatcher(
        self,
        request: FixtureRequest,
        run: Run,
    ) -> Callable[[deque[Step]], object] | None:
        """Provide alternative approach to execute scenario steps."""

    def pytest_bdd_attach(  # noqa: PLR0913, PLR0917
        self,
        request: FixtureRequest,
        attachment: object,
        media_type: str | None,
        file_name: str | None,
        source_data: str | None,
        source_media_type: str | None,
        source_uri: str | None,
        url: str | None,
        as_external: bool,  # noqa: FBT001
        test_run_hook_started_id: str | None,
        test_run_started_id: str | None,
    ) -> None:
        """Add attachment to a test case from an internal hook."""
