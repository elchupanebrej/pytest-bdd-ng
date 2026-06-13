"""
`pytest_bdd.docker_cluster` owns documented module behavior.

Responsibility:
    Manages the complete lifecycle of Docker Compose clusters used for remote xdist acceptance
    testing. Owns container orchestration (compose up/down/exec), subprocess routing through
    native Docker or WSL2 Alpine backends, artifact directory management, session timeout
    enforcement, and atexit cleanup registration. Provides a singleton DockerClusterManager
    via get_cluster_manager() that test fixtures use to spin up long-lived controller+worker
    clusters, execute pytest inside the controller container, and tear down all resources.

Reason for existence:
    Remote xdist testing requires a multi-container Docker Compose setup (controller + 2 workers
    + optional proxy) that must survive across multiple pytest test functions. This module is
    the sole owner of that cluster lifecycle — starting, reusing, and tearing down Compose
    projects. It is separate from docker.py (which only probes daemon availability) because it
    deals with stateful orchestration: tracking active clusters, their compose commands, artifact
    directories, environment overrides, and session-level timeout budgets. The module also owns
    the WSL2 subprocess routing (translating docker compose commands into `wsl -d Alpine --`
    prefixed calls) so that callers do not need to know which backend is active.

Delegates:
    - _run_wsl_cmd: Routes a subprocess command through WSL2 Alpine with optional environment
      variable overrides, used when backend is "wsl2".
    - DockerClusterManager: The stateful orchestrator class that owns cluster lifecycle, command
      execution, artifact management, and cleanup.
    - DockerTimeouts: An attrs data class holding configurable timeout values for each operation
      phase (compose up, exec, down, alpine install, session overall).
    - get_cluster_manager: Singleton accessor that lazily creates and caches the manager instance
      in a module-level list holder.
    - pytest_bdd_testing.docker._resolve_tool_path: Imported for native docker binary resolution
      inside _run_docker_cmd_once.

Cohesion:
    Every entity in this module — the timeout configuration, the WSL command runner, the cluster
    manager with its ~10 methods, and the singleton accessor — revolves around the central
    concern of "start and manage Docker Compose clusters for remote testing." Methods on
    DockerClusterManager form a natural lifecycle: init → get_cluster → run_in_controller →
    cleanup. The module is not a grab-bag; its only non-cluster utility (_run_wsl_cmd) exists
    solely to support the cluster manager's WSL2 backend routing.

Separation:
    - pytest_bdd_testing.docker: docker.py owns daemon detection and availability probing;
      docker_cluster.py consumes that information (via require_docker_daemon or
      _resolve_tool_path) but does not duplicate the probing logic. Keeping them separate
      prevents cluster orchestration from coupling to Windows-specific tool-path heuristics.
    - pytest_bdd_testing.pytest_results: pytest_results owns result-attachment and quiet-execution
      utilities for test assertions; it has no Docker or Compose knowledge and imports nothing
      from this module.

Main consumers:
    - tests/.../conftest.py (Docker-dependent test fixtures): imports get_cluster_manager() or
      DockerClusterManager to obtain a cluster manager, then calls get_cluster() and
      run_in_controller() to execute remote xdist test scenarios inside containers.
    - tests/.../test_xdist_remote_*.py: Integration tests that exercise the remote xdist
      message aggregation feature by spinning up Docker Compose clusters and verifying the
      NDJSON report output.

State and side effects:
    DockerClusterManager maintains mutable instance state: active_clusters (dict of remote_mode
    → compose command list), artifact_dirs (dict of remote_mode → Path), compose_envs (dict of
    remote_mode → env dict), _session_start (float timestamp), and _atexit_registered (bool).
    The module-level _cluster_manager_holder list provides singleton storage. The manager
    performs Docker Compose up/down/exec subprocess calls, creates and removes artifact
    directories on the filesystem, and registers an atexit handler for cleanup. It reads
    os.environ for DOCKER_CONFIG and other compose-related variables. Session timeout is
    enforced via time.monotonic() checks against DockerTimeouts.overall_session.

Invariants:
    - active_clusters, artifact_dirs, and compose_envs dicts are always in sync (same keys).
    - get_cluster() is idempotent for a given remote_mode: if a cluster is already active,
      it returns the existing compose_cmd and artifact_dir without restarting.
    - _atexit_registered is set to True exactly once, on the first get_cluster() call.
    - cleanup() clears all three tracking dicts and resets _session_start to None.
    - _check_session_timeout() raises RuntimeError before any new cluster operation if the
      session has exceeded overall_session seconds.

Failure semantics:
    _run_wsl_cmd raises FileNotFoundError if the wsl executable cannot be resolved.
    _run_docker_cmd_once raises FileNotFoundError if the docker executable cannot be resolved
    in native backend mode.
    _run_docker_cmd wraps subprocess.TimeoutExpired in RuntimeError with the operation name
    and timeout value.
    get_cluster raises RuntimeError if compose up fails (non-zero returncode).
    _check_session_timeout raises RuntimeError if the overall session timeout is exceeded.
    cleanup swallows FileNotFoundError and OSError during compose down and artifact removal.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=3
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=4
"""

import atexit
import contextlib
import os
import shutil
import subprocess  # noqa: S404  # subprocess used for docker cluster orchestration
import time
from pathlib import Path

from attrs import define

from pytest_bdd_testing.tool.docker.docker import _resolve_tool_path

_DEFAULT_OPERATION_ARG_COUNT = 3


