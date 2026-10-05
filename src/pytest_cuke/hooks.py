from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pytest import hookspec

if TYPE_CHECKING:
    from collections.abc import Iterable
    from io import BufferedIOBase, TextIOBase
    from pathlib import Path

    from pytest_cuke.compatibility.pytest import Config, FixtureRequest, Mark
    from pytest_cuke.model import Feature
    from pytest_cuke.model.message_extension import EventEnvelope as Message
    from pytest_cuke.model.scenario import Scenario
    from pytest_cuke.model.step import Step

"""Pytest-bdd pytest hooks."""


def pytest_cuke_before_scenario(request: FixtureRequest, feature: Feature, scenario: Scenario) -> None:
    """Called before scenario is executed."""


def pytest_cuke_run_scenario(request: FixtureRequest, feature: Feature, scenario: Scenario) -> Any:
    """Execution scenario protocol"""


def pytest_cuke_after_scenario(request: FixtureRequest, feature: Feature, scenario: Scenario) -> None:
    """Called after scenario is executed."""


def pytest_cuke_run_step(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, previous_step: Step | None
) -> Any:
    """Execution of run step protocol"""


def pytest_cuke_before_step(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, step_func: Any
) -> None:
    """Called before step function is set up."""


def pytest_cuke_step_bypassed(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_definition: Any,
    status: Literal["passed", "skipped"],
    message: str | None = None,
) -> None:
    """Called when a not-implemented step is reported without executing its body."""


def pytest_cuke_before_step_call(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Any,
    step_func_args: tuple[Any, ...],
    step_definition: Any,
) -> None:
    """Called before step function is executed."""


def pytest_cuke_after_step(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Any,
    step_func_args: tuple[Any, ...],
    step_definition: Any,
) -> None:
    """Called after step function is successfully executed."""


def pytest_cuke_step_error(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Any,
    step_func_args: tuple[Any, ...],
    exception: BaseException,
    step_definition: Any,
    tolerated: bool = False,
) -> None:
    """Called when a step body or its setup failed to execute.

    ``tolerated`` is true only when an ordinary body exception is ignored by
    the configured tolerant-step policy. The step still failed and should
    retain its error evidence in reports.
    """


def pytest_cuke_step_func_lookup_error(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, exception: Exception
) -> None:
    """Called when step lookup failed."""


@hookspec(firstresult=True)
def pytest_cuke_apply_tag(tag: Any, function: Any) -> Any:
    """Apply a tag (from a .feature file) to the given test function."""


@hookspec(firstresult=True)
def pytest_cuke_convert_tag_to_marks(feature: Feature, scenario: Scenario, tag: Any) -> Iterable[Mark] | None:
    """Apply a tag (from a .feature file) to the given test item.

    The default implementation does the equivalent of
    getattr(pytest.mark, tag)(function), but you can override this hook and
    return True to do more sophisticated handling of tags.
    """


@hookspec(firstresult=True)
def pytest_cuke_match_step_definition_to_step(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, previous_step: Step | None
) -> Any:
    """Find match between scenario step and user defined step function"""


@hookspec(firstresult=True)
def pytest_cuke_get_step_caller(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Any,
    step_func_args: tuple[Any, ...],
    step_definition: Any,
) -> Any:
    """Provide alternative approach to execute step"""


@hookspec(firstresult=True)
def pytest_cuke_get_step_dispatcher(request: FixtureRequest, feature: Feature, scenario: Any) -> Any:
    """Provide alternative approach to execute scenario steps"""


def pytest_cuke_message(config: Config, message: Message) -> None:
    """Implement cucumber message protocol https://github.com/cucumber/messages"""


def pytest_cuke_message_validated(config: Config, message: Message) -> None:
    """Receive one envelope after schema and stream validation accepts it."""


@hookspec(firstresult=True)
def pytest_cuke_is_collectible(config: Config, path: Path) -> bool | None:
    """Verifies if path could be collected by pytest_cuke"""


@hookspec(firstresult=True)
def pytest_cuke_get_parser(config: Config, mimetype: str) -> Any:
    """Get parser for specific file path"""


@hookspec(firstresult=True)
def pytest_cuke_get_mimetype(config: Config, path: Path) -> str | None:
    """Get parser for specific file path"""


def pytest_cuke_attach(
    request: FixtureRequest,
    attachment: str | bytes | bytearray | BufferedIOBase | TextIOBase,
    media_type: str | None,
    file_name: str | None,
) -> None:
    """Internal hook to add attachment to a test case"""
