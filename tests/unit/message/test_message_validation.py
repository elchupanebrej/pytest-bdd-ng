from __future__ import annotations

from pytest_cuke.model import message_types as messages
import pytest

from pytest_cuke.model.background import Background
from pytest_cuke.model.feature import Feature
from pytest_cuke.model.message_converter import (
    feature_to_envelope,
    make_test_case_finished,
    make_test_case_started,
    make_test_run_finished,
    make_test_run_started,
    make_test_step_finished,
    make_test_step_started,
    pickle_to_envelope,
    scenario_to_pickle,
    scenario_to_test_case,
    test_case_to_envelope as convert_test_case_to_envelope,
)
from pytest_cuke.model.message_stream_validation import MessageStreamValidator
from pytest_cuke.model.message_validation import (
    MessageValidationDiagnostic,
    MessageValidationError,
    message_diagnostic_to_dict,
    validate_envelope,
)
from pytest_cuke.model.scenario import Scenario
from pytest_cuke.model.step import Step


def _fixture_messages() -> tuple[messages.Envelope, ...]:
    step = Step(name="ready", keyword="Given ", line=2, id="step-1")
    scenario = Scenario(name="Run", keyword="Scenario", line=3, id="scenario-1", steps=(step,))
    feature = Feature(
        name="Validation",
        line=1,
        id="feature-1",
        background=Background(line=1),
        scenarios=(scenario,),
    )
    pickle = scenario_to_pickle(scenario, uri="features/validation.feature", default_id="pickle-1")
    test_case = scenario_to_test_case(scenario, pickle_id=pickle.id, default_id="case-1")
    return (
        feature_to_envelope(feature, uri="features/validation.feature"),
        pickle_to_envelope(pickle),
        convert_test_case_to_envelope(test_case),
        make_test_run_started(100.0),
        make_test_case_started(test_case_id=test_case.id, id="attempt-1", timestamp=101.0),
        make_test_step_started("attempt-1", test_step_id="scenario-1-step-0", timestamp=101.1),
        make_test_step_finished("attempt-1", "scenario-1-step-0", timestamp=101.2),
        make_test_case_finished("attempt-1", timestamp=101.3),
        make_test_run_finished(timestamp=102.0),
    )


def test_validate_envelope_requires_exactly_one_payload() -> None:
    empty = messages.Envelope()
    multiple = messages.Envelope(
        test_run_started=messages.TestRunStarted(timestamp=messages.Timestamp(seconds=1, nanos=0)),
        test_run_finished=messages.TestRunFinished(
            success=True,
            timestamp=messages.Timestamp(seconds=2, nanos=0),
        ),
    )

    empty_diagnostics = validate_envelope(empty)
    multiple_diagnostics = validate_envelope(multiple, position=4)

    assert [item.code for item in empty_diagnostics] == ["INVALID_PAYLOAD_SHAPE"]
    assert empty_diagnostics[0].payload_kind is None
    assert multiple_diagnostics[0].code == "INVALID_PAYLOAD_SHAPE"
    assert multiple_diagnostics[0].position == 4


def test_validate_envelope_uses_official_schema_and_reports_instance_path() -> None:
    timestamp = messages.Timestamp(seconds=1, nanos=0)
    finish = messages.TestRunFinished(success=True, timestamp=timestamp)
    finish.success = "not-a-boolean"  # type: ignore[assignment]
    envelope = messages.Envelope(test_run_finished=finish)

    diagnostics = validate_envelope(envelope)

    assert diagnostics
    assert all(item.code == "SCHEMA_VALIDATION_ERROR" for item in diagnostics)
    assert diagnostics[0].instance_path == ("testRunFinished", "success")


def test_validate_envelope_checks_meta_protocol_against_pinned_release() -> None:
    product = messages.Product(name="pytest-cuke", version="2.3.1")
    supported = messages.Envelope(
        meta=messages.Meta(
            protocol_version="28.0.0",
            implementation=product,
            runtime=product,
            os=product,
            cpu=product,
        )
    )
    unsupported = messages.Envelope(
        meta=messages.Meta(
            protocol_version="28.0.1",
            implementation=product,
            runtime=product,
            os=product,
            cpu=product,
        )
    )

    assert validate_envelope(supported) == ()
    diagnostics = validate_envelope(unsupported)
    assert [item.code for item in diagnostics] == ["UNSUPPORTED_PROTOCOL_VERSION"]
    assert diagnostics[0].instance_path == ("meta", "protocolVersion")


def test_stream_validator_accepts_a_schema_valid_completed_run() -> None:
    validator = MessageStreamValidator()

    for envelope in _fixture_messages():
        validator.accept(envelope)

    assert validator.finish() == ()
    assert validator.diagnostics == ()


