"""
`pytest_bdd.assets.docker.remote_xdist.worker_entrypoint` owns documented module behavior.

Responsibility:
    The entrypoint script executed inside each Docker worker container during remote xdist
    acceptance tests. Based on the PYTEST_REMOTE_MODE environment variable, starts either an
    execnet socket server (for socket/via/proxy modes) or an SSH daemon (for ssh mode). Uses
    os.execl to replace the current process with the server/daemon, meaning this script never
    returns normally — it transforms into the long-running worker service. For socket modes,
    runs `python -m execnet.script.socketserver 0.0.0.0:8888`. For SSH mode, sets up the SSH
    directory structure, copies the controller's public key, generates host keys, and starts
    sshd in debug foreground mode.

Reason for existence:
    Remote xdist testing requires worker containers to run services that the controller can
    connect to — either raw TCP socket servers (execnet's socketserver) or SSH daemons.
    This module encapsulates all worker-side setup into a single script that the Docker
    worker container's CMD or entrypoint can invoke. It is separate from controller_entrypoint
    because workers and controllers serve fundamentally different roles (server vs client) and
    run in different containers. The os.execl pattern is used instead of subprocess to ensure
    the worker service runs as PID 1 in the container, receiving signals correctly.

Delegates:
    - os.execl: Replaces the current process with the execnet socket server or SSH daemon
      (does not return).
    - subprocess.run: Used only for ssh-keygen -A (host key generation) before execl.
    - shutil.copy2: Copies the controller's public key to authorized_keys for SSH auth.
    - pathlib.Path: Creates /run/sshd and ~/.ssh directories with proper permissions.
    - sys.exit: Terminates for unsupported PYTEST_REMOTE_MODE values.
    - os.environ: Reads PYTEST_REMOTE_MODE to determine the startup mode.

Cohesion:
    The module has one function (main) with one purpose: start the appropriate worker service
    based on remote_mode. The branching (socket/via/proxy → execnet socketserver, ssh → sshd)
    all serves this single startup decision. No unrelated utilities or configuration.

Separation:
    - controller_entrypoint.py: The controller-side counterpart that connects to these workers;
      the worker does not import or depend on the controller.
    - DockerClusterManager: The host-side orchestrator that sets PYTEST_REMOTE_MODE and starts
      worker containers; the worker script has no Docker knowledge.

Main consumers:
    - Docker worker containers: This script is set as the container CMD/entrypoint so that
      each worker container automatically starts its appropriate service on boot.

State and side effects:
    Creates directories (/run/sshd, /root/.ssh) and files (authorized_keys) on the filesystem.
    Runs ssh-keygen -A to generate host keys. Calls os.execl which replaces the current process
    — this is a terminal side effect (the Python process ceases to exist). Reads
    PYTEST_REMOTE_MODE from os.environ. No pytest stash access.

Invariants:
    - For socket/via/proxy modes, os.execl is called and never returns.
    - For ssh mode, os.execl is called after setup and never returns.
    - For unsupported modes, sys.exit is called and never returns.
    - The script never returns normally from main() — it always ends in process replacement
      or exit.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=3
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=5
"""

import os
import shutil
import subprocess  # noqa: S404  # subprocess for SSH server setup
import sys
from pathlib import Path


def main() -> None:
    """
    `pytest_bdd.assets.docker.remote_xdist.worker_entrypoint.main` owns documented function behavior.

    Responsibility:
        Reads PYTEST_REMOTE_MODE from the environment and starts the appropriate worker service
        by replacing the current process: for "socket", "via", or "proxy" modes, execs into
        `python -m execnet.script.socketserver 0.0.0.0:8888`; for "ssh" mode, sets up SSH
        directories, copies the controller's public key to authorized_keys, generates host keys
        via ssh-keygen, and execs into `/usr/sbin/sshd -D -e` (foreground debug mode). Calls
        sys.exit for unsupported modes. This function never returns — it always ends in os.execl
        or sys.exit.

    Reason for existence:
        The worker container's sole purpose is to run a service that the controller can connect
        to. This function is the container's entry point: it translates the PYTEST_REMOTE_MODE
        env var (set by DockerClusterManager via docker-compose) into the correct service startup.
        Using os.execl rather than subprocess ensures the service runs as PID 1, properly
        receiving Docker stop signals. The SSH mode setup (directories, authorized_keys,
        ssh-keygen) is included here because it is a prerequisite for the SSH daemon to start
        correctly.

    Delegates:
        - os.execl: Replaces the current process with the execnet socket server or SSH daemon.
        - pathlib.Path: Creates directories and sets permissions for SSH setup.
        - shutil.copy2: Copies the controller's public key to authorized_keys.
        - subprocess.run: Runs ssh-keygen -A for host key generation (check=True).
        - sys.exit: Terminates for unsupported PYTEST_REMOTE_MODE values.
        - os.environ: Reads PYTEST_REMOTE_MODE.
        - sys.executable: Used as the Python interpreter path for os.execl.

    Cohesion:
        The function does exactly one thing: branch on remote_mode and exec into the right
        service. The SSH setup sub-steps (mkdir, chmod, copy2, ssh-keygen) are all prerequisites
        for the sshd exec and have no purpose outside that branch.

    Separation:
        - controller_entrypoint.main: The controller-side orchestrator that connects to the
          services started here; the worker has no awareness of the controller's test execution
          pipeline.
        - Docker worker container CMD: This function is the container's entrypoint, invoked
          automatically when the container starts.

    Main consumers:
        - Docker worker containers: Invoked as the container entrypoint (CMD or custom
          entrypoint script) when the Docker Compose cluster starts worker services.

    State and side effects:
        Creates directories (/run/sshd, /root/.ssh) and files (authorized_keys) on the
        filesystem. Generates SSH host keys via ssh-keygen. Calls os.execl which replaces
        the current process — the Python interpreter ceases to exist and is replaced by
        the target service. Reads PYTEST_REMOTE_MODE from os.environ. No pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    remote_mode = os.environ.get("PYTEST_REMOTE_MODE", "socket")

    if remote_mode in {"socket", "via", "proxy"}:
        python_executable = sys.executable
        os.execl(  # noqa: S606  # os.execl for SSH daemon startup
            python_executable,
            python_executable,
            "-m",
            "execnet.script.socketserver",
            "0.0.0.0:8888",
        )
    elif remote_mode == "ssh":
        Path("/run/sshd").mkdir(parents=True, exist_ok=True)
        ssh_dir = Path("/root/.ssh")
        ssh_dir.mkdir(parents=True, exist_ok=True)
        ssh_dir.chmod(0o700)

        pub_key = Path("/etc/pytest-bdd/controller_ed25519.pub")
        if pub_key.exists():
            auth_keys = ssh_dir / "authorized_keys"
            shutil.copy2(pub_key, auth_keys)
            auth_keys.chmod(0o600)

        subprocess.run(["ssh-keygen", "-A"], check=True)  # noqa: S607  # ssh-keygen with trusted command
        os.execl("/usr/sbin/sshd", "/usr/sbin/sshd", "-D", "-e")  # noqa: S606  # os.execl for SSH daemon startup
    else:
        sys.exit(f"Unsupported PYTEST_REMOTE_MODE: {remote_mode}")


if __name__ == "__main__":
    main()
