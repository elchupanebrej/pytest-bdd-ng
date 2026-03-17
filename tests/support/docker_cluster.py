import subprocess
import atexit
import tempfile
import os
import shutil
from pathlib import Path


class DockerClusterManager:
    def __init__(self):
        self.active_clusters = {}
        self.artifact_dirs = {}
        atexit.register(self.cleanup)

    def get_cluster(self, remote_mode: str, fixture_dir: Path, repo_root: Path):
        if remote_mode in self.active_clusters:
            return self.active_clusters[remote_mode], self.artifact_dirs[remote_mode]

        docker_artifact_dir = tempfile.mkdtemp(prefix=f"pytest-bdd-remote-artifacts-{remote_mode}-", dir=repo_root)

        env = {
            **os.environ,
            "BUILDKIT_PROGRESS": "plain",
            "REPO_ROOT": str(repo_root),
            "ARTIFACT_DIR": docker_artifact_dir,
            "PYTEST_REMOTE_MODE": remote_mode,
            "COMPOSE_PROJECT_NAME": f"pytestbddremote{remote_mode}",
        }

        compose_cmd = ["docker", "compose", "-f", str(fixture_dir / "docker-compose.yml")]

        # Start the long-lived cluster
        subprocess.run([*compose_cmd, "up", "-d", "--build"], check=True, env=env)

        self.active_clusters[remote_mode] = compose_cmd
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

        env = {
            **os.environ,
            "COMPOSE_PROJECT_NAME": f"pytestbddremote{remote_mode}",
            "REPORT_PATH": f"/artifacts/remote-xdist.ndjson",
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

        result = subprocess.run(exec_cmd, check=False, capture_output=True, text=True, env=env)
        return result, Path(docker_artifact_dir)

    def cleanup(self):
        for remote_mode, compose_cmd in self.active_clusters.items():
            env = {
                **os.environ,
                "COMPOSE_PROJECT_NAME": f"pytestbddremote{remote_mode}",
            }
            subprocess.run([*compose_cmd, "down", "--volumes", "--remove-orphans"], check=False, env=env)

        for artifact_dir in self.artifact_dirs.values():
            if os.path.exists(artifact_dir):
                shutil.rmtree(artifact_dir, ignore_errors=True)


cluster_manager = DockerClusterManager()
