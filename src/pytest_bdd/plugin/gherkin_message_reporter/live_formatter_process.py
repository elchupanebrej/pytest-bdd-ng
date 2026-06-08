"""
Provide live formatter process lifecycle helpers.

Responsibility:
    Provide live formatter process lifecycle helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process`
    because it keeps the nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - LiveFormatterProcess: owns nested behavior below this boundary
    - LiveFormatterProcessMixin: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
      `live_formatter_process`

State and side effects:
    mutates stdin, normalized_lines, logger, stdout, stderr; depends on __future__.annotations, json, logging,
    subprocess, sys.

Invariants:
    - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process` keeps its documented import path, ownership
      boundary, and observable behavior stable for callers.

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

from __future__ import annotations

import json
import logging
import subprocess  # noqa: S404
import sys
from contextlib import suppress
from typing import IO, TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pytest_bdd.plugin.gherkin_message_reporter.plugin import GherkinMessageReporter

logger = logging.getLogger(__name__)


class LiveFormatterProcess(Protocol):
    """
    Represent live formatter process state.

    Responsibility:
        Represent live formatter process state. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcess` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - poll: owns nested behavior below this boundary
        - wait: owns nested behavior below this boundary
        - kill: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
          `LiveFormatterProcess`
        - src/pytest_bdd/plugin/gherkin_message_reporter/plugin.py: imports or references `LiveFormatterProcess`

    State and side effects:
        mutates stdin, stdout, stderr, returncode.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcess` keeps its documented
          import path, ownership boundary, and observable behavior stable for callers.

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

    stdin: IO[str] | None
    stdout: IO[str] | None
    stderr: IO[str] | None
    returncode: int | None

    def poll(self) -> int | None:
        """
        Handle poll.

        Responsibility:
            Handle poll. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcess.poll` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `poll`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references `poll`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references `poll`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        ...

    def wait(self, timeout: float | None = None) -> int:
        """
        Handle wait.

        Responsibility:
            Handle wait. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcess.wait` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `wait`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references `wait`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        ...

    def kill(self) -> None:
        """
        Handle kill.

        Responsibility:
            Handle kill. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcess.kill` because it
            keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/debug_mcp/entrypoint.py: imports or references `kill`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references `kill`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """
        ...


class LiveFormatterProcessMixin:
    """
    Provide live formatter process lifecycle behavior.

    Responsibility:
        Provide live formatter process lifecycle behavior. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _finalize_live_formatter_process: owns nested behavior below this boundary
        - _wait_for_live_formatter_process: owns nested behavior below this boundary
        - _join_live_formatter_threads: owns nested behavior below this boundary
        - _record_live_formatter_failure: owns nested behavior below this boundary
        - _emit_live_formatter_json_lines: owns nested behavior below this boundary
        - emit_live_formatter_json_lines: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
          `LiveFormatterProcessMixin`

    State and side effects:
        mutates normalized_lines, reporter, flush_lines, self.reporter._live_formatter_stdout_thread,
        self.reporter._live_formatter_stderr_thread.

    Invariants:
        - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin` keeps its
          documented import path, ownership boundary, and observable behavior stable for callers.

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

    if TYPE_CHECKING:
        reporter: GherkinMessageReporter

    def _finalize_live_formatter_process(self, process: LiveFormatterProcess) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._finalize_live_formatter_process`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._finalize_live_formatter_process`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._build_live_formatter_flush_json_lines: collaborator call used by this boundary
            - self._emit_live_formatter_json_lines: collaborator call used by this boundary
            - suppress: collaborator call used by this boundary
            - process.stdin.close: collaborator call used by this boundary
            - self._wait_for_live_formatter_process: collaborator call used by this boundary
            - self._record_live_formatter_failure: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_finalize_live_formatter_process`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `_finalize_live_formatter_process`

        State and side effects:
            mutates flush_lines.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._finalize_live_formatter_process`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        flush_lines = self._build_live_formatter_flush_json_lines()
        if flush_lines:
            self._emit_live_formatter_json_lines(flush_lines, source="formatter session final flush")
        if process.stdin is not None:
            with suppress(OSError, ValueError):
                process.stdin.close()
        self._wait_for_live_formatter_process(process)
        if process.returncode not in {None, 0}:
            self._record_live_formatter_failure(
                f"Live cucumber formatter session exited with code {process.returncode}.",
            )

    def _wait_for_live_formatter_process(self, process: LiveFormatterProcess) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._wait_for_live_formatter_process`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._wait_for_live_formatter_process`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - process.wait: collaborator call used by this boundary
            - suppress: collaborator call used by this boundary
            - self._record_live_formatter_failure: collaborator call used by this boundary
            - process.kill: collaborator call used by this boundary
            - process.poll: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_wait_for_live_formatter_process`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._record_live_formatter_failure("Live cucumber formatter session did not terminate after stdin closed.")
            with suppress(OSError):
                process.kill()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._record_live_formatter_failure(
                    "Live cucumber formatter session did not terminate after forced shutdown.",
                )
        finally:
            if process.poll() is None:
                with suppress(OSError):
                    process.kill()
                with suppress(subprocess.TimeoutExpired, OSError):
                    process.wait(timeout=5)

    def _join_live_formatter_threads(self) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._join_live_formatter_threads`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._join_live_formatter_threads`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.reporter._live_formatter_stdout_thread.join: collaborator call used by this boundary
            - self.reporter._live_formatter_stderr_thread.join: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_join_live_formatter_threads`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `_join_live_formatter_threads`

        State and side effects:
            mutates self.reporter._live_formatter_stdout_thread, self.reporter._live_formatter_stderr_thread.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._join_live_formatter_threads`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        if self.reporter._live_formatter_stdout_thread is not None:  # noqa: SLF001
            self.reporter._live_formatter_stdout_thread.join(timeout=5)  # noqa: SLF001
            self.reporter._live_formatter_stdout_thread = None  # noqa: SLF001
        if self.reporter._live_formatter_stderr_thread is not None:  # noqa: SLF001
            self.reporter._live_formatter_stderr_thread.join(timeout=5)  # noqa: SLF001
            self.reporter._live_formatter_stderr_thread = None  # noqa: SLF001

    def _record_live_formatter_failure(self, message: str) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._record_live_formatter_failure`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._record_live_formatter_failure`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - getattr: collaborator call used by this boundary
            - restore_terminal_reporter: collaborator call used by this boundary
            - logger.error: collaborator call used by this boundary
            - sys.stderr.write: collaborator call used by this boundary
            - sys.stderr.flush: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_hooks.py: imports or references
              `_record_live_formatter_failure`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runner.py: imports or references
              `_record_live_formatter_failure`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_record_live_formatter_failure`

        State and side effects:
            mutates self.reporter._live_formatter_failure_message, restore_terminal_reporter,
            self.reporter._restore_terminal_reporter.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._record_live_formatter_failure`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        if self.reporter._live_formatter_failure_message == message:  # noqa: SLF001
            return
        if self.reporter._live_formatter_failure_message is None:  # noqa: SLF001
            self.reporter._live_formatter_failure_message = message  # noqa: SLF001
            restore_terminal_reporter = getattr(self.reporter, "_restore_terminal_reporter", None)
            if restore_terminal_reporter is not None:
                restore_terminal_reporter()
                self.reporter._restore_terminal_reporter = None  # noqa: SLF001
        logger.error("%s", message)
        sys.stderr.write(f"{message}\n")
        sys.stderr.flush()

    def _emit_live_formatter_json_lines(self, message_json_lines: list[str], *, source: str) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._emit_live_formatter_json_lines`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._emit_live_formatter_json_lines`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._record_live_formatter_failure: collaborator call used by this boundary
            - stdin.write: collaborator call used by this boundary
            - self._normalize_live_formatter_json_lines: collaborator call used by this boundary
            - process.poll: collaborator call used by this boundary
            - stdin.flush: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/lifecycle_runtime/_core.py: imports or references
              `_emit_live_formatter_json_lines`
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_emit_live_formatter_json_lines`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `_emit_live_formatter_json_lines`

        State and side effects:
            mutates normalized_lines, process, stdin.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._emit_live_formatter_json_lines`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        normalized_lines = self._normalize_live_formatter_json_lines(message_json_lines)
        if not normalized_lines or self.reporter._live_formatter_failure_message is not None:  # noqa: SLF001
            return
        process = self.reporter._live_formatter_process  # noqa: SLF001
        if process is None:
            return
        stdin = process.stdin
        if stdin is None:
            self._record_live_formatter_failure(
                f"Live cucumber formatter delivery from {source} failed because "
                "the formatter stdin pipe is unavailable.",
            )
            return
        if process.poll() is not None:
            self._record_live_formatter_failure(
                f"Live cucumber formatter session exited early with code {process.returncode} while handling {source}.",
            )
            return
        with self.reporter._live_formatter_lock:  # noqa: SLF001
            try:
                for message_json in normalized_lines:
                    stdin.write(message_json)
                    stdin.write("\n")
                stdin.flush()
            except OSError as exc:
                self._record_live_formatter_failure(
                    f"Live cucumber formatter delivery from {source} failed before session completion: {exc}",
                )

    def emit_live_formatter_json_lines(self, message_json_lines: list[str], *, source: str) -> None:
        """
        Handle emit live formatter json lines.

        Responsibility:
            Handle emit live formatter json lines. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin.emit_live_formatter_json_lines`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self._emit_live_formatter_json_lines: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `emit_live_formatter_json_lines`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        self._emit_live_formatter_json_lines(message_json_lines, source=source)

    def _normalize_live_formatter_json_lines(self, message_json_lines: list[str]) -> list[str]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._normalize_live_formatter_json_lines`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._normalize_live_formatter_json_lines`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - json.loads: collaborator call used by this boundary
            - normalized_lines.extend: collaborator call used by this boundary
            - json.dumps: collaborator call used by this boundary
            - self.reporter._live_formatter_envelope_adapter.adapt_envelope_dict: collaborator call used by this
              boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_normalize_live_formatter_json_lines`

        State and side effects:
            mutates normalized_lines, envelope_dict.

        Invariants:
            - `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._normalize_live_formatter_json_lines`
              keeps its documented import path, ownership boundary, and observable behavior stable for callers.

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
        normalized_lines: list[str] = []
        for message_json in message_json_lines:
            envelope_dict = json.loads(message_json)
            normalized_lines.extend(
                json.dumps(adapted_envelope_dict)
                for adapted_envelope_dict in self.reporter._live_formatter_envelope_adapter.adapt_envelope_dict(  # noqa: SLF001
                    envelope_dict,
                )
            )
        return normalized_lines

    def _build_live_formatter_flush_json_lines(self) -> list[str]:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._build_live_formatter_flush_json_lines`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._build_live_formatter_flush_json_lines`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - json.dumps: collaborator call used by this boundary
            - self.reporter._live_formatter_envelope_adapter.flush: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_build_live_formatter_flush_json_lines`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        return [json.dumps(envelope_dict) for envelope_dict in self.reporter._live_formatter_envelope_adapter.flush()]  # noqa: SLF001

    @staticmethod
    def _close_live_formatter_stream(stream: IO[str] | None) -> None:
        """
        Responsibility:
            Responsibility: Responsibility:
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._close_live_formatter_stream`
            owns documented method behavior. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.gherkin_message_reporter.live_formatter_process.LiveFormatterProcessMixin._close_live_formatter_stream`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - suppress: collaborator call used by this boundary
            - stream.close: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/gherkin_message_reporter/live_formatter_runtime.py: imports or references
              `_close_live_formatter_stream`
            - src/pytest_bdd/plugin/gherkin_message_reporter/transport_runtime.py: imports or references
              `_close_live_formatter_stream`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3
        """
        if stream is None:
            return
        with suppress(OSError, ValueError):
            stream.close()
