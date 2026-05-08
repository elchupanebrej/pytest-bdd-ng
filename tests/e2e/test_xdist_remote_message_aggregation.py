"""Provide test xdist remote message aggregation helpers."""

from __future__ import annotations

import os
import shutil
import subprocess  # noqa: S404 - test intentionally exercises subprocess-driven integration flow
from pathlib import Path

import pytest
from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]

from pytest_bdd.model.message_validation import validate_message_stream
from tests.messages.message_stream_assertions import (
    assert_single_output_file,
    count_payload_kinds,
    gateway_modes_for_payloads,
    parse_ndjson_messages,
    worker_ids_for_payloads,
)
from tests.support.cucumber_formatters import (
    assert_pytest_terminal_reporter_suppressed,
    expected_formatter_visible_line,
    materialize_fake_node_runtime,
    read_fake_formatter_telemetry,
)
from tests.support.docker import require_docker_daemon

pytestmark = [pytest.mark.xdist, pytest.mark.docker, pytest.mark.slow]

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "remote_xdist"
REPORT_NAME = "remote-xdist.ndjson"
REMOTE_MODES = ("socket", "via", "ssh")


def _run_local_xdist(  # noqa: C901
    tmp_path: Path,
    *,
    remote_mode: str,
    verify_mode: str,
    fail_transport_workers: str = "",
) -> subprocess.CompletedProcess[str]:
    import socket
    import sys
    import time

    def endpoint_is_ready(host: str, port: int) -> tuple[bool, OSError | None]:
        try:
            with socket.create_connection((host, port), timeout=0.1):
                return True, None
        except OSError as exc:
            return False, exc

    def wait_for_endpoint(host: str, port: int):
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            is_ready, _ = endpoint_is_ready(host, port)
            if is_ready:
                return
            time.sleep(0.1)
        msg = f"Timed out waiting for {host}:{port}"
        raise RuntimeError(msg)

    env = dict(os.environ)
    servers = []

    # Start local socket servers
    if remote_mode == "socket":
        servers.extend(
            (
                subprocess.Popen(
                    [sys.executable, "-m", "execnet.script.socketserver", "127.0.0.1:8888"],
                    env=env,
                ),
                subprocess.Popen(
                    [sys.executable, "-m", "execnet.script.socketserver", "127.0.0.1:8889"],
                    env=env,
                ),
            )
        )
        wait_for_endpoint("127.0.0.1", 8888)
        wait_for_endpoint("127.0.0.1", 8889)
        socket_chdir = tmp_path.as_posix()
        raw_xdist_args = (
            f"--tx socket=127.0.0.1:8888//chdir={socket_chdir} --tx socket=127.0.0.1:8889//chdir={socket_chdir}"
        )
    elif remote_mode == "via":
        servers.append(
            subprocess.Popen(
                [sys.executable, "-m", "execnet.script.socketserver", "127.0.0.1:8888"],
                env=env,
            )
        )
        wait_for_endpoint("127.0.0.1", 8888)
        raw_xdist_args = (
            f"--px id=proxy//socket=127.0.0.1:8888 --tx 2*popen//via=proxy//python={sys.executable}//chdir={tmp_path}"
        )
    else:
        msg = f"Unsupported local mode: {remote_mode}"
        raise ValueError(msg)

    xdist_args = raw_xdist_args.split()
    ini_override_args = []
    if fail_transport_workers:
        ini_override_args = ["-o", f"pytest_bdd_transport_fail_workers={fail_transport_workers}"]

    if verify_mode == "success-live":
        materialize_fake_node_runtime(tmp_path / "fake-node-runtime", preinstalled_packages=("@cucumber/cucumber",))
        fake_node_root_path = tmp_path / "fake-node-runtime"
        env["PATH"] = f"{fake_node_root_path / 'fake-node-bin'}{os.pathsep}{env.get('PATH', '')}"
        env["NODE_PATH"] = str(fake_node_root_path / "fake-node-modules")
        env["FAKE_GLOBAL_NODE_MODULES_ROOT"] = str(fake_node_root_path / "fake-global-node-modules")
        env["PYTEST_BDD_FAKE_NODE_CAPTURE_DIR"] = str(tmp_path / "fake-node-captures")
        extra_args = ["--cucumber-progress"]
    else:
        extra_args = []

    repo_root = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(repo_root / "src"), env.get("PYTHONPATH", "")]))

    report_path = tmp_path / REPORT_NAME

    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-o",
        "log_cli=true",
        "--log-cli-level=WARNING",
        *ini_override_args,
        "--dist=load",
        *xdist_args,
        f"--messages-ndjson={report_path}",
        "--pyargs",
        "tests.e2e.fixtures.remote_xdist.project.test_remote_aggregation",
        *extra_args,
        "-q",
    ]

    try:
        pytest_result = subprocess.run(pytest_cmd, capture_output=True, text=True, env=env, check=False)

        # Verify step
        verify_cmd = [
            sys.executable,
            "-m",
            "tests.e2e.fixtures.remote_xdist.verify_report",
            str(report_path),
            "success" if verify_mode == "success-live" else verify_mode,
            remote_mode,
        ]
        if verify_mode == "success-live":
            verify_cmd.extend(["--min-console-writes", "2", "--expect-controller-only"])

        subprocess.run(verify_cmd, capture_output=True, text=True, env=env, check=False)

        return pytest_result
    finally:
        for p in servers:
            p.terminate()
            p.wait()


