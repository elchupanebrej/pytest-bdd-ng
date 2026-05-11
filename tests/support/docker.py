"""Provide docker helpers."""

from __future__ import annotations

import os
import shutil
import subprocess  # noqa: S404
import time
from functools import lru_cache
from pathlib import Path, PureWindowsPath

import pytest

_NATIVE_PATH = type(Path())


def _windows_tool_candidate_exists(candidate: PureWindowsPath) -> bool:
    return Path.exists(_NATIVE_PATH(str(candidate)))


def _resolve_tool_path(name: str) -> str | None:
    resolved = shutil.which(name)
    if resolved is not None:
        return resolved

    if os.name != "nt":
        return None

    candidates: list[PureWindowsPath] = []
    system_root = PureWindowsPath(os.environ.get("SYSTEMROOT") or os.environ.get("SystemRoot", r"C:\Windows"))  # noqa: SIM112

    if name == "wsl":
        candidates.append(system_root / "System32" / "wsl.exe")
    elif name == "powershell":
        candidates.append(system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe")
    elif name == "docker":
        candidates.extend(
            [
                PureWindowsPath(os.environ.get("PROGRAMFILES") or os.environ.get("ProgramFiles", r"C:\Program Files"))  # noqa: SIM112
                / "Docker"
                / "Docker"
                / "resources"
                / "bin"
                / "docker.exe",
                PureWindowsPath(os.environ.get("PROGRAMDATA") or os.environ.get("ProgramData", r"C:\ProgramData"))  # noqa: SIM112
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
    """Detect if WSL2 Alpine dist exists by parsing ``wsl -l -v`` output."""
    wsl_bin = _resolve_tool_path("wsl")
    if wsl_bin is None:
        return False
    result = subprocess.run(  # noqa: S603
        [wsl_bin, "-l", "-v"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return False
    stdout = result.stdout
    if isinstance(stdout, bytes):
        try:
            stdout = stdout.decode("utf-16-le")
        except UnicodeDecodeError:
            stdout = stdout.decode(errors="replace")
    return any("Alpine" in line and "2" in line.split()[-1] for line in stdout.splitlines())


# ── T003: Docker Desktop auto-start ───────────────────────────────────────────


def _start_docker_desktop() -> None:
    """Launch Docker Desktop via PowerShell.

    Raises:
        RuntimeError: If PowerShell is unavailable or Docker Desktop fails to start.
    """
    ps = _resolve_tool_path("powershell")
    if ps is None:
        msg = "PowerShell not found"
        raise RuntimeError(msg)
    result = subprocess.run(  # noqa: S603
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
    """Poll ``docker info`` (native) or ``wsl -d Alpine docker info`` (wsl2)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if backend == "native":
            docker_bin = _resolve_tool_path("docker")
            if docker_bin is None:
                time.sleep(2)
                continue
            result = subprocess.run(  # noqa: S603
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
            result = subprocess.run(  # noqa: S603
                [wsl_bin, "-d", "Alpine", "docker", "info"],
                check=False,
                capture_output=True,
                text=True,
            )
        if result.returncode == 0:
            return True
        time.sleep(2)
    return False


# ── T005: Ensure docker-cli inside Alpine ─────────────────────────────────────


def _ensure_docker_cli_in_alpine(timeout: int = 60) -> None:
    """Install ``docker-cli`` in Alpine WSL2 dist when missing."""
    wsl_bin = _resolve_tool_path("wsl")
    if wsl_bin is None:
        pytest.fail("WSL not available")
    result = subprocess.run(  # noqa: S603
        [wsl_bin, "-d", "Alpine", "--", "which", "docker"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return
    install = subprocess.run(  # noqa: S603
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
    """Return ``(available, backend)`` where backend is ``"native"`` or ``"wsl2"``."""
    # Try native docker first
    docker_bin = _resolve_tool_path("docker")
    if docker_bin is not None:
        result = subprocess.run(  # noqa: S603
            [docker_bin, "info"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return (True, "native")

    # Fall back to WSL2 Alpine
    if _alpine_wsl2_available():
        wsl_bin = _resolve_tool_path("wsl")
        if wsl_bin is not None:
            result = subprocess.run(  # noqa: S603
                [wsl_bin, "-d", "Alpine", "docker", "info"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
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


def require_docker_daemon() -> str:
    """Return backend name (``"native"`` or ``"wsl2"``).  Fail on missing prereqs."""
    cache_clear = getattr(docker_daemon_available, "cache_clear", None)
    if callable(cache_clear):
        cache_clear()
    available, backend = docker_daemon_available()
    if available:
        return backend

    # Determine the specific failure reason
    docker_bin = _resolve_tool_path("docker")
    if docker_bin is None:
        pytest.fail("Docker Desktop not installed")

    if not _alpine_wsl2_available():
        pytest.fail("WSL2 Alpine dist not found")

    pytest.fail("Docker Desktop did not start within timeout")
