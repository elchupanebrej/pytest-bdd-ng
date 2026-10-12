"""Own formatter subprocesses and stream validated Cucumber Messages to them."""

from __future__ import annotations

import codecs
import json
import os
import queue
import subprocess
import sys
import tempfile
from contextlib import suppress
from pathlib import Path, PurePosixPath
from threading import Lock, Thread
from typing import TYPE_CHECKING, Any

from pytest_cuke.model.message_consolidation import LiveMessageAdapter
from pytest_cuke.model.message_stream_validation import MessageStreamValidator, MessageValidationError
from pytest_cuke.model.message_types import message_from_dict, message_to_dict

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config
    from pytest_cuke.formatter_api import FormatterRequest
    from pytest_cuke.model.message_types import Envelope as Message


_STOP_WRITER = object()


class FormatterRuntimeError(RuntimeError):
    """A selected formatter failed to consume or finish its Messages stream."""


class _TerminalOutputRelay:
    def __init__(self, config: Config | None, *, bypass_capture: bool = False) -> None:
        self.config = config
        self.bypass_capture = bypass_capture
        self._lock = Lock()
        self._layout_prepared = False

    def write(self, text: str, *, stderr: bool) -> None:
        if not text:
            return
        with self._lock:
            terminalreporter = (
                self.config.pluginmanager.get_plugin("terminalreporter") if self.config is not None else None
            )
            original_writer = self._original_capture_writer(stderr=stderr) if self.bypass_capture else None
            if original_writer is not None:
                if not self._layout_prepared:
                    has_open_terminal_line = bool(getattr(terminalreporter, "currentfspath", None))
                    ensure_newline = getattr(terminalreporter, "ensure_newline", None)
                    if callable(ensure_newline):
                        ensure_newline()
                    if has_open_terminal_line and not text.startswith("\n"):
                        original_writer("\n")
                    self._layout_prepared = True
                original_writer(text)
                return
            if self.bypass_capture and self._capture_is_active():
                raise OSError("pytest capture is active, but the original terminal writer is unavailable")
            if terminalreporter is not None:
                if not self._layout_prepared:
                    terminalreporter.ensure_newline()
                    self._layout_prepared = True
                writer = getattr(terminalreporter, "write_err", None) if stderr else terminalreporter.write
                if writer is not None:
                    writer(text, flush=True)
                    return
            target = sys.stderr if stderr else sys.stdout
            target.write(text)
            target.flush()

    def _original_capture_writer(self, *, stderr: bool) -> Any:
        if self.config is None:
            return None
        capture_manager = self.config.pluginmanager.get_plugin("capturemanager")
        global_capture = getattr(capture_manager, "_global_capturing", None)
        captured_stream = getattr(global_capture, "err" if stderr else "out", None)
        writer = getattr(captured_stream, "writeorg", None)
        if callable(writer):
            return writer
        tee_stream = getattr(captured_stream, "_other", None)
        writer = getattr(tee_stream, "write", None)
        if not callable(writer):
            return None
        flush = getattr(tee_stream, "flush", None)
        if not callable(flush):
            return writer

        def write_and_flush(text: str) -> Any:
            result = writer(text)
            flush()
            return result

        return write_and_flush

    def _capture_is_active(self) -> bool:
        if self.config is None:
            return False
        capture_manager = self.config.pluginmanager.get_plugin("capturemanager")
        if capture_manager is None:
            return False
        is_capturing = getattr(capture_manager, "is_capturing", None)
        if not callable(is_capturing):
            return True
        return callable(is_capturing) and is_capturing() not in (None, False, "no")


