from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from pytest_cuke import formatter_runtime
from pytest_cuke.formatter_api import FormatterAsset, FormatterRequest
from pytest_cuke.formatter_runtime import FormatterRuntimeError, FormatterSession
from pytest_cuke.model.message_types import Envelope, TestRunFinished, TestRunStarted, Timestamp

TestRunStarted.__test__ = False


class _PluginManager:
    def __init__(self, plugins: dict[str, object] | None = None) -> None:
        self.plugins = plugins or {}

    def get_plugin(self, name: str) -> object | None:
        return self.plugins.get(name)


def _config() -> SimpleNamespace:
    return SimpleNamespace(pluginmanager=_PluginManager())


def _started_message() -> Envelope:
    return Envelope(test_run_started=TestRunStarted(id="controller-run", timestamp=Timestamp(seconds=1, nanos=0)))


def _finished_message() -> Envelope:
    return Envelope(
        test_run_finished=TestRunFinished(
            success=True,
            timestamp=Timestamp(seconds=2, nanos=0),
            test_run_started_id="controller-run",
        )
    )


def _send_successful_run(session: FormatterSession) -> None:
    session.pytest_cuke_message_validated(_config(), _started_message())
    session.pytest_cuke_message_validated(_config(), _finished_message())


def _request(
    tmp_path: Path,
    code: str,
    *,
    output: str | None = "formatter-output.txt",
    timeout: float = 1.0,
    assets: tuple[FormatterAsset, ...] = (),
    command: tuple[str, ...] | None = None,
) -> FormatterRequest:
    return FormatterRequest(
        name="test-formatter",
        command=command or (sys.executable, "-c", code),
        output_path=tmp_path / output if output is not None else None,
        working_directory=tmp_path,
        timeout_seconds=timeout,
        runtime_assets=assets,
    )


def test_formatter_streams_messages_and_publishes_file_only_after_clean_exit(tmp_path: Path) -> None:
    output = tmp_path / "formatter-output.txt"
    session = FormatterSession(
        _config(),
        (_request(tmp_path, "import sys; sys.stdout.write(sys.stdin.read())", output=output.name),),
    )
    session.start()
    _send_successful_run(session)

    assert not output.exists()
    session.finish()

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows[0] == {"testRunStarted": {"timestamp": {"seconds": 1, "nanos": 0}, "id": "controller-run"}}
    assert rows[1]["testRunFinished"]["success"] is True
    assert not session.failed
    formatter = session._processes[0]
    assert formatter._process is not None and formatter._process.returncode == 0
    assert all(
        thread is None or not thread.is_alive()
        for thread in (formatter._writer_thread, formatter._stdout_thread, formatter._stderr_thread)
    )


