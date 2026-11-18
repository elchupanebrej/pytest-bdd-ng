"""External acceptance for remote pytest-xdist transports and Cucumber Messages reporting."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.external

REPO_ROOT = Path(__file__).resolve().parents[2]
REMOTE_XDIST_DIR = Path(__file__).with_name("remote-xdist")
COMPOSE_FILE = REMOTE_XDIST_DIR / "compose.yaml"
REMOTE_MODES = ("socket", "via", "ssh")
REMOTE_DEBUG_SECRET = "remote-debug-secret-value"


def _run_compose(
    project_name: str,
    env: dict[str, str],
    *arguments: str,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", "--project-name", project_name, "--file", str(COMPOSE_FILE), *arguments],
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        timeout=timeout,
    )


def _require_prerequisites(mode: str) -> None:
    if shutil.which("docker") is None:
        pytest.fail(
            "remote xdist lane requires Docker Engine and Docker Compose v2; install Docker Desktop/Engine and make `docker` available",
            pytrace=False,
        )
    compose = subprocess.run(
        ["docker", "compose", "version"],
        capture_output=True,
        check=False,
        text=True,
        timeout=15,
    )
    if compose.returncode != 0:
        pytest.fail(
            "remote xdist lane requires the Docker Compose v2 plugin; install/enable `docker compose` and rerun this Linux external lane",
            pytrace=False,
        )
    daemon = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        capture_output=True,
        check=False,
        text=True,
        timeout=20,
    )
    if daemon.returncode != 0 or not daemon.stdout.strip():
        details = (daemon.stderr or daemon.stdout).strip()
        pytest.fail(
            "remote xdist lane cannot reach the Docker Engine. Start the Docker daemon (for example, `sudo systemctl start docker`) "
            f"and rerun; docker info reported: {details or 'no server version'}",
            pytrace=False,
        )
    if mode == "ssh" and shutil.which("ssh-keygen") is None:
        pytest.fail(
            "remote xdist SSH lane requires `ssh-keygen` to create its ephemeral key; install OpenSSH client tools "
            "(for example, `sudo apt install openssh-client`) and rerun this lane",
            pytrace=False,
        )


def _make_ssh_key(directory: Path) -> None:
    result = subprocess.run(
        [
            "ssh-keygen",
            "-q",
            "-t",
            "ed25519",
            "-N",
            "",
            "-C",
            "pytest-cuke-remote-xdist",
            "-f",
            str(directory / "id_ed25519"),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        pytest.fail(
            "remote xdist SSH lane could not create an ephemeral SSH key; verify OpenSSH client installation and write access "
            f"to the pytest temporary directory: {(result.stderr or result.stdout).strip()}",
            pytrace=False,
        )
    (directory / "id_ed25519").chmod(0o600)


def _compose_environment(mode: str, ssh_dir: Path, crash_worker: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment["REMOTE_XDIST_MODE"] = mode
    environment["REMOTE_XDIST_CRASH_WORKER"] = crash_worker
    environment["REMOTE_XDIST_SSH_DIR"] = ssh_dir.as_posix()
    environment["REMOTE_DEBUG_SECRET"] = REMOTE_DEBUG_SECRET
    return environment


def _read_observations(project_name: str, env: dict[str, str]) -> dict[str, dict[str, Any]]:
    code = (
        "import json; from pathlib import Path; "
        "root=Path('/artifacts/observations'); "
        "print(json.dumps({p.stem: json.loads(p.read_text(encoding='utf-8')) "
        "for p in sorted(root.glob('*.json'))}))"
    )
    result = _run_compose(project_name, env, "exec", "-T", "controller", "python", "-c", code)
    assert result.returncode == 0, f"could not read remote worker observations:\n{result.stdout}\n{result.stderr}"
    observations = json.loads(result.stdout)
    assert isinstance(observations, dict)
    return observations


def _record_remote_worker_runtimes(mode: str, partial: bool, observations: dict[str, dict[str, Any]]) -> None:
    """Persist versions reported by remote workers for the matrix proof artifact."""
    workers: list[dict[str, str]] = []
    for worker_id, observation in sorted(observations.items()):
        worker = {"worker_id": worker_id}
        for key in ("runtime", "python", "pytest", "pytest-xdist"):
            value = observation.get(key)
            assert isinstance(value, str) and value, f"remote worker {worker_id} omitted {key}: {observation!r}"
            worker[key] = value
        workers.append(worker)

    evidence_path = os.environ.get("PYTEST_CUKE_REMOTE_RUNTIME_EVIDENCE")
    if not evidence_path:
        return

    path = Path(evidence_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"schema_version": 1, "runs": []}
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict) and payload.get("schema_version") == 1, payload
    runs = payload.get("runs")
    assert isinstance(runs, list), payload
    runs = [
        run for run in runs if not (isinstance(run, dict) and run.get("mode") == mode and run.get("partial") is partial)
    ]
    runs.append({"mode": mode, "partial": partial, "workers": workers})
    payload["runs"] = runs
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary_path.replace(path)


def _read_report(project_name: str, env: dict[str, str], destination: Path) -> list[dict[str, Any]]:
    result = _run_compose(
        project_name,
        env,
        "cp",
        "controller:/artifacts/messages.ndjson",
        str(destination),
    )
    assert result.returncode == 0, f"could not copy the remote Messages report:\n{result.stdout}\n{result.stderr}"
    assert destination.is_file(), f"remote Messages report was not copied to {destination}"
    messages = [json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert messages, "remote pytest run produced an empty Cucumber Messages NDJSON report"
    return messages


def _validate_report(messages: list[dict[str, Any]]) -> set[str]:
    from pytest_cuke.model.message_stream_validation import validate_message_stream
    from pytest_cuke.model.message_types import message_from_dict

    envelopes = [message_from_dict(message) for message in messages]
    diagnostics = validate_message_stream(envelopes)
    assert not diagnostics, f"remote Cucumber Messages stream failed schema/lifecycle validation: {diagnostics!r}"

    payloads: dict[str, list[dict[str, Any]]] = {}
    for message in messages:
        for kind, payload in message.items():
            if isinstance(payload, dict):
                payloads.setdefault(kind, []).append(payload)
    assert len(payloads.get("meta", [])) == 1, payloads
    assert len(payloads.get("testRunStarted", [])) == 1, payloads
    assert len(payloads.get("testRunFinished", [])) == 1, payloads
    run_finished = payloads["testRunFinished"][0]
    assert messages[-1].get("testRunFinished") == run_finished, "the controller must close the final Messages stream"
    worker_ids = {
        started.get("workerId")
        for started in payloads.get("testCaseStarted", [])
        if isinstance(started.get("workerId"), str) and started.get("workerId")
    }
    assert len(worker_ids) == 2, f"expected two xdist workers in the remote Messages stream, got {worker_ids!r}"
    return worker_ids


@pytest.mark.parametrize("mode", REMOTE_MODES, ids=REMOTE_MODES)
@pytest.mark.parametrize("partial", (False, True), ids=("complete", "worker-interrupted"))
def test_remote_xdist_report_preserves_worker_contract(
    mode: str,
    partial: bool,
    tmp_path: Path,
) -> None:
    """Exercise each real gateway type and verify complete and interrupted report finalization."""
    _require_prerequisites(mode)

    ssh_dir = tmp_path / "ssh"
    ssh_dir.mkdir()
    if mode == "ssh":
        _make_ssh_key(ssh_dir)
    project_name = f"pytest-cuke-remote-{uuid.uuid4().hex[:12]}"
    crash_worker = "gw1" if partial else ""
    env = _compose_environment(mode, ssh_dir, crash_worker)

    try:
        started = _run_compose(project_name, env, "up", "--detach", "--build", timeout=1200)
        assert started.returncode == 0, (
            f"could not start the remote xdist Compose cluster:\n{started.stdout}\n{started.stderr}"
        )
        runner = _run_compose(
            project_name,
            env,
            "exec",
            "-T",
            "controller",
            "python",
            "/workspace/tests/external/remote-xdist/controller_runner.py",
            "--mode",
            mode,
            *(["--crash-worker", crash_worker] if partial else []),
            timeout=1000,
        )
        output = runner.stdout + "\n" + runner.stderr
        assert f"REMOTE_XDIST_MODE={mode}" in output, output
        assert "REMOTE_XDIST_GATEWAYS=" in output, output
        if partial:
            assert runner.returncode != 0, f"the worker crash must make the pytest lane fail:\n{output}"
            assert "not relative to an rsync root" not in output, output
            diagnostic_lines = [
                line.split("=", maxsplit=1)[1]
                for line in output.splitlines()
                if line.startswith("PYTEST_CUKE_MESSAGE_DIAGNOSTIC=")
            ]
            diagnostics = [json.loads(line) for line in diagnostic_lines]
            assert any(
                diagnostic.get("code") == "interrupted_worker_transfer"
                and crash_worker in diagnostic.get("offending_ids", [])
                for diagnostic in diagnostics
            ), (
                f"expected Cucumber Messages to report the abrupt exit of xdist worker {crash_worker!r}; "
                f"got diagnostics {diagnostics!r}\n{output}"
            )
        else:
            assert runner.returncode == 0, output

        report_path = tmp_path / "messages.ndjson"
        messages = _read_report(project_name, env, report_path)
        worker_ids = _validate_report(messages)
        observations = _read_observations(project_name, env)
        assert set(observations) == worker_ids, (observations, worker_ids)
        assert all(item.get("worker_id") == worker_id for worker_id, item in observations.items()), observations
        assert all(item.get("mode") == mode for item in observations.values()), observations
        _record_remote_worker_runtimes(mode, partial, observations)

        observed_hosts = {item.get("host") for item in observations.values()}
        if mode == "via":
            assert observed_hosts == {"proxy"}, observed_hosts
        else:
            assert observed_hosts == {"worker1", "worker2"}, observed_hosts
        if mode == "ssh":
            controller = _run_compose(project_name, env, "exec", "-T", "controller", "hostname")
            assert controller.returncode == 0, controller.stdout + controller.stderr
            assert controller.stdout.strip() == "controller"
            assert controller.stdout.strip() not in observed_hosts, (
                "SSH workers must run in separate containers from the controller"
            )

        run_finished = next(message["testRunFinished"] for message in messages if "testRunFinished" in message)
        assert run_finished.get("success") is (not partial), run_finished
        if partial:
            assert crash_worker in worker_ids, worker_ids
            codes_for_crashed_worker = {
                diagnostic.get("code")
                for diagnostic in diagnostics
                if crash_worker in diagnostic.get("offending_ids", [])
            }
            assert "missing_worker_manifest" in codes_for_crashed_worker, diagnostics
            assert "partial_stream" in codes_for_crashed_worker, diagnostics
            assert "interrupted_worker_transfer" in codes_for_crashed_worker, diagnostics
    finally:
        stopped = _run_compose(project_name, env, "down", "--volumes", "--remove-orphans", timeout=180)
        if stopped.returncode != 0:
            pytest.fail(
                f"remote xdist Compose cleanup failed; check Docker daemon state:\n{stopped.stdout}\n{stopped.stderr}",
                pytrace=False,
            )


@contextmanager
def _remote_cluster(mode: str, tmp_path: Path) -> Iterator[tuple[str, dict[str, str]]]:
    """Start one Compose cluster with independent worker containers and always tear it down."""
    ssh_dir = tmp_path / "ssh"
    ssh_dir.mkdir()
    if mode == "ssh":
        _make_ssh_key(ssh_dir)
    project_name = f"pytest-cuke-remote-{uuid.uuid4().hex[:12]}"
    env = _compose_environment(mode, ssh_dir, "")
    started = _run_compose(project_name, env, "up", "--detach", "--build", timeout=1200)
    assert started.returncode == 0, (
        f"could not start the remote xdist Compose cluster:\n{started.stdout}\n{started.stderr}"
    )
    try:
        yield project_name, env
    finally:
        stopped = _run_compose(project_name, env, "down", "--volumes", "--remove-orphans", timeout=180)
        if stopped.returncode != 0:
            pytest.fail(
                f"remote xdist Compose cleanup failed; check Docker daemon state:\n{stopped.stdout}\n{stopped.stderr}",
                pytrace=False,
            )


def _run_group_barrier(
    mode: str,
    project_name: str,
    env: dict[str, str],
    *extra: str,
) -> subprocess.CompletedProcess[str]:
    return _run_compose(
        project_name,
        env,
        "exec",
        "-T",
        "controller",
        "python",
        "/workspace/tests/external/remote-xdist/controller_runner.py",
        "--mode",
        mode,
        "--group-barrier",
        *extra,
        timeout=1000,
    )


def _read_group_events(project_name: str, env: dict[str, str]) -> list[dict[str, Any]]:
    code = (
        "import json; from pathlib import Path; root=Path('/artifacts/observations/groups'); "
        "print(json.dumps([json.loads(p.read_text(encoding='utf-8')) for p in sorted(root.glob('*.json'))]))"
    )
    result = _run_compose(project_name, env, "exec", "-T", "controller", "python", "-c", code)
    assert result.returncode == 0, f"could not read remote group events:\n{result.stdout}\n{result.stderr}"
    events = json.loads(result.stdout)
    assert isinstance(events, list), f"unexpected grouped remote event payload: {result.stdout!r}"
    return events


@pytest.mark.parametrize("mode", REMOTE_MODES, ids=REMOTE_MODES)
def test_remote_xdist_group_barrier_carries_state_without_a_shared_volume(mode: str, tmp_path: Path) -> None:
    """Grouped remote workers must hold group order through the relay, not a shared directory."""
    _require_prerequisites(mode)
    with _remote_cluster(mode, tmp_path) as (project_name, env):
        runner = _run_group_barrier(mode, project_name, env)
        output = runner.stdout + "\n" + runner.stderr
        assert "REMOTE_XDIST_GROUP_BARRIER=relay=controller:8889" in output, output
        assert runner.returncode == 0, output

        events = _read_group_events(project_name, env)
        assert {event.get("mode") for event in events} == {mode}, events
        unit_timestamps = [event["timestamp_ns"] for event in events if event.get("group") == "unit"]
        integration_timestamps = [event["timestamp_ns"] for event in events if event.get("group") == "integration"]
        assert len(unit_timestamps) == 5, events
        assert len(integration_timestamps) == 1, events
        assert max(unit_timestamps) <= min(integration_timestamps), (
            f"the integration group started before every remote unit scenario settled: {events!r}"
        )
        assert {event.get("worker") for event in events} == {"gw0", "gw1"}, events
        assert not any(event.get("barrier_state_dir") for event in events), (
            "a remote worker fell back to local barrier state; grouped state must travel over the relay"
        )


@pytest.mark.parametrize("mode", REMOTE_MODES, ids=REMOTE_MODES)
def test_remote_xdist_group_barrier_names_the_dead_workers_unfinished_group(mode: str, tmp_path: Path) -> None:
    """A worker that dies before its receipt must name the open group and keep the next one closed."""
    _require_prerequisites(mode)
    with _remote_cluster(mode, tmp_path) as (project_name, env):
        runner = _run_group_barrier(mode, project_name, env, "--group-crash")
        output = runner.stdout + "\n" + runner.stderr
        assert runner.returncode != 0, f"the remote worker crash must fail the grouped run:\n{output}"
        assert "stopped before publishing terminal receipts" in output, output
        assert "'unit'" in output, output
        assert "remote-units-crash.feature" in output, output
        assert "controller:8889" in output, output

        events = _read_group_events(project_name, env)
        assert not [event for event in events if event.get("group") == "integration"], (
            f"the integration group ran even though a unit worker died: {events!r}"
        )


def _debug_environment(env: dict[str, str]) -> dict[str, str]:
    return {**env, "REMOTE_DEBUG_SECRET": REMOTE_DEBUG_SECRET}


def _start_remote_debug_run(
    mode: str,
    project_name: str,
    env: dict[str, str],
    tmp_path: Path,
) -> tuple[subprocess.Popen[str], Path]:
    log_path = tmp_path / f"remote-debug-{mode}.log"
    command = [
        "docker",
        "compose",
        "--project-name",
        project_name,
        "--file",
        str(COMPOSE_FILE),
        "exec",
        "-T",
        "controller",
        "python",
        "/workspace/tests/external/remote-xdist/controller_runner.py",
        "--mode",
        mode,
        "--debug-mcp",
    ]
    output = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(  # noqa: S603  # Fixed docker compose command and arguments.
        command,
        cwd=REPO_ROOT,
        env=env,
        stdout=output,
        stderr=subprocess.STDOUT,
        text=True,
    )
    process._pytest_cuke_log = output  # type: ignore[attr-defined]
    return process, log_path


def _wait_remote_debug_run(process: subprocess.Popen[str], log_path: Path, *, timeout: int = 600) -> tuple[int, str]:
    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        process.kill()
        process.wait(timeout=30)
        raise AssertionError(
            f"remote Debug MCP run did not finish within {timeout}s:\n{log_path.read_text(encoding='utf-8')}"
        ) from error
    finally:
        output = getattr(process, "_pytest_cuke_log", None)
        if output is not None:
            output.close()
    return returncode, log_path.read_text(encoding="utf-8")


def _run_remote_debug_client(
    project_name: str,
    env: dict[str, str],
    *arguments: str,
    timeout: int = 240,
) -> dict[str, Any]:
    result = _run_compose(
        project_name,
        env,
        "exec",
        "-T",
        "controller",
        "python",
        "/workspace/tests/external/remote-xdist/debug_client.py",
        *arguments,
        timeout=timeout,
    )
    output = result.stdout + "\n" + result.stderr
    assert result.returncode == 0, f"remote Debug MCP client failed:\n{output}"
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines, output
    observation = json.loads(lines[-1])
    assert isinstance(observation, dict), observation
    return observation


def _read_remote_debug_files(project_name: str, env: dict[str, str]) -> dict[str, str]:
    code = (
        "import json; from pathlib import Path; "
        "roots=[Path('/artifacts/debug-mcp'), "
        "Path('/workspace/tests/external/remote-xdist/project/.pytest_cache/cuke/debug-mcp')]; "
        "print(json.dumps({str(p): p.read_text(encoding='utf-8') for root in roots "
        "if root.exists() for p in root.rglob('*') if p.is_file()}))"
    )
    result = _run_compose(project_name, env, "exec", "-T", "controller", "python", "-c", code)
    assert result.returncode == 0, f"could not read remote Debug MCP files:\n{result.stdout}\n{result.stderr}"
    payload = json.loads(result.stdout)
    assert isinstance(payload, dict), payload
    return payload


def _stop_remote_worker(project_name: str, env: dict[str, str], worker_id: str) -> None:
    code = f"from pathlib import Path; Path('/artifacts/debug-stop-worker').write_text({worker_id!r}, encoding='utf-8')"
    result = _run_compose(project_name, env, "exec", "-T", "controller", "python", "-c", code)
    assert result.returncode == 0, f"could not request a remote worker stop:\n{result.stdout}\n{result.stderr}"


@pytest.mark.parametrize("mode", REMOTE_MODES, ids=REMOTE_MODES)
def test_remote_xdist_debug_mcp_attaches_releases_and_redacts(mode: str, tmp_path: Path) -> None:
    """Remote workers publish endpoints through the registry and the agent attaches across the network."""
    _require_prerequisites(mode)
    with _remote_cluster(mode, tmp_path) as (project_name, base_env):
        env = _debug_environment(base_env)
        process, log_path = _start_remote_debug_run(mode, project_name, env, tmp_path)
        try:
            observation = _run_remote_debug_client(
                project_name,
                env,
                "--action",
                "release",
                "--expected-holds",
                "2",
                "--secret",
                REMOTE_DEBUG_SECRET,
                "--output",
                "/artifacts/debug-release.json",
            )
        finally:
            returncode, output = _wait_remote_debug_run(process, log_path)

        assert returncode != 0, output
        assert f"REMOTE_XDIST_DEBUG_MCP=registry=controller:8890" in output, output
        initial = observation["initial"]
        expected_hosts = {"proxy"} if mode == "via" else {"worker1", "worker2"}
        assert {worker["host"] for worker in initial["workers"]} == expected_hosts, initial
        assert {release["endpoint_host"] for release in observation["released"]} == expected_hosts, observation
        assert all(observation["cleared"].values()), observation

        files = _read_remote_debug_files(project_name, env)
        combined = "\n".join(files.values())
        assert REMOTE_DEBUG_SECRET not in combined, "the remote Debug MCP transport or artifacts leaked a secret"
        assert "<redacted>" in combined, "the remote failure was not redacted in transported state or artifacts"
        index = json.loads(
            files["/workspace/tests/external/remote-xdist/project/.pytest_cache/cuke/debug-mcp/workers.json"]
        )
        assert index["status"] == "closed", index
        assert len(index["workers"]) == 2, index
        assert all(worker["active_failure"] is None for worker in index["workers"]), index
        assert all(worker["debugger_endpoint"] is None for worker in index["workers"]), index
        assert all(worker["inspection_endpoint"] is None for worker in index["workers"]), index


@pytest.mark.parametrize("mode", REMOTE_MODES, ids=REMOTE_MODES)
def test_remote_xdist_debug_mcp_reports_a_stopped_worker_to_the_agent(mode: str, tmp_path: Path) -> None:
    """A worker that exits during its hold is advertised as stopped instead of a stale waiting endpoint."""
    _require_prerequisites(mode)
    with _remote_cluster(mode, tmp_path) as (project_name, base_env):
        env = _debug_environment(base_env)
        process, log_path = _start_remote_debug_run(mode, project_name, env, tmp_path)
        try:
            waiting = _run_remote_debug_client(
                project_name,
                env,
                "--action",
                "wait",
                "--expected-holds",
                "2",
                "--output",
                "/artifacts/debug-wait.json",
            )
            workers = waiting["initial"]["workers"]
            target = workers[0]["worker_id"]
            _stop_remote_worker(project_name, env, target)
            crashed = _run_remote_debug_client(
                project_name,
                env,
                "--action",
                "observe-crash",
                "--worker-id",
                target,
                "--output",
                "/artifacts/debug-crash.json",
            )
            survivor = next(worker["worker_id"] for worker in workers if worker["worker_id"] != target)
            released = _run_remote_debug_client(
                project_name,
                env,
                "--action",
                "release",
                "--expected-holds",
                "1",
                "--secret",
                REMOTE_DEBUG_SECRET,
                "--output",
                "/artifacts/debug-survivor.json",
            )
        finally:
            returncode, output = _wait_remote_debug_run(process, log_path)

        assert returncode != 0, output
        record = crashed["worker"]
        assert record["worker_id"] == target, crashed
        assert record["status"] == "worker_crashed", crashed
        assert record["debugger_endpoint"] is None, crashed
        assert record["inspection_endpoint"] is None, crashed
        assert survivor in released["cleared"], (survivor, released)
        assert all(released["cleared"].values()), released

        files = _read_remote_debug_files(project_name, env)
        combined = "\n".join(files.values())
        assert REMOTE_DEBUG_SECRET not in combined, "the stopped remote worker leaked a secret"
        index = json.loads(
            files["/workspace/tests/external/remote-xdist/project/.pytest_cache/cuke/debug-mcp/workers.json"]
        )
        records = {worker["worker_id"]: worker for worker in index["workers"]}
        assert records[target]["status"] == "worker_crashed", records
        assert records[target]["debugger_endpoint"] is None, records
        assert records[survivor]["active_failure"] is None, records
