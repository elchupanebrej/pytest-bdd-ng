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
    from pytest_cuke.model.session_run import RunContext

"""Pytest-bdd pytest hooks."""


def pytest_cuke_before_scenario(request: FixtureRequest, run: RunContext) -> None:
    """Called before scenario is executed."""


def pytest_cuke_run_scenario(request: FixtureRequest, run: RunContext) -> Any:
    """Execution scenario protocol"""


def pytest_cuke_after_scenario(request: FixtureRequest, run: RunContext) -> None:
    """Called after scenario is executed."""


def pytest_cuke_run_step(request: FixtureRequest, run: RunContext) -> Any:
    """Execution of run step protocol"""


def pytest_cuke_before_step(request: FixtureRequest, run: RunContext, step_func: Any) -> None:
    """Called before step function is set up."""


def pytest_cuke_step_bypassed(
    request: FixtureRequest,
    run: RunContext,
    step_definition: Any,
    status: Literal["passed", "skipped"],
    message: str | None = None,
) -> None:
    """Called when a not-implemented step is reported without executing its body."""


def pytest_cuke_before_step_call(
    request: FixtureRequest,
    run: RunContext,
    step_func: Any,
    step_func_args: dict[str, Any],
    step_definition: Any,
) -> None:
    """Called before step function is executed."""


def pytest_cuke_after_step(
    request: FixtureRequest,
    run: RunContext,
    step_func: Any,
    step_func_args: dict[str, Any],
    step_definition: Any,
) -> None:
    """Called after step function is successfully executed."""


def pytest_cuke_step_error(
    request: FixtureRequest,
    run: RunContext,
    step_func: Any,
    step_func_args: dict[str, Any],
    exception: BaseException,
    step_definition: Any,
    tolerated: bool,
) -> None:
    """Called when a step body or its setup failed to execute.

    ``tolerated`` is true only when an ordinary body exception is ignored by
    the configured tolerant-step policy. The step still failed and should
    retain its error evidence in reports.
    """


def pytest_cuke_step_func_lookup_error(
    request: FixtureRequest, run: RunContext, exception: Exception
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
    request: FixtureRequest, run: RunContext
) -> Any:
    """Find match between scenario step and user defined step function"""


@hookspec(firstresult=True)
def pytest_cuke_get_step_caller(
    request: FixtureRequest,
    run: RunContext,
    step_func: Any,
    step_func_args: dict[str, Any],
    step_definition: Any,
) -> Any:
    """Provide alternative approach to execute step"""


@hookspec(firstresult=True)
def pytest_cuke_get_step_dispatcher(request: FixtureRequest, run: RunContext) -> Any:
    """Provide alternative approach to execute scenario steps"""


def pytest_cuke_message(config: Config, message: Message) -> None:
    """Implement cucumber message protocol https://github.com/cucumber/messages"""


def pytest_cuke_message_validated(config: Config, message: Message) -> None:
    """Receive one envelope after schema and stream validation accepts it."""


def pytest_cuke_message_batch(config: Config, batch: dict[str, Any]) -> None:
    """Receive a partial worker message batch on the xdist controller.

    Batches carry a worker ID, a sequence number, and JSON Cucumber Messages
    envelopes. They are transport evidence, not a complete or final stream.
    """


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
    run: RunContext,
    attachment: str | bytes | bytearray | BufferedIOBase | TextIOBase,
    media_type: str | None,
    file_name: str | None,
) -> None:
    """Internal hook to add attachment to a test case"""


def pytest_cuke_debug_mcp_artifact_created(
    nodeid: str,
    pytest_phase: Literal["setup", "call", "teardown"],
    bdd_metadata: dict[str, Any],
    json_path: Path,
    markdown_path: Path,
    status: Literal["investigated", "needs_followup", "resolved"],
    summary: str,
) -> None:
    """Receive a validated Debug MCP artifact after its paired files are written."""