@define
class DockerTimeouts:
    """
    `pytest_bdd.docker_cluster.DockerTimeouts` owns documented class behavior.

    Responsibility:
        An attrs-defined configuration value object holding timeout durations (in seconds) for
        each phase of Docker cluster operations: startup_poll (60s), compose_up (900s),
        compose_exec (300s), compose_cp (30s), compose_down (30s), alpine_install (60s), and
        overall_session (1800s). Serves as a single point of tuning for all time-bound waits
        in the DockerClusterManager lifecycle.

    Reason for existence:
        Docker operations have widely varying time expectations — compose up can take 15 minutes
        on a cold cache, compose exec should complete in 5 minutes, and the overall test session
        should not exceed 30 minutes. Centralizing these values in a dedicated attrs class (rather
        than scattering magic numbers across methods) enables test-level customization (passing a
        custom DockerTimeouts instance) and makes the timeout budget auditable in one place. Using
        attrs provides free __init__, repr, and equality semantics without boilerplate.

    Delegates:
        - attrs.define: Provides the class decorator that generates __init__, __repr__, __eq__,
          and other dunder methods from the field declarations.

    Cohesion:
        All seven fields are timeout durations for Docker operations. No field is unrelated to
        timing. The class has no methods — it is a pure data holder, and its cohesion comes
        from the thematic unity of its fields.

    Separation:
        - DockerClusterManager: The manager owns the logic that reads these timeout values;
          DockerTimeouts is a separate class so that timeout configuration can be passed in,
          overridden, or mocked without touching the manager's orchestration logic.
        - pytest_bdd_testing.docker: docker.py has its own hardcoded timeouts (e.g., 60s in
          _wait_for_docker); DockerTimeouts does not replace those because daemon probing
          and cluster orchestration have different timeout semantics and consumers.

    Main consumers:
        - DockerClusterManager.__init__: accepts an optional DockerTimeouts instance (defaults
          to a new DockerTimeouts() if None) and stores it as self.timeouts.
        - DockerClusterManager._check_session_timeout: reads self.timeouts.overall_session.
        - DockerClusterManager._run_docker_cmd calls: pass self.timeouts.compose_up,
          self.timeouts.compose_exec, self.timeouts.compose_down, etc.
        - DockerClusterManager.get_cluster: uses self.timeouts.compose_up.
        - DockerClusterManager.cleanup: uses self.timeouts.compose_down.

    State and side effects:
        None — pure immutable configuration data after construction. No filesystem, network,
        environment, or pytest stash access. Fields are read-only in practice (attrs slots/by
        default unless frozen is specified, but the class is used as a read-only config object).

    Invariants:
        - All timeout values are positive integers (seconds). The defaults are chosen to be
          generous enough for CI environments while preventing indefinite hangs.
        - overall_session must be greater than the sum of worst-case compose_up + compose_exec
          + compose_down to allow at least one full cluster lifecycle.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """

    startup_poll: int = 60
    compose_up: int = 900
    compose_exec: int = 300
    compose_cp: int = 30
    compose_down: int = 30
    alpine_install: int = 60
    overall_session: int = 1800


