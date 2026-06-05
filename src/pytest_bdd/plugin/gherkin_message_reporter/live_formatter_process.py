"""Provide live formatter process lifecycle helpers."""

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
    """Represent live formatter process state."""

    stdin: IO[str] | None
    stdout: IO[str] | None
    stderr: IO[str] | None
    returncode: int | None

    def poll(self) -> int | None:
        """Handle poll."""
        ...

    def wait(self, timeout: float | None = None) -> int:
        """Handle wait."""
        ...

    def kill(self) -> None:
        """Handle kill."""
        ...


class LiveFormatterProcessMixin:
    """Provide live formatter process lifecycle behavior."""

    if TYPE_CHECKING:
        reporter: GherkinMessageReporter

    def _finalize_live_formatter_process(self, process: LiveFormatterProcess) -> None:
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
        if self.reporter._live_formatter_stdout_thread is not None:  # noqa: SLF001
            self.reporter._live_formatter_stdout_thread.join(timeout=5)  # noqa: SLF001
            self.reporter._live_formatter_stdout_thread = None  # noqa: SLF001
        if self.reporter._live_formatter_stderr_thread is not None:  # noqa: SLF001
            self.reporter._live_formatter_stderr_thread.join(timeout=5)  # noqa: SLF001
            self.reporter._live_formatter_stderr_thread = None  # noqa: SLF001

    def _record_live_formatter_failure(self, message: str) -> None:
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
        """Handle emit live formatter json lines."""
        self._emit_live_formatter_json_lines(message_json_lines, source=source)

    def _normalize_live_formatter_json_lines(self, message_json_lines: list[str]) -> list[str]:
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
        return [json.dumps(envelope_dict) for envelope_dict in self.reporter._live_formatter_envelope_adapter.flush()]  # noqa: SLF001

    @staticmethod
    def _close_live_formatter_stream(stream: IO[str] | None) -> None:
        if stream is None:
            return
        with suppress(OSError, ValueError):
            stream.close()
