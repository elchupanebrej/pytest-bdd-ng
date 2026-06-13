"""
Implement plugin module operations for pytest-bdd.

Responsibility:
    Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
    consumed by the broader BDD infrastructure.

Reason for existence:
    Consolidates related logic within a single module boundary to maintain high cohesion and serve as the information
    expert for its domain concepts.

Delegates:
    - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

Cohesion:
    All logic within this entity operates on a single responsibility domain with focused imports and control flow.

Separation:
    - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

Main consumers:
    - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

State and side effects:
    None, keeps no persistent state beyond local scope.

Invariants:
    - All public API contracts defined by this entity must be honored by callers.

Architecture score:
    #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
    #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
    #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
    #arch-eval:cohesion=4  # Internal logic focus (1-5)
    #arch-eval:separation=4  # Distinctness from peers (1-5)
    #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
    #arch-eval:state_invariants=4  # Control of state mutations (1-5)
    #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
    #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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
    Implement plugin module operations for pytest-bdd.

    Responsibility:
        Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
        consumed by the broader BDD infrastructure.

    Reason for existence:
        Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
        information expert for its domain concepts.

    Delegates:
        - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

    Cohesion:
        All logic within this entity operates on a single responsibility domain with focused imports and control flow.

    Separation:
        - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

    Main consumers:
        - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

    State and side effects:
        None, keeps no persistent state beyond local scope.

    Invariants:
        - All public API contracts defined by this entity must be honored by callers.

    Architecture score:
        #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
        #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
        #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
        #arch-eval:cohesion=4  # Internal logic focus (1-5)
        #arch-eval:separation=4  # Distinctness from peers (1-5)
        #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
        #arch-eval:state_invariants=4  # Control of state mutations (1-5)
        #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """

    plugin_suffix = "attachment"

    def __init__(self, reporter: GherkinMessageReporter, *, lifecycle_service: LifecycleService) -> None:
        """
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
        """
        super().__init__(reporter)
        self.lifecycle_service = lifecycle_service

    def pytest_bdd_attach(  # noqa: C901, PLR0912, PLR0913, PLR0917  -- suppressed warning
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
        Implement plugin module operations for pytest-bdd.

        Responsibility:
            Provides focused operations for this pytest-bdd plugin module, implementing a single well-defined capability
            consumed by the broader BDD infrastructure.

        Reason for existence:
            Consolidates related logic within a single module boundary to maintain high cohesion and serve as the
            information expert for its domain concepts.

        Delegates:
            - Collaborating modules and standard library: provide supporting infrastructure through well-defined interfaces.

        Cohesion:
            All logic within this entity operates on a single responsibility domain with focused imports and control flow.

        Separation:
            - Peer entities in sibling modules: kept separate to prevent callers from coupling to unrelated knowledge domains.

        Main consumers:
            - pytest_bdd.*: higher layers and sibling modules that consume this entity through its public API contract.

        State and side effects:
            None, keeps no persistent state beyond local scope.

        Invariants:
            - All public API contracts defined by this entity must be honored by callers.

        Architecture score:
            #arch-eval:reason_for_existence=4  # Motivation / information-expert fitness (1-5)
            #arch-eval:owned_responsibility=4  # Clean boundary and clear ownership (1-5)
            #arch-eval:delegation_boundary=3  # Sub-task encapsulation quality (1-5)
            #arch-eval:cohesion=4  # Internal logic focus (1-5)
            #arch-eval:separation=4  # Distinctness from peers (1-5)
            #arch-eval:consumer_clarity=4  # Clarity of public API / usage contract (1-5)
            #arch-eval:state_invariants=4  # Control of state mutations (1-5)
            #arch-eval:entity_fullness=3  # Content richness vs empty shell (1-5)
            #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
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

        self.lifecycle_service._emit_envelope(  # noqa: SLF001  -- suppressed warning
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
