"""Run one remote xdist Cucumber Messages contract inside the controller container."""

from __future__ import annotations

import argparse
from importlib.metadata import version
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path("/workspace/tests/external/remote-xdist/project")
REPORT_PATH = Path("/artifacts/messages.ndjson")


def _wait_for_tcp(host: str, port: int, *, timeout: float = 90.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: OSError | None = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError as error:
            last_error = error
            time.sleep(0.25)
    raise RuntimeError(
        f"remote xdist {host}:{port} did not become ready within {timeout:g}s: {last_error}. "
        "Check Docker Compose worker logs and the remote xdist lane prerequisites."
    )


def _ssh_config() -> None:
    private_key = Path("/run/remote-ssh/id_ed25519")
    if not private_key.is_file():
        raise RuntimeError(
            "remote xdist SSH controller has no ephemeral private key; ensure the test host can run ssh-keygen"
        )
    ssh_dir = Path("/root/.ssh")
    ssh_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    ssh_dir.chmod(0o700)
    config = ssh_dir / "config"
    config.write_text(
        "Host worker1 worker2\n"
        "  User root\n"
        "  IdentityFile /run/remote-ssh/id_ed25519\n"
        "  BatchMode yes\n"
        "  StrictHostKeyChecking no\n"
        "  UserKnownHostsFile /dev/null\n"
        "  LogLevel ERROR\n",
        encoding="utf-8",
    )
    config.chmod(0o600)


def _wait_for_ssh(host: str) -> None:
    _wait_for_tcp(host, 22)
    result = subprocess.run(
        ["ssh", host, "/usr/local/bin/python -c 'print(1)'"],
        capture_output=True,
        check=False,
        text=True,
        timeout=15,
    )
    if result.returncode != 0 or result.stdout.strip() != "1":
        details = (result.stderr or result.stdout).strip() or f"ssh exited with {result.returncode}"
        raise RuntimeError(
            f"remote xdist SSH gateway {host!r} is not usable: {details}. "
            "Install the OpenSSH client on the controller image and verify the Compose worker service."
        )


def _transport_args(mode: str) -> tuple[list[str], str]:
    if mode == "socket":
        _wait_for_tcp("worker1", 8888)
        _wait_for_tcp("worker2", 8888)
        return (
            [
                "--tx=socket=worker1:8888//chdir=/workspace",
                "--tx=socket=worker2:8888//chdir=/workspace",
            ],
            "worker1:8888,worker2:8888",
        )
    if mode == "via":
        _wait_for_tcp("proxy", 8888)
        return (
            [
                "--px=id=proxy//socket=proxy:8888",
                "--tx=2*popen//via=proxy//python=python//chdir=/workspace",
            ],
            "proxy:8888 via execnet popen workers",
        )
    if mode == "ssh":
        _ssh_config()
        _wait_for_ssh("worker1")
        _wait_for_ssh("worker2")
        return (
            [
                "--tx=ssh=worker1//python=/usr/local/bin/python//chdir=/workspace",
                "--tx=ssh=worker2//python=/usr/local/bin/python//chdir=/workspace",
            ],
            "ssh=worker1,ssh=worker2",
        )
    raise ValueError(f"unsupported remote xdist mode: {mode!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("socket", "via", "ssh"), required=True)
    parser.add_argument("--crash-worker", default="")
    args = parser.parse_args()

    Path("/artifacts/observations").mkdir(parents=True, exist_ok=True)
    Path("/artifacts/remote-mode").write_text(args.mode, encoding="utf-8")
    crash_marker = Path("/artifacts/crash-worker")
    if args.crash_worker:
        crash_marker.write_text(args.crash_worker, encoding="utf-8")
    else:
        crash_marker.unlink(missing_ok=True)
    transport_args, gateway_summary = _transport_args(args.mode)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        str(PROJECT_ROOT / "pytest.ini"),
        "--cuke-autoload",
        f"--cuke-features-dir={PROJECT_ROOT / 'features'}",
        "--cuke-strict",
        f"--cuke-messages-ndjson={REPORT_PATH}",
        "--dist=load",
        "--max-worker-restart=0",
        *transport_args,
        "-q",
    ]
    print(f"REMOTE_XDIST_MODE={args.mode}", flush=True)
    print(
        "REMOTE_XDIST_RUNTIME="
        f"python={sys.version.split()[0]},pytest={version('pytest')},pytest-xdist={version('pytest-xdist')}",
        flush=True,
    )
    print(f"REMOTE_XDIST_GATEWAYS={gateway_summary}", flush=True)
    print(f"REMOTE_XDIST_COMMAND={shlex.join(command)}", flush=True)
    result = subprocess.run(command, capture_output=True, check=False, text=True, timeout=900)
    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr, flush=True)
    if not REPORT_PATH.is_file():
        print(f"remote xdist pytest did not create its Messages report at {REPORT_PATH}", file=sys.stderr)
        return result.returncode or 2
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