def test_formatter_replays_stdout_and_stderr_to_pytest_streams(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = (
        "import sys; print('formatter stderr sentinel', file=sys.stderr, flush=True); "
        "print('formatter stdout sentinel', flush=True); sys.stdin.read()"
    )
    session = FormatterSession(_config(), (_request(tmp_path, code, output=None),))
    session.start()
    _send_successful_run(session)
    session.finish()

    captured = capsys.readouterr()
    assert "formatter stdout sentinel" in captured.out
    assert "formatter stderr sentinel" in captured.err


def test_formatter_can_bypass_pytest_capture_for_live_terminal_output() -> None:
    class OriginalCapture:
        def __init__(self) -> None:
            self.writes: list[str] = []

        def writeorg(self, text: str) -> None:
            self.writes.append(text)

    class TerminalReporter:
        currentfspath = "test_feature.py"

        def __init__(self) -> None:
            self.newline_calls = 0

        def ensure_newline(self) -> None:
            self.newline_calls += 1
            self.currentfspath = None

    stdout = OriginalCapture()
    stderr = OriginalCapture()
    reporter = TerminalReporter()
    capture_manager = SimpleNamespace(
        _global_capturing=SimpleNamespace(out=stdout, err=stderr),
        is_capturing=lambda: "global",
    )
    config = SimpleNamespace(
        pluginmanager=_PluginManager({"capturemanager": capture_manager, "terminalreporter": reporter}),
    )
    relay = formatter_runtime._TerminalOutputRelay(config, bypass_capture=True)

    relay.write("pretty output\n", stderr=False)
    relay.write("backend warning\n", stderr=True)

    assert stdout.writes == ["\n", "pretty output\n"]
    assert stderr.writes == ["backend warning\n"]
    assert reporter.newline_calls == 1


def test_formatter_does_not_silently_restore_capture_when_original_writer_is_missing() -> None:
    capture_manager = SimpleNamespace(
        _global_capturing=SimpleNamespace(out=object(), err=object()),
        is_capturing=lambda: "global",
    )
    config = SimpleNamespace(
        pluginmanager=_PluginManager({"capturemanager": capture_manager}),
    )
    relay = formatter_runtime._TerminalOutputRelay(config, bypass_capture=True)

    with pytest.raises(OSError, match="original terminal writer is unavailable"):
        relay.write("pretty output\n", stderr=False)


def test_formatter_fails_loudly_when_capture_state_api_is_unavailable() -> None:
    capture_manager = SimpleNamespace(
        _global_capturing=SimpleNamespace(out=object(), err=object()),
    )
    config = SimpleNamespace(
        pluginmanager=_PluginManager({"capturemanager": capture_manager}),
    )
    relay = formatter_runtime._TerminalOutputRelay(config, bypass_capture=True)

    with pytest.raises(OSError, match="original terminal writer is unavailable"):
        relay.write("pretty output\n", stderr=False)


def test_formatter_materializes_and_removes_runtime_assets(tmp_path: Path) -> None:
    code = (
        "from pathlib import Path; import sys; asset = Path(sys.argv[1]); print(asset.read_text()); print(asset.parent)"
    )
    session = FormatterSession(
        _config(),
        (
            _request(
                tmp_path,
                code,
                command=(sys.executable, "-c", code, "{asset_dir}/formatter.conf"),
                assets=(FormatterAsset("formatter.conf", "configured"),),
            ),
        ),
    )
    session.start()
    _send_successful_run(session)
    session.finish()

    lines = (tmp_path / "formatter-output.txt").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "configured"
    assert not Path(lines[1]).exists()


def test_formatter_asset_staging_failure_removes_temporary_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    created_directories: list[Path] = []
    temporary_directory = formatter_runtime.tempfile.TemporaryDirectory
    write_bytes = Path.write_bytes

    def track_temporary_directory(*, prefix: str) -> object:
        directory = temporary_directory(prefix=prefix, dir=tmp_path)
        created_directories.append(Path(directory.name))
        return directory

    def fail_asset_write(path: Path, content: bytes) -> int:
        if path.name == "formatter.conf":
            raise OSError("simulated asset staging failure")
        return write_bytes(path, content)

    monkeypatch.setattr(formatter_runtime.tempfile, "TemporaryDirectory", track_temporary_directory)
    monkeypatch.setattr(Path, "write_bytes", fail_asset_write)

    session = FormatterSession(
        _config(),
        (
            _request(
                tmp_path,
                "import sys; sys.stdin.read()",
                assets=(FormatterAsset("formatter.conf", "configured"),),
            ),
        ),
    )

    with pytest.raises(FormatterRuntimeError, match="simulated asset staging failure"):
        session.start()

    assert len(created_directories) == 1
    assert not created_directories[0].exists()


def test_formatter_cleanup_diagnostic_preserves_windows_path_spelling() -> None:
    class WindowsLookingPath:
        def __str__(self) -> str:
            return r"C:\agent\_temp\.report.ndjson.123.pytest-cuke-tmp"

        def unlink(self, *, missing_ok: bool) -> None:
            del missing_ok
            raise OSError("simulated cleanup failure")

    formatter = formatter_runtime._FormatterProcess(
        _request(Path("."), "pass"), config=_config(), label="live formatter"
    )
    formatter._temporary_output_path = WindowsLookingPath()  # type: ignore[assignment]

    formatter._discard_staged_output()

    failure = formatter.failure
    assert failure is not None
    assert r"C:\agent\_temp\.report.ndjson.123.pytest-cuke-tmp" in str(failure)
    assert r"C:\\agent\\_temp" not in str(failure)


def test_formatter_timeout_kills_child_and_removes_staged_output(tmp_path: Path) -> None:
    output = tmp_path / "formatter-output.txt"
    code = "import sys, time; sys.stdin.read(); time.sleep(10)"
    session = FormatterSession(
        _config(),
        (_request(tmp_path, code, output=output.name, timeout=0.05),),
    )
    session.start()
    _send_successful_run(session)

    with pytest.raises(FormatterRuntimeError, match="did not exit within"):
        session.finish()

    assert session.failed
    assert not output.exists()
    assert not list(tmp_path.glob(".formatter-output.txt.*.pytest-cuke-tmp"))


def test_formatter_output_publication_rolls_back_sibling_files_on_commit_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_output = tmp_path / "first.ndjson"
    second_output = tmp_path / "second.ndjson"
    first_output.write_text("previous report", encoding="utf-8")
    code = "import sys; sys.stdout.write(sys.stdin.read())"
    session = FormatterSession(
        _config(),
        (
            _request(tmp_path, code, output=first_output.name),
            _request(tmp_path, code, output=second_output.name),
        ),
    )
    session.start()
    _send_successful_run(session)
    replace = formatter_runtime.os.replace

    def fail_second_output(source: str | bytes | Path, destination: str | bytes | Path) -> None:
        if Path(destination) == second_output:
            raise OSError("simulated second output publication failure")
        replace(source, destination)

    monkeypatch.setattr(formatter_runtime.os, "replace", fail_second_output)

    with pytest.raises(FormatterRuntimeError, match="Could not publish live formatter outputs"):
        session.finish()

    assert first_output.read_text(encoding="utf-8") == "previous report"
    assert not second_output.exists()
    assert not list(tmp_path.glob(".*.pytest-cuke-tmp"))
    assert not list(tmp_path.glob(".*.pytest-cuke-backup"))


def test_formatter_output_publication_preserves_backup_when_rollback_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_output = tmp_path / "first.ndjson"
    second_output = tmp_path / "second.ndjson"
    first_output.write_text("previous report", encoding="utf-8")
    second_output.write_text("previous sibling report", encoding="utf-8")
    code = "import sys; sys.stdout.write(sys.stdin.read())"
    session = FormatterSession(
        _config(),
        (
            _request(tmp_path, code, output=first_output.name),
            _request(tmp_path, code, output=second_output.name),
        ),
    )
    session.start()
    _send_successful_run(session)
    replace = formatter_runtime.os.replace

    def fail_publication_and_restore(source: str | bytes | Path, destination: str | bytes | Path) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        if destination_path == second_output:
            if source_path.suffix == ".pytest-cuke-backup":
                raise OSError("simulated backup restoration failure")
            raise OSError("simulated second output publication failure")
        replace(source, destination)

    monkeypatch.setattr(formatter_runtime.os, "replace", fail_publication_and_restore)

    with pytest.raises(FormatterRuntimeError, match="rollback also failed"):
        session.finish()

    backups = list(tmp_path.glob(".*.pytest-cuke-backup"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "previous sibling report"
    assert first_output.read_text(encoding="utf-8") == "previous report"


def test_formatter_output_publication_reports_backup_cleanup_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "report.ndjson"
    output.write_text("previous report", encoding="utf-8")
    code = "import sys; sys.stdout.write(sys.stdin.read())"
    session = FormatterSession(_config(), (_request(tmp_path, code, output=output.name),))
    session.start()
    _send_successful_run(session)
    unlink = Path.unlink

    def fail_backup_cleanup(path: Path, *args: object, **kwargs: object) -> None:
        if path.suffix == ".pytest-cuke-backup":
            raise OSError("simulated output backup cleanup failure")
        unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_backup_cleanup)

    with pytest.raises(FormatterRuntimeError, match="Could not remove live formatter output backup") as failure:
        session.finish()

    backups = list(tmp_path.glob(".*.pytest-cuke-backup"))
    assert len(backups) == 1
    assert str(backups[0]) in str(failure.value)
    assert backups[0].read_text(encoding="utf-8") == "previous report"
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows[0].get("testRunStarted")
    assert rows[-1].get("testRunFinished", {}).get("success") is True


def test_formatter_output_rollback_reports_temporary_backup_cleanup_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "report.ndjson"
    output.write_text("previous report", encoding="utf-8")
    code = "import sys; sys.stdout.write(sys.stdin.read())"
    session = FormatterSession(_config(), (_request(tmp_path, code, output=output.name),))
    session.start()
    _send_successful_run(session)
    replace = formatter_runtime.os.replace
    unlink = Path.unlink

    def fail_backup_move(source: str | bytes | Path, destination: str | bytes | Path) -> None:
        if Path(source) == output and Path(destination).suffix == ".pytest-cuke-backup":
            raise OSError("simulated output backup move failure")
        replace(source, destination)

    def fail_backup_cleanup(path: Path, *args: object, **kwargs: object) -> None:
        if path.suffix == ".pytest-cuke-backup":
            raise OSError("simulated rollback backup cleanup failure")
        unlink(path, *args, **kwargs)

    monkeypatch.setattr(formatter_runtime.os, "replace", fail_backup_move)
    monkeypatch.setattr(Path, "unlink", fail_backup_cleanup)

    with pytest.raises(FormatterRuntimeError, match="Could not publish live formatter outputs") as failure:
        session.finish()

    backups = list(tmp_path.glob(".*.pytest-cuke-backup"))
    assert len(backups) == 1
    assert str(backups[0]) in str(failure.value)
    assert output.read_text(encoding="utf-8") == "previous report"


def test_formatter_output_rollback_reports_staged_output_cleanup_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "report.ndjson"
    output.write_text("previous report", encoding="utf-8")
    code = "import sys; sys.stdout.write(sys.stdin.read())"
    session = FormatterSession(_config(), (_request(tmp_path, code, output=output.name),))
    session.start()
    _send_successful_run(session)
    replace = formatter_runtime.os.replace
    unlink = Path.unlink

    def fail_backup_move(source: str | bytes | Path, destination: str | bytes | Path) -> None:
        if Path(source) == output and Path(destination).suffix == ".pytest-cuke-backup":
            raise OSError("simulated output backup move failure")
        replace(source, destination)

    def fail_staged_cleanup(path: Path, *args: object, **kwargs: object) -> None:
        if path.suffix == ".pytest-cuke-tmp":
            raise OSError("simulated staged output cleanup failure")
        unlink(path, *args, **kwargs)

    monkeypatch.setattr(formatter_runtime.os, "replace", fail_backup_move)
    monkeypatch.setattr(Path, "unlink", fail_staged_cleanup)

    with pytest.raises(FormatterRuntimeError, match="Could not publish live formatter outputs") as failure:
        session.finish()

    staged_outputs = list(tmp_path.glob(".*.pytest-cuke-tmp"))
    assert len(staged_outputs) == 1
    assert str(staged_outputs[0]) in str(failure.value)
    assert output.read_text(encoding="utf-8") == "previous report"


def test_formatter_broken_pipe_is_reported_and_child_is_cleaned_up(tmp_path: Path) -> None:
    output = tmp_path / "formatter-output.txt"
    session = FormatterSession(
        _config(),
        (_request(tmp_path, "import time; time.sleep(0.1)", output=output.name),),
    )
    session.start()
    session.pytest_cuke_message_validated(_config(), _started_message())
    session._write_envelope(
        {
            "source": {
                "uri": "features/large.feature",
                "data": "Feature: " + ("x" * 1_000_000),
                "mediaType": "text/x.cucumber.gherkin+plain",
            }
        }
    )
    formatter = session._processes[0]
    deadline = time.monotonic() + 2
    while formatter.failure is None and time.monotonic() < deadline:
        time.sleep(0.01)

    assert formatter.failure is not None and "stopped reading Messages" in str(formatter.failure)
    session.abort()

    assert formatter._process is not None and formatter._process.poll() is not None
    assert not output.exists()
    assert not list(tmp_path.glob(".formatter-output.txt.*.pytest-cuke-tmp"))


def test_formatter_detects_early_exit_and_removes_staged_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "formatter-output.txt"
    ready = tmp_path / "formatter-ready.marker"
    code = (
        "from pathlib import Path; import sys; "
        "print('formatter exited early sentinel', file=sys.stderr, flush=True); "
        "Path(sys.argv[1]).touch(); raise SystemExit(17)"
    )
    session = FormatterSession(
        _config(),
        (
            _request(
                tmp_path,
                code,
                output=output.name,
                command=(sys.executable, "-c", code, str(ready)),
            ),
        ),
    )
    session.start()
    deadline = time.monotonic() + 2
    while not ready.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert ready.exists(), "formatter child did not start"
    deadline = time.monotonic() + 2
    while session._processes[0]._process is not None and session._processes[0]._process.poll() is None:
        if time.monotonic() >= deadline:
            pytest.fail("formatter child did not exit")
        time.sleep(0.01)

    with pytest.raises(FormatterRuntimeError, match="exited before the Messages stream finished"):
        session.pytest_cuke_message_validated(_config(), _started_message())
    session.abort()

    captured = capsys.readouterr()
    assert "formatter exited early sentinel" in captured.err
    assert not output.exists()
    assert not list(tmp_path.glob(".formatter-output.txt.*.pytest-cuke-tmp"))
