"""Provide attachment runtime helpers."""

from __future__ import annotations

from base64 import b64encode
from io import BufferedIOBase, TextIOBase
from typing import TYPE_CHECKING

from cucumber_messages import Attachment, AttachmentContentEncoding, ExternalAttachment, Source
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]

from pytest_bdd.model.run import Run
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import FixtureRequest
    from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime import LifecycleService
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter


class AttachmentService(ReporterServiceBase):
    """Represent attachment service state."""

    plugin_suffix = "attachment"

    def __init__(self, reporter: GherkinMessageReporter, *, lifecycle_service: LifecycleService) -> None:
        """Initialize the attachment service."""
        super().__init__(reporter)
        self.lifecycle_service = lifecycle_service

    def pytest_bdd_attach(  # noqa: C901, PLR0912, PLR0913, PLR0917
        self,
        request: FixtureRequest,
        attachment: str | bytes | bytearray | BufferedIOBase | TextIOBase | object,
        media_type: str | None,
        file_name: str | None,
        source_data: str | None,
        source_media_type: str | None,
        source_uri: str | None,
        url: str | None,
        as_external: bool,  # noqa: FBT001 -- pytest hook spec supplies this as a positional argument.
        test_run_hook_started_id: str | None,
        test_run_started_id: str | None,
    ) -> None:
        """Handle the pytest bdd attach pytest hook."""
        if self.reporter.is_disabled:
            return
        config = request.config
        run = Run.find_in_stash(config.stash).value_or(None)
        reporting_state = run.reporting_state if run is not None else None
        test_case_started_id = reporting_state.active_test_case_started_id if reporting_state is not None else None
        active_test_step_id = reporting_state.active_test_step_id if reporting_state is not None else None
        attachment_timestamp = self.lifecycle_service.get_timestamp()
        effective_test_run_hook_started_id = test_run_hook_started_id or (
            run.reporting_state.test_run_hook_started_id if run is not None else None
        )
        effective_test_run_started_id = test_run_started_id or (
            run.reporting_state.run_started_id if run is not None else None
        )

        if isinstance(attachment, (str, TextIOBase)):
            content_encoding = AttachmentContentEncoding.identity
            media_type_ = "text/plain;charset=UTF-8" if media_type is None else media_type
        elif isinstance(attachment, (bytes, bytearray, BufferedIOBase)):
            content_encoding = AttachmentContentEncoding.base64
            media_type_ = "application/octet-stream" if media_type is None else media_type
        else:
            content_encoding = AttachmentContentEncoding.identity
            media_type_ = "text/plain;charset=UTF-8" if media_type is None else media_type

        if isinstance(attachment, str):
            body = attachment
        elif isinstance(attachment, TextIOBase):
            body = attachment.read()
        elif isinstance(attachment, (bytes, bytearray, BufferedIOBase)):
            if isinstance(attachment, bytes):
                body_bytes = attachment
            elif isinstance(attachment, bytearray):
                body_bytes = bytes(attachment)
            elif isinstance(attachment, BufferedIOBase):
                body_bytes = attachment.read()
            else:  # pragma: no cover
                body_bytes = b""

            body = b64encode(body_bytes).decode("ascii")
        else:
            body = str(attachment)

        source = None
        if source_data is not None and source_media_type is not None and source_uri is not None:
            source = Source(
                data=str(source_data),
                media_type=source_media_type,
                uri=source_uri,
            )
        attachment_url = url

        self.lifecycle_service._emit_envelope(  # noqa: SLF001
            config,
            Message(
                attachment=Attachment(
                    **({"test_step_id": active_test_step_id} if active_test_step_id is not None else {}),
                    **({"test_case_started_id": test_case_started_id} if test_case_started_id is not None else {}),
                    **(
                        {"test_run_hook_started_id": effective_test_run_hook_started_id}
                        if effective_test_run_hook_started_id is not None
                        else {}
                    ),
                    **(
                        {"test_run_started_id": effective_test_run_started_id}
                        if effective_test_run_started_id is not None
                        else {}
                    ),
                    media_type=media_type_,
                    **({"file_name": str(file_name)} if file_name is not None else {}),
                    **({"source": source} if source is not None else {}),
                    **({"url": attachment_url} if attachment_url is not None else {}),
                    timestamp=attachment_timestamp,
                    content_encoding=content_encoding,
                    body=body,
                ),
            ),
        )

        if as_external and attachment_url is not None:
            external_media_type = media_type_ or "application/octet-stream"
            self.lifecycle_service._emit_envelope(  # noqa: SLF001
                config,
                Message(
                    external_attachment=ExternalAttachment(
                        media_type=external_media_type,
                        url=attachment_url,
                        **({"test_case_started_id": test_case_started_id} if test_case_started_id is not None else {}),
                        **({"test_step_id": active_test_step_id} if active_test_step_id is not None else {}),
                        **(
                            {"test_run_hook_started_id": effective_test_run_hook_started_id}
                            if effective_test_run_hook_started_id is not None
                            else {}
                        ),
                        timestamp=attachment_timestamp,
                    ),
                ),
            )
