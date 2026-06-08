"""
Pytest hook implementations for the lifecycle runtime — session management.

Responsibility:
    Pytest hook implementations for the lifecycle runtime — session management. It directly owns the observable
    contract, local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._hooks`
    because it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _pytest_sessionfinish: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates envelopes, logger, config, run_started_id, run_success; depends on __future__.annotations, logging, shutil,
    pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._hooks` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=2
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


def _pytest_sessionfinish(self: LifecycleService, session: Session, exitstatus: int | ExitCode) -> None:  # noqa: C901, PLR0912
    """
    Handle the pytest sessionfinish pytest hook.

    Responsibility:
        Handle the pytest sessionfinish pytest hook. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._hooks._pytest_sessionfinish` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - self._emit_envelope: collaborator call used by this boundary
        - Message: collaborator call used by this boundary
        - self.get_timestamp: collaborator call used by this boundary
        - logger.error: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
          `_pytest_sessionfinish`

    State and side effects:
        mutates envelopes, config, run_started_id, run_success, run_exception.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.lifecycle_runtime._hooks._pytest_sessionfinish` keeps its
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
        #arch-eval:locational_stability=3
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
            self.reporter._xdist_worker_temp_messages_path is not None  # noqa: SLF001
            and self.reporter._xdist_worker_temp_messages_path.exists()  # noqa: SLF001
        ):
            self.reporter._xdist_worker_temp_messages_path.unlink()  # noqa: SLF001
        return

    if self.reporter.is_xdist_controller:
        self.reporter._xdist_fragment_records["master"] = {  # noqa: SLF001
            "worker_id": "master",
            "role": "controller",
            "path": self.reporter.messages_file_path,
            "complete": True,
            "manifest_received": True,
        }
        envelopes = self.transport_service._finalize_xdist_messages_file()  # noqa: SLF001
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
    if self.reporter._mapping_diagnostics_count:  # noqa: SLF001
        logger.error(
            "Detected %s mapping diagnostic warning(s) in message emission flow.",
            self.reporter._mapping_diagnostics_count,  # noqa: SLF001
        )
    if not self._check_derived_output_consistency(envelopes):
        logger.error("Derived-output consistency check failed: required run lifecycle envelopes are incomplete.")

    if (
        self.reporter.requested_cucumber_formatters
        and not self.reporter._live_formatter_session_started  # noqa: SLF001
        and self.reporter._live_formatter_failure_message is None  # noqa: SLF001
    ):
        self.live_formatter_service._record_live_formatter_failure(  # noqa: SLF001
            "Requested cucumber formatters were not attached to a live session; "
            "post-run replay is disabled for live formatter runs.",
        )
    if self.reporter.config.option.cucumber_html_path is not None:
        self.live_formatter_service.generate_html_report()
    if self.reporter.is_messages_file_temp:
        Path(self.reporter.final_messages_file_path).unlink()
    if self.reporter.xdist_fragment_dir is not None and self.reporter.xdist_fragment_dir.exists():
        shutil.rmtree(self.reporter.xdist_fragment_dir)
