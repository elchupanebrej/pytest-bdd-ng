"""Provide docker cluster helpers."""

import atexit
import contextlib
import os
import shutil
import subprocess  # noqa: S404
import time
from pathlib import Path

from attrs import define

from pytest_bdd.testing.docker import _resolve_tool_path

_DEFAULT_OPERATION_ARG_COUNT = 3


@define
class DockerTimeouts:
    """Represent docker timeouts state."""

    startup_poll: int = 60
    compose_up: int = 900
    compose_exec: int = 300
    compose_cp: int = 30
    compose_down: int = 30
    alpine_install: int = 60
    overall_session: int = 1800


def _run_wsl_cmd(args: list[str], timeout: int, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """
    Run a command inside WSL2 Alpine distro.

    Returns:
        Completed WSL subprocess result.

    Raises:
        FileNotFoundError: If the WSL executable is unavailable.

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
    return subprocess.run(  # noqa: S603
        [wsl_bin, "-d", "Alpine", "--", *command_args],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class DockerClusterManager:
    """
    Represent docker cluster manager state.

    Raises:
        RuntimeError: If the operation cannot be completed.
        FileNotFoundError: If the operation cannot be completed.

    """

    def __init__(self, backend: str = "native", timeouts: DockerTimeouts | None = None) -> None:
        """Initialize the docker cluster manager."""
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
    ) -> subprocess.CompletedProcess:
        if self.backend == "wsl2":
            return _run_wsl_cmd(args, timeout=timeout, env=env)
        if args and args[0] == "docker":
            docker_bin = _resolve_tool_path("docker")
            if docker_bin is None:
                msg = "docker executable not found"
                raise FileNotFoundError(msg)
            args = [docker_bin, *args[1:]]
        return subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout, env=env)  # noqa: S603

    def _run_docker_cmd(
        self,
        args: list[str],
        timeout: int,
        operation: str = "",
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """
        Route Docker command through the appropriate backend.

        Returns:
            Completed Docker subprocess result.

        Raises:
            RuntimeError: If the Docker command exceeds its timeout.

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
        """Handle set backend."""
        if self.backend == backend:
            return
        if self.active_clusters:
            self.cleanup()
        self.backend = backend

    @staticmethod
    def _compose_env(remote_mode: str, *, docker_config_dir: Path | None = None) -> dict[str, str]:
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
        return fixture_dir / "artifacts"

    @staticmethod
    def _reset_artifacts(artifact_dir: Path) -> None:
        report_path = artifact_dir / "remote-xdist.ndjson"
        if report_path.exists():
            report_path.unlink()

        capture_dir = artifact_dir / "fake-node-runtime" / "fake-node-captures"
        if capture_dir.exists():
            shutil.rmtree(capture_dir, ignore_errors=True)

    def _check_session_timeout(self) -> None:
        """
        Raise RuntimeError if overall session timeout exceeded.

        Raises:
            RuntimeError: If the configured overall session timeout is exceeded.

        """
        if self._session_start is None:
            return
        elapsed = time.monotonic() - self._session_start
        if elapsed > self.timeouts.overall_session:
            msg = f"Overall session timeout exceeded ({self.timeouts.overall_session}s)"
            raise RuntimeError(msg)

    def get_cluster(self, remote_mode: str, fixture_dir: Path, repo_root: Path) -> tuple[list[str], Path]:  # noqa: ARG002
        """
        Return cluster.

        Returns:
            Docker compose command and artifact directory for the remote mode.

        Raises:
            RuntimeError: If the operation cannot be completed.

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
    ) -> tuple[subprocess.CompletedProcess, Path]:
        """
        Run in controller.

        Returns:
            Completed controller subprocess result and artifact directory.

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
            "tests/assets/docker/remote_xdist/controller_entrypoint.py",
        ]

        result = self._run_docker_cmd(exec_cmd, timeout=self.timeouts.compose_exec, operation="compose_exec", env=env)
        return result, Path(docker_artifact_dir)

    def cleanup(self) -> None:
        """Handle cleanup."""
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
    Return the session-scoped DockerClusterManager singleton, lazily initialized.

    Returns:
        Session-scoped Docker cluster manager.

    """
    if not _cluster_manager_holder:
        _cluster_manager_holder.append(DockerClusterManager())
    return _cluster_manager_holder[0]


# Backwards-compatible alias — prefer get_cluster_manager() for new code.
cluster_manager = None  # type: ignore[assignment]  # see get_cluster_manager()
