"""Collection-only NDJSON events for code-generation consumers."""

from __future__ import annotations

import json
import sys
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

from pytest_cuke.compatibility.pytest import PYTEST7, wrap_session
from pytest_cuke.generation import STEP_TYPE_TO_STEP_PREFIX, iter_step_definition_matches
from pytest_cuke.model import StepType
from pytest_cuke.scenario_locator import FileScenarioLocator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pytest_cuke.compatibility.pytest import Config, ExitCode, Session
    from pytest_cuke.model import Feature, Pickle


@dataclass(frozen=True)
class MissingScenarioBindingEvent:
    feature: str
    scenario: str
    line: int | None
    type: Literal["missing_scenario_binding"] = "missing_scenario_binding"


@dataclass(frozen=True)
class MissingStepDefinitionEvent:
    feature: str
    scenario: str
    keyword: str
    text: str
    line: int | None
    type: Literal["missing_step_definition"] = "missing_step_definition"


CodeGenerationEvent = MissingScenarioBindingEvent | MissingStepDefinitionEvent


def _feature_path(feature: Feature) -> str:
    return str(Path(feature.filename or feature.rel_filename).resolve())


def _collect_events(session: Session, features: Sequence[Feature]) -> list[CodeGenerationEvent]:
    selected_paths = {_feature_path(feature) for feature in features}
    seen: set[tuple[str, str]] = set()
    missing_steps: list[CodeGenerationEvent] = []
    for item in session.items:
        if not {"feature", "scenario"}.issubset(getattr(item, "fixturenames", ())):
            continue
        _inspect_item(item, selected_paths, seen, missing_steps)

    events: list[CodeGenerationEvent] = [
        MissingScenarioBindingEvent(
            feature=_feature_path(feature), scenario=scenario.name, line=feature._get_pickle_line_number(scenario)
        )
        for feature in features
        for scenario in feature.pickles
        if (_feature_path(feature), scenario.name) not in seen
    ]
    return events + missing_steps


def _inspect_item(
    item: Any,
    selected_paths: set[str],
    seen: set[tuple[str, str]],
    missing_steps: list[CodeGenerationEvent],
) -> None:
    setup_state = item.session._setupstate
    try:
        setup_name = "setup" if PYTEST7 else "prepare"
        getattr(setup_state, setup_name)(item)
        request = item._request
        feature = cast("Feature", request.getfixturevalue("feature"))
        scenario = cast("Pickle", request.getfixturevalue("scenario"))
        feature_path = _feature_path(feature)
        if feature_path not in selected_paths:
            return
        seen.add((feature_path, scenario.name))
        for match in iter_step_definition_matches(request, feature, scenario):
            if not match.matched:
                step = match.step
                missing_steps.append(
                    MissingStepDefinitionEvent(
                        feature=feature_path,
                        scenario=scenario.name,
                        keyword=STEP_TYPE_TO_STEP_PREFIX[StepType(step.type or StepType.unknown)],
                        text=step.text,
                        line=feature._get_step_line_number(step),
                    )
                )
    finally:
        if PYTEST7:
            setup_state.teardown_exact(None)
        else:
            setup_state.teardown_exact(item, None)


def gather_and_print_missing_events(config: Config, feature_paths: Sequence[Path]) -> int | ExitCode:
    """Inspect bindings and definitions without entering the test call phase."""
    if not feature_paths:
        print("The --cuke-feature parameter is required.", file=sys.stderr)
        return 100

    events: list[CodeGenerationEvent] = []

    def collect(config: Config, session: Session) -> int:
        features = list(
            FileScenarioLocator(feature_paths=[path.resolve() for path in feature_paths]).resolve_features(config)
        )
        config.hook.pytest_collection(session=session)
        if session.testsfailed:
            return 2
        events.extend(_collect_events(session, features))
        return 100 if events else 0

    captured_stdout = StringIO()
    try:
        with redirect_stdout(captured_stdout):
            exit_status = wrap_session(config=config, doit=collect)
    except Exception:
        print(captured_stdout.getvalue(), end="", file=sys.stderr)
        raise
    if int(exit_status) not in {0, 100}:
        print(captured_stdout.getvalue(), end="", file=sys.stderr)
        return exit_status
    for event in events:
        print(json.dumps(asdict(event), sort_keys=True))
    return exit_status