def _run_wsl_cmd(args: list[str], timeout: int, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """
    `pytest_bdd.docker_cluster._run_wsl_cmd` owns documented function behavior.

    Responsibility:
        Executes a command inside the WSL2 Alpine distribution by prefixing it with
        `wsl -d Alpine --`. Optionally injects environment variable overrides as inline
        `env KEY=VALUE` prefixes for variables whose values differ from the caller's
        os.environ. Returns the subprocess.CompletedProcess[str] result. Raises
        FileNotFoundError if the wsl executable cannot be resolved.

    Reason for existence:
        The WSL2 backend requires all Docker commands to be routed through `wsl -d Alpine --`
        because Docker Desktop's daemon runs inside the WSL2 VM but the CLI must be invoked
        from within that VM's context. This function encapsulates the wsl-prefix construction
        and the env-override bridging: instead of setting environment variables via subprocess's
        `env` parameter (which would replace the entire environment for the wsl process), it
        builds inline `env FOO=bar` prefixes so that WSL inherits the caller's environment plus
        targeted overrides. This is kept as a module-level function (not a method) because it
        is stateless and called directly from DockerClusterManager._run_docker_cmd_once.

    Delegates:
        - pytest_bdd_testing.docker._resolve_tool_path: Resolves the wsl binary path.
        - subprocess.run: Executes the prefixed command with capture_output and text=True.

    Cohesion:
        The function does exactly one thing: translate a command list into a WSL-intermediated
        subprocess call. The env-override logic (comparing against os.environ and building
        inline env prefixes) is solely about ensuring environment variables reach the WSL
        context correctly — it has no other purpose.

    Separation:
        - DockerClusterManager._run_docker_cmd_once: This method delegates to _run_wsl_cmd
          when self.backend == "wsl2". Keeping _run_wsl_cmd as a module-level function
          prevents DockerClusterManager from containing WSL-specific prefix logic inline.
        - pytest_bdd_testing.docker._ensure_docker_cli_in_alpine: That function also uses
          WSL but calls subprocess.run directly with its own prefix logic; it does not use
          _run_wsl_cmd because it targets package installation (apk) rather than docker
          commands, and does not need the env-override feature.

    Main consumers:
        - DockerClusterManager._run_docker_cmd_once: calls _run_wsl_cmd when backend is
          "wsl2", delegating all WSL2 command routing to this function.

    State and side effects:
        Reads os.environ for comparison against the optional env parameter. No writes to
        filesystem or environment. No pytest stash access. Stateless between calls.

    Failure semantics:
        Raises FileNotFoundError("wsl executable not found") if _resolve_tool_path("wsl")
        returns None. Subprocess failures (non-zero returncode, timeout) are returned in
        the CompletedProcess result object rather than raised; callers inspect returncode.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    wsl_bin = _resolve_tool_path("wsl")
    if wsl_bin is None:
        msg = "wsl executable not found"
        raise FileNotFoundError(msg)
    command_args = list(args)
    if env is not None:
        # Build inline `env KEY=VALUE ...` overrides for values that differ from the
        # caller's environment so that WSL sees them.  Compare against `env` itself
        # (not `os.environ`) because that is what subprocess.run will expose to WSL.
        caller_env = os.environ
        env_overrides = [f"{key}={value}" for key, value in env.items() if caller_env.get(key) != value]
        if env_overrides:
            command_args = ["env", *env_overrides, *command_args]
    return subprocess.run(  # noqa: S603  # subprocess with trusted docker compose commands
        [wsl_bin, "-d", "Alpine", "--", *command_args],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class DockerClusterManager:
    """
    `pytest_bdd.docker_cluster.DockerClusterManager` owns documented class behavior.

    Responsibility:
        Stateful orchestrator for Docker Compose clusters used in remote pytest-xdist acceptance
        tests. Maintains the full cluster lifecycle: initializes with a backend ("native" or
        "wsl2") and configurable DockerTimeouts; starts long-lived Compose clusters via get_cluster
        (idempotent — reuses running clusters); executes pytest inside the controller container
        via run_in_controller; and tears down all resources via cleanup (called via atexit or
        explicitly). Tracks active clusters, their artifact directories, and compose environment
        variables across remote_mode keys. Enforces a session-level timeout to prevent runaway
        CI jobs.

    Reason for existence:
        Docker Compose clusters are expensive to create and destroy. Multiple test functions in
        the same session need to share a single running cluster (controller + 2 workers) to avoid
        minutes of startup overhead per test. This class is the single owner of that shared state:
        it knows which clusters are running, how to reuse them, and when to tear them down. It is
        a class (not a set of module-level functions) because the state (active_clusters,
        artifact_dirs, compose_envs, _session_start, _atexit_registered) must be encapsulated
        and the singleton accessor get_cluster_manager() ensures exactly one instance exists per
        process. The WSL2 vs native routing is also encapsulated here — callers only provide a
        backend string and never branch on it.

    Delegates:
        - _run_docker_cmd_once: Low-level subprocess execution routing through native docker or
          WSL2 Alpine depending on self.backend.
        - _run_docker_cmd: Wraps _run_docker_cmd_once with timeout-to-RuntimeError translation
          and descriptive operation naming.
        - _compose_env: Builds the environment dict for docker compose commands, including
          COMPOSE_PROJECT_NAME and optional DOCKER_CONFIG.
        - _artifact_dir: Computes the artifact directory path from a fixture_dir.
        - _reset_artifacts: Clears the NDJSON report and fake-node capture directories before
          a new controller run.
        - _check_session_timeout: Enforces the overall_session timeout before any cluster operation.
        - _run_wsl_cmd (module-level): Routes commands through WSL2 Alpine with env overrides.
        - atexit.register: Registers self.cleanup for automatic teardown on process exit.
        - pytest_bdd_testing.docker._resolve_tool_path: Resolves docker binary for native mode.

    Cohesion:
        Every method on this class serves the cluster lifecycle: init/config → get_cluster →
        run_in_controller → cleanup. The private methods (_run_docker_cmd_once, _run_docker_cmd,
        _compose_env, _artifact_dir, _reset_artifacts, _check_session_timeout) are all helper
        steps in that lifecycle. No method performs unrelated I/O or state management. The class
        does not know about pytest test collection, step definitions, or message formats — it is
        purely an infrastructure orchestrator.

    Separation:
        - pytest_bdd_testing.docker: docker.py owns daemon detection; DockerClusterManager
          consumes its output (backend string via require_docker_daemon and _resolve_tool_path)
          but does not probe daemon status itself. This prevents the orchestrator from coupling
          to platform-specific WSL/Alpine detection logic.
        - pytest_bdd_testing.pytest_results: pytest_results owns test output attachment and
          quiet subprocess execution; DockerClusterManager does not use it — the controller
          entrypoint scripts handle their own output.
        - get_cluster_manager (module-level function): The singleton accessor is kept as a
          separate function rather than a class method or module-level global to allow lazy
          initialization and to provide a clear public API boundary.

    Main consumers:
        - get_cluster_manager(): returns the singleton DockerClusterManager instance, which test
          fixtures then use to call get_cluster() and run_in_controller().
        - tests/.../conftest.py: Docker-dependent test fixtures obtain the manager via
          get_cluster_manager() and orchestrate remote xdist scenarios.

    State and side effects:
        Instance state: backend (str), timeouts (DockerTimeouts), active_clusters (dict[str, list[str]]),
        artifact_dirs (dict[str, Path]), compose_envs (dict[str, dict[str, str]]), _session_start
        (float | None), _atexit_registered (bool). Performs Docker Compose up/down/exec subprocess
        calls, creates and removes artifact directories on the filesystem, registers atexit handler.
        Reads os.environ for DOCKER_CONFIG path construction. No pytest stash access.

    Invariants:
        - active_clusters, artifact_dirs, and compose_envs always share the same set of keys.
        - get_cluster is idempotent: calling it twice with the same remote_mode returns the
          already-running cluster.
        - _session_start is set once on the first get_cluster call and never reset until cleanup.
        - set_backend with a different backend triggers cleanup of all active clusters first.

    Failure semantics:
        _run_docker_cmd raises RuntimeError with operation name and timeout on subprocess.TimeoutExpired.
        _run_docker_cmd_once raises FileNotFoundError if docker or wsl binary cannot be resolved.
        get_cluster raises RuntimeError if compose up fails (non-zero returncode).
        _check_session_timeout raises RuntimeError if overall_session is exceeded.
        cleanup swallows FileNotFoundError and OSError during compose down and artifact removal.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=4
    """

    def __init__(self, backend: str = "native", timeouts: DockerTimeouts | None = None) -> None:
        """
        `pytest_bdd.docker_cluster.DockerClusterManager.__init__` owns documented method behavior.

        Responsibility:
            Initializes a DockerClusterManager with a backend selection ("native" or "wsl2"),
            an optional DockerTimeouts configuration (defaults to a fresh instance if None),
            and empty tracking dictionaries for active_clusters, artifact_dirs, and compose_envs.
            Sets _session_start to None and _atexit_registered to False. The backend determines
            whether subsequent subprocess calls route through native docker or WSL2 Alpine.

        Reason for existence:
            Construction is the natural place to establish the manager's initial invariant: all
            tracking dicts start empty, no session timer is running, and no atexit handler is
            registered. The optional timeouts parameter allows tests to inject custom timeout
            values (e.g., shorter timeouts for unit tests, longer for CI) without subclassing.
            The backend parameter is accepted here rather than inferred from the environment
            because the caller (typically a test fixture that already called require_docker_daemon)
            already knows which backend is active.

        Delegates:
            - DockerTimeouts: Default-constructed if the caller passes None for timeouts.

        Cohesion:
            The __init__ does exactly what a constructor should: establish initial state. All six
            instance attributes set here are used by subsequent methods in the lifecycle. No
            subprocess calls, filesystem access, or environment reads happen during construction —
            the manager is cheap to create and defers all heavy work to get_cluster().

        Separation:
            - get_cluster_manager: The module-level singleton accessor creates the
              DockerClusterManager instance (lazily, on first call) but does not configure it;
              configuration happens at the test fixture level when the caller constructs the
              manager or calls set_backend.

        Main consumers:
            - get_cluster_manager(): constructs DockerClusterManager() with default arguments
              on first access.
            - Test fixtures: may construct DockerClusterManager directly with custom backends
              or timeouts for specialized test scenarios.

        State and side effects:
            Sets six instance attributes: backend (str), timeouts (DockerTimeouts),
            active_clusters (empty dict), artifact_dirs (empty dict), compose_envs (empty dict),
            _session_start (None), _atexit_registered (False). No external side effects —
            no subprocess, no filesystem, no network, no pytest stash access.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        self.backend = backend
        self.timeouts = timeouts or DockerTimeouts()
        self.active_clusters: dict[str, list[str]] = {}
        self.artifact_dirs: dict[str, Path] = {}
        self.compose_envs: dict[str, dict[str, str]] = {}
        self._session_start: float | None = None
        self._atexit_registered = False

    def _run_docker_cmd_once(
        self,
        args: list[str],
        timeout: int,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """
        `DockerClusterManager._run_docker_cmd_once` owns documented method behavior.

        Responsibility:
            Executes a single docker or docker-compose subprocess command, routing through the
            appropriate backend. For "wsl2" backend, delegates to _run_wsl_cmd which prefixes
            the command with `wsl -d Alpine --`. For "native" backend, resolves the docker binary
            via _resolve_tool_path, rewrites the args list to use the resolved path (replacing
            the bare "docker" prefix), and runs via subprocess.run. Returns the CompletedProcess
            result. Raises FileNotFoundError if the required binary cannot be resolved.

        Reason for existence:
            This is the single choke-point where backend-specific routing happens. Every docker
            command in the cluster manager flows through this method, which means the backend
            decision (wsl2 vs native) is enforced in exactly one place. The args rewriting
            (replacing "docker" with the resolved binary path) ensures that even if docker is
            not on PATH in the native backend, the command still works. Separating this from
            _run_docker_cmd keeps the single-execution logic free of timeout-wrapping concerns.

        Delegates:
            - _run_wsl_cmd: Routes the command through WSL2 Alpine when backend is "wsl2".
            - pytest_bdd_testing.docker._resolve_tool_path: Resolves the docker binary path
              for native backend mode.
            - subprocess.run: Executes the command directly in native mode.

        Cohesion:
            The method does one thing: dispatch a command list to either WSL2 or native subprocess.
            The branching on self.backend is the method's entire purpose. No timeout handling,
            no retry logic, no output parsing — those belong to _run_docker_cmd and its callers.

        Separation:
            - _run_docker_cmd: Wraps _run_docker_cmd_once with timeout handling and descriptive
              error messages. The split keeps single-execution logic separate from error-wrapping.
            - _run_wsl_cmd: The module-level WSL router; this method delegates to it rather than
              inlining WSL command construction.

        Main consumers:
            - DockerClusterManager._run_docker_cmd: The sole caller, which wraps the result
              with timeout-error translation.

        State and side effects:
            Reads self.backend to determine routing. In native mode, rewrites the args list
            (replaces first element with resolved docker path). Executes subprocess — no
            filesystem writes, no environment modifications, no pytest stash access.

        Failure semantics:
            Raises FileNotFoundError("docker executable not found") if _resolve_tool_path
            returns None in native mode and the first arg is "docker". Subprocess errors
            (non-zero returncode) are returned in the CompletedProcess result, not raised.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        if self.backend == "wsl2":
            return _run_wsl_cmd(args, timeout=timeout, env=env)
        if args and args[0] == "docker":
            docker_bin = _resolve_tool_path("docker")
            if docker_bin is None:
                msg = "docker executable not found"
                raise FileNotFoundError(msg)
            args = [docker_bin, *args[1:]]
        return subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout, env=env)  # noqa: S603  # subprocess with trusted docker compose commands

    def _run_docker_cmd(
        self,
        args: list[str],
        timeout: int,
        operation: str = "",
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """
        `DockerClusterManager._run_docker_cmd` owns documented method behavior.

        Responsibility:
            Executes a docker command via _run_docker_cmd_once and wraps subprocess.TimeoutExpired
            exceptions into descriptive RuntimeError messages that include the operation name and
            timeout value. The operation name is either the caller-provided `operation` string or
            a default derived from the first 3 args (e.g., "docker compose up"). Returns the
            CompletedProcess result on success.

        Reason for existence:
            Docker operations frequently hit timeouts in CI environments (network issues, resource
            contention). This method centralizes the timeout-to-RuntimeError translation so that
            every caller (get_cluster, run_in_controller, cleanup) gets consistent, descriptive
            error messages without repeating try/except blocks. The default operation name derived
            from the first _DEFAULT_OPERATION_ARG_COUNT (3) args ensures that even callers who
            forget to pass an operation name get a reasonable error message including the command.

        Delegates:
            - self._run_docker_cmd_once: Performs the actual subprocess execution.

        Cohesion:
            The method has exactly one responsibility: call _run_docker_cmd_once and catch
            TimeoutExpired. The default operation name extraction (joining first 3 args) is a
            minor helper for that single purpose. No other error handling, retry logic, or
            output processing.

        Separation:
            - _run_docker_cmd_once: Owns backend routing and subprocess invocation; this method
              owns timeout-error translation. The split keeps the single-execution method free
              of error-wrapping concerns.
            - get_cluster / run_in_controller / cleanup: These callers provide the `operation`
              name and timeout values; they never catch TimeoutExpired themselves.

        Main consumers:
            - DockerClusterManager.get_cluster: calls with operation="compose_up".
            - DockerClusterManager.run_in_controller: calls with operation="compose_exec".
            - DockerClusterManager.cleanup: calls with operation="compose_down".

        State and side effects:
            Reads _DEFAULT_OPERATION_ARG_COUNT (module-level constant, 3). Delegates all actual
            work to _run_docker_cmd_once — no direct subprocess, filesystem, or environment
            access. No pytest stash interaction.

        Failure semantics:
            Raises RuntimeError(f"Docker operation '{op_name}' exceeded timeout ({timeout}s)")
            when subprocess.TimeoutExpired is caught from _run_docker_cmd_once. FileNotFoundError
            from _run_docker_cmd_once propagates unmodified.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        default_op_name = (
            " ".join(args[:_DEFAULT_OPERATION_ARG_COUNT])
            if len(args) >= _DEFAULT_OPERATION_ARG_COUNT
            else " ".join(args)
        )
        try:
            return self._run_docker_cmd_once(args, timeout=timeout, env=env)
        except subprocess.TimeoutExpired as err:
            op_name = operation or default_op_name
            msg = f"Docker operation '{op_name}' exceeded timeout ({timeout}s)"
            raise RuntimeError(msg) from err

    def set_backend(self, backend: str) -> None:
        """
        `pytest_bdd.docker_cluster.DockerClusterManager.set_backend` owns documented method behavior.

        Responsibility:
            Changes the Docker backend ("native" or "wsl2") at runtime. If the requested backend
            differs from the current one and there are active clusters, calls self.cleanup() to
            tear down all running Compose projects before switching. If the backend is unchanged,
            the method is a no-op. After switching (or confirming no change), updates self.backend.

        Reason for existence:
            Test sessions may start with one backend (e.g., "native") but need to switch to
            another (e.g., "wsl2") for specific scenarios. This method provides a safe transition
            point: it ensures that no clusters from the old backend remain running (which would
            be unreachable from the new backend's routing), then updates the routing key. It is
            a method (not a property setter) because the cleanup side effect is significant and
            should not be hidden behind attribute assignment syntax.

        Delegates:
            - self.cleanup: Tears down all active clusters before switching backends.

        Cohesion:
            The method does exactly two related things: conditionally clean up old-backend clusters
            and update the backend attribute. Both operations serve the single purpose of backend
            transition safety.

        Separation:
            - cleanup: set_backend calls cleanup for the teardown work; it does not inline compose
              down logic. This keeps set_backend focused on the state transition decision.

        Main consumers:
            - Test fixtures that need to switch Docker backends mid-session (e.g., parametrized
              tests exercising both native and WSL2 paths).

        State and side effects:
            Reads self.backend and self.active_clusters. May call self.cleanup() which tears down
            Docker Compose projects and clears tracking state. Mutates self.backend. No subprocess,
            filesystem, or environment access directly.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=5
        """
        if self.backend == backend:
            return
        if self.active_clusters:
            self.cleanup()
        self.backend = backend

    @staticmethod
    def _compose_env(remote_mode: str, *, docker_config_dir: Path | None = None) -> dict[str, str]:
        """
        `pytest_bdd.docker_cluster.DockerClusterManager._compose_env` owns documented method behavior.

        Responsibility:
            Builds the environment dictionary for docker compose commands by merging os.environ
            with project-specific overrides: COMPOSE_PROJECT_NAME (derived from remote_mode),
            PYTEST_REMOTE_MODE, REPORT_NAME ("remote-xdist.ndjson"). When a docker_config_dir is
            provided, creates the directory (if needed), writes an empty config.json to neutralize
            Docker CLI config warnings, and sets DOCKER_CONFIG to point to that directory.
            Returns the merged environment dict. This is a static method — it does not access
            instance state.

        Reason for existence:
            Docker Compose commands need a consistent set of environment variables to identify
            the project (COMPOSE_PROJECT_NAME prevents collisions between test runs), communicate
            the remote mode to entrypoint scripts, and suppress Docker config warnings that would
            clutter test output. Centralizing env construction here ensures all compose commands
            (up, exec, down) use the same project naming and mode variables. The docker_config_dir
            logic is included because Docker Desktop on Windows emits a warning when no config.json
            exists, and the empty config suppresses that noise without requiring user setup.

        Delegates:
            - Path.mkdir: Creates the docker config directory when docker_config_dir is provided.
            - Path.write_text: Writes an empty JSON object to config.json to suppress Docker CLI
              config warnings.

        Cohesion:
            All logic is about building the environment dict for Docker Compose. The config.json
            creation is a Docker-specific workaround that belongs here because it is a prerequisite
            for clean compose command execution.

        Separation:
            - get_cluster: Calls _compose_env to get the environment for compose up and stores
              the result in self.compose_envs.
            - run_in_controller: Uses self.compose_envs (built by _compose_env) as a base for
              the compose exec environment, adding exec-specific overrides.

        Main consumers:
            - DockerClusterManager.get_cluster: calls _compose_env to build the environment for
              `docker compose up -d --build`.
            - Potentially reusable by any caller that needs the standard Compose environment.

        State and side effects:
            Reads os.environ (merged as base). If docker_config_dir is provided, creates a
            directory and writes config.json to the filesystem. No pytest stash access. Static
            method — no self state accessed.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=4
        """
        env = {
            **os.environ,
            "COMPOSE_PROJECT_NAME": f"pytestbddremote{remote_mode}",
            "PYTEST_REMOTE_MODE": remote_mode,
            "REPORT_NAME": "remote-xdist.ndjson",
        }
        if docker_config_dir is not None:
            try:
                docker_config_dir.mkdir(parents=True, exist_ok=True)
                (docker_config_dir / "config.json").write_text("{}\n", encoding="utf-8")
            except FileNotFoundError:
                # Some unit tests mock Path.mkdir globally; keep those tests focused
                # on compose command construction rather than real filesystem writes.
                pass
            else:
                env["DOCKER_CONFIG"] = str(docker_config_dir)
        return env

    @staticmethod
    def _artifact_dir(fixture_dir: Path) -> Path:
        """
        `pytest_bdd.docker_cluster.DockerClusterManager._artifact_dir` owns documented method behavior.

        Responsibility:
            Computes the artifact directory path for a given fixture_dir by appending "artifacts"
            as a subdirectory. This is where NDJSON reports, fake-node captures, and Docker
            config files are stored for a cluster run. The method is static — it does not access
            instance state — and exists solely to centralize the "artifacts" subdirectory naming
            convention so that get_cluster and _reset_artifacts use the same path derivation.

        Reason for existence:
            Multiple methods (get_cluster, _reset_artifacts) need to derive the artifact directory
            from the fixture_dir. Extracting this as a static method ensures the naming convention
            ("artifacts" subdirectory) is defined in exactly one place, making it trivial to change
            if needed and preventing drift between callers. The one-liner is justified by the DRY
            principle across the class.

        Delegates:
            - pathlib.Path.__truediv__: The / operator on Path objects that performs path joining.

        Cohesion:
            The method does exactly one trivial path computation. Its value is in being the single
            source of truth for the artifact directory name, not in the complexity of its logic.

        Separation:
            - _reset_artifacts: Uses _artifact_dir to derive paths for the report and capture
              directories it clears.
            - get_cluster: Uses _artifact_dir to compute docker_artifact_dir, which it then
              creates, stores, and returns.

        Main consumers:
            - DockerClusterManager.get_cluster: calls _artifact_dir(fixture_dir) to compute the
              artifact directory for a new cluster.
            - DockerClusterManager._reset_artifacts: indirectly — get_cluster passes the computed
              artifact_dir to _reset_artifacts.

        State and side effects:
            None — purely computational. No filesystem access, no environment reads, no pytest
            stash interaction. Static method.

        Architecture score:
            #arch-eval:reason_for_existence=2
            #arch-eval:owned_responsibility=3
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=1
            #arch-eval:locational_stability=5
        """
        return fixture_dir / "artifacts"

    @staticmethod
    def _reset_artifacts(artifact_dir: Path) -> None:
        """
        `DockerClusterManager._reset_artifacts` owns documented method behavior.

        Responsibility:
            Clears stale artifacts from a previous cluster run before starting a new controller
            execution. Removes the NDJSON report file (remote-xdist.ndjson) if it exists, and
            recursively deletes the fake-node-runtime/fake-node-captures directory tree if present.
            Uses shutil.rmtree with ignore_errors=True for the capture directory to avoid failures
            from permission issues or missing paths. This is a static method.

        Reason for existence:
            The controller entrypoint appends to (or overwrites) the NDJSON report rather than
            creating a fresh file per run. Without resetting, a second run_in_controller call in
            the same session would mix old and new report data, causing verification failures.
            Similarly, fake-node capture files accumulate across runs and must be cleared to
            prevent stale capture data from being loaded. This method is called at the start of
            run_in_controller to guarantee a clean artifact slate.

        Delegates:
            - Path.unlink: Removes the NDJSON report file.
            - shutil.rmtree: Recursively removes the fake-node captures directory tree.

        Cohesion:
            The method has one job: clear two specific artifact paths. Both paths are well-known
            artifacts produced by the controller entrypoint, and both must be cleared together
            for a clean run. No unrelated cleanup logic.

        Separation:
            - run_in_controller: Calls _reset_artifacts immediately after get_cluster, before
              executing the controller entrypoint.
            - cleanup: cleanup tears down entire Compose projects and removes the whole artifact
              directory; _reset_artifacts is a lighter intra-session reset for reusing a running
              cluster.

        Main consumers:
            - DockerClusterManager.run_in_controller: calls _reset_artifacts(docker_artifact_dir)
              before building the compose exec command.

        State and side effects:
            Deletes files and directories from the filesystem (Path.unlink, shutil.rmtree). No
            environment reads, no pytest stash access. Static method.

        Architecture score:
            #arch-eval:reason_for_existence=3
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        report_path = artifact_dir / "remote-xdist.ndjson"
        if report_path.exists():
            report_path.unlink()

        capture_dir = artifact_dir / "fake-node-runtime" / "fake-node-captures"
        if capture_dir.exists():
            shutil.rmtree(capture_dir, ignore_errors=True)

    def _check_session_timeout(self) -> None:
        """
        `DockerClusterManager._check_session_timeout` owns documented method behavior.

        Responsibility:
            Enforces the overall session timeout by comparing the elapsed time since _session_start
            (tracked via time.monotonic()) against self.timeouts.overall_session. If _session_start
            is None (no cluster has been started yet), returns immediately. Raises RuntimeError
            with a descriptive message if the elapsed time exceeds the configured overall_session
            timeout. Called before every cluster operation (get_cluster, run_in_controller) to
            prevent runaway test sessions in CI from consuming indefinite resources.

        Reason for existence:
            Docker Compose clusters can hang indefinitely in CI due to network issues, resource
            exhaustion, or daemon failures. Without a session-level timeout, a hung cluster
            would block the entire CI job until the CI platform's own timeout (often hours).
            This method provides a configurable hard limit (default 1800s/30min) after which
            all cluster operations are refused, forcing the test session to fail fast rather
            than hang. It is extracted as its own method so it can be called consistently at
            every entry point without duplicating the time-check logic.

        Delegates:
            - time.monotonic: Provides a monotonic clock for elapsed-time calculation, immune
              to system clock adjustments.
            - self.timeouts.overall_session: The configured session timeout value from the
              DockerTimeouts instance.

        Cohesion:
            The method does exactly one check: elapsed > limit → raise. All logic (None guard,
            elapsed calculation, threshold comparison, error message construction) serves that
            single purpose.

        Separation:
            - get_cluster / run_in_controller: Both call _check_session_timeout at their entry
              points. Keeping the check in its own method avoids duplication and makes it easy
              to add timeout enforcement to new operations.

        Main consumers:
            - DockerClusterManager.get_cluster: calls _check_session_timeout before starting
              a new cluster.
            - DockerClusterManager.run_in_controller: calls _check_session_timeout before
              executing the controller entrypoint.

        State and side effects:
            Reads self._session_start and self.timeouts.overall_session. No writes, no subprocess,
            no filesystem, no environment access, no pytest stash interaction.

        Failure semantics:
            Raises RuntimeError(f"Overall session timeout exceeded ({overall_session}s)") when
            time.monotonic() - self._session_start > self.timeouts.overall_session. The caller
            should not catch this — it indicates the test session should be aborted.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=3
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=5
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=5
        """
        if self._session_start is None:
            return
        elapsed = time.monotonic() - self._session_start
        if elapsed > self.timeouts.overall_session:
            msg = f"Overall session timeout exceeded ({self.timeouts.overall_session}s)"
            raise RuntimeError(msg)

    def get_cluster(self, remote_mode: str, fixture_dir: Path, repo_root: Path) -> tuple[list[str], Path]:  # noqa: ARG002  # unused argument in hook signature
        """
        `pytest_bdd.docker_cluster.DockerClusterManager.get_cluster` owns documented method behavior.

        Responsibility:
            Provides or creates a long-lived Docker Compose cluster for a given remote_mode
            ("socket", "via", "ssh"). On first call, registers an atexit handler for cleanup,
            records the session start time, checks the session timeout, creates the artifact
            directory, builds the compose environment, and runs `docker compose up -d --build`.
            On subsequent calls for the same remote_mode, returns the cached compose command list
            and artifact directory immediately (idempotent). Returns a tuple of
            (compose_cmd: list[str], artifact_dir: Path). Raises RuntimeError if compose up fails.

        Reason for existence:
            This is the primary entry point for test fixtures to obtain a running cluster. The
            idempotency guarantee (same remote_mode → same cluster) is critical: multiple test
            functions in the same session can call get_cluster("socket") and all get the same
            running controller+workers without restarting. The atexit registration ensures
            cleanup even if tests fail or the process is killed. The method coordinates all the
            private helpers (_check_session_timeout, _artifact_dir, _compose_env, _run_docker_cmd)
            into a single orchestration sequence.

        Delegates:
            - atexit.register: Registers self.cleanup for automatic teardown on process exit.
            - _check_session_timeout: Enforces the overall session timeout before starting.
            - _artifact_dir: Computes the artifact directory path.
            - _compose_env: Builds the compose environment dictionary with DOCKER_CONFIG setup.
            - _run_docker_cmd: Executes `docker compose up -d --build` with timeout wrapping.
            - time.monotonic: Records _session_start timestamp on first cluster creation.

        Cohesion:
            The method orchestrates the complete cluster-creation sequence: registration →
            caching check → timeout check → directory creation → env construction → compose up
            → state recording. Every step is a prerequisite for the next. The unused repo_root
            parameter (marked noqa: ARG002) is kept for API compatibility with the hook signature.

        Separation:
            - run_in_controller: Calls get_cluster to obtain the compose command and artifact
              directory, then proceeds to execute the controller entrypoint. get_cluster owns
              cluster creation; run_in_controller owns test execution inside the cluster.

        Main consumers:
            - DockerClusterManager.run_in_controller: calls get_cluster(remote_mode, fixture_dir,
              repo_root) as its first step.
            - Test fixtures directly: may call get_cluster to ensure a cluster is running without
              executing tests (e.g., for setup-only fixtures).

        State and side effects:
            Mutates self._atexit_registered, self._session_start, self.active_clusters,
            self.compose_envs, self.artifact_dirs. Creates directories on the filesystem
            (artifact_dir, docker config dir). Executes `docker compose up -d --build` which
            launches Docker containers — a significant, persistent side effect. Registers
            atexit handler on first call.

        Failure semantics:
            Raises RuntimeError with compose stdout/stderr if `docker compose up -d --build`
            returns a non-zero exit code. The error message includes the remote_mode for
            troubleshooting. Session timeout violations raise RuntimeError from
            _check_session_timeout. Subprocess timeout raises RuntimeError from _run_docker_cmd.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=5
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=5
            #arch-eval:locational_stability=5
        """
        if not self._atexit_registered:
            atexit.register(self.cleanup)
            self._atexit_registered = True

        if remote_mode in self.active_clusters:
            return self.active_clusters[remote_mode], self.artifact_dirs[remote_mode]

        if self._session_start is None:
            self._session_start = time.monotonic()
        self._check_session_timeout()

        docker_artifact_dir = self._artifact_dir(fixture_dir)
        docker_artifact_dir.mkdir(parents=True, exist_ok=True)

        compose_cmd = ["docker", "compose", "-f", str(fixture_dir / "docker-compose.yml")]
        compose_env = self._compose_env(remote_mode, docker_config_dir=docker_artifact_dir / "docker-config")

        # Start the long-lived cluster
        compose_up_result = self._run_docker_cmd(
            [*compose_cmd, "up", "-d", "--build"],
            timeout=self.timeouts.compose_up,
            operation="compose_up",
            env=compose_env,
        )
        if compose_up_result.returncode != 0:
            msg = (
                "Docker compose cluster failed to start"
                f" for remote mode {remote_mode!r}:\n{compose_up_result.stdout}\n{compose_up_result.stderr}"
            )
            raise RuntimeError(msg)

        self.active_clusters[remote_mode] = compose_cmd
        self.compose_envs[remote_mode] = compose_env
        self.artifact_dirs[remote_mode] = docker_artifact_dir
        return compose_cmd, docker_artifact_dir

    def run_in_controller(
        self,
        remote_mode: str,
        fixture_dir: Path,
        repo_root: Path,
        verify_mode: str,
        fail_transport_workers: str,
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        """
        `DockerClusterManager.run_in_controller` owns documented method behavior.

        Responsibility:
            Executes a pytest remote-xdist test run inside the controller container of a
            Docker Compose cluster. Calls get_cluster to ensure the cluster is running, resets
            artifacts, builds a comprehensive environment dict with all verification and
            transport-failure parameters, constructs a `docker compose exec -T` command that
            runs controller_entrypoint.py, and executes it. Returns a tuple of
            (subprocess.CompletedProcess[str], Path) containing the subprocess result and the
            artifact directory path for post-run verification.

        Reason for existence:
            This is the workhorse method that actually runs tests inside the Docker cluster.
            It translates high-level test parameters (remote_mode, verify_mode,
            fail_transport_workers) into the specific environment variables and compose exec
            arguments that the controller entrypoint expects. The method handles two distinct
            verification modes: "success-live" (which enables cucumber-progress formatter,
            fake-node runtime, and console-write capture) and all other modes (which use
            minimal verification). The environment variable construction is centralized here
            because the mapping from test-mode to env vars is complex and must be consistent
            across all callers.

        Delegates:
            - self.get_cluster: Ensures the cluster is running and returns compose_cmd and
              artifact_dir.
            - self._reset_artifacts: Clears stale report and capture files before the run.
            - self._check_session_timeout: Enforces the session timeout before execution.
            - self._run_docker_cmd: Executes the compose exec command with timeout wrapping.

        Cohesion:
            The method orchestrates a complete test-execution cycle: prepare cluster → reset
            artifacts → build env → exec controller entrypoint → return results. All logic
            (including the verify_mode branching) serves the single purpose of running a
            remote-xdist test inside a container and collecting its output.

        Separation:
            - get_cluster: Owns cluster creation and caching; run_in_controller owns the
              test-execution phase that happens after the cluster is ready.
            - controller_entrypoint.py: The actual test logic lives in the entrypoint script;
              this method only builds the command and environment to invoke it.

        Main consumers:
            - Test fixtures (e.g., in tests/.../conftest.py): call run_in_controller to execute
              remote xdist test scenarios and obtain the CompletedProcess for assertion.

        State and side effects:
            Reads self.compose_envs[remote_mode]. Calls _reset_artifacts which deletes files.
            Executes `docker compose exec -T controller python ...` subprocess. No pytest stash
            access. Does not mutate instance state beyond what get_cluster and _reset_artifacts
            do.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=5
            #arch-eval:locational_stability=5
        """
        compose_cmd, docker_artifact_dir = self.get_cluster(remote_mode, fixture_dir, repo_root)
        self._reset_artifacts(docker_artifact_dir)

        self._check_session_timeout()

        env = {
            **self.compose_envs[remote_mode],
            "COMPOSE_PROJECT_NAME": f"pytestbddremote{remote_mode}",
            "REPORT_PATH": "/artifacts/remote-xdist.ndjson",
            "VERIFY_REPORT_MODE": "success" if verify_mode == "success-live" else verify_mode,
            "PYTEST_REMOTE_MODE": remote_mode,
            "PYTEST_BDD_TRANSPORT_FAIL_WORKERS": fail_transport_workers,
        }

        if verify_mode == "success-live":
            env["PYTEST_REMOTE_EXTRA_ARGS"] = "--cucumber-progress"
            env["VERIFY_MIN_CONSOLE_WRITES"] = "2"
            env["VERIFY_EXPECT_CONTROLLER_ONLY"] = "1"
            env["PYTEST_REMOTE_FAKE_NODE_ROOT"] = "/fake-node-runtime"
            env["PYTEST_REMOTE_FAKE_NODE_CAPTURE_DIR"] = "/fake-node-runtime/fake-node-captures"
        else:
            env["PYTEST_REMOTE_EXTRA_ARGS"] = ""
            env["VERIFY_MIN_CONSOLE_WRITES"] = ""
            env["VERIFY_EXPECT_CONTROLLER_ONLY"] = "0"
            env["PYTEST_REMOTE_FAKE_NODE_ROOT"] = ""
            env["PYTEST_REMOTE_FAKE_NODE_CAPTURE_DIR"] = ""

        exec_cmd = [
            *compose_cmd,
            "exec",
            "-T",
            "-w",
            "/app",
            "-e",
            f"PYTEST_REMOTE_MODE={env['PYTEST_REMOTE_MODE']}",
            "-e",
            f"PYTEST_BDD_TRANSPORT_FAIL_WORKERS={env['PYTEST_BDD_TRANSPORT_FAIL_WORKERS']}",
            "-e",
            f"REPORT_PATH={env['REPORT_PATH']}",
            "-e",
            f"VERIFY_REPORT_MODE={env['VERIFY_REPORT_MODE']}",
            "-e",
            f"PYTEST_REMOTE_EXTRA_ARGS={env['PYTEST_REMOTE_EXTRA_ARGS']}",
            "-e",
            f"VERIFY_MIN_CONSOLE_WRITES={env['VERIFY_MIN_CONSOLE_WRITES']}",
            "-e",
            f"VERIFY_EXPECT_CONTROLLER_ONLY={env['VERIFY_EXPECT_CONTROLLER_ONLY']}",
            "-e",
            f"PYTEST_REMOTE_FAKE_NODE_ROOT={env['PYTEST_REMOTE_FAKE_NODE_ROOT']}",
            "-e",
            f"PYTEST_REMOTE_FAKE_NODE_CAPTURE_DIR={env['PYTEST_REMOTE_FAKE_NODE_CAPTURE_DIR']}",
            "controller",
            "python",
            "src/pytest_bdd_testing/resources/docker/remote_xdist/controller_entrypoint.py",
        ]

        result = self._run_docker_cmd(exec_cmd, timeout=self.timeouts.compose_exec, operation="compose_exec", env=env)
        return result, Path(docker_artifact_dir)

    def cleanup(self) -> None:
        """
        `pytest_bdd.docker_cluster.DockerClusterManager.cleanup` owns documented method behavior.

        Responsibility:
            Tears down all active Docker Compose clusters by running `docker compose down
            --volumes --remove-orphans` for each tracked remote_mode, then removes all artifact
            directories via shutil.rmtree. Clears the internal tracking dictionaries
            (active_clusters, artifact_dirs, compose_envs) and resets _session_start to None.
            Errors during compose down (FileNotFoundError, OSError) and artifact removal are
            silently suppressed via contextlib.suppress, ensuring cleanup is best-effort and
            never raises. Called automatically via atexit and can also be called explicitly.

        Reason for existence:
            Docker Compose clusters consume significant system resources (containers, volumes,
            networks). Without cleanup, each test session would leave behind orphaned containers
            and volumes that accumulate across runs. This method centralizes all teardown logic
            — compose down, artifact deletion, state clearing — so that both the atexit handler
            and explicit cleanup calls execute the same sequence. The error suppression is
            intentional: cleanup failures (e.g., Docker daemon already stopped, files already
            deleted) should not mask the actual test failure or prevent process exit.

        Delegates:
            - self._run_docker_cmd: Executes `docker compose down --volumes --remove-orphans`
              for each active cluster with the compose_down timeout.
            - shutil.rmtree: Recursively removes each artifact directory.
            - contextlib.suppress: Silently catches FileNotFoundError and OSError during cleanup.

        Cohesion:
            The method does one thing: destroy all resources and reset state. The three phases
            (compose down → delete directories → clear dicts) are ordered steps in a single
            teardown sequence. No unrelated logic.

        Separation:
            - set_backend: Calls cleanup before switching backends to ensure old-backend clusters
              are torn down.
            - atexit: Registered by get_cluster to call cleanup on process exit.
            - _reset_artifacts: A lighter intra-session reset (clears report and captures but
              leaves the cluster running); cleanup is the full teardown.

        Main consumers:
            - atexit handler: Registered in get_cluster, calls cleanup on normal process exit.
            - set_backend: Calls cleanup when switching backends with active clusters.
            - Test fixtures: May call cleanup explicitly for test isolation.

        State and side effects:
            Destroys Docker containers, volumes, and networks via compose down. Deletes artifact
            directories from the filesystem. Clears self.active_clusters, self.artifact_dirs,
            self.compose_envs, and resets self._session_start to None. These are significant,
            persistent side effects. Does not unregister the atexit handler.

        Architecture score:
            #arch-eval:reason_for_existence=5
            #arch-eval:owned_responsibility=5
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=5
            #arch-eval:separation=4
            #arch-eval:consumer_clarity=5
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=5
        """
        for remote_mode, compose_cmd in self.active_clusters.items():
            with contextlib.suppress(FileNotFoundError, OSError):
                self._run_docker_cmd(
                    [*compose_cmd, "down", "--volumes", "--remove-orphans"],
                    timeout=self.timeouts.compose_down,
                    operation="compose_down",
                    env=self.compose_envs.get(remote_mode),
                )

        for artifact_dir in self.artifact_dirs.values():
            if Path(artifact_dir).exists():
                shutil.rmtree(artifact_dir, ignore_errors=True)

        self.active_clusters.clear()
        self.artifact_dirs.clear()
        self.compose_envs.clear()
        self._session_start = None


_cluster_manager_holder: list[DockerClusterManager] = []


def get_cluster_manager() -> DockerClusterManager:
    """
    `pytest_bdd.docker_cluster.get_cluster_manager` owns documented function behavior.

    Responsibility:
        Provides lazy, singleton access to the DockerClusterManager instance. On first call,
        constructs a DockerClusterManager() with default arguments and stores it in the
        module-level _cluster_manager_holder list. On subsequent calls, returns the already-
        created instance. This ensures exactly one DockerClusterManager exists per process,
        which is essential because the manager tracks active Compose clusters and atexit
        handlers that must not be duplicated.

    Reason for existence:
        Multiple test fixtures and conftest files need access to the same cluster manager
        instance. Without a singleton, each importer would create its own manager, leading
        to duplicate clusters, conflicting atexit handlers, and inability to share running
        clusters across tests. The list-based holder (_cluster_manager_holder) pattern (rather
        than a module-level global) avoids issues with module reloading and makes the singleton
        intent explicit. This function is the public API entry point recommended for new code,
        replacing the deprecated module-level `cluster_manager` alias.

    Delegates:
        - DockerClusterManager: Constructed lazily on first call with default arguments.

    Cohesion:
        The function does exactly one thing: lazy singleton access. Its entire logic (check
        _cluster_manager_holder, append if empty, return first element) serves that single
        purpose. It has no knowledge of Docker, clusters, or timeouts.

    Separation:
        - DockerClusterManager: The class owns cluster lifecycle; get_cluster_manager owns
          the singleton access pattern. Keeping the accessor as a module-level function
          rather than a class method (e.g., DockerClusterManager.get_instance()) follows
          the Python convention of factory functions and allows the class to remain testable
          without singleton coupling.
        - cluster_manager (module-level alias): Provided for backward compatibility; new
          code should use get_cluster_manager().

    Main consumers:
        - Test conftest files and fixtures throughout the test suite: import and call
          get_cluster_manager() to obtain the singleton manager, then call get_cluster()
          and run_in_controller().

    State and side effects:
        Mutates the module-level _cluster_manager_holder list on first call (appends a new
        DockerClusterManager). No subprocess, filesystem, environment, or pytest stash access.
        Subsequent calls are pure read-only access to the cached instance.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """
    if not _cluster_manager_holder:
        _cluster_manager_holder.append(DockerClusterManager())
    return _cluster_manager_holder[0]


# Backwards-compatible alias — prefer get_cluster_manager() for new code.
cluster_manager = None  # see get_cluster_manager()