class _FormatterProcess:
    def __init__(self, request: FormatterRequest, *, config: Config | None, label: str) -> None:
        self.request = request
        self.label = label
        self.terminal_relay = _TerminalOutputRelay(config, bypass_capture=request.bypass_capture)
        self._input: queue.Queue[bytes | object] = queue.Queue(maxsize=32)
        self._lock = Lock()
        self._failure: Exception | None = None
        self._closed = False
        self._aborted = False
        self._process: subprocess.Popen[bytes] | None = None
        self._writer_thread: Thread | None = None
        self._stdout_thread: Thread | None = None
        self._stderr_thread: Thread | None = None
        self._asset_directory: tempfile.TemporaryDirectory[str] | None = None
        self._temporary_output_path: Path | None = None
        self._output_file: Any = None

    @property
    def failure(self) -> Exception | None:
        with self._lock:
            return self._failure

    def start(self) -> None:
        if self._process is not None:
            return

        command = list(self.request.command)
        try:
            if self.request.runtime_assets:
                self._asset_directory = tempfile.TemporaryDirectory(prefix="pytest-cuke-formatter-")
                asset_root = Path(self._asset_directory.name)
                for asset in self.request.runtime_assets:
                    target = asset_root.joinpath(*PurePosixPath(asset.path.replace("\\", "/")).parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    content = asset.content.encode("utf-8") if isinstance(asset.content, str) else asset.content
                    target.write_bytes(content)
                command = [argument.replace("{asset_dir}", str(asset_root)) for argument in command]

            if self.request.output_path is not None:
                descriptor, temporary_path = tempfile.mkstemp(
                    prefix=f".{self.request.output_path.name}.",
                    suffix=".pytest-cuke-tmp",
                    dir=self.request.output_path.parent,
                )
                self._temporary_output_path = Path(temporary_path)
                self._output_file = os.fdopen(descriptor, "wb")

            self._process = subprocess.Popen(  # noqa: S603 -- formatter commands are explicitly selected by installed plugins.
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.request.working_directory,
                bufsize=0,
            )
        except (OSError, ValueError) as error:
            self._cleanup_staged_files()
            raise FormatterRuntimeError(
                f"Unable to start {self.label} {self.request.name!r}: {type(error).__name__}: {error}"
            ) from error

        self._writer_thread = Thread(
            target=self._write_input,
            name=f"pytest-cuke-formatter-{self.request.name}-stdin",
            daemon=True,
        )
        self._stdout_thread = Thread(
            target=self._read_stdout,
            name=f"pytest-cuke-formatter-{self.request.name}-stdout",
            daemon=True,
        )
        self._stderr_thread = Thread(
            target=self._read_stderr,
            name=f"pytest-cuke-formatter-{self.request.name}-stderr",
            daemon=True,
        )
        self._writer_thread.start()
        self._stdout_thread.start()
        self._stderr_thread.start()

    def write_envelope(self, envelope: dict[str, Any]) -> None:
        process = self._process
        if process is None:
            raise FormatterRuntimeError(f"{self.label.capitalize()} {self.request.name!r} has not started.")
        self._raise_failure()
        return_code = process.poll()
        if return_code is not None:
            error = FormatterRuntimeError(
                f"{self.label.capitalize()} {self.request.name!r} exited before the Messages stream finished "
                f"(status {return_code})."
            )
            self._record_failure(error)
            raise error

        line = (json.dumps(envelope, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            self._input.put(line, timeout=self.request.timeout_seconds)
        except queue.Full as error:
            failure = FormatterRuntimeError(
                f"{self.label.capitalize()} {self.request.name!r} stopped accepting Messages for "
                f"{self.request.timeout_seconds:g} seconds."
            )
            self._record_failure(failure)
            self._terminate_child()
            raise failure from error

    def check_running(self) -> None:
        process = self._process
        if process is None:
            return
        return_code = process.poll()
        if return_code is not None:
            failure = FormatterRuntimeError(
                f"{self.label.capitalize()} {self.request.name!r} exited before the Messages stream finished "
                f"(status {return_code})."
            )
            self._record_failure(failure)
            raise failure
        self._raise_failure()

    def close(self, *, abort: bool = False) -> None:
        if self._closed:
            self._raise_failure()
            return
        self._closed = True
        self._aborted = self._aborted or abort
        process = self._process
        if process is None:
            self._cleanup_staged_files()
            self._raise_failure()
            return

        try:
            if abort or self.failure is not None:
                self._terminate_child()
                with suppress(queue.Full):
                    self._input.put_nowait(_STOP_WRITER)
            else:
                try:
                    self._input.put(_STOP_WRITER, timeout=self.request.timeout_seconds)
                except queue.Full:
                    self._record_failure(
                        FormatterRuntimeError(f"Timed out closing input for {self.label} {self.request.name!r}.")
                    )
                    self._terminate_child()

            writer_thread = self._writer_thread
            if writer_thread is not None:
                writer_thread.join(timeout=self.request.timeout_seconds)
                if writer_thread.is_alive():
                    self._record_failure(
                        FormatterRuntimeError(f"Timed out flushing Messages to {self.label} {self.request.name!r}.")
                    )
                    self._terminate_child()
                    writer_thread.join(timeout=self.request.timeout_seconds)

            try:
                process.wait(timeout=self.request.timeout_seconds)
            except subprocess.TimeoutExpired:
                self._record_failure(
                    FormatterRuntimeError(
                        f"{self.label.capitalize()} {self.request.name!r} did not exit within "
                        f"{self.request.timeout_seconds:g} seconds after the final flush."
                    )
                )
                self._terminate_child()
                try:
                    process.wait(timeout=self.request.timeout_seconds)
                except subprocess.TimeoutExpired as error:
                    self._record_failure(
                        FormatterRuntimeError(f"Unable to stop {self.label} {self.request.name!r} after timeout.")
                    )
                    self._close_pipes()
                    raise FormatterRuntimeError(
                        f"Unable to stop {self.label} {self.request.name!r} after timeout."
                    ) from error

            for thread in (self._stdout_thread, self._stderr_thread):
                if thread is not None:
                    thread.join(timeout=self.request.timeout_seconds)
                    if thread.is_alive():
                        self._record_failure(
                            FormatterRuntimeError(f"Output relay for {self.label} {self.request.name!r} did not stop.")
                        )
                        self._close_pipes()
                        thread.join(timeout=self.request.timeout_seconds)

            if process.returncode not in (None, 0):
                self._record_failure(
                    FormatterRuntimeError(
                        f"{self.label.capitalize()} {self.request.name!r} exited with status {process.returncode}."
                    )
                )
        finally:
            self._close_output_file()
            if self._aborted or self.failure is not None:
                self._discard_staged_output()
            self._cleanup_assets()

        self._raise_failure()

    def discard_output(self) -> None:
        """Remove any staged bytes that this formatter has not published."""
        if self._output_file is not None:
            self._close_output_file()
        self._discard_staged_output()
        self._raise_failure()

    def _write_input(self) -> None:
        process = self._process
        if process is None or process.stdin is None:
            self._record_failure(
                FormatterRuntimeError(f"{self.label.capitalize()} {self.request.name!r} has no stdin pipe.")
            )
            return
        try:
            while True:
                entry = self._input.get()
                if entry is _STOP_WRITER:
                    break
                if not isinstance(entry, bytes):
                    raise ValueError("formatter input queue received a non-byte message")
                remaining = memoryview(entry)
                while remaining:
                    written = process.stdin.write(remaining)
                    if written is None or written <= 0:
                        raise BrokenPipeError("formatter stdin accepted no bytes")
                    remaining = remaining[written:]
        except (BrokenPipeError, OSError, ValueError) as error:
            self._record_failure(
                FormatterRuntimeError(
                    f"{self.label.capitalize()} {self.request.name!r} stopped reading Messages: "
                    f"{type(error).__name__}: {error}"
                )
            )
        finally:
            with suppress(OSError):
                process.stdin.close()

    def _read_stdout(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        try:
            while chunk := process.stdout.read(4096):
                if self._output_file is not None:
                    self._output_file.write(chunk)
                else:
                    self.terminal_relay.write(decoder.decode(chunk), stderr=False)
            if self._output_file is None:
                self.terminal_relay.write(decoder.decode(b"", final=True), stderr=False)
        except (OSError, ValueError) as error:
            self._record_failure(
                FormatterRuntimeError(
                    f"Could not relay stdout from {self.label} {self.request.name!r}: {type(error).__name__}: {error}"
                )
            )

    def _read_stderr(self) -> None:
        process = self._process
        if process is None or process.stderr is None:
            return
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        try:
            while chunk := process.stderr.read(4096):
                self.terminal_relay.write(decoder.decode(chunk), stderr=True)
            self.terminal_relay.write(decoder.decode(b"", final=True), stderr=True)
        except (OSError, ValueError) as error:
            self._record_failure(
                FormatterRuntimeError(
                    f"Could not relay stderr from {self.label} {self.request.name!r}: {type(error).__name__}: {error}"
                )
            )

    def _record_failure(self, error: Exception) -> None:
        with self._lock:
            if self._failure is None:
                self._failure = error

    def _raise_failure(self) -> None:
        failure = self.failure
        if failure is not None:
            raise failure

    def _terminate_child(self) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            return
        try:
            process.kill()
        except OSError:
            return
        try:
            process.wait(timeout=self.request.timeout_seconds)
        except subprocess.TimeoutExpired:
            return

    def _close_pipes(self) -> None:
        process = self._process
        if process is None:
            return
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                with suppress(OSError):
                    stream.close()

    def _close_output_file(self) -> None:
        output_file = self._output_file
        self._output_file = None
        if output_file is None:
            return
        try:
            output_file.flush()
            os.fsync(output_file.fileno())
        except OSError as error:
            self._record_failure(
                FormatterRuntimeError(f"Could not flush staged output for {self.label} {self.request.name!r}: {error}")
            )
        try:
            output_file.close()
        except OSError as error:
            self._record_failure(
                FormatterRuntimeError(f"Could not close staged output for {self.label} {self.request.name!r}: {error}")
            )

    def _discard_staged_output(self) -> None:
        temporary_path = self._temporary_output_path
        self._temporary_output_path = None
        if temporary_path is None:
            return
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError as error:
            self._record_failure(
                FormatterRuntimeError(
                    f"Could not remove staged output for {self.label} "
                    f"{self.request.name!r} at {temporary_path}: {error}"
                )
            )

    def _cleanup_assets(self) -> None:
        asset_directory = self._asset_directory
        self._asset_directory = None
        if asset_directory is not None:
            asset_directory.cleanup()

    def _cleanup_staged_files(self) -> None:
        output_file = self._output_file
        self._output_file = None
        if output_file is not None:
            output_file.close()
        if self._temporary_output_path is not None:
            self._temporary_output_path.unlink(missing_ok=True)
            self._temporary_output_path = None
        self._cleanup_assets()


class FormatterSession:
    """Run all selected formatter requests as one validated Messages sink set."""

    def __init__(
        self,
        config: Config | None,
        requests: tuple[FormatterRequest, ...],
        *,
        mode: str = "live",
    ) -> None:
        if mode not in {"live", "replay"}:
            raise ValueError(f"unsupported formatter session mode: {mode!r}")
        self.config = config
        self.requests = requests
        self._label = f"{mode} formatter"
        self._processes: list[_FormatterProcess] = []
        self._started = False
        self._finished = False
        self._failure: Exception | None = None
        self._failure_reported = False
        self._message_adapter = LiveMessageAdapter()
        self._stream_validator = MessageStreamValidator()
        self._next_worker_sequence: dict[str, int] = {}

    @property
    def failed(self) -> bool:
        return self._failure is not None or any(process.failure is not None for process in self._processes)

    def start(self) -> None:
        if self._started:
            return
        if self._finished:
            raise FormatterRuntimeError(f"A closed {self._label} session cannot be restarted.")
        self._started = True
        try:
            for request in self.requests:
                process = _FormatterProcess(request, config=self.config, label=self._label)
                self._processes.append(process)
                process.start()
        except Exception as error:
            self._record_failure(error)
            for process in reversed(self._processes):
                with suppress(Exception):
                    process.close(abort=True)
            raise FormatterRuntimeError(str(error)) from error

    def pytest_cuke_message_validated(self, config: Config, message: Message) -> None:
        del config
        self.write_message(message)

    def write_message(self, message: Message) -> None:
        """Send one controller message through the live/replay normalization path."""
        try:
            envelope = self._message_adapter.controller_envelope(message_to_dict(message))
        except (TypeError, ValueError) as error:
            raise FormatterRuntimeError(f"Could not adapt controller Cucumber Messages: {error}") from error
        if envelope is not None:
            self._write_envelope(envelope)

    def pytest_cuke_message_batch(self, config: Config, batch: dict[str, Any]) -> None:
        del config
        worker_id = batch.get("worker_id")
        sequence = batch.get("sequence")
        envelopes = batch.get("envelopes")
        if not isinstance(worker_id, str) or not worker_id or type(sequence) is not int or sequence < 0:
            raise FormatterRuntimeError(
                f"A {self._label} received a worker Messages batch without a valid ID/sequence."
            )
        if not isinstance(envelopes, list):
            raise FormatterRuntimeError(f"A {self._label} received a malformed worker Messages batch.")
        expected_sequence = self._next_worker_sequence.get(worker_id, 0)
        if sequence != expected_sequence:
            raise FormatterRuntimeError(
                f"{self._label.capitalize()} worker '{worker_id}' batch sequence is incomplete: "
                f"expected {expected_sequence}, received {sequence}."
            )
        for envelope in envelopes:
            if not isinstance(envelope, dict):
                raise FormatterRuntimeError(f"A {self._label} received a non-object worker Messages envelope.")
            try:
                normalized = self._message_adapter.worker_envelope(envelope, worker_id=worker_id)
            except (TypeError, ValueError) as error:
                raise FormatterRuntimeError(
                    f"Could not adapt worker '{worker_id}' Cucumber Messages: {error}"
                ) from error
            if normalized is not None:
                self._write_envelope(normalized)
        self._next_worker_sequence[worker_id] = expected_sequence + 1

    def check_running(self) -> None:
        self._raise_failure()
        for process in self._processes:
            try:
                process.check_running()
            except Exception as error:
                self._record_failure(error)
                self._failure_reported = True
                self._raise_failure()

    def finish(self) -> None:
        if self._finished:
            self._raise_failure()
            return
        self._finished = True
        if self._failure is None:
            diagnostics = self._stream_validator.finish()
            if diagnostics:
                first = diagnostics[0]
                self._record_failure(
                    FormatterRuntimeError(
                        f"{self._label.capitalize()} received an incomplete Cucumber Messages stream: "
                        f"{first.code}: {first.message}"
                    )
                )
        errors: list[Exception] = []
        for process in reversed(self._processes):
            try:
                process.close(abort=self._failure is not None or process.failure is not None)
            except Exception as error:
                errors.append(error)
                self._record_failure(error)
        publish_outputs = not self.failed and not errors
        if publish_outputs:
            try:
                self._publish_staged_outputs()
            except Exception as error:
                errors.append(error)
                self._record_failure(error)
                publish_outputs = False
        if not publish_outputs:
            for process in self._processes:
                with suppress(Exception):
                    process.discard_output()
        if errors and not self._failure_reported:
            self._failure_reported = True
            self._raise_failure()
        if self._failure is not None and not self._failure_reported:
            self._failure_reported = True
            self._raise_failure()

    def abort(self) -> None:
        if self._finished:
            return
        self._finished = True
        for process in reversed(self._processes):
            with suppress(Exception):
                process.close(abort=True)
            with suppress(Exception):
                process.discard_output()

    def _write_envelope(self, envelope: dict[str, Any]) -> None:
        if not self.requests:
            return
        self._raise_failure()
        if not self._started or self._finished:
            error = FormatterRuntimeError(f"A {self._label} received a Messages event outside its active session.")
            self._record_failure(error)
            self._raise_failure()
        try:
            self._stream_validator.accept(message_from_dict(envelope))
        except MessageValidationError as error:
            failure = FormatterRuntimeError(
                f"{self._label.capitalize()} received an invalid Cucumber Messages stream: {error}"
            )
            self._record_failure(failure)
            self._failure_reported = True
            self._raise_failure()
        errors: list[Exception] = []
        for process in self._processes:
            try:
                process.write_envelope(envelope)
            except Exception as error:
                errors.append(error)
        if errors:
            self._record_failure(errors[0])
            self._failure_reported = True
            self._raise_failure()

    def _record_failure(self, error: Exception) -> None:
        if self._failure is None:
            self._failure = error if isinstance(error, FormatterRuntimeError) else FormatterRuntimeError(str(error))

    def _publish_staged_outputs(self) -> None:
        backups: list[tuple[Path, Path | None]] = []
        backup_paths: list[Path] = []
        published_paths: list[Path] = []
        try:
            for process in self._processes:
                staged_path = process._temporary_output_path
                output_path = process.request.output_path
                if staged_path is None or output_path is None:
                    continue

                backup_path: Path | None = None
                if output_path.exists():
                    descriptor, temporary_backup = tempfile.mkstemp(
                        prefix=f".{output_path.name}.",
                        suffix=".pytest-cuke-backup",
                        dir=output_path.parent,
                    )
                    backup_path = Path(temporary_backup)
                    backup_paths.append(backup_path)
                    os.close(descriptor)
                    os.replace(output_path, backup_path)

                backups.append((output_path, backup_path))
                os.replace(staged_path, output_path)
                process._temporary_output_path = None
                published_paths.append(output_path)
        except OSError as error:
            rollback_errors: list[OSError] = []
            preserved_backup_paths: list[Path] = []
            backup_cleanup_errors: list[tuple[Path, OSError]] = []
            staged_cleanup_errors: list[str] = []
            for output_path in reversed(published_paths):
                try:
                    output_path.unlink(missing_ok=True)
                except OSError as rollback_error:
                    rollback_errors.append(rollback_error)
            for output_path, backup_path in reversed(backups):
                if backup_path is None or not backup_path.exists():
                    continue
                try:
                    os.replace(backup_path, output_path)
                except OSError as rollback_error:
                    rollback_errors.append(rollback_error)
                    preserved_backup_paths.append(backup_path)
            for backup_path in backup_paths:
                if backup_path in preserved_backup_paths:
                    continue
                try:
                    backup_path.unlink(missing_ok=True)
                except OSError as cleanup_error:
                    backup_cleanup_errors.append((backup_path, cleanup_error))
            for process in self._processes:
                with suppress(OSError):
                    process._discard_staged_output()
                if process.failure is not None:
                    staged_cleanup_errors.append(str(process.failure))
            detail = f"{type(error).__name__}: {error}"
            if rollback_errors:
                detail += f"; rollback also failed: {rollback_errors[0]}"
            if preserved_backup_paths:
                preserved = ", ".join(str(path) for path in preserved_backup_paths)
                detail += f"; preserved previous output backup(s): {preserved}"
            if backup_cleanup_errors:
                cleanup_details = ", ".join(
                    f"{path} ({type(cleanup_error).__name__}: {cleanup_error})"
                    for path, cleanup_error in backup_cleanup_errors
                )
                detail += f"; could not remove temporary output backup(s): {cleanup_details}"
            if staged_cleanup_errors:
                detail += "; staged output cleanup also failed: " + "; ".join(staged_cleanup_errors)
            raise FormatterRuntimeError(f"Could not publish {self._label} outputs: {detail}") from error

        cleanup_errors: list[tuple[Path, OSError]] = []
        for backup_path in backup_paths:
            try:
                backup_path.unlink(missing_ok=True)
            except OSError as caught_cleanup_error:
                cleanup_errors.append((backup_path, caught_cleanup_error))
        if cleanup_errors:
            cleanup_path, cleanup_exception = cleanup_errors[0]
            raise FormatterRuntimeError(
                f"Could not remove {self._label} output backup "
                f"{cleanup_path}: {type(cleanup_exception).__name__}: {cleanup_exception}"
            ) from cleanup_exception

    def _raise_failure(self) -> None:
        if self._failure is not None:
            raise self._failure


__all__ = ["FormatterRuntimeError", "FormatterSession"]
