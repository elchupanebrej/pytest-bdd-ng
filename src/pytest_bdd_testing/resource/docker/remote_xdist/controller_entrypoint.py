"""
`pytest_bdd.assets.docker.remote_xdist.controller_entrypoint` owns documented module behavior.

Responsibility:
    The main entrypoint script executed inside the Docker controller container during remote
    xdist acceptance tests. Owns the complete test-execution pipeline: waiting for worker
    endpoints to become ready (TCP socket or SSH), building the pytest command with xdist
    arguments appropriate for the transport mode (socket/via/ssh), constructing the environment
    for pytest (including fake-node runtime injection for formatter capture tests), running
    pytest as a subprocess, verifying the NDJSON report via verify_report, and copying the
    report to the shared artifact volume. Exposes a main() function invoked by
    `docker compose exec controller python controller_entrypoint.py`.

Reason for existence:
    Remote xdist testing requires coordination between a controller and workers running in
    separate Docker containers. This module encapsulates all controller-side logic — worker
    readiness polling, xdist argument construction, fake-node runtime setup, pytest invocation,
    and report verification — into a single self-contained script that the
    DockerClusterManager.run_in_controller method can invoke. It is kept as a separate module
    (not part of the cluster manager) because it represents the "inside the container" logic
    that operates in a different environment (Linux container with Python 3.14, SSH, and the
    pytest-bdd package installed) than the host-side cluster manager. The separation also
    allows the controller logic to be tested independently by running the script directly.

Delegates:
    - endpoint_is_ready: Probes a TCP host:port for connectivity with a short timeout.
    - wait_for_endpoint: Polls endpoint_is_ready in a loop until the worker is reachable or
      30 seconds elapse, then calls sys.exit on failure.
    - ssh_ready: Tests SSH connectivity to a worker by running a simple Python command.
    - wait_for_ssh_ready: Polls ssh_ready until SSH is working or 30 seconds elapse.
    - _build_pytest_env: Constructs the environment dict for the pytest subprocess, including
      optional fake-node PATH/NODE_PATH injection.
    - _default_xdist_args: Returns the xdist --tx/--px arguments for the given remote_mode,
      blocking until worker endpoints are ready.
    - _build_pytest_cmd: Builds the full pytest command list from xdist args, extra args, and
      ini override args.
    - _build_verify_cmd: Builds the verify_report invocation command with mode and
      console-write verification flags.
    - _make_fake_node_binaries_executable: Ensures fake node/npm binaries have execute
      permissions in the fake-node runtime directory.
    - subprocess.run: Executes the pytest and verify_report commands.
    - shutil.copy2: Copies the NDJSON report from the local directory to the shared artifact path.
    - os.environ: Reads PYTEST_REMOTE_MODE, REPORT_PATH, PYTEST_REMOTE_EXTRA_ARGS,
      PYTEST_BDD_TRANSPORT_FAIL_WORKERS, PYTEST_REMOTE_FAKE_NODE_ROOT, and related variables.

Cohesion:
    Every function in this module contributes to the controller's test-execution pipeline:
    wait for workers → build environment → build pytest command → run pytest → verify report
    → copy artifacts. The functions form a clear dependency chain (endpoint_is_ready →
    wait_for_endpoint → _default_xdist_args → main) with no unrelated utilities. The module is
    a cohesive script, not a library of reusable functions.

Separation:
    - worker_entrypoint.py: The worker-side counterpart that starts execnet socket servers or
      SSH daemons; controller_entrypoint connects to those workers. They are separate because
      controller and worker run in different Docker containers with different lifecycles.
    - verify_report.py: The report verification logic invoked by the controller after pytest
      completes; separated to allow verification to be tested independently of the controller
      orchestration.
    - DockerClusterManager.run_in_controller: The host-side orchestrator that invokes this
      script; the script itself has no knowledge of Docker, Compose, or the host environment.

Main consumers:
    - DockerClusterManager.run_in_controller: Builds a `docker compose exec controller python
      controller_entrypoint.py` command that executes this script inside the controller container.
    - Direct invocation: Can be run as `python controller_entrypoint.py` inside the controller
      container for debugging.

State and side effects:
    Reads os.environ extensively for configuration (REPORT_PATH, PYTEST_REMOTE_MODE,
    PYTEST_REMOTE_EXTRA_ARGS, PYTEST_BDD_TRANSPORT_FAIL_WORKERS, PYTEST_REMOTE_FAKE_NODE_ROOT,
    PYTEST_REMOTE_FAKE_NODE_CAPTURE_DIR, VERIFY_REPORT_MODE, VERIFY_MIN_CONSOLE_WRITES,
    VERIFY_EXPECT_CONTROLLER_ONLY). Executes subprocesses (pytest, verify_report). Creates
    directories (local_report_dir, report_path parent). Modifies file permissions via chmod.
    Copies files via shutil.copy2. Writes no pytest stash.

Invariants:
    - wait_for_endpoint and wait_for_ssh_ready call sys.exit on timeout (they never return
      normally on failure).
    - _default_xdist_args calls sys.exit for unsupported remote_mode values.
    - pytest is always run before verify_report; the report file must exist before verification.
    - The report is always copied from the local path to the REPORT_PATH after verification.
    - main() is idempotent in the sense that it can be called multiple times in the same
      container, though each call runs a fresh pytest session.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

import os
import shlex
import shutil
import socket
import subprocess  # noqa: S404  # subprocess for docker container management
import sys
import time
from contextlib import suppress
from pathlib import Path


def endpoint_is_ready(host: str, port: int) -> tuple[bool, OSError | None]:
    """
    `controller_entrypoint.endpoint_is_ready` owns documented function behavior.

    Responsibility:
        Probes a TCP endpoint (host, port) for connectivity by attempting a socket connection
        with a 1-second timeout. Returns a tuple of (bool, OSError | None): True and None if
        the connection succeeds, False and the caught OSError if it fails. Does not send any
        data — the connection attempt itself is the probe. Used by wait_for_endpoint to poll
        worker readiness before the controller starts dispatching tests.

    Reason for existence:
        Docker containers start asynchronously — the container process may be running before
        the socket server inside it is accepting connections. This function provides a
        non-destructive connectivity probe (connect-and-close) that wait_for_endpoint can call
        in a polling loop. Returning the OSError alongside False allows the polling loop to
        report the last error on timeout, aiding debugging. The function is kept minimal (just
        socket.create_connection) so that the polling strategy (sleep interval, deadline) lives
        entirely in wait_for_endpoint.

    Delegates:
        - socket.create_connection: Creates a TCP connection to (host, port) with the specified
          timeout; raises OSError on failure.

    Cohesion:
        The function does exactly one thing: try a TCP connect and return success/failure.
        No retry, no logging, no environment access.

    Separation:
        - wait_for_endpoint: The polling loop that calls endpoint_is_ready repeatedly with
          a 0.5s sleep and 30s deadline. Separation keeps the probe and the retry strategy
          independently understandable.
        - ssh_ready: A different readiness probe for SSH transport mode; endpoint_is_ready
          is for raw TCP/socket modes.

    Main consumers:
        - controller_entrypoint.wait_for_endpoint: Calls endpoint_is_ready in a loop.
        - controller_entrypoint._default_xdist_args: Calls wait_for_endpoint indirectly.

    State and side effects:
        Opens and immediately closes a TCP socket (transient network I/O). No filesystem
        access, no environment reads, no pytest stash interaction. Stateless between calls.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True, None
    except OSError as exc:
        return False, exc


