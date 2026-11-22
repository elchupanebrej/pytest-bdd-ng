from pytest_cuke.const import (
    PYTEST_OUTCOME_MEDIA_TYPE,
    PYTEST_SOURCE_MEDIA_TYPE,
    PYTEST_STEP_OUTCOME_MEDIA_TYPE,
)
from pytest_cuke.model.message_extension import (
    PYTEST_OUTCOME_MEDIA_TYPE as RE_EXPORTED_OUTCOME,
    PYTEST_SOURCE_MEDIA_TYPE as RE_EXPORTED_SOURCE,
    PYTEST_STEP_OUTCOME_MEDIA_TYPE as RE_EXPORTED_STEP_OUTCOME,
    REFERENCE_MEDIA_TYPE,
    external_attachment_reference,
)
from pytest_cuke.model.message_types import Envelope, ExternalAttachment, Timestamp


def test_media_type_constants_remain_importable_from_message_extension():
    assert RE_EXPORTED_OUTCOME == PYTEST_OUTCOME_MEDIA_TYPE
    assert RE_EXPORTED_STEP_OUTCOME == PYTEST_STEP_OUTCOME_MEDIA_TYPE
    assert RE_EXPORTED_SOURCE == PYTEST_SOURCE_MEDIA_TYPE


def _external(url: str, name: str | None = None) -> Envelope:
    return Envelope(
        external_attachment=ExternalAttachment(
            media_type="video/mp4",
            url=url,
            test_case_started_id=name,
            test_step_id="step-1",
            timestamp=Timestamp(seconds=1, nanos=0),
        )
    )


def test_external_attachment_becomes_a_link_only_attachment():
    envelope = external_attachment_reference(_external("https://example.invalid/video/clip.mp4", "attempt-1"))

    assert envelope.external_attachment is None
    assert envelope.attachment is not None
    assert envelope.attachment.body == "https://example.invalid/video/clip.mp4"
    assert envelope.attachment.media_type == REFERENCE_MEDIA_TYPE
    assert envelope.attachment.file_name == "clip.mp4"
    assert envelope.attachment.test_case_started_id == "attempt-1"
    assert envelope.attachment.test_step_id == "step-1"


def test_external_attachment_without_path_gets_a_safe_name():
    envelope = external_attachment_reference(_external("https://example.invalid"))

    assert envelope.attachment.file_name == "external-attachment.txt"


def test_regular_envelopes_are_unchanged():
    envelope = Envelope()

    assert external_attachment_reference(envelope) is envelope
