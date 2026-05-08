"""Provide docker cluster helpers."""

import atexit
import contextlib
import os
import shutil
import subprocess  # noqa: S404
import time
from pathlib import Path

from attrs import define

from tests.support.docker import _resolve_tool_path


@define
class DockerTimeouts:
    """Represent docker timeouts state."""

    startup_poll: int = 60
    compose_up: int = 300
    compose_exec: int = 300
    compose_cp: int = 30
    compose_down: int = 30
    alpine_install: int = 60
    overall_session: int = 900


def _run_wsl_cmd(args: list[str], timeout: int, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run a command inside WSL2 Alpine distro.

    Raises:
        FileNotFoundError: If the WSL executable is unavailable.
    """
    wsl_bin = _resolve_tool_path("wsl")
    if wsl_bin is None:
        msg = "wsl executable not found"
        raise FileNotFoundError(msg)
    command_args = list(args)
    if env is not None:
        env_overrides = [f"{key}={value}" for key, value in env.items() if os.environ.get(key) != value]
        if env_overrides:
            command_args = ["env", *env_overrides, *command_args]
    return subprocess.run(  # noqa: S603
        [wsl_bin, "-d", "Alpine", "--", *command_args],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


class DockerClusterManager:
    """
    Represent docker cluster manager state.

    Raises:
        RuntimeError: If the operation cannot be completed.
        FileNotFoundError: If the operation cannot be completed.

    """

    def __init__(self, backend: str = "native", timeouts: DockerTimeouts | None = None):
        """Initialize the docker cluster manager."""
        self.backend = backend
        self.timeouts = timeouts or DockerTimeouts()
        self.active_clusters = {}
        self.artifact_dirs = {}
        self.compose_envs = {}
        self._session_start: float | None = None
        atexit.register(self.cleanup)

    def _run_docker_cmd(
        self,
        args: list[str],
        timeout: int,
        operation: str = "",
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """Route Docker command through the appropriate backend.

        Raises:
            FileNotFoundError: If the Docker executable is unavailable.
            RuntimeError: If the Docker command exceeds its timeout.
        """
        try:
            if self.backend == "wsl2":
                return _run_wsl_cmd(args, timeout=timeout, env=env)
            if args and args[0] == "docker":
                docker_bin = _resolve_tool_path("docker")
                if docker_bin is None:
                    msg = "docker executable not found"
                    raise FileNotFoundError(msg)
                args = [docker_bin, *args[1:]]
            return subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout, env=env)  # noqa: S603
        except subprocess.TimeoutExpired as err:
            op_name = operation or " ".join(args[:3]) if len(args) >= 3 else " ".join(args)
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

    def _check_session_timeout(self):
        """Raise RuntimeError if overall session timeout exceeded.

        Raises:
            RuntimeError: If the configured overall session timeout is exceeded.
        """
        if self._session_start is None:
            return
        elapsed = time.monotonic() - self._session_start
        if elapsed > self.timeouts.overall_session:
            msg = f"Overall session timeout exceeded ({self.timeouts.overall_session}s)"
            raise RuntimeError(msg)

    def get_cluster(self, remote_mode: str, fixture_dir: Path, repo_root: Path):  # noqa: ARG002
        """
        Return cluster.

        Raises:
            RuntimeError: If the operation cannot be completed.

        """
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
        """Run in controller."""
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
            env["PYTEST_REMOTE_FAKE_NODE_ROOT"] = "/artifacts/fake-node-runtime"
            env["PYTEST_REMOTE_FAKE_NODE_CAPTURE_DIR"] = "/artifacts/fake-node-runtime/fake-node-captures"
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
            "tests/e2e/fixtures/remote_xdist/controller_entrypoint.py",
        ]

        result = self._run_docker_cmd(exec_cmd, timeout=self.timeouts.compose_exec, operation="compose_exec", env=env)
        return result, Path(docker_artifact_dir)

    def cleanup(self):
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


cluster_manager = DockerClusterManager()
