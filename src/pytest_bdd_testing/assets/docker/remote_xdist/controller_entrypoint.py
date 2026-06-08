"""Provide controller entrypoint helpers."""

import os
import shlex
import shutil
import socket
import subprocess  # noqa: S404
import sys
import time
from contextlib import suppress
from pathlib import Path


def endpoint_is_ready(host: str, port: int) -> tuple[bool, OSError | None]:
    """
    Handle endpoint is ready.

    Returns:
        Readiness flag and last socket error, if any.

    """
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True, None
    except OSError as exc:
        return False, exc


def wait_for_endpoint(host: str, port: int) -> None:
    """Handle wait for endpoint."""
    deadline = time.monotonic() + 30.0
    last_error = None
    while time.monotonic() < deadline:
        is_ready, last_error = endpoint_is_ready(host, port)
        if is_ready:
            return
        time.sleep(0.5)
    sys.exit(f"Timed out waiting for {host}:{port}: {last_error}")


def ssh_ready(host: str) -> tuple[bool, str]:
    """
    Handle ssh ready.

    Returns:
        Readiness flag and diagnostic message.

    """
    command = ["ssh", host, "/usr/local/bin/python3.14 -c 'print(1)'"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)  # noqa: S603
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if result.returncode == 0 and result.stdout.strip() == "1":
        return True, ""
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    return False, stderr or stdout or f"ssh exited with {result.returncode}"


def wait_for_ssh_ready(host: str) -> None:
    """Handle wait for ssh ready."""
    deadline = time.monotonic() + 30.0
    last_error = ""
    while time.monotonic() < deadline:
        is_ready, last_error = ssh_ready(host)
        if is_ready:
            return
        time.sleep(0.5)
    sys.exit(f"Timed out waiting for ssh readiness on {host}: {last_error}")


def _build_pytest_env() -> dict[str, str]:
    pytest_env = dict(os.environ)
    fake_node_root = os.environ.get("PYTEST_REMOTE_FAKE_NODE_ROOT", "").strip()
    if not fake_node_root:
        return pytest_env

    fake_node_root_path = Path(fake_node_root)
    pytest_env["PATH"] = f"{fake_node_root_path / 'fake-node-bin'}{os.pathsep}{pytest_env['PATH']}"
    pytest_env["NODE_PATH"] = str(fake_node_root_path / "fake-node-modules")
    pytest_env["FAKE_GLOBAL_NODE_MODULES_ROOT"] = str(fake_node_root_path / "fake-global-node-modules")
    pytest_env["PYTEST_BDD_FAKE_NODE_CAPTURE_DIR"] = os.environ.get(
        "PYTEST_REMOTE_FAKE_NODE_CAPTURE_DIR",
        str(fake_node_root_path / "fake-node-captures"),
    )
    return pytest_env


def _default_xdist_args(remote_mode: str) -> str:
    if remote_mode == "socket":
        wait_for_endpoint("worker1", 8888)
        wait_for_endpoint("worker2", 8888)
        return "--tx socket=worker1:8888//chdir=/app --tx socket=worker2:8888//chdir=/app"
    if remote_mode == "via":
        wait_for_endpoint("proxy", 8888)
        return "--px id=proxy//socket=proxy:8888 --tx 2*popen//via=proxy//python=python3.14//chdir=/app"
    if remote_mode == "ssh":
        wait_for_endpoint("worker1", 22)
        wait_for_endpoint("worker2", 22)
        wait_for_ssh_ready("worker1")
        wait_for_ssh_ready("worker2")
        return (
            "--tx ssh=worker1//python=/usr/local/bin/python3.14//chdir=/app"
            " --tx ssh=worker2//python=/usr/local/bin/python3.14//chdir=/app"
        )
    sys.exit(f"Unsupported PYTEST_REMOTE_MODE: {remote_mode}")


def _build_pytest_cmd(
    *,
    local_report_rel: Path,
    xdist_args: list[str],
    extra_pytest_args: list[str],
    ini_override_args: list[str],
) -> list[str]:
    # Remote acceptance should exercise the real product path. Terminal formatter
    # runs rely on pytest-bdd-ng's automatic capture switching instead of helper-
    # injected `-s` or `--capture=no` flags.
    return [
        "pytest",
        "-p",
        "pytest_bdd.plugin.test_group_ordering.entrypoint",
        "-o",
        "log_cli=true",
        "--log-cli-level=WARNING",
        *ini_override_args,
        "--dist=load",
        *xdist_args,
        f"--messages-ndjson={local_report_rel}",
        "--pyargs",
        "pytest_bdd_testing.assets.docker.remote_xdist.project.remote_aggregation_case",
        *extra_pytest_args,
        "-q",
    ]


def _build_verify_cmd(local_report_path: Path, *, remote_mode: str) -> list[str]:
    verify_cmd = [
        "python",
        "-m",
        "pytest_bdd_testing.assets.docker.remote_xdist.verify_report",
        str(local_report_path),
        os.environ.get("VERIFY_REPORT_MODE", "success"),
        remote_mode,
    ]
    verify_min_console_writes = os.environ.get("VERIFY_MIN_CONSOLE_WRITES", "").strip()
    verify_expect_controller_only = os.environ.get("VERIFY_EXPECT_CONTROLLER_ONLY", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if verify_min_console_writes:
        verify_cmd.extend(["--min-console-writes", verify_min_console_writes])
    if verify_expect_controller_only:
        verify_cmd.append("--expect-controller-only")
    return verify_cmd


def _make_fake_node_binaries_executable(fake_node_root: str) -> None:
    if not fake_node_root:
        return
    fake_node_bin = Path(fake_node_root) / "fake-node-bin"
    for name in ("node", "npm"):
        bin_path = fake_node_bin / name
        if bin_path.exists():
            with suppress(OSError):
                bin_path.chmod(bin_path.stat().st_mode | 0o755)


def main() -> None:
    """Run main."""
    report_path = os.environ.get("REPORT_PATH", "")
    local_report_dir = Path("/app/.pytest-bdd-remote")
    report_name = Path(report_path).name
    local_report_path = local_report_dir / report_name
    remote_mode = os.environ.get("PYTEST_REMOTE_MODE", "socket")

    local_report_dir.mkdir(parents=True, exist_ok=True)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)

    _make_fake_node_binaries_executable(os.environ.get("PYTEST_REMOTE_FAKE_NODE_ROOT", "").strip())

    raw_xdist = os.environ.get("PYTEST_XDIST_ARGS", "") or _default_xdist_args(remote_mode)

    fail_workers = os.environ.get("PYTEST_BDD_TRANSPORT_FAIL_WORKERS", "").strip()

    pytest_cmd = _build_pytest_cmd(
        local_report_rel=Path(".pytest-bdd-remote") / report_name,
        xdist_args=raw_xdist.split(),
        extra_pytest_args=shlex.split(os.environ.get("PYTEST_REMOTE_EXTRA_ARGS", "")),
        ini_override_args=["-o", f"pytest_bdd_transport_fail_workers={fail_workers}"] if fail_workers else [],
    )

    pytest_env = _build_pytest_env()
    subprocess.run(pytest_cmd, check=False, env=pytest_env)  # noqa: S603

    verify_cmd = _build_verify_cmd(local_report_path, remote_mode=remote_mode)
    subprocess.run(verify_cmd, check=True, env=pytest_env)  # noqa: S603

    shutil.copy2(local_report_path, report_path)


if __name__ == "__main__":
    main()
