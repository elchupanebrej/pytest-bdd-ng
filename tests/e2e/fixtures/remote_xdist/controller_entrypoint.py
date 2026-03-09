import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path


def wait_for_endpoint(host: str, port: int):
    deadline = time.monotonic() + 30.0
    last_error = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError as exc:
            last_error = exc
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

    pytest_cmd = [
        "pytest",
        "-o",
        "log_cli=true",
        "--log-cli-level=WARNING",
        "--dist=load",
        *xdist_args,
        "--messages-ndjson",
        str(local_report_rel),
        "--pyargs",
        "tests.e2e.fixtures.remote_xdist.project.test_remote_aggregation",
        "-q",
    ]
    subprocess.run(pytest_cmd, check=True)

    verify_cmd = [
        "python",
        "-m",
        "tests.e2e.fixtures.remote_xdist.verify_report",
        str(local_report_path),
        os.environ.get("VERIFY_REPORT_MODE", "success"),
        remote_mode,
    ]
    subprocess.run(verify_cmd, check=True)

    shutil.copy2(local_report_path, report_path)


if __name__ == "__main__":
    main()
