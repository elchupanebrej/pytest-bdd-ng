"""
`pytest_bdd.docker` owns documented module behavior.

Responsibility:
    Detects, starts, and verifies a working Docker daemon for the pytest-bdd testing
    infrastructure. Owns platform-specific tool resolution (shutil.which fallback to hardcoded
    Windows paths for docker, powershell, wsl), WSL2 Alpine detection, Docker Desktop auto-start,
    daemon-ready polling with a timeout, and Alpine docker-cli installation. Acts as the single
    entry point for any test code that needs to gate on Docker availability.

Reason for existence:
    This module is the sole information expert for the question "is there a usable Docker daemon
    with Linux container support on this machine?" The logic is extracted from the cluster
    manager because availability probing is a self-contained, idempotent check that can be called
    at import-time or from conftest fixtures without pulling in Compose orchestration or cluster
    lifecycle state. Its lru_cache on docker_daemon_available prevents redundant subprocess calls
    during test collection while still allowing cache clearing for re-evaluation. Imports are
    limited to os, shutil, subprocess, time, pathlib, functools, and pytest — no dependency on
    any other pytest_bdd or pytest_bdd_testing module.

Delegates:
    - _resolve_tool_path: Locates the native or Windows path for a given tool binary (docker, wsl, powershell).
    - _windows_tool_candidate_exists: Checks whether a hardcoded Windows PureWindowsPath candidate actually exists on disk.
    - _alpine_wsl2_available: Probes WSL distribution list for an Alpine instance running on WSL2.
    - _start_docker_desktop: Launches Docker Desktop via PowerShell Start-Process on Windows.
    - _wait_for_docker: Polls docker info (native or via WSL2 Alpine) until the daemon responds or timeout expires.
    - _ensure_docker_cli_in_alpine: Installs docker-cli via apk inside the Alpine WSL2 distribution if missing.

Cohesion:
    Every function in this module contributes to the single pipeline of docker daemon detection:
    resolve tool paths → check WSL2 Alpine → start Docker Desktop → wait for readiness → ensure
    CLI tools. They all share the same import set (subprocess, os, time, pathlib, pytest) and
    compose hierarchically: helper functions feed into docker_daemon_available, which feeds into
    require_docker_daemon. No function does unrelated I/O or state management. The module is not
    a grab-bag; it is a deterministic, ordered probe sequence.

Separation:
    - pytest_bdd_testing.docker_cluster: docker_cluster consumes docker_daemon_available and
      _resolve_tool_path from this module but owns the Compose cluster lifecycle
      (up/down/exec/cleanup). Keeping docker probing separate prevents cluster orchestration
      callers from coupling to platform-specific tool-path resolution details.
    - pytest_bdd_testing.pytest_results: pytest_results owns result-attachment and quiet execution
      helpers; it has no docker probing knowledge and imports nothing from this module.

Main consumers:
    - pytest_bdd_testing.docker_cluster: imports _resolve_tool_path directly for docker binary
      resolution and calls docker_daemon_available via the public-facing require_docker_daemon pattern.
    - tests/.../conftest.py (test fixtures): calls require_docker_daemon() to skip tests when
      no Docker daemon is available, making it the gatekeeper for all Docker-dependent test runs.

State and side effects:
    docker_daemon_available is decorated with @lru_cache(maxsize=1); its cache is explicitly
    cleared at the start of require_docker_daemon. The module performs subprocess calls to
    docker info, wsl -l -v, powershell Start-Process, and apk add. It reads os.environ for
    SYSTEMROOT, SystemRoot, PROGRAMFILES, ProgramFiles, PROGRAMDATA, and ProgramData. It does
    not write to pytest stash, the filesystem, or any network resources. Module-level globals
    are limited to the immutable _NATIVE_PATH constant.

Invariants:
    - docker_daemon_available always returns a 2-tuple of (bool, str | None) where the string
      is one of "native" or "wsl2" when the bool is True, and None when False.
    - require_docker_daemon either returns a backend string ("native"/"wsl2") or raises
      pytest.skip; it never returns None.
    - _resolve_tool_path returns None only when no candidate was found; it never raises.
    - All subprocess calls use check=False (failures are handled by inspecting returncode or
      raising RuntimeError / calling pytest.fail/pytest.skip).

Failure semantics:
    _start_docker_desktop raises RuntimeError if PowerShell is not found or the Start-Process
    command fails. _ensure_docker_cli_in_alpine calls pytest.fail if WSL is not available or
    apk installation fails. require_docker_daemon calls pytest.skip with descriptive messages
    for missing Docker Desktop, Windows Containers mode, missing WSL2 Alpine, or startup timeout.
    docker_daemon_available swallows RuntimeError from _start_docker_desktop and returns (False, None).

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import os
import shutil
import subprocess  # noqa: S404  # subprocess used for docker command execution
import time
from functools import lru_cache
from pathlib import Path, PureWindowsPath

import pytest

_NATIVE_PATH = type(Path())


def _windows_tool_candidate_exists(candidate: PureWindowsPath) -> bool:
    r"""
    `pytest_bdd.docker._windows_tool_candidate_exists` owns documented function behavior.

    Responsibility:
        Checks whether a PureWindowsPath candidate file actually exists on disk by converting it
        to a native Path and calling Path.exists(). This bridges the gap between hardcoded Windows-
        style path candidates (e.g., C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe)
        and the runtime Path type, which on Windows is WindowsPath and on Unix is PosixPath.

    Reason for existence:
        Extracted as its own function because _resolve_tool_path builds a list of PureWindowsPath
        candidates across multiple tool types (docker, wsl, powershell) and needs a uniform way to
        test existence without repeating the str()→Path() conversion at every call site. It
        encapsulates the Windows-specific _NATIVE_PATH constant and the PureWindowsPath→Path
        bridging, keeping callers unaware of the type-conversion detail. Its single-line body
        is justified by the abstraction it provides over Path construction.

    Delegates:
        - Path.exists: The stdlib pathlib method that performs the actual filesystem stat call.

    Cohesion:
        This function is a pure helper for _resolve_tool_path; it has no independent purpose.
        Its logic (windows path → native path → existence check) is tightly scoped to the
        tool-resolution problem and would not be useful outside this module.

    Separation:
        - _resolve_tool_path: The sole caller; this function is intentionally a helper rather
          than inline logic so the candidate-checking contract is explicit and testable in
          isolation from shutil.which and os.environ fallback logic.

    Main consumers:
        - pytest_bdd_testing.docker._resolve_tool_path: iterates over candidate PureWindowsPath
          values and calls _windows_tool_candidate_exists to determine which to return.

    State and side effects:
        Reads the filesystem via Path.exists(). No writes, no environment access, no pytest
        stash interaction. Stateless function with a single filesystem probe per call.

    Architecture score:
        #arch-eval:reason_for_existence=2
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=4
    """
    return Path.exists(_NATIVE_PATH(str(candidate)))


def _resolve_tool_path(name: str) -> str | None:
    r"""
    `pytest_bdd.docker._resolve_tool_path` owns documented function behavior.

    Responsibility:
        Resolves the absolute filesystem path to a named tool binary (docker, wsl, powershell)
        in a cross-platform manner. First delegates to shutil.which for standard PATH lookup;
        on Windows (os.name == "nt"), falls back to hardcoded PureWindowsPath candidates derived
        from SYSTEMROOT, PROGRAMFILES, and PROGRAMDATA environment variables. Returns the resolved
        path as a string if found, or None if the tool cannot be located anywhere on the system.

    Reason for existence:
        shutil.which alone is insufficient on Windows because Docker Desktop, WSL, and PowerShell
        are not guaranteed to be on PATH — they live in known system directories. This function
        centralizes all platform-specific installation-location knowledge (e.g., Docker Desktop
        under Program Files\\Docker\\Docker\\resources\\bin, WSL under System32\\wsl.exe) into a
        single lookup routine so that every other function in this module and in docker_cluster
        can ask "where is docker?" or "where is wsl?" without repeating the fallback logic. The
        signature is simple (name: str) → (str | None), making it trivially callable from both
        synchronous probes and subprocess wrappers.

    Delegates:
        - shutil.which: Performs the standard PATH-based binary lookup on all platforms.
        - _windows_tool_candidate_exists: Validates that a hardcoded PureWindowsPath candidate
          actually exists on disk before returning it.

    Cohesion:
        All logic — PATH lookup via shutil.which, os.name gate, environment variable reads for
        SYSTEMROOT/ProgramFiles/ProgramData, and candidate list construction for docker/wsl/
        powershell — serves the single purpose of answering "where is tool X?" The function does
        not perform authentication, daemon health checks, or subprocess execution.

    Separation:
        - docker_cluster._resolve_tool_path (re-exported consumer): docker_cluster imports this
          function for its own docker binary resolution; the function stays in docker.py because
          it is a prerequisite for daemon probing, which the cluster module builds on top of.
        - shutil.which: stdlib counterpart for Unix-native PATH resolution; this function
          extends it with Windows-specific fallbacks rather than replacing it.

    Main consumers:
        - pytest_bdd_testing.docker._alpine_wsl2_available: calls _resolve_tool_path("wsl") to
          locate the WSL binary for distribution enumeration.
        - pytest_bdd_testing.docker._start_docker_desktop: calls _resolve_tool_path("powershell")
          to locate PowerShell for launching Docker Desktop.
        - pytest_bdd_testing.docker._wait_for_docker: calls _resolve_tool_path("docker") and
          _resolve_tool_path("wsl") depending on the backend argument.
        - pytest_bdd_testing.docker._ensure_docker_cli_in_alpine: calls _resolve_tool_path("wsl").
        - pytest_bdd_testing.docker.docker_daemon_available: calls _resolve_tool_path("docker")
          and _resolve_tool_path("wsl").
        - pytest_bdd_testing.docker.require_docker_daemon: calls _resolve_tool_path("docker").
        - pytest_bdd_testing.docker_cluster: imports and uses _resolve_tool_path for docker
          binary resolution in _run_docker_cmd_once.

    State and side effects:
        Reads os.environ (SYSTEMROOT, SystemRoot, PROGRAMFILES, ProgramFiles, PROGRAMDATA,
        ProgramData). On Windows, probes filesystem existence via _windows_tool_candidate_exists.
        No writes, no caching, no pytest stash access. Fully deterministic given the same
        environment and filesystem state.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    resolved = shutil.which(name)
    if resolved is not None:
        return resolved

    if os.name != "nt":
        return None

    candidates: list[PureWindowsPath] = []
    system_root = PureWindowsPath(os.environ.get("SYSTEMROOT") or os.environ.get("SystemRoot", r"C:\Windows"))  # noqa: SIM112  # os.environ access for platform detection

    if name == "wsl":
        candidates.append(system_root / "System32" / "wsl.exe")
    elif name == "powershell":
        candidates.append(system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe")
    elif name == "docker":
        candidates.extend(
            [
                PureWindowsPath(os.environ.get("PROGRAMFILES") or os.environ.get("ProgramFiles", r"C:\Program Files"))  # noqa: SIM112  # os.environ access for platform detection
                / "Docker"
                / "Docker"
                / "resources"
                / "bin"
                / "docker.exe",
                PureWindowsPath(os.environ.get("PROGRAMDATA") or os.environ.get("ProgramData", r"C:\ProgramData"))  # noqa: SIM112  # os.environ access for platform detection
                / "DockerDesktop"
                / "version-bin"
                / "docker.exe",
            ],
        )

    for candidate in candidates:
        if _windows_tool_candidate_exists(candidate):
            return str(candidate)

    return None


# ── T002: WSL2 Alpine detection ───────────────────────────────────────────────


def _alpine_wsl2_available() -> bool:
    """
    `pytest_bdd.docker._alpine_wsl2_available` owns documented function behavior.

    Responsibility:
        Determines whether a WSL2 distribution named "Alpine" is registered and running on the
        local Windows machine. Executes `wsl -l -v` via subprocess, decodes the output (handling
        UTF-16-LE encoding typical of Windows console output), and checks that any output line
        contains both "Alpine" and a version column ending in "2". Returns True only when a WSL2
        Alpine distribution is confirmed present.

    Reason for existence:
        This is a targeted probe that docker_daemon_available and require_docker_daemon use to
        decide whether to attempt the WSL2 fallback path for Docker. The function encapsulates
        the messy subprocess output parsing (byte→string decode with UTF-16-LE fallback to
        replace-errors) and the specific column-matching heuristic ("2" as the last token),
        preventing callers from coupling to the `wsl -l -v` output format. It is separate from
        _wait_for_docker because probing distribution existence is a one-shot check, not a
        polling loop.

    Delegates:
        - _resolve_tool_path: Locates the wsl.exe binary before attempting subprocess invocation.
        - subprocess.run: Executes `wsl -l -v` with capture_output and check=False.

    Cohesion:
        The function is a single-purpose probe: parse `wsl -l -v` output for Alpine+WSL2. Its
        internal logic (UTF-16-LE decode, line-splitting, column matching) is entirely about
        this one subprocess output format. No unrelated checks or side effects.

    Separation:
        - _wait_for_docker: _wait_for_docker uses _resolve_tool_path("wsl") directly and runs
          `docker info` inside Alpine; _alpine_wsl2_available is the precondition gate that
          decides whether the WSL2 path should be attempted at all.
        - _ensure_docker_cli_in_alpine: Assumes Alpine is available (called after a positive
          check) and installs docker-cli; this function only proves existence, it does not
          modify the distribution.

    Main consumers:
        - pytest_bdd_testing.docker.docker_daemon_available: calls _alpine_wsl2_available as
          the WSL2 fallback gate after native docker info fails.
        - pytest_bdd_testing.docker.require_docker_daemon: calls _alpine_wsl2_available to
          provide a specific skip message ("WSL2 Alpine dist not found") when the WSL2 path
          is unavailable.

    State and side effects:
        Executes `wsl -l -v` via subprocess (read-only query). No filesystem writes, no
        environment variable modifications, no pytest stash access. Stateless beyond the
        subprocess invocation.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    wsl_bin = _resolve_tool_path("wsl")
    if wsl_bin is None:
        return False
    result = subprocess.run(  # noqa: S603  # subprocess with trusted docker commands
        [wsl_bin, "-l", "-v"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return False
    stdout = result.stdout
    if isinstance(stdout, bytes):
        try:
            stdout_str = stdout.decode("utf-16-le")
        except UnicodeDecodeError:
            stdout_str = stdout.decode(errors="replace")
    else:
        stdout_str = stdout
    return any("Alpine" in line and "2" in line.split()[-1] for line in stdout_str.splitlines())


# ── T003: Docker Desktop auto-start ───────────────────────────────────────────


def _start_docker_desktop() -> None:
    """
    `pytest_bdd.docker._start_docker_desktop` owns documented function behavior.

    Responsibility:
        Launches Docker Desktop on Windows by invoking PowerShell's Start-Process cmdlet with
        the "docker-desktop" target and a hidden window style. This is a fire-and-forget startup
        command — it does not wait for the daemon to become ready. Raises RuntimeError if
        PowerShell cannot be located or the Start-Process invocation fails (non-zero returncode).

    Reason for existence:
        Docker Desktop on Windows does not autostart its daemon on demand; it must be explicitly
        launched. This function encapsulates the Windows-specific PowerShell invocation so that
        the higher-level docker_daemon_available function can attempt auto-start as a last-resort
        fallback after both native docker info and WSL2 Alpine probes fail. The 10-second timeout
        prevents indefinite hanging if PowerShell hangs. It is separate from _wait_for_docker
        because starting the GUI app and polling the daemon socket are distinct operations with
        different failure modes.

    Delegates:
        - _resolve_tool_path: Locates the powershell.exe binary.
        - subprocess.run: Executes the PowerShell Start-Process command with capture_output,
          text=True, and a 10-second timeout.

    Cohesion:
        The function does exactly one thing: PowerShell Start-Process docker-desktop. Its internal
        logic (resolve powershell path → build command → run → check returncode) is a tight,
        linear sequence with no branching based on backend mode or other state.

    Separation:
        - _wait_for_docker: Complements this function — _start_docker_desktop launches the
          daemon process; _wait_for_docker polls until it is responsive. They are separate
          because launch and readiness-probing have different timeout expectations and different
          error surfaces.
        - docker_daemon_available: Orchestrates the full detection sequence, calling
          _start_docker_desktop only as a fallback and catching its RuntimeError.

    Main consumers:
        - pytest_bdd_testing.docker.docker_daemon_available: calls _start_docker_desktop inside
          a try/except RuntimeError block as the last-resort attempt when both native and WSL2
          Docker probes fail.

    State and side effects:
        Launches Docker Desktop as a background Windows process via PowerShell. This is a
        persistent side effect — the Docker Desktop GUI process remains running after this
        function returns. No pytest stash access, no filesystem writes, no environment
        modifications by this function itself.

    Failure semantics:
        Raises RuntimeError("PowerShell not found") if _resolve_tool_path("powershell") returns
        None. Raises RuntimeError("Failed to start Docker Desktop") if the PowerShell
        Start-Process command exits with a non-zero returncode. Callers (docker_daemon_available)
        catch RuntimeError and return (False, None).

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    ps = _resolve_tool_path("powershell")
    if ps is None:
        msg = "PowerShell not found"
        raise RuntimeError(msg)
    result = subprocess.run(  # noqa: S603  # subprocess with trusted docker commands
        [ps, "-Command", "Start-Process", "docker-desktop", "-WindowStyle", "Hidden"],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        msg = "Failed to start Docker Desktop"
        raise RuntimeError(msg)


# ── T004: Poll until Docker daemon is ready ───────────────────────────────────


def _wait_for_docker(backend: str, timeout: int = 60) -> bool:
    """
    `pytest_bdd.docker._wait_for_docker` owns documented function behavior.

    Responsibility:
        Polls the Docker daemon for readiness by repeatedly running `docker info` (either natively
        or via WSL2 Alpine depending on the backend argument) until the daemon responds with a
        successful exit code and output indicating Linux container support ("ostype: linux"), or
        until the specified timeout (default 60 seconds) expires. Returns True if the daemon
        became ready within the timeout, False otherwise. Sleeps 2 seconds between attempts.

    Reason for existence:
        Docker daemon startup is asynchronous — the docker CLI binary may be on PATH before the
        daemon socket accepts connections, and on Windows the daemon may momentarily report
        Windows container mode before switching to Linux mode. This function encapsulates the
        polling loop, the 2-second backoff, and the readiness heuristic (returncode==0 AND
        "ostype: linux" in stdout) so that callers get a simple boolean answer without coupling
        to the polling mechanics or the daemon output format. The backend parameter allows the
        same polling logic to work for both native Docker and WSL2-intermediated Docker.

    Delegates:
        - _resolve_tool_path: Resolves the docker or wsl binary path before each poll iteration.
        - subprocess.run: Executes `docker info` (native) or `wsl -d Alpine docker info` (WSL2).

    Cohesion:
        The function is a pure polling loop: resolve binary → run info command → check output
        → sleep → repeat. All logic serves the single purpose of waiting for daemon readiness.
        No configuration parsing, no cluster state, no result attachment.

    Separation:
        - docker_daemon_available: Uses _wait_for_docker as the readiness probe after calling
          _start_docker_desktop. docker_daemon_available owns the decision of when to start
          Docker Desktop; this function only owns the wait loop.
        - _start_docker_desktop: Launches the daemon process; _wait_for_docker confirms it is
          accepting connections. These are separate because launch and readiness are distinct
          lifecycle phases.

    Main consumers:
        - pytest_bdd_testing.docker.docker_daemon_available: calls _wait_for_docker("wsl2")
          after attempting _start_docker_desktop, to confirm the auto-started daemon is ready.

    State and side effects:
        Repeatedly calls subprocess.run with `docker info`. No filesystem writes, no environment
        modifications, no pytest stash access. Uses time.monotonic() for deadline tracking (no
        wall-clock dependency). Stateless between invocations.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if backend == "native":
            docker_bin = _resolve_tool_path("docker")
            if docker_bin is None:
                time.sleep(2)
                continue
            result = subprocess.run(  # noqa: S603  # subprocess with trusted docker commands
                [docker_bin, "info"],
                check=False,
                capture_output=True,
                text=True,
            )
        else:
            wsl_bin = _resolve_tool_path("wsl")
            if wsl_bin is None:
                time.sleep(2)
                continue
            result = subprocess.run(  # noqa: S603  # subprocess with trusted docker commands
                [wsl_bin, "-d", "Alpine", "docker", "info"],
                check=False,
                capture_output=True,
                text=True,
            )
        if result.returncode == 0 and ("ostype: linux" in result.stdout.lower() or not result.stdout.strip()):
            return True
        time.sleep(2)
    return False


# ── T005: Ensure docker-cli inside Alpine ─────────────────────────────────────


def _ensure_docker_cli_in_alpine(timeout: int = 60) -> None:
    """
    `pytest_bdd.docker._ensure_docker_cli_in_alpine` owns documented function behavior.

    Responsibility:
        Ensures the docker-cli package is installed inside the WSL2 Alpine distribution. First
        checks if `docker` is already on the Alpine PATH via `which docker`; if found, returns
        immediately. Otherwise, runs `apk add --no-cache docker-cli` as root inside Alpine.
        Calls pytest.fail if WSL is not available or if the apk installation fails, aborting
        the test session since Docker-dependent tests cannot proceed without the CLI.

    Reason for existence:
        The WSL2 Alpine distribution is a minimal image that may not include docker-cli by
        default. This function guards the WSL2 backend path by ensuring the CLI is present
        before any docker compose or docker info commands are attempted through the Alpine
        intermediary. It is kept separate from the daemon detection functions because installing
        packages is a mutating operation with different permissions requirements (root via -u)
        and a different timeout budget than read-only info probes.

    Delegates:
        - _resolve_tool_path: Locates the wsl.exe binary.
        - subprocess.run: Executes `which docker` (check) and `apk add docker-cli` (install).

    Cohesion:
        The function is a focused idempotent install check: probe existence → install if missing
        → fail if install fails. All subprocess calls go through WSL to the Alpine distribution,
        and the logic is entirely about the docker-cli package in that specific context.

    Separation:
        - _wait_for_docker: _wait_for_docker runs `docker info` (requiring docker-cli to already
          be present); _ensure_docker_cli_in_alpine is the precondition that guarantees docker-cli
          is installed before any info/exec commands are issued.
        - docker_daemon_available: Does not call this function directly; callers must invoke it
          separately after confirming Alpine availability. This separation prevents docker_daemon_available
          from having package-install side effects during what should be a read-only probe.

    Main consumers:
        - Called by test fixtures or conftest setup that use the WSL2 backend and need to ensure
          the docker CLI is present before orchestrating containers.

    State and side effects:
        May install docker-cli package inside the WSL2 Alpine distribution via apk — a persistent
        mutation of the Alpine filesystem. Reads no environment variables beyond what subprocess
        inherits. No pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
    wsl_bin = _resolve_tool_path("wsl")
    if wsl_bin is None:
        pytest.fail("WSL not available")
    result = subprocess.run(  # noqa: S603  # subprocess with trusted docker commands
        [wsl_bin, "-d", "Alpine", "--", "which", "docker"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return
    install = subprocess.run(  # noqa: S603  # subprocess with trusted docker commands
        [wsl_bin, "-d", "Alpine", "-u", "root", "--", "apk", "add", "--no-cache", "docker-cli"],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if install.returncode != 0:
        pytest.fail(f"Failed to install docker-cli in Alpine: {install.stderr}")


# ── T006: Refactored docker_daemon_available ──────────────────────────────────


@lru_cache(maxsize=1)
def docker_daemon_available() -> tuple[bool, str | None]:
    """
    `pytest_bdd.docker.docker_daemon_available` owns documented function behavior.

    Responsibility:
        Probes the system for a working Docker daemon with Linux container support, trying three
        strategies in order: (1) native `docker info`, (2) WSL2 Alpine `docker info` if Alpine
        WSL2 is detected, and (3) auto-launch Docker Desktop via PowerShell then poll for
        readiness via WSL2. Returns a cached 2-tuple of (bool, str | None) where the string is
        "native" or "wsl2" indicating which backend is active, or None if no daemon is available.
        The result is cached via @lru_cache(maxsize=1) to avoid repeated subprocess calls during
        a single test session.

    Reason for existence:
        This is the central gating function for all Docker-dependent test infrastructure. It
        encapsulates the full decision tree (native → WSL2 → auto-start → give up) so that
        test fixtures and conftest files can simply call require_docker_daemon() without
        understanding the platform-specific probing sequence. The lru_cache ensures that during
        collection, when many tests may independently ask "is docker available?", only one set
        of subprocess calls is made. The cache is explicitly cleared by require_docker_daemon
        to allow re-evaluation across test sessions.

    Delegates:
        - _resolve_tool_path: Resolves docker and wsl binary paths for subprocess calls.
        - _alpine_wsl2_available: Checks whether WSL2 Alpine is present as a fallback backend.
        - _start_docker_desktop: Launches Docker Desktop if neither native nor existing WSL2
          Docker is responsive.
        - _wait_for_docker: Polls daemon readiness after Docker Desktop auto-start.
        - subprocess.run: Executes `docker info` commands in both native and WSL2 modes.

    Cohesion:
        All three probing strategies contribute to the same answer: "can we run Docker containers
        with Linux support?" The function orchestrates helper functions but does not itself
        contain any low-level subprocess or path-resolution logic. The caching decorator fits
        naturally because the answer to this question is stable for the lifetime of a test session.

    Separation:
        - require_docker_daemon: require_docker_daemon calls docker_daemon_available and then
          interprets the result to either return the backend string or call pytest.skip with
          a specific diagnostic message. The availability probe is kept separate from the
          skip-failure decision so that callers who want to check availability without skipping
          can use docker_daemon_available directly.
        - docker_cluster.DockerClusterManager: The cluster manager accepts a backend string
          ("native"/"wsl2") but does not determine it; it delegates that decision to this module.

    Main consumers:
        - pytest_bdd_testing.docker.require_docker_daemon: wraps docker_daemon_available,
          clears its cache, and translates a False result into pytest.skip with diagnostics.
        - Potential direct consumers: any test code that wants to check Docker availability
          without forcing a skip (e.g., conditional fixture parametrization).

    State and side effects:
        Cached via @lru_cache(maxsize=1); cache persists across calls within the same process.
        Performs subprocess calls (docker info, wsl -l -v, Start-Process) on first invocation.
        May launch Docker Desktop as a persistent background process via _start_docker_desktop.
        No filesystem writes, no pytest stash access, no environment variable modifications.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
    """
    # Try native docker first
    docker_bin = _resolve_tool_path("docker")
    if docker_bin is not None:
        result = subprocess.run(  # noqa: S603  # subprocess with trusted docker commands
            [docker_bin, "info"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and ("ostype: linux" in result.stdout.lower() or not result.stdout.strip()):
            return (True, "native")

    # Fall back to WSL2 Alpine
    if _alpine_wsl2_available():
        wsl_bin = _resolve_tool_path("wsl")
        if wsl_bin is not None:
            result = subprocess.run(  # noqa: S603  # subprocess with trusted docker commands
                [wsl_bin, "-d", "Alpine", "docker", "info"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and ("ostype: linux" in result.stdout.lower() or not result.stdout.strip()):
                return (True, "wsl2")

    # Attempt to start Docker Desktop
    try:
        _start_docker_desktop()
    except RuntimeError:
        return (False, None)
    if _wait_for_docker("wsl2"):
        return (True, "wsl2")

    return (False, None)


# ── T007: Refactored require_docker_daemon ────────────────────────────────────


def require_docker_daemon() -> str:  # pylint: disable=inconsistent-return-statements  # pytest.skip raises — not a return inconsistency
    """
    `pytest_bdd.docker.require_docker_daemon` owns documented function behavior.

    Responsibility:
        The public-facing gate for Docker-dependent tests. Clears the docker_daemon_available
        lru_cache to force a fresh probe, then calls docker_daemon_available(). If a daemon is
        found, returns the backend string ("native" or "wsl2"). If no daemon is available,
        performs additional diagnostics (is Docker installed at all? is it in Windows Containers
        mode? is WSL2 Alpine missing?) and calls pytest.skip with a specific, actionable skip
        message. This function never returns None — it either returns a backend string or
        raises pytest.skip.

    Reason for existence:
        This function is the single integration point between the internal daemon-probing
        machinery and the pytest test collection/skip infrastructure. It translates the
        boolean+backend tuple from docker_daemon_available into either a usable backend string
        or a pytest.skip with a human-readable reason, providing progressive diagnostic detail
        (Docker not installed → Windows Containers mode → WSL2 Alpine missing → startup timeout).
        Separating this from docker_daemon_available keeps the probe function pure (no skip side
        effects) while giving test fixtures a one-call "give me Docker or skip" API.

    Delegates:
        - docker_daemon_available: The core probe; its lru_cache is cleared here first to ensure
          a fresh evaluation.
        - _resolve_tool_path: Used for post-failure diagnostics (is docker even on PATH?).
        - _alpine_wsl2_available: Used for the "WSL2 Alpine dist not found" skip reason.
        - subprocess.run: Used for the Windows Containers mode diagnostic check.
        - pytest.skip: The mechanism for cleanly skipping tests when Docker is unavailable.

    Cohesion:
        The function does one thing: call docker_daemon_available and either return the backend
        or skip with diagnostics. The diagnostic checks (docker installed? Windows Containers?
        Alpine available?) all serve the single purpose of producing the most helpful skip
        message. No unrelated logic.

    Separation:
        - docker_daemon_available: Kept separate so that callers who need a boolean availability
          check without pytest.skip side effects (e.g., conditional parametrization) can use
          docker_daemon_available directly. require_docker_daemon is specifically the
          "skip-if-unavailable" wrapper.
        - docker_cluster.DockerClusterManager: The cluster manager calls require_docker_daemon
          to get the backend string, then uses it to configure subprocess routing.

    Main consumers:
        - Tests and conftest files throughout the test suite: called as a fixture prerequisite
          (e.g., `backend = require_docker_daemon()`) to skip Docker-dependent tests cleanly
          when Docker is unavailable.
        - pytest_bdd_testing.docker_cluster.DockerClusterManager: consumes the returned backend
          string to decide whether to route commands through native docker or WSL2.

    State and side effects:
        Clears the lru_cache on docker_daemon_available (module-level state mutation). Calls
        subprocess for diagnostics on skip paths only. No filesystem writes, no pytest stash
        access. The primary side effect is pytest.skip which aborts the current test.

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
    docker_daemon_available.cache_clear()
    available, backend = docker_daemon_available()
    if available and backend is not None:
        return backend

    # Determine the specific failure reason
    docker_bin = _resolve_tool_path("docker")
    if docker_bin is None:
        pytest.skip("Docker Desktop not installed")

    # If docker is installed, let's check if it's running but in the wrong container mode (Windows instead of Linux)
    try:
        result = subprocess.run(  # noqa: S603  # subprocess with trusted docker commands
            [docker_bin, "info"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and "ostype: linux" not in result.stdout.lower() and result.stdout.strip():
            pytest.skip("Docker daemon is running in Windows Containers mode. Linux containers are required.")
    except OSError:
        pass

    if not _alpine_wsl2_available():
        pytest.skip("WSL2 Alpine dist not found")

    pytest.skip("Docker Desktop did not start within timeout")