def test_stream_validator_rejects_orphan_case_before_accepting_it() -> None:
    validator = MessageStreamValidator()
    validator.accept(make_test_run_started(100.0))

    with pytest.raises(MessageValidationError) as captured:
        validator.accept(make_test_case_started(test_case_id="missing-case", id="attempt-1"))

    diagnostic = captured.value.diagnostics[0]
    assert diagnostic.code == "ORPHAN_REFERENCE"
    assert diagnostic.position == 1
    assert diagnostic.offending_ids == ("missing-case",)
    assert validator.diagnostics == captured.value.diagnostics


def test_attachment_step_reference_must_belong_to_its_case_attempt() -> None:
    validator = MessageStreamValidator()
    messages_in = _fixture_messages()
    for envelope in messages_in[:4]:
        validator.accept(envelope)

    other_step = Step(name="other", keyword="Given ", line=2, id="other-step")
    other_scenario = Scenario(
        name="Other",
        keyword="Scenario",
        line=3,
        id="other-scenario",
        steps=(other_step,),
    )
    other_pickle = scenario_to_pickle(other_scenario, uri="features/other.feature", default_id="other-pickle")
    other_case = scenario_to_test_case(other_scenario, pickle_id=other_pickle.id, default_id="other-case")
    validator.accept(pickle_to_envelope(other_pickle))
    validator.accept(convert_test_case_to_envelope(other_case))
    validator.accept(messages_in[4])
    validator.accept(make_test_case_started(test_case_id=other_case.id, id="other-attempt", timestamp=101.0))

    with pytest.raises(MessageValidationError) as captured:
        validator.accept(
            messages.Envelope(
                attachment=messages.Attachment(
                    body="cross-case-step",
                    content_encoding=messages.ContentEncoding.identity,
                    media_type="text/plain",
                    test_case_started_id="attempt-1",
                    test_step_id=other_case.test_steps[0].id,
                )
            )
        )

    diagnostic = captured.value.diagnostics[0]
    assert diagnostic.code == "ORPHAN_REFERENCE"
    assert diagnostic.offending_ids == ("attempt-1", other_case.test_steps[0].id)
    assert diagnostic.instance_path == ("testStepId",)


def test_message_diagnostic_serialization_encodes_json_pointer_components() -> None:
    diagnostic = MessageValidationDiagnostic(
        code="SCHEMA_VALIDATION_ERROR",
        severity="error",
        position=7,
        payload_kind="test_run_started",
        message="invalid timestamp",
        offending_ids=("run-1",),
        instance_path=("testRunStarted", "a/b~c"),
    )

    assert message_diagnostic_to_dict(diagnostic) == {
        "code": "SCHEMA_VALIDATION_ERROR",
        "severity": "error",
        "position": 7,
        "payload_kind": "test_run_started",
        "message": "invalid timestamp",
        "offending_ids": ["run-1"],
        "instance_path": "/testRunStarted/a~1b~0c",
    }


def test_stream_validator_rejects_duplicate_case_attempt_ids() -> None:
    validator = MessageStreamValidator()
    messages_in = _fixture_messages()
    for envelope in messages_in[:4]:
        validator.accept(envelope)
    validator.accept(messages_in[4])

    with pytest.raises(MessageValidationError) as captured:
        validator.accept(messages_in[4])

    assert captured.value.diagnostics[0].code == "DUPLICATE_LIFECYCLE_ID"
    assert captured.value.diagnostics[0].offending_ids == ("attempt-1",)


def test_finish_reports_open_run_case_and_step_starts() -> None:
    validator = MessageStreamValidator()
    messages_in = _fixture_messages()
    for envelope in messages_in[:6]:
        validator.accept(envelope)

    diagnostics = validator.finish()

    assert [item.code for item in diagnostics] == [
        "INCOMPLETE_LIFECYCLE",
        "INCOMPLETE_LIFECYCLE",
        "INCOMPLETE_LIFECYCLE",
    ]
    assert {item.payload_kind for item in diagnostics} == {
        "test_run_started",
        "test_case_started",
        "test_step_started",
    }
    assert [item.position for item in diagnostics] == [6, 6, 6]
    assert validator.finish() == diagnostics


def test_test_case_hook_reference_must_resolve_before_acceptance() -> None:
    validator = MessageStreamValidator()
    pickle = messages.Pickle(
        id="pickle-1",
        uri="features/hook.feature",
        name="hook case",
        language="en",
        steps=[],
        tags=[],
        ast_node_ids=["ast-1"],
    )
    validator.accept(pickle_to_envelope(pickle))
    test_case = messages.TestCase(
        id="case-1",
        pickle_id="pickle-1",
        test_steps=[messages.TestStep(id="test-step-1", hook_id="missing-hook")],
    )

    with pytest.raises(MessageValidationError) as captured:
        validator.accept(convert_test_case_to_envelope(test_case))

    diagnostic = captured.value.diagnostics[0]
    assert diagnostic.code == "ORPHAN_REFERENCE"
    assert diagnostic.offending_ids == ("missing-hook",)
