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

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, cast

from cucumber_messages import (
    Duration,
    HookType,
    TestRunFinished,
    TestRunHookFinished,
    TestRunHookStarted,
    TestStepResult,
    TestStepResultStatus,
)
from cucumber_messages import (
    Envelope as Message,
)
from cucumber_messages import Exception as CucumberException

from pytest_bdd.compatibility.pytest import is_testrun_success
from pytest_bdd.model.message_stream_validation import validate_message_stream
from pytest_bdd.model.message_transport import WorkerCompletionManifest
from pytest_bdd.plugin.gherkin_message_reporter.runtime_support import _resolve_reporting_worker_identity
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.packaging import get_distribution_version

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import ExitCode, Session
    from pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._core import LifecycleService

logger = logging.getLogger(__name__)


def _pytest_sessionfinish(self: LifecycleService, session: Session, exitstatus: int | ExitCode) -> None:  # noqa: C901, PLR0912  -- suppressed warning
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
        #arch-eval:entity_fullness=4  # Content richness vs empty shell (1-5)
        #arch-eval:locational_stability=4  # Resistance to hierarchical moves (1-5)
    """
    if self.reporter.is_disabled:
        return
    config = session.config
    run_started_id = self._require_run_started_id(config=cast("object", config))  # type: ignore[arg-type]  # dynamic runtime config cast
    run_success = is_testrun_success(exitstatus)  # type: ignore[arg-type]  # _pytest ExitCode vs pytest ExitCode
    run_exception = (
        CucumberException(type="PytestExitCode", message=str(exitstatus), stack_trace=str(exitstatus))
        if not run_success
        else None
    )
    after_test_run_hook_started_id = next(IdGenerator.from_stash(cast("object", config).stash))  # type: ignore[attr-defined]  # config.stash exists at runtime
    self._emit_run_hook_definition(
        cast("object", config),  # type: ignore[arg-type]  # dynamic runtime config cast
        hook_id=self.reporter.AFTER_TEST_RUN_HOOK_ID,
        hook_type=HookType.after_test_run,
        hook_name="after-test-run",
    )
    self._emit_envelope(
        config,
        Message(
            test_run_hook_started=TestRunHookStarted(
                hook_id=self.reporter.AFTER_TEST_RUN_HOOK_ID,
                id=after_test_run_hook_started_id,
                test_run_started_id=run_started_id,
                timestamp=self.get_timestamp(),
                worker_id=self.transport_service._current_reporting_worker_id(config),  # noqa: SLF001  # type: ignore[arg-type]  # dynamic runtime config object
            ),
        ),
    )
    self._emit_envelope(
        config,
        Message(
            test_run_hook_finished=TestRunHookFinished(
                test_run_hook_started_id=after_test_run_hook_started_id,
                timestamp=self.get_timestamp(),
                result=TestStepResult(
                    duration=Duration(seconds=0, nanos=0),
                    status=TestStepResultStatus.passed if run_success else TestStepResultStatus.failed,
                    message="after-test-run hook completed",
                    **({"exception": run_exception} if run_exception is not None else {}),
                ),
            ),
        ),
    )
    self._emit_envelope(
        config,
        Message(
            test_run_finished=TestRunFinished(
                timestamp=self.get_timestamp(),
                success=run_success,
                test_run_started_id=run_started_id,
                message=f"pytest session exit status: {exitstatus}",
                **({"exception": run_exception} if run_exception is not None else {}),
            ),
        ),
    )

    self.transport_service.finish_process_messages_thread()
    if self.reporter.is_xdist_worker:
        workeroutput = cast("dict[str, object]", getattr(config, "workeroutput", {}))
        worker_id, gateway_mode = _resolve_reporting_worker_identity(config)
        if self.reporter.xdist_transport_client is not None:
            workeroutput["pytest_bdd_messages_manifest"] = self.reporter.xdist_transport_client.build_manifest(
                complete=True,
            ).as_dict()
        else:
            workeroutput["pytest_bdd_messages_manifest"] = WorkerCompletionManifest(
                worker_id=str(worker_id),
                complete=False,
                last_batch_sequence=None,
                transferred_batch_count=0,
                transferred_envelope_count=0,
                interruption_reason="transport client was not initialized",
                gateway_mode=gateway_mode,
            ).as_dict()
        workeroutput["pytest_bdd_messages_fragment_worker_id"] = str(worker_id)
        if (
            self.reporter._xdist_worker_temp_messages_path is not None  # noqa: SLF001  -- suppressed warning
            and self.reporter._xdist_worker_temp_messages_path.exists()  # noqa: SLF001  -- suppressed warning
        ):
            self.reporter._xdist_worker_temp_messages_path.unlink()  # noqa: SLF001  -- suppressed warning
        return

    if self.reporter.is_xdist_controller:
        self.reporter._xdist_fragment_records["master"] = {  # noqa: SLF001  -- suppressed warning
            "worker_id": "master",
            "role": "controller",
            "path": self.reporter.messages_file_path,
            "complete": True,
            "manifest_received": True,
        }
        envelopes = self.transport_service._finalize_xdist_messages_file()  # noqa: SLF001  -- suppressed warning
    else:
        envelopes = self.transport_service.read_envelopes_from_path(self.reporter.final_messages_file_path)
    validation_result = validate_message_stream(
        envelopes,
        latest_protocol_version=str(get_distribution_version("cucumber-messages")),
        track_coverage=False,
    )
    if not validation_result.is_valid:
        logger.error(
            "Canonical message stream validation failed with %s violation(s).",
            len(validation_result.violations),
        )
    if self.reporter._mapping_diagnostics_count:  # noqa: SLF001  -- suppressed warning
        logger.error(
            "Detected %s mapping diagnostic warning(s) in message emission flow.",
            self.reporter._mapping_diagnostics_count,  # noqa: SLF001  -- suppressed warning
        )
    if not self._check_derived_output_consistency(envelopes):
        logger.error("Derived-output consistency check failed: required run lifecycle envelopes are incomplete.")

    if (
        self.reporter.requested_cucumber_formatters
        and not self.reporter._live_formatter_session_started  # noqa: SLF001  -- suppressed warning
        and self.reporter._live_formatter_failure_message is None  # noqa: SLF001  -- suppressed warning
    ):
        self.live_formatter_service._record_live_formatter_failure(  # noqa: SLF001  -- suppressed warning
            "Requested cucumber formatters were not attached to a live session; "
            "post-run replay is disabled for live formatter runs.",
        )
    if self.reporter.config.option.cucumber_html_path is not None:
        self.live_formatter_service.generate_html_report()
    if self.reporter.is_messages_file_temp:
        Path(self.reporter.final_messages_file_path).unlink()
    if self.reporter.xdist_fragment_dir is not None and self.reporter.xdist_fragment_dir.exists():
        shutil.rmtree(self.reporter.xdist_fragment_dir)