def wait_for_endpoint(host: str, port: int) -> None:
    """
    `controller_entrypoint.wait_for_endpoint` owns documented function behavior.

    Responsibility:
        Polls a TCP endpoint for readiness by calling endpoint_is_ready in a loop with a 0.5s
        sleep interval and a 30-second deadline. Returns normally when the endpoint becomes
        reachable. If the deadline expires, calls sys.exit with a message including the host,
        port, and last observed OSError. This is a blocking call that does not return on failure.

    Reason for existence:
        Worker containers may take several seconds to start their socket servers after the
        container process begins. This function provides a standardized 30-second readiness
        window with a 0.5s polling interval, balancing fast startup detection against busy-wait
        CPU usage. The sys.exit on failure is appropriate because the controller cannot proceed
        without workers — there is no graceful degradation path. Extracting this as a separate
        function from _default_xdist_args keeps the polling strategy isolated from the xdist
        argument construction.

    Delegates:
        - endpoint_is_ready: The single-probe function called in each loop iteration.
        - time.monotonic: Deadline tracking immune to system clock adjustments.
        - time.sleep: 0.5s backoff between probes.
        - sys.exit: Terminates the process on timeout (does not return).

    Cohesion:
        The function does one thing: poll until ready or die. The deadline management, sleep,
        and last-error tracking all serve that single purpose.

    Separation:
        - endpoint_is_ready: The single-attempt probe; wait_for_endpoint owns the retry loop.
        - wait_for_ssh_ready: The SSH-mode equivalent; kept separate because SSH readiness
          uses a different probe (ssh_ready) and has different timeout semantics.

    Main consumers:
        - controller_entrypoint._default_xdist_args: calls wait_for_endpoint for each worker
          hostname before returning xdist connection strings.

    State and side effects:
        Opens TCP connections via endpoint_is_ready (up to ~60 per call if the full 30s elapses).
        Calls sys.exit on timeout — terminates the process. No filesystem, environment, or
        pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
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
    `controller_entrypoint.ssh_ready` owns documented function behavior.

    Responsibility:
        Tests SSH connectivity to a worker host by running `ssh <host> /usr/local/bin/python3.14 -c 'print(1)'`
        with a 5-second timeout. Returns a tuple of (bool, str): True and empty string if the
        command succeeds and outputs exactly "1", False and an error description string (the
        exception message for OSError/TimeoutExpired, or the stderr/stdout/returncode for
        failed commands) otherwise. This is a one-shot probe, not a polling loop.

    Reason for existence:
        In SSH transport mode, the xdist controller connects to workers via SSH rather than raw
        TCP sockets. SSH readiness is more complex than TCP readiness — the SSH daemon must be
        running AND key-based authentication must be configured AND the Python interpreter must
        be functional. This function encapsulates the full SSH+Python readiness check into a
        single probe that wait_for_ssh_ready can poll. The exact output check ("1") ensures that
        the Python interpreter on the worker actually executes commands, not just that the SSH
        daemon accepts connections.

    Delegates:
        - subprocess.run: Executes the ssh command with capture_output, text=True, and a 5s
          timeout. Uses check=False to handle failures in-band.

    Cohesion:
        The function does exactly one thing: run an SSH command and interpret the result as
        ready/not-ready. The error-string construction (stderr, stdout, returncode fallback)
        serves only to provide diagnostic detail in the failure case.

    Separation:
        - endpoint_is_ready: Probes raw TCP connectivity for socket/via modes; ssh_ready probes
          SSH+Python readiness for ssh mode. They are separate because the SSH probe requires
          subprocess execution and output parsing, not just socket creation.
        - wait_for_ssh_ready: The polling loop that calls ssh_ready; separation keeps probe
          and retry strategy distinct.

    Main consumers:
        - controller_entrypoint.wait_for_ssh_ready: Calls ssh_ready in a polling loop.
        - controller_entrypoint._default_xdist_args: Calls wait_for_ssh_ready indirectly.

    State and side effects:
        Executes `ssh <host> ...` subprocess (network I/O). No filesystem writes, no environment
        modifications, no pytest stash access. Stateless between calls.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    command = ["ssh", host, "/usr/local/bin/python3.14 -c 'print(1)'"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)  # noqa: S603  # trusted entrypoint commands
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if result.returncode == 0 and result.stdout.strip() == "1":
        return True, ""
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    return False, stderr or stdout or f"ssh exited with {result.returncode}"


def wait_for_ssh_ready(host: str) -> None:
    """
    `controller_entrypoint.wait_for_ssh_ready` owns documented function behavior.

    Responsibility:
        Polls a worker host for SSH readiness by calling ssh_ready in a loop with a 0.5s sleep
        interval and a 30-second deadline. Returns normally when SSH+Python is confirmed working.
        Calls sys.exit with the host and last error message if the deadline expires. Mirrors the
        pattern of wait_for_endpoint but uses the SSH-specific probe.

    Reason for existence:
        SSH daemon startup inside Docker containers involves multiple steps: sshd must start,
        host keys must be generated, and the authorized_keys file must be in place. This function
        provides a 30-second readiness window with SSH-specific probing (not just TCP connect,
        but actual command execution). The sys.exit on failure is appropriate because the
        controller cannot dispatch tests to unreachable SSH workers.

    Delegates:
        - ssh_ready: The single-attempt SSH probe called in each loop iteration.
        - time.monotonic / time.sleep: Deadline tracking and poll backoff.
        - sys.exit: Terminates the process on timeout.

    Cohesion:
        The function does exactly one thing: poll SSH readiness until success or timeout death.
        All internal state (deadline, last_error) serves this single retry-loop purpose.

    Separation:
        - wait_for_endpoint: The TCP-mode polling equivalent; kept separate because the probes
          (ssh_ready vs endpoint_is_ready) and their failure messages differ.
        - ssh_ready: The single-attempt probe; wait_for_ssh_ready owns the retry loop.

    Main consumers:
        - controller_entrypoint._default_xdist_args: calls wait_for_ssh_ready for each SSH
          worker hostname.

    State and side effects:
        Executes ssh subprocess via ssh_ready (network I/O). Calls sys.exit on timeout —
        terminates the process. No filesystem, environment, or pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    deadline = time.monotonic() + 30.0
    last_error = ""
    while time.monotonic() < deadline:
        is_ready, last_error = ssh_ready(host)
        if is_ready:
            return
        time.sleep(0.5)
    sys.exit(f"Timed out waiting for ssh readiness on {host}: {last_error}")