def _run_remote_xdist_compose(
    tmp_path: Path,
    *,
    remote_mode: str,
    verify_mode: str,
    fail_transport_workers: str = "",
) -> subprocess.CompletedProcess[str]:
    original_cwd = Path.cwd()
    if remote_mode in {"socket", "via"}:
        try:
            return _run_local_xdist(
                tmp_path,
                remote_mode=remote_mode,
                verify_mode=verify_mode,
                fail_transport_workers=fail_transport_workers,
            )
        finally:
            os.chdir(original_cwd)

    from tests.support.docker_cluster import cluster_manager

    try:
        cluster_manager.set_backend(require_docker_daemon())
        repo_root = Path(__file__).resolve().parents[2]

        if verify_mode == "success-live":
            _, artifact_dir = cluster_manager.get_cluster(remote_mode, FIXTURE_DIR, repo_root)
            materialize_fake_node_runtime(
                Path(artifact_dir) / "fake-node-runtime", preinstalled_packages=("@cucumber/cucumber",)
            )

        result, docker_artifact_dir = cluster_manager.run_in_controller(
            remote_mode, FIXTURE_DIR, repo_root, verify_mode, fail_transport_workers
        )

        docker_report_path = docker_artifact_dir / "remote-xdist.ndjson"
        if docker_report_path.exists():
            shutil.copy2(docker_report_path, tmp_path / REPORT_NAME)

        docker_capture_dir = docker_artifact_dir / "fake-node-runtime" / "fake-node-captures"
        if docker_capture_dir.exists():
            shutil.copytree(docker_capture_dir, tmp_path / "fake-node-captures", dirs_exist_ok=True)

        return result
    finally:
        os.chdir(original_cwd)


@pytest.mark.parametrize("remote_mode", REMOTE_MODES, ids=REMOTE_MODES)
def test_remote_xdist_run_aggregates_into_one_ndjson(tmp_path: Path, remote_mode: str) -> None:
    """Verify remote xdist run aggregates into one ndjson."""
    result = _run_remote_xdist_compose(tmp_path, remote_mode=remote_mode, verify_mode="success")

    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    ndjson_path = assert_single_output_file([tmp_path / REPORT_NAME])
    messages = parse_ndjson_messages(ndjson_path)
    validation_result = validate_message_stream(messages, track_coverage=False)
    payload_counts = count_payload_kinds(messages)
    worker_ids = worker_ids_for_payloads(messages, CucumberTestCaseStarted)
    gateway_modes = gateway_modes_for_payloads(messages, CucumberTestCaseStarted)

    assert validation_result.status == "pass"
    assert payload_counts["meta"] == 1
    assert payload_counts["test_run_started"] == 1
    assert payload_counts["test_run_finished"] == 1
    assert len(worker_ids) >= 2
    assert gateway_modes == {remote_mode}


