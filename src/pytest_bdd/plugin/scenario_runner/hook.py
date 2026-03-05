from io import BufferedIOBase, TextIOBase
from typing import Any

import pytest
from cucumber_messages import GherkinDocument, Pickle  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.compatibility.pytest import FixtureRequest


class ScenarioRunnerHookSpec:
    def pytest_bdd_before_scenario(self, request: FixtureRequest, gherkin_document: GherkinDocument, pickle: Pickle):
        """Called before scenario is executed."""

    def pytest_bdd_run_scenario(self, request: FixtureRequest, gherkin_document: GherkinDocument, pickle: Pickle):
        """Execution scenario protocol"""

    def pytest_bdd_after_scenario(self, request: FixtureRequest, gherkin_document: GherkinDocument, pickle: Pickle):
        """Called after scenario is executed."""

    def pytest_bdd_run_step(
        self,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        step,
        previous_step,
    ):
        """Execution of run step protocol"""

    def pytest_bdd_before_step(
        self,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        step,
        step_func,
    ):
        """Called before step function is set up."""

    def pytest_bdd_before_step_call(
        self,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        step,
        step_func,
        step_func_args,
        step_definition,
    ):
        """Called before step function is executed."""

    def pytest_bdd_after_step(
        self,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        step,
        step_func,
        step_func_args,
        step_definition,
    ):
        """Called after step function is successfully executed."""

    def pytest_bdd_step_error(
        self,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        step,
        step_func,
        step_func_args,
        exception,
        step_definition,
    ):
        """Called when step function failed to execute."""

    def pytest_bdd_step_func_lookup_error(
        self,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        step,
        exception,
    ):
        """Called when step lookup failed."""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_match_step_definition_to_step(
        self,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        step,
        previous_step,
    ):
        """Find match between scenario step and user defined step function"""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_step_caller(
        self,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
        step,
        step_func,
        step_func_args,
        step_definition,
    ):
        """Provide alternative approach to execute step"""

    @pytest.hookspec(firstresult=True)
    def pytest_bdd_get_step_dispatcher(
        self,
        request: FixtureRequest,
        gherkin_document: GherkinDocument,
        pickle: Pickle,
    ):
        """Provide alternative approach to execute scenario steps"""

    def pytest_bdd_attach(
        self,
        request: FixtureRequest,
        attachment: str | bytes | bytearray | BufferedIOBase | TextIOBase | Any,
        media_type: str | None,
        file_name: str | None,
        source_data: str | None,
        source_media_type: str | None,
        source_uri: str | None,
        url: str | None,
        as_external: bool,  # noqa: FBT001
        test_run_hook_started_id: str | None,
        test_run_started_id: str | None,
    ):
        """Internal hook to add attachment to a test case"""