def _build_pytest_env() -> dict[str, str]:
    """
    `controller_entrypoint._build_pytest_env` owns documented function behavior.

    Responsibility:
        Constructs the environment dictionary for the pytest subprocess by starting from
        os.environ and conditionally injecting fake-node runtime paths when
        PYTEST_REMOTE_FAKE_NODE_ROOT is set. Adds the fake-node-bin directory to PATH, sets
        NODE_PATH to fake-node-modules, FAKE_GLOBAL_NODE_MODULES_ROOT to
        fake-global-node-modules, and PYTEST_BDD_FAKE_NODE_CAPTURE_DIR to the capture
        directory (defaulting to fake-node-captures). Returns the unmodified os.environ copy
        when PYTEST_REMOTE_FAKE_NODE_ROOT is empty.

    Reason for existence:
        The live formatter capture tests ("success-live" verify mode) require a fake Node.js
        runtime to intercept @cucumber/cucumber formatter calls and verify console output.
        This function sets up the PATH and NODE_PATH so that the fake node and npm binaries
        take precedence over any real Node.js installation in the container. Keeping this as
        a separate function from main() isolates the environment-construction logic, making it
        clear which variables are set and under what conditions.

    Delegates:
        - os.environ: Read for the base environment and PYTEST_REMOTE_FAKE_NODE_ROOT.
        - pathlib.Path: Used for path construction from the fake_node_root.

    Cohesion:
        All logic serves the single purpose of "add fake-node paths to the environment if
        configured." The conditional on PYTEST_REMOTE_FAKE_NODE_ROOT gates the entire injection
        block. No unrelated configuration.

    Separation:
        - _make_fake_node_binaries_executable: Ensures the fake node/npm binaries have execute
          permissions (called before _build_pytest_env); this function only adds them to PATH.
        - _build_pytest_cmd: Uses the env dict produced here when running the pytest subprocess.

    Main consumers:
        - controller_entrypoint.main: calls _build_pytest_env() and passes the result as the
          env= parameter to subprocess.run for the pytest command.

    State and side effects:
        Copies os.environ (reads all current environment variables). No filesystem writes,
        no subprocess calls, no pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
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
    """
    `controller_entrypoint._default_xdist_args` owns documented function behavior.

    Responsibility:
        Returns the pytest-xdist `--tx` or `--px` argument string for a given remote_mode.
        Blocks until worker endpoints are confirmed ready via wait_for_endpoint or
        wait_for_ssh_ready, then returns the appropriate connection string:
        - "socket": two `--tx socket=workerN:8888//chdir=/app` for worker1 and worker2
        - "via": `--px id=proxy//socket=proxy:8888` with 2 popen workers via proxy
        - "ssh": two `--tx ssh=workerN//python=/usr/local/bin/python3.14//chdir=/app`
        Calls sys.exit for unsupported modes.

    Reason for existence:
        Each xdist transport mode requires different connection syntax (socket:// for raw TCP,
        //via=proxy for proxy-routed, ssh:// for SSH). This function encapsulates all
        transport-specific connection construction and the readiness-gating (blocking until
        workers are ready). It is kept separate from _build_pytest_cmd because the xdist args
        may be overridden via PYTEST_XDIST_ARGS environment variable, and this function only
        provides the default. The readiness blocking is included here (not in main) because
        the args cannot be constructed until workers are confirmed reachable.

    Delegates:
        - wait_for_endpoint: Blocks until worker TCP sockets are accepting connections.
        - wait_for_ssh_ready: Blocks until worker SSH daemons are ready with Python.
        - sys.exit: Terminates for unsupported remote_mode values.

    Cohesion:
        The function does one thing: given a mode, block until ready and return xdist args.
        The three branches (socket/via/ssh) all follow the same pattern: wait → return args.
        No unrelated logic.

    Separation:
        - _build_pytest_cmd: Splits the returned xdist args string and inserts it into the
          full pytest command list; xdist arg construction is separate from general pytest
          argument assembly.
        - main: Reads PYTEST_XDIST_ARGS env var first; only falls back to _default_xdist_args
          if the env var is empty.

    Main consumers:
        - controller_entrypoint.main: calls _default_xdist_args(remote_mode) when
          PYTEST_XDIST_ARGS is not set in the environment.

    State and side effects:
        Blocks on network I/O (wait_for_endpoint/wait_for_ssh_ready). May call sys.exit on
        unsupported mode. No filesystem, environment writes, or pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=5
    """
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
    """
    `controller_entrypoint._build_pytest_cmd` owns documented function behavior.

    Responsibility:
        Assembles the complete pytest command list for remote xdist execution. Returns a list
        starting with "pytest", including: log_cli configuration (-o), ini override args,
        --dist=load, the xdist connection args (split
        from the xdist_args string), the NDJSON messages output path (--messages-ndjson), the
        target test module via --pyargs, extra pytest args (e.g., --cucumber-progress), and
        -q for quiet mode. All arguments are keyword-only for clarity at the call site.

    Reason for existence:
        The pytest command for remote acceptance testing has many fixed requirements: it must
        set log_cli to suppress noisy logs, use --dist=load for xdist, output NDJSON messages to
        the report path, and collect the specific remote_aggregation_case test module. This
        function centralizes all these requirements into a single command builder, ensuring
        consistency across all transport modes and verify modes. The keyword-only parameters
        (local_report_rel, xdist_args, extra_pytest_args, ini_override_args) make the call site in
        main() self-documenting.

    Delegates:
        - None directly — the function is a pure list constructor with no subprocess or I/O.

    Cohesion:
        The function has one job: build a pytest command list. Every argument in the returned
        list is a necessary part of the remote xdist test invocation. No unrelated options or
        conditionals.

    Separation:
        - _default_xdist_args: Produces the xdist_args string consumed here; separation keeps
          transport-specific connection construction out of the general pytest command builder.
        - _build_verify_cmd: Builds the separate verify_report command that runs after pytest;
          kept separate because verification has its own CLI and arguments.

    Main consumers:
        - controller_entrypoint.main: calls _build_pytest_cmd with parameters derived from
          environment variables and _default_xdist_args output.

    State and side effects:
        None — pure list construction. No filesystem, environment, subprocess, or pytest
        stash access.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    # Remote acceptance should exercise the real product path. Terminal formatter
    # runs rely on pytest-bdd-ng's automatic capture switching instead of helper-
    # injected `-s` or `--capture=no` flags.
    return [
        "pytest",
        "-o",
        "log_cli=true",
        "--log-cli-level=WARNING",
        *ini_override_args,
        "--dist=load",
        *xdist_args,
        f"--messages-ndjson={local_report_rel}",
        "--pyargs",
        "pytest_bdd_testing.resource.docker.remote_xdist.project.remote_aggregation_case",
        *extra_pytest_args,
        "-q",
    ]


def _build_verify_cmd(local_report_path: Path, *, remote_mode: str) -> list[str]:
    """
    `controller_entrypoint._build_verify_cmd` owns documented function behavior.

    Responsibility:
        Builds the command list for invoking verify_report.py after pytest completes. The base
        command is `python -m pytest_bdd_testing.resource.docker.remote_xdist.verify_report`
        with the local report path, VERIFY_REPORT_MODE from the environment, and remote_mode.
        Conditionally appends --min-console-writes (from VERIFY_MIN_CONSOLE_WRITES env var)
        and --expect-controller-only (from VERIFY_EXPECT_CONTROLLER_ONLY env var, parsed as
        a boolean). Returns the full command list for subprocess execution.

    Reason for existence:
        The verify_report module has multiple verification modes (success, partial) and optional
        flags (--min-console-writes for live formatter capture tests, --expect-controller-only
        for controller-only capture verification). This function translates environment variables
        set by DockerClusterManager.run_in_controller into the correct CLI arguments, keeping
        the env-var-to-CLI translation in one place rather than scattering it across main().

    Delegates:
        - os.environ: Reads VERIFY_REPORT_MODE, VERIFY_MIN_CONSOLE_WRITES, and
          VERIFY_EXPECT_CONTROLLER_ONLY.

    Cohesion:
        The function has one job: build the verify_report command from environment variables.
        The conditional flag appending (--min-console-writes, --expect-controller-only) is
        directly related to the verification mode configuration.

    Separation:
        - verify_report.main: The actual verification logic lives in verify_report.py; this
          function only builds the command to invoke it.
        - _build_pytest_cmd: Builds the pytest command; _build_verify_cmd builds the
          post-pytest verification command. They are separate because they invoke different
          tools with different argument conventions.

    Main consumers:
        - controller_entrypoint.main: calls _build_verify_cmd after pytest completes and
          runs the resulting command via subprocess.run with check=True.

    State and side effects:
        Reads os.environ. No filesystem, subprocess, or pytest stash access. Pure command
        list construction.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    verify_cmd = [
        "python",
        "-m",
        "pytest_bdd_testing.resource.docker.remote_xdist.verify_report",
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
    """
    `controller_entrypoint._make_fake_node_binaries_executable` owns documented function behavior.

    Responsibility:
        Ensures the fake node and npm binaries in the fake-node runtime directory have execute
        permissions (chmod 0o755). Operates on {fake_node_root}/fake-node-bin/node and
        {fake_node_root}/fake-node-bin/npm. Silently skips missing binaries and suppresses
        OSError during chmod via contextlib.suppress. Returns immediately if fake_node_root
        is empty/falsy. This is a prerequisite for the fake-node runtime used in live
        formatter capture tests.

    Reason for existence:
        Files mounted into Docker containers from Windows host volumes may lose their execute
        permission bits. Since the fake node and npm binaries are shell scripts that must be
        executable to intercept @cucumber/cucumber formatter calls, this function ensures
        they have the correct permissions before pytest is invoked. The error suppression is
        intentional: if the fake-node setup fails, the test should still proceed (the
        formatter just won't use the fake runtime), not crash the entire controller.

    Delegates:
        - pathlib.Path: Used for path construction and stat/chmod operations.
        - contextlib.suppress: Silently ignores OSError during chmod.

    Cohesion:
        The function does exactly two permission fixes (node and npm) in the fake-node
        directory. All logic serves the "make fake binaries runnable" purpose. No unrelated
        file operations.

    Separation:
        - _build_pytest_env: Adds the fake-node-bin directory to PATH after this function
          ensures the binaries are executable. The two functions are separate because
          permission fixing (filesystem mutation) and environment construction (dict building)
          are different concerns.

    Main consumers:
        - controller_entrypoint.main: calls _make_fake_node_binaries_executable before
          _build_pytest_env to ensure the fake runtime is ready.

    State and side effects:
        Modifies file permissions on the filesystem via Path.chmod (writes). Reads file
        metadata via Path.exists and Path.stat. No environment, subprocess, or pytest
        stash access.

    Architecture score:
        #arch-eval:reason_for_existence=2
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """
    if not fake_node_root:
        return
    fake_node_bin = Path(fake_node_root) / "fake-node-bin"
    for name in ("node", "npm"):
        bin_path = fake_node_bin / name
        if bin_path.exists():
            with suppress(OSError):
                bin_path.chmod(bin_path.stat().st_mode | 0o755)


def main() -> None:
    """
    `controller_entrypoint.main` owns documented function behavior.

    Responsibility:
        The top-level orchestrator for the controller container's test execution pipeline.
        Reads configuration from environment variables (REPORT_PATH, PYTEST_REMOTE_MODE,
        PYTEST_XDIST_ARGS, PYTEST_REMOTE_EXTRA_ARGS, PYTEST_BDD_TRANSPORT_FAIL_WORKERS),
        creates necessary directories, ensures fake-node binaries are executable, builds
        the pytest command via _build_pytest_cmd (falling back to _default_xdist_args if
        PYTEST_XDIST_ARGS is not set), runs pytest as a subprocess, verifies the NDJSON
        report via _build_verify_cmd, and copies the verified report to the shared artifact
        volume path. Does not handle exceptions — failures propagate to the caller
        (DockerClusterManager.run_in_controller) which inspects the CompletedProcess result.

    Reason for existence:
        This function is the single entry point that DockerClusterManager.run_in_controller
        invokes inside the controller container. It ties together all the helper functions
        (readiness waiting, env construction, command building, execution, verification) into
        a sequential pipeline. The function is intentionally procedural (no return value) because
        it is invoked as a script entry point and its success/failure is communicated via the
        subprocess exit code, not a return value.

    Delegates:
        - os.environ: Reads all configuration variables.
        - _make_fake_node_binaries_executable: Ensures fake node/npm have execute permissions.
        - _default_xdist_args: Provides default xdist connection args when PYTEST_XDIST_ARGS
          is not set.
        - _build_pytest_cmd: Builds the pytest command list.
        - _build_pytest_env: Builds the environment dict for the pytest subprocess.
        - _build_verify_cmd: Builds the verify_report command list.
        - subprocess.run: Executes pytest (check=False) and verify_report (check=True).
        - shutil.copy2: Copies the NDJSON report to the shared artifact path.
        - pathlib.Path: Creates directories for reports.

    Cohesion:
        The function is a pure orchestrator: read config → prepare → build commands → execute
        → verify → copy. Every step is a necessary part of the controller's test execution
        pipeline. No unrelated file I/O or configuration parsing.

    Separation:
        - DockerClusterManager.run_in_controller: The host-side method that sets environment
          variables and invokes this script via docker compose exec. main() has no knowledge
          of Docker, Compose, or the host environment — it only reads env vars and runs
          subprocesses.
        - worker_entrypoint.main: The worker-side counterpart that starts socket servers or
          SSH daemons; controller main connects to those workers.

    Main consumers:
        - DockerClusterManager.run_in_controller: Invokes this function by running
          `docker compose exec controller python controller_entrypoint.py`.
        - Direct invocation: `python controller_entrypoint.py` inside the controller container.

    State and side effects:
        Reads extensive environment variables. Creates directories on the filesystem
        (local_report_dir, report_path parent). Modifies file permissions via
        _make_fake_node_binaries_executable. Executes subprocesses (pytest, verify_report).
        Copies files via shutil.copy2. Writes no pytest stash.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=5
        #arch-eval:cohesion=5
        #arch-eval:separation=5
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """
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
    subprocess.run(pytest_cmd, check=False, env=pytest_env)  # noqa: S603  # trusted entrypoint commands

    verify_cmd = _build_verify_cmd(local_report_path, remote_mode=remote_mode)
    subprocess.run(verify_cmd, check=True, env=pytest_env)  # noqa: S603  # trusted entrypoint commands

    shutil.copy2(local_report_path, report_path)


if __name__ == "__main__":
    main()
