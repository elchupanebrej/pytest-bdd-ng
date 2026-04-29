import atexit
import contextlib
import dataclasses
import os
import shutil
import subprocess  # noqa: S404
import time
from pathlib import Path

from tests.support.docker import _resolve_tool_path


@dataclasses.dataclass
class DockerTimeouts:
    startup_poll: int = 60
    compose_up: int = 120
    compose_exec: int = 300
    compose_cp: int = 30
    compose_down: int = 30
    alpine_install: int = 60
    overall_session: int = 600


def _run_wsl_cmd(args: list[str], timeout: int, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run a command inside WSL2 Alpine distro."""
    wsl_bin = _resolve_tool_path("wsl")
    if wsl_bin is None:
        msg = "wsl executable not found"
        raise FileNotFoundError(msg)
    return subprocess.run(  # noqa: S603
        [wsl_bin, "-d", "Alpine", "--", *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


class DockerClusterManager:
    def __init__(self, backend: str = "native", timeouts: DockerTimeouts | None = None):
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
        """Route Docker command through the appropriate backend."""
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
        if self.backend == backend:
            return
        if self.active_clusters:
            self.cleanup()
        self.backend = backend

    @staticmethod
    def _compose_env(remote_mode: str) -> dict[str, str]:
        return {
            **os.environ,
            "COMPOSE_PROJECT_NAME": f"pytestbddremote{remote_mode}",
            "PYTEST_REMOTE_MODE": remote_mode,
            "REPORT_NAME": "remote-xdist.ndjson",
        }

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
        """Raise RuntimeError if overall session timeout exceeded."""
        if self._session_start is None:
            return
        elapsed = time.monotonic() - self._session_start
        if elapsed > self.timeouts.overall_session:
            msg = f"Overall session timeout exceeded ({self.timeouts.overall_session}s)"
            raise RuntimeError(msg)

    def get_cluster(self, remote_mode: str, fixture_dir: Path, repo_root: Path):
        if remote_mode in self.active_clusters:
            return self.active_clusters[remote_mode], self.artifact_dirs[remote_mode]

        if self._session_start is None:
            self._session_start = time.monotonic()
        self._check_session_timeout()

        docker_artifact_dir = self._artifact_dir(fixture_dir)
        docker_artifact_dir.mkdir(parents=True, exist_ok=True)

        compose_cmd = ["docker", "compose", "-f", str(fixture_dir / "docker-compose.yml")]
        compose_env = self._compose_env(remote_mode)

        # Start the long-lived cluster
        self._run_docker_cmd(
            [*compose_cmd, "up", "-d", "--build"],
            timeout=self.timeouts.compose_up,
            operation="compose_up",
            env=compose_env,
        )

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
            "PYTEST_REMOTE_MODE",
            "-e",
            "PYTEST_BDD_TRANSPORT_FAIL_WORKERS",
            "-e",
            "REPORT_PATH",
            "-e",
            "VERIFY_REPORT_MODE",
            "-e",
            "PYTEST_REMOTE_EXTRA_ARGS",
            "-e",
            "VERIFY_MIN_CONSOLE_WRITES",
            "-e",
            "VERIFY_EXPECT_CONTROLLER_ONLY",
            "-e",
            "PYTEST_REMOTE_FAKE_NODE_ROOT",
            "-e",
            "PYTEST_REMOTE_FAKE_NODE_CAPTURE_DIR",
            "controller",
            "python",
            "tests/e2e/fixtures/remote_xdist/controller_entrypoint.py",
        ]

        result = self._run_docker_cmd(exec_cmd, timeout=self.timeouts.compose_exec, operation="compose_exec", env=env)
        return result, Path(docker_artifact_dir)

    def cleanup(self):
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
