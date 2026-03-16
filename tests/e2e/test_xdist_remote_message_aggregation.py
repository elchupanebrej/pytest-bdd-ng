from __future__ import annotations

import os
import shutil
import subprocess  # noqa: S404
import tempfile
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

pytestmark = [pytest.mark.xdist, pytest.mark.docker, pytest.mark.long_running]

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "remote_xdist"
REPORT_NAME = "remote-xdist.ndjson"
REMOTE_MODES = ("socket", "via", "ssh")


def _run_remote_xdist_compose(
    tmp_path: Path,
    *,
    remote_mode: str,
    verify_mode: str,
    fail_transport_workers: str = "",
) -> subprocess.CompletedProcess[str]:
    require_docker_daemon()

    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="pytest-bdd-remote-artifacts-", dir=repo_root) as docker_artifact_dir:
        artifact_root = Path(docker_artifact_dir)
        verification_mode = "success" if verify_mode == "success-live" else verify_mode
        env = {
            **os.environ,
            "BUILDKIT_PROGRESS": "plain",
            "REPO_ROOT": str(repo_root),
            "ARTIFACT_DIR": docker_artifact_dir,
            "REPORT_NAME": REPORT_NAME,
            "VERIFY_REPORT_MODE": verification_mode,
            "PYTEST_REMOTE_MODE": remote_mode,
            "PYTEST_BDD_TRANSPORT_FAIL_WORKERS": fail_transport_workers,
            "COMPOSE_PROJECT_NAME": (f"pytestbddremote{remote_mode}{tmp_path.name.replace('-', '').replace('_', '')}"),
        }
        if verify_mode == "success-live":
            materialize_fake_node_runtime(
                artifact_root / "fake-node-runtime", preinstalled_packages=("@cucumber/cucumber",)
            )
            env["PYTEST_REMOTE_EXTRA_ARGS"] = "--cucumber-progress"
            env["PYTEST_REMOTE_FAKE_NODE_ROOT"] = "/artifacts/fake-node-runtime"
            env["PYTEST_REMOTE_FAKE_NODE_CAPTURE_DIR"] = "/artifacts/fake-node-runtime/fake-node-captures"
            env["VERIFY_MIN_CONSOLE_WRITES"] = "2"
            env["VERIFY_EXPECT_CONTROLLER_ONLY"] = "1"
        command = [
            "docker",
            "compose",
            "-f",
            str(FIXTURE_DIR / "docker-compose.yml"),
        ]
        try:
            result = subprocess.run(  # noqa: S603
                [*command, "up", "--build", "--abort-on-container-exit", "--exit-code-from", "controller"],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
        finally:
            subprocess.run(  # noqa: S603
                [*command, "down", "--volumes", "--remove-orphans"],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )

        docker_report_path = Path(docker_artifact_dir, REPORT_NAME)
        if docker_report_path.exists():
            shutil.copy2(docker_report_path, tmp_path / REPORT_NAME)
        docker_capture_dir = artifact_root / "fake-node-runtime" / "fake-node-captures"
        if docker_capture_dir.exists():
            shutil.copytree(docker_capture_dir, tmp_path / "fake-node-captures", dirs_exist_ok=True)
    return result


@pytest.mark.parametrize("remote_mode", REMOTE_MODES, ids=REMOTE_MODES)
def test_remote_xdist_run_aggregates_into_one_ndjson(tmp_path: Path, remote_mode: str) -> None:
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
