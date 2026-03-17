import os
import shlex
import shutil
import socket
import subprocess  # noqa: S404
import sys
import time
from pathlib import Path


def endpoint_is_ready(host: str, port: int) -> tuple[bool, OSError | None]:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True, None
    except OSError as exc:
        return False, exc


def wait_for_endpoint(host: str, port: int):
    deadline = time.monotonic() + 30.0
    last_error = None
    while time.monotonic() < deadline:
        is_ready, last_error = endpoint_is_ready(host, port)
        if is_ready:
            return
        time.sleep(0.5)
    sys.exit(f"Timed out waiting for {host}:{port}: {last_error}")


def main():
    report_path = os.environ.get("REPORT_PATH", "")
    local_report_dir = Path("/app/.pytest-bdd-remote")
    report_filename = Path(report_path).name
    # Need to keep relative to /app as requested by pytest arguments in some cases
    local_report_rel = Path(".pytest-bdd-remote") / report_filename
    local_report_path = local_report_dir / report_filename
    remote_mode = os.environ.get("PYTEST_REMOTE_MODE", "socket")
    raw_xdist_args = os.environ.get("PYTEST_XDIST_ARGS", "")
    raw_extra_pytest_args = os.environ.get("PYTEST_REMOTE_EXTRA_ARGS", "")
    raw_fail_transport_workers = os.environ.get("PYTEST_BDD_TRANSPORT_FAIL_WORKERS", "").strip()
    pytest_env = dict(os.environ)
    fake_node_root = os.environ.get("PYTEST_REMOTE_FAKE_NODE_ROOT", "").strip()
    verify_min_console_writes = os.environ.get("VERIFY_MIN_CONSOLE_WRITES", "").strip()
    verify_expect_controller_only = os.environ.get("VERIFY_EXPECT_CONTROLLER_ONLY", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }

    if fake_node_root:
        fake_node_root_path = Path(fake_node_root)
        pytest_env["PATH"] = f"{fake_node_root_path / 'fake-node-bin'}{os.pathsep}{pytest_env['PATH']}"
        pytest_env["NODE_PATH"] = str(fake_node_root_path / "fake-node-modules")
        pytest_env["FAKE_GLOBAL_NODE_MODULES_ROOT"] = str(fake_node_root_path / "fake-global-node-modules")
        pytest_env["PYTEST_BDD_FAKE_NODE_CAPTURE_DIR"] = os.environ.get(
            "PYTEST_REMOTE_FAKE_NODE_CAPTURE_DIR",
            str(fake_node_root_path / "fake-node-captures"),
        )

    local_report_dir.mkdir(parents=True, exist_ok=True)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)

    if not raw_xdist_args:
        if remote_mode == "socket":
            wait_for_endpoint("worker1", 8888)
            wait_for_endpoint("worker2", 8888)
            raw_xdist_args = "--tx socket=worker1:8888//chdir=/app --tx socket=worker2:8888//chdir=/app"
        elif remote_mode == "via":
            wait_for_endpoint("proxy", 8888)
            raw_xdist_args = "--px id=proxy//socket=proxy:8888 --tx 2*popen//via=proxy//python=python3.14//chdir=/app"
        elif remote_mode == "ssh":
            wait_for_endpoint("worker1", 22)
            wait_for_endpoint("worker2", 22)
            raw_xdist_args = (
                "--tx ssh=worker1//python=python3.14//chdir=/app --tx ssh=worker2//python=python3.14//chdir=/app"
            )
        else:
            sys.exit(f"Unsupported PYTEST_REMOTE_MODE: {remote_mode}")

    xdist_args = raw_xdist_args.split()
    extra_pytest_args = shlex.split(raw_extra_pytest_args)
    ini_override_args = []
    if raw_fail_transport_workers:
        ini_override_args = ["-o", f"pytest_bdd_transport_fail_workers={raw_fail_transport_workers}"]

    # Remote acceptance should exercise the real product path. Terminal formatter
    # runs rely on pytest-bdd-ng's automatic capture switching instead of helper-
    # injected `-s` or `--capture=no` flags.
    pytest_cmd = [
        "pytest",
        "-o",
        "log_cli=true",
        "--log-cli-level=WARNING",
        *ini_override_args,
        "--dist=load",
        *xdist_args,
        f"--messages-ndjson={local_report_rel}",
        "--pyargs",
        "tests.e2e.fixtures.remote_xdist.project.test_remote_aggregation",
        *extra_pytest_args,
        "-q",
    ]
    subprocess.run(pytest_cmd, check=False, env=pytest_env)  # noqa: S603

    verify_cmd = [
        "python",
        "-m",
        "tests.e2e.fixtures.remote_xdist.verify_report",
        str(local_report_path),
        os.environ.get("VERIFY_REPORT_MODE", "success"),
        remote_mode,
    ]
    if verify_min_console_writes:
        verify_cmd.extend(["--min-console-writes", verify_min_console_writes])
    if verify_expect_controller_only:
        verify_cmd.append("--expect-controller-only")
    subprocess.run(verify_cmd, check=True, env=pytest_env)  # noqa: S603

    shutil.copy2(local_report_path, report_path)


if __name__ == "__main__":
    main()
