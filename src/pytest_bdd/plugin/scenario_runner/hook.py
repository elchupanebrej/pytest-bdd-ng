from io import BufferedIOBase, TextIOBase
from typing import Any, Optional, Union

import pytest
from cucumber_messages import Pickle  # type:ignore[import-untyped]

from pytest_bdd.compatibility.pytest import FixtureRequest
from pytest_bdd.model.gherkin_document import Feature


class ScenarioRunnerHookSpec:
    def pytest_bdd_before_scenario(self, request, feature, scenario):
        """Called before scenario is executed."""

    def pytest_bdd_run_scenario(self, request, feature, scenario):
        """Execution scenario protocol"""

    def pytest_bdd_after_scenario(self, request, feature, scenario):
        """Called after scenario is executed."""

    def pytest_bdd_run_step(self, request, feature, scenario, step, previous_step):
        """Execution of run step protocol"""

    def pytest_bdd_before_step(self, request, feature, scenario, step, step_func):
        """Called before step function is set up."""

    def pytest_bdd_before_step_call(
        self,
        request,
        feature,
        scenario,
        step,
        step_func,
        step_func_args,
        step_definition,
    ):
        """Called before step function is executed."""

    def pytest_bdd_after_step(
        self,
        request,
        feature,
        scenario,
        step,
        step_func,
        step_func_args,
        step_definition,
    ):
        """Called after step function is successfully executed."""

    def pytest_bdd_step_error(
        self,
        request,
        feature,
        scenario,
        step,
        step_func,
        step_func_args,
        exception,
        step_definition,
    ):
        """Called when step function failed to execute."""

    def pytest_bdd_step_func_lookup_error(self, request, feature, scenario, step, exception):
        """Called when step lookup failed."""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_match_step_definition_to_step(self, request, feature, scenario, step, previous_step):
        """Find match between scenario step and user defined step function"""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_step_caller(
        self,
        request,
        feature,
        scenario,
        step,
        step_func,
        step_func_args,
        step_definition,
    ):
        """Provide alternative approach to execute step"""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_step_dispatcher(self, request: FixtureRequest, feature: Feature, scenario: Pickle):
        """Provide alternative approach to execute scenario steps"""

    def pytest_bdd_attach(
        self,
        request: FixtureRequest,
        attachment: Union[str, bytes, bytearray, BufferedIOBase, TextIOBase, Any],
        media_type: Optional[str],
        file_name: Optional[str],
    ):
        """Internal hook to add attachment to a test case"""
