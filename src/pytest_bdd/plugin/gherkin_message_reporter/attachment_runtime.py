"""
Provide attachment runtime helpers.

Responsibility:
    Provide attachment runtime helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime` because it
    keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - AttachmentService: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `attachment_runtime`
    - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `attachment_runtime`

State and side effects:
    mutates body, body_bytes, content_encoding, media_type_, source; depends on __future__.annotations,
    base64.b64encode, io.BufferedIOBase, io.TextIOBase, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=3
"""

from __future__ import annotations

from base64 import b64encode
from io import BufferedIOBase, TextIOBase
from typing import TYPE_CHECKING

from cucumber_messages import Attachment, AttachmentContentEncoding, Source
from cucumber_messages import (
    Envelope as Message,  # upstream type stubs missing this attribute
)

from pytest_bdd.model.run import Run
from pytest_bdd.plugin.gherkin_message_reporter.service_base import ReporterServiceBase

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import FixtureRequest
    from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime import LifecycleService
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter


class AttachmentService(ReporterServiceBase):
    """
    Represent attachment service state.

    Responsibility:
        Represent attachment service state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime.AttachmentService` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - __init__: owns nested behavior below this boundary
        - pytest_bdd_attach: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `AttachmentService`
        - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references `AttachmentService`

    State and side effects:
        mutates body, body_bytes, content_encoding, media_type_, source.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime.AttachmentService` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """

    plugin_suffix = "attachment"

    def __init__(self, reporter: GherkinMessageReporter, *, lifecycle_service: LifecycleService) -> None:
        """
        Initialize the attachment service.

        Responsibility:
            Initialize the attachment service. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime.AttachmentService.__init__` because it keeps
            the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - super.__init__: collaborator call used by this boundary
            - super: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/_gherkin_go/_types.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/plugin_patterns.py: imports or references `__init__`
            - src/pytest_bdd/_pylint/checkers/quality_gates.py: imports or references `__init__`
            - src/pytest_bdd/model/message_extension.py: imports or references `__init__`

        State and side effects:
            mutates self.lifecycle_service.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime.AttachmentService.__init__` keeps its
              documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
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
        as_external: bool,  # noqa: FBT001, ARG002 -- pytest hook spec supplies this as a positional argument.
        test_run_hook_started_id: str | None,
        test_run_started_id: str | None,
    ) -> None:
        """
        Handle the pytest bdd attach pytest hook.

        Responsibility:
            Handle the pytest bdd attach pytest hook. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime.AttachmentService.pytest_bdd_attach` because
            it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - isinstance: collaborator call used by this boundary
            - str: collaborator call used by this boundary
            - attachment.read: collaborator call used by this boundary
            - Run.find_in_stash.value_or: collaborator call used by this boundary
            - Run.find_in_stash: collaborator call used by this boundary
            - self.lifecycle_service.get_timestamp: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `pytest_bdd_attach`
            - src/pytest_bdd/plugin/gherkin_message_reporter/runtime_assembly.py: imports or references
              `pytest_bdd_attach`
            - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `pytest_bdd_attach`

        State and side effects:
            mutates body, body_bytes, content_encoding, media_type_, source.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.attachment_runtime.AttachmentService.pytest_bdd_attach` keeps
              its documented import path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=4
        """
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