@pytest.mark.parametrize("remote_mode", REMOTE_MODES, ids=REMOTE_MODES)
def test_remote_xdist_partial_worker_transport_still_emits_one_report(tmp_path: Path, remote_mode: str) -> None:
    """Verify remote xdist partial worker transport still emits one report."""
    result = _run_remote_xdist_compose(
        tmp_path,
        remote_mode=remote_mode,
        verify_mode="partial",
        fail_transport_workers="gw1",
    )

    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    ndjson_path = assert_single_output_file([tmp_path / REPORT_NAME])
    messages = parse_ndjson_messages(ndjson_path)
    validation_result = validate_message_stream(messages, track_coverage=False)
    payload_counts = count_payload_kinds(messages)
    worker_ids = worker_ids_for_payloads(messages, CucumberTestCaseStarted)
    gateway_modes = gateway_modes_for_payloads(messages, CucumberTestCaseStarted)
    output = result.stdout + "\n" + result.stderr

    assert validation_result.status == "pass"
    assert payload_counts["meta"] == 1
    assert payload_counts["test_run_started"] == 1
    assert payload_counts["test_run_finished"] == 1
    assert len(worker_ids) == 1
    assert gateway_modes == {remote_mode}
    assert "Worker transport data for 'gw1' was not registered." in output
    assert "Worker transfer for 'gw1' was interrupted:" in output
    assert "Worker fragment for 'gw1' is incomplete." in output


@pytest.mark.parametrize("remote_mode", REMOTE_MODES, ids=REMOTE_MODES)
def test_remote_xdist_live_formatter_stream_is_rendered_once_by_controller(tmp_path: Path, remote_mode: str) -> None:
    """Verify remote xdist live formatter stream is rendered once by controller."""
    result = _run_remote_xdist_compose(tmp_path, remote_mode=remote_mode, verify_mode="success-live")

    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    ndjson_path = assert_single_output_file([tmp_path / REPORT_NAME])
    messages = parse_ndjson_messages(ndjson_path)
    validation_result = validate_message_stream(messages, track_coverage=False)
    payload_counts = count_payload_kinds(messages)
    worker_ids = worker_ids_for_payloads(messages, CucumberTestCaseStarted)
    gateway_modes = gateway_modes_for_payloads(messages, CucumberTestCaseStarted)
    output = result.stdout + "\n" + result.stderr

    assert validation_result.status == "pass"
    assert payload_counts["meta"] == 1
    assert payload_counts["test_run_started"] == 1
    assert payload_counts["test_run_finished"] == 1
    assert len(worker_ids) >= 2
    assert gateway_modes == {remote_mode}
    assert output.count(expected_formatter_visible_line("progress")) == 1
    assert_pytest_terminal_reporter_suppressed(output)

    telemetry = read_fake_formatter_telemetry(tmp_path)

    assert len(telemetry) == 1
    assert telemetry[0]["sourceMode"] == "stdin"
    assert telemetry[0]["formatterNames"] == ["progress"]
    assert telemetry[0]["emittedVisibleOutputDuringStream"] is True
    assert int(telemetry[0]["consoleWriteCount"]) >= 2
    assert int(telemetry[0]["envelopeCount"]) > 0
    assert set(telemetry[0]["workerIds"]).issuperset({f"{remote_mode}:gw0", f"{remote_mode}:gw1"})
