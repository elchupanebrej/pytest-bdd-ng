import json

import pytest

from pytest_cuke.message_capability_governance_cli import main as capability_main
from pytest_cuke.model.message_stream_validation import MessageStreamValidator
from pytest_cuke.model.message_types import (
    Attachment,
    ContentEncoding,
    Envelope,
    ExternalAttachment,
    Pickle,
    PickleStep,
    Snippet,
    Suggestion,
    message_from_dict,
    message_to_dict,
)
from pytest_cuke.model.message_validation import MessageValidationError, validate_envelope, validate_envelope_data


def test_suggestion_round_trips_official_wire_names() -> None:
    message = Envelope(
        suggestion=Suggestion(
            id="suggestion-1",
            pickle_step_id="step-1",
            snippets=[Snippet(code="def missing_step():\n    pass\n", language="python")],
        )
    )
    wire = message_to_dict(message)
    assert wire == {
        "suggestion": {
            "id": "suggestion-1",
            "pickleStepId": "step-1",
            "snippets": [{"code": "def missing_step():\n    pass\n", "language": "python"}],
        }
    }
    restored = message_from_dict(wire)
    assert restored == message
    assert isinstance(restored.suggestion, Suggestion)
    assert isinstance(restored.suggestion.snippets[0], Snippet)
    assert validate_envelope(message) == ()


def test_external_attachment_round_trips_official_wire_names() -> None:
    message = Envelope(
        external_attachment=ExternalAttachment(
            media_type="text/plain",
            url="https://example.invalid/log.txt",
            test_case_started_id="attempt-1",
            test_step_id="test-step-1",
        )
    )
    wire = message_to_dict(message)
    assert wire == {
        "externalAttachment": {
            "mediaType": "text/plain",
            "url": "https://example.invalid/log.txt",
            "testCaseStartedId": "attempt-1",
            "testStepId": "test-step-1",
        }
    }
    restored = message_from_dict(wire)
    assert restored == message
    assert isinstance(restored.external_attachment, ExternalAttachment)
    assert validate_envelope(message) == ()


def test_latest_schema_rejects_a_snippet_without_its_language() -> None:
    errors = validate_envelope_data(
        {
            "suggestion": {
                "id": "suggestion-1",
                "pickleStepId": "step-1",
                "snippets": [{"code": "def missing_step():\n    pass\n"}],
            }
        }
    )
    assert any(error.code == "SCHEMA_VALIDATION_ERROR" and error.payload_kind == "suggestion" for error in errors)


def test_capability_cli_uses_the_schema_version_instead_of_the_binding_version(tmp_path):
    destination = tmp_path / "capabilities.json"
    assert capability_main(["sync", "--baseline-release", "34.2.1", "--output", str(destination)]) == 0
    inventory = json.loads(destination.read_text())
    assert inventory["baseline_release"] == "34.2.1"
    assert {row["baseline_release"] for row in inventory["capabilities"]} == {"34.2.1"}
    ids = {row["capability_id"] for row in inventory["capabilities"]}
    assert {"suggestion.snippets.language", "external_attachment.url", "pickle.location.column"} <= ids


def test_capability_cli_rejects_a_binding_version_as_the_installed_schema_baseline(tmp_path):
    destination = tmp_path / "wrong-baseline.json"
    assert capability_main(["sync", "--baseline-release", "34.2.0", "--output", str(destination)]) == 2
    assert not destination.exists()


@pytest.mark.parametrize(
    "message",
    [
        Envelope(
            attachment=Attachment(
                body="log",
                content_encoding=ContentEncoding.identity,
                media_type="text/plain",
                test_case_started_id="missing-case",
            )
        ),
        Envelope(
            external_attachment=ExternalAttachment(
                media_type="text/plain", url="https://example.invalid/log", test_case_started_id="missing-case"
            )
        ),
    ],
)
def test_attachment_kinds_both_reject_orphan_correlations(message):
    with pytest.raises(MessageValidationError, match="unknown test_case_started"):
        MessageStreamValidator().accept(message)


def test_suggestion_requires_a_declared_pickle_step():
    message = Envelope(
        suggestion=Suggestion(
            id="suggestion-1", pickle_step_id="missing-step", snippets=[Snippet(code="pass", language="python")]
        )
    )
    with pytest.raises(MessageValidationError, match="unknown pickle_step"):
        MessageStreamValidator().accept(message)


def test_suggestion_ids_are_unique_within_the_stream():
    validator = MessageStreamValidator()
    validator.accept(
        Envelope(
            pickle=Pickle(
                ast_node_ids=["scenario-ast"],
                id="pickle-1",
                language="en",
                name="scenario",
                steps=[PickleStep(ast_node_ids=["step-ast"], id="step-1", text="missing")],
                tags=[],
                uri="features/example.feature",
            )
        )
    )
    message = Envelope(
        suggestion=Suggestion(
            id="suggestion-1", pickle_step_id="step-1", snippets=[Snippet(code="pass", language="python")]
        )
    )
    assert validator.accept(message) == message
    with pytest.raises(MessageValidationError, match="duplicate suggestion"):
        validator.accept(message)
