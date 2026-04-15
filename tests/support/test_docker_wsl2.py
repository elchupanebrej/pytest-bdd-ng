from __future__ import annotations

import subprocess  # noqa: S404
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.support.docker import (
    _alpine_wsl2_available,
    _ensure_docker_cli_in_alpine,
    _start_docker_desktop,
    _wait_for_docker,
    docker_daemon_available,
    require_docker_daemon,
)
from tests.support.docker_cluster import DockerClusterManager, DockerTimeouts


class TestAlpineWsl2Available:
    def test_returns_true_when_alpine_wsl2_found(self):
        wsl_output = subprocess.CompletedProcess(
            args=["wsl", "-l", "-v"],
            returncode=0,
            stdout="  NAME            STATE           VERSION\n* Alpine          Running         2\n",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/wsl"),
            patch("tests.support.docker.subprocess.run", return_value=wsl_output),
        ):
            assert _alpine_wsl2_available() is True

    def test_returns_false_when_alpine_not_present(self):
        wsl_output = subprocess.CompletedProcess(
            args=["wsl", "-l", "-v"],
            returncode=0,
            stdout="  NAME            STATE           VERSION\n* Ubuntu          Running         2\n",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/wsl"),
            patch("tests.support.docker.subprocess.run", return_value=wsl_output),
        ):
            assert _alpine_wsl2_available() is False

    def test_returns_false_when_wsl_not_found(self):
        with patch("tests.support.docker.shutil.which", return_value=None):
            assert _alpine_wsl2_available() is False

    def test_returns_false_when_wsl_command_fails(self):
        wsl_output = subprocess.CompletedProcess(
            args=["wsl", "-l", "-v"],
            returncode=1,
            stdout="",
            stderr="wsl: not installed",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/wsl"),
            patch("tests.support.docker.subprocess.run", return_value=wsl_output),
        ):
            assert _alpine_wsl2_available() is False

    def test_returns_false_when_alpine_version_1(self):
        wsl_output = subprocess.CompletedProcess(
            args=["wsl", "-l", "-v"],
            returncode=0,
            stdout="  NAME            STATE           VERSION\n* Alpine          Running         1\n",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/wsl"),
            patch("tests.support.docker.subprocess.run", return_value=wsl_output),
        ):
            assert _alpine_wsl2_available() is False


class TestStartDockerDesktop:
    def test_starts_docker_desktop_successfully(self):
        result = subprocess.CompletedProcess(
            args=["powershell", "-Command", "Start-Process", "docker-desktop", "-WindowStyle", "Hidden"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="powershell"),
            patch("tests.support.docker.subprocess.run", return_value=result),
        ):
            _start_docker_desktop()


class TestWaitForDocker:
    def test_returns_true_when_docker_ready_immediately_native(self):
        result = subprocess.CompletedProcess(
            args=["docker", "info"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/docker"),
            patch("tests.support.docker.subprocess.run", return_value=result) as mock_run,
        ):
            assert _wait_for_docker("native", timeout=5) is True
            mock_run.assert_called_once()

    def test_returns_true_when_docker_ready_immediately_wsl2(self):
        result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "docker", "info"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/wsl"),
            patch("tests.support.docker.subprocess.run", return_value=result) as mock_run,
        ):
            assert _wait_for_docker("wsl2", timeout=5) is True
            mock_run.assert_called_once()

    def test_polls_until_ready_native(self):
        fail_result = subprocess.CompletedProcess(
            args=["docker", "info"],
            returncode=1,
            stdout="",
            stderr="Cannot connect",
        )
        success_result = subprocess.CompletedProcess(
            args=["docker", "info"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/docker"),
            patch(
                "tests.support.docker.subprocess.run", side_effect=[fail_result, fail_result, success_result]
            ) as mock_run,
            patch("tests.support.docker.time.sleep"),
        ):
            assert _wait_for_docker("native", timeout=5) is True
            assert mock_run.call_count == 3

    def test_polls_until_ready_wsl2(self):
        fail_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "docker", "info"],
            returncode=1,
            stdout="",
            stderr="Cannot connect",
        )
        success_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "docker", "info"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/wsl"),
            patch(
                "tests.support.docker.subprocess.run", side_effect=[fail_result, fail_result, success_result]
            ) as mock_run,
            patch("tests.support.docker.time.sleep"),
        ):
            assert _wait_for_docker("wsl2", timeout=5) is True
            assert mock_run.call_count == 3

    def test_returns_false_on_timeout(self):
        fail_result = subprocess.CompletedProcess(
            args=["docker", "info"],
            returncode=1,
            stdout="",
            stderr="Cannot connect",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/docker"),
            patch("tests.support.docker.subprocess.run", return_value=fail_result),
            patch("tests.support.docker.time.sleep"),
        ):
            assert _wait_for_docker("native", timeout=2) is False


class TestEnsureDockerCliInAlpine:
    def test_does_nothing_when_docker_cli_exists(self):
        result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "which", "docker"],
            returncode=0,
            stdout="/usr/bin/docker\n",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/wsl"),
            patch("tests.support.docker.subprocess.run", return_value=result) as mock_run,
        ):
            _ensure_docker_cli_in_alpine()
            mock_run.assert_called_once()

    def test_installs_docker_cli_when_missing(self):
        which_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "which", "docker"],
            returncode=1,
            stdout="",
            stderr="which: no docker",
        )
        install_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "-u", "root", "--", "apk", "add", "--no-cache", "docker-cli"],
            returncode=0,
            stdout="OK\n",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/wsl"),
            patch("tests.support.docker.subprocess.run", side_effect=[which_result, install_result]) as mock_run,
        ):
            _ensure_docker_cli_in_alpine()
            assert mock_run.call_count == 2

    def test_fails_when_installation_fails(self):
        which_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "which", "docker"],
            returncode=1,
            stdout="",
            stderr="which: no docker",
        )
        install_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "-u", "root", "--", "apk", "add", "--no-cache", "docker-cli"],
            returncode=1,
            stdout="",
            stderr="apk: permission denied",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/wsl"),
            patch("tests.support.docker.subprocess.run", side_effect=[which_result, install_result]),
            pytest.raises(pytest.fail.Exception),
        ):
            _ensure_docker_cli_in_alpine()


class TestDockerDaemonAvailable:
    def test_returns_native_when_native_docker_works(self):
        docker_bin = "/usr/bin/docker"
        info_result = subprocess.CompletedProcess(
            args=[docker_bin, "info"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value=docker_bin),
            patch("tests.support.docker.subprocess.run", return_value=info_result),
        ):
            docker_daemon_available.cache_clear()
            available, backend = docker_daemon_available()
            assert available is True
            assert backend == "native"

    def test_returns_wsl2_when_native_fails_but_wsl2_works(self):
        docker_bin = "/usr/bin/docker"
        info_result = subprocess.CompletedProcess(
            args=[docker_bin, "info"],
            returncode=1,
            stdout="",
            stderr="Cannot connect",
        )
        wsl_info_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "docker", "info"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value=docker_bin),
            patch("tests.support.docker.subprocess.run", side_effect=[info_result, wsl_info_result]),
            patch("tests.support.docker._alpine_wsl2_available", return_value=True),
        ):
            docker_daemon_available.cache_clear()
            available, backend = docker_daemon_available()
            assert available is True
            assert backend == "wsl2"

    def test_returns_false_when_both_fail_and_desktop_not_available(self):
        docker_bin = "/usr/bin/docker"
        info_result = subprocess.CompletedProcess(
            args=[docker_bin, "info"],
            returncode=1,
            stdout="",
            stderr="Cannot connect",
        )
        desktop_fail = subprocess.CompletedProcess(
            args=["powershell", "-Command", "Start-Process", "docker-desktop", "-WindowStyle", "Hidden"],
            returncode=1,
            stdout="",
            stderr="not found",
        )
        with (
            patch("tests.support.docker.shutil.which", return_value=docker_bin),
            patch("tests.support.docker.subprocess.run", side_effect=[info_result, desktop_fail]),
            patch("tests.support.docker._alpine_wsl2_available", return_value=False),
        ):
            docker_daemon_available.cache_clear()
            available, backend = docker_daemon_available()
            assert available is False
            assert backend is None


class TestRequireDockerDaemon:
    def test_returns_backend_when_available(self):
        with patch("tests.support.docker.docker_daemon_available", return_value=(True, "native")):
            result = require_docker_daemon()
            assert result == "native"

    def test_fails_when_docker_desktop_not_installed(self):
        with (
            patch("tests.support.docker.docker_daemon_available", return_value=(False, None)),
            patch("tests.support.docker.shutil.which", return_value=None),
            pytest.raises(pytest.fail.Exception, match="Docker Desktop not installed"),
        ):
            require_docker_daemon()

    def test_fails_when_wsl2_alpine_not_found(self):
        with (
            patch("tests.support.docker.docker_daemon_available", return_value=(False, None)),
            patch("tests.support.docker.shutil.which", return_value="/usr/bin/docker"),
            patch("tests.support.docker._alpine_wsl2_available", return_value=False),
            pytest.raises(pytest.fail.Exception, match="WSL2 Alpine dist not found"),
        ):
            require_docker_daemon()


class TestDockerTimeouts:
    def test_default_values(self):
        timeouts = DockerTimeouts()
        assert timeouts.startup_poll == 60
        assert timeouts.compose_up == 120
        assert timeouts.compose_exec == 300
        assert timeouts.compose_cp == 30
        assert timeouts.compose_down == 30
        assert timeouts.alpine_install == 60
        assert timeouts.overall_session == 600

    def test_overall_session_gte_sum_of_per_step(self):
        timeouts = DockerTimeouts()
        per_step_sum = (
            timeouts.startup_poll
            + timeouts.compose_up
            + timeouts.compose_exec
            + timeouts.compose_cp
            + timeouts.compose_down
            + timeouts.alpine_install
        )
        assert timeouts.overall_session >= per_step_sum

    def test_custom_values(self):
        timeouts = DockerTimeouts(compose_up=60, compose_exec=120)
        assert timeouts.compose_up == 60
        assert timeouts.compose_exec == 120
        assert timeouts.startup_poll == 60  # default preserved


class TestRunWslCmd:
    def test_constructs_wsl_command_correctly(self):
        result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "docker", "compose", "up", "-d"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with patch("tests.support.docker_cluster.subprocess.run", return_value=result) as mock_run:
            from tests.support.docker_cluster import _run_wsl_cmd

            _run_wsl_cmd(["docker", "compose", "up", "-d"], timeout=120)
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert "wsl" in call_args[0][0][0].lower()
            assert call_args[0][0][1:5] == ["-d", "Alpine", "--", "docker"]
            assert call_args.kwargs["timeout"] == 120

    def test_passes_env_and_capture_settings(self):
        result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "docker", "info"],
            returncode=0,
            stdout="Server Version: 24.0\n",
            stderr="",
        )
        with patch("tests.support.docker_cluster.subprocess.run", return_value=result) as mock_run:
            from tests.support.docker_cluster import _run_wsl_cmd

            _run_wsl_cmd(["docker", "info"], timeout=60)
            call_kwargs = mock_run.call_args.kwargs
            assert call_kwargs["capture_output"] is True
            assert call_kwargs["text"] is True

    def test_returns_completed_process(self):
        result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "echo", "hello"],
            returncode=0,
            stdout="hello\n",
            stderr="",
        )
        with patch("tests.support.docker_cluster.subprocess.run", return_value=result):
            from tests.support.docker_cluster import _run_wsl_cmd

            returned = _run_wsl_cmd(["echo", "hello"], timeout=30)
            assert returned.returncode == 0
            assert returned.stdout == "hello\n"


class TestDockerClusterManagerBackend:
    def test_wsl2_backend_routes_get_cluster_through_wsl(self):
        """DockerClusterManager with backend='wsl2' uses _run_wsl_cmd in get_cluster."""
        up_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "docker", "compose", "up", "-d", "--build"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker_cluster._run_wsl_cmd", return_value=up_result) as mock_wsl,
            patch("tests.support.docker_cluster.tempfile.mkdtemp", return_value="/tmp/artifacts"),  # noqa: S108
        ):
            mgr = DockerClusterManager(backend="wsl2")
            mgr.get_cluster("socket", Path("/fixtures"), Path("/repo"))
            mock_wsl.assert_called_once()
            call_args = mock_wsl.call_args[0][0]
            assert call_args[:2] == ["docker", "compose"]
            assert call_args[-3:] == ["up", "-d", "--build"]
            assert "-f" in call_args

    def test_native_backend_uses_subprocess_run_directly(self):
        """DockerClusterManager with backend='native' uses subprocess.run directly."""
        up_result = subprocess.CompletedProcess(
            args=["docker", "compose", "up", "-d", "--build"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker_cluster.subprocess.run", return_value=up_result) as mock_run,
            patch("tests.support.docker_cluster._run_wsl_cmd") as mock_wsl,
            patch("tests.support.docker_cluster.tempfile.mkdtemp", return_value="/tmp/artifacts"),  # noqa: S108
        ):
            mgr = DockerClusterManager(backend="native")
            mgr.get_cluster("socket", Path("/fixtures"), Path("/repo"))
            mock_run.assert_called_once()
            mock_wsl.assert_not_called()

    def test_wsl2_backend_routes_run_in_controller_through_wsl(self):
        """DockerClusterManager with backend='wsl2' routes exec through _run_wsl_cmd."""
        up_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "docker", "compose", "up", "-d", "--build"],
            returncode=0,
            stdout="",
            stderr="",
        )
        exec_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "docker", "compose", "exec", "controller"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker_cluster._run_wsl_cmd", side_effect=[up_result, exec_result]) as mock_wsl,
            patch("tests.support.docker_cluster.tempfile.mkdtemp", return_value="/tmp/artifacts"),  # noqa: S108
        ):
            mgr = DockerClusterManager(backend="wsl2")
            mgr.run_in_controller("socket", Path("/fixtures"), Path("/repo"), "success-live", "")
            assert mock_wsl.call_count == 2
            exec_args = mock_wsl.call_args_list[1][0][0]
            assert "exec" in exec_args

    def test_wsl2_backend_routes_cleanup_through_wsl(self):
        """DockerClusterManager with backend='wsl2' routes cleanup through _run_wsl_cmd."""
        up_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "docker", "compose", "up", "-d", "--build"],
            returncode=0,
            stdout="",
            stderr="",
        )
        down_result = subprocess.CompletedProcess(
            args=["wsl", "-d", "Alpine", "--", "docker", "compose", "down", "--volumes", "--remove-orphans"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("tests.support.docker_cluster._run_wsl_cmd", side_effect=[up_result, down_result]) as mock_wsl,
            patch("tests.support.docker_cluster.tempfile.mkdtemp", return_value="/tmp/artifacts"),  # noqa: S108
            patch("tests.support.docker_cluster.Path.exists", return_value=False),
        ):
            mgr = DockerClusterManager(backend="wsl2")
            mgr.get_cluster("socket", Path("/fixtures"), Path("/repo"))
            mgr.cleanup()
            down_args = mock_wsl.call_args_list[1][0][0]
            assert down_args[:2] == ["docker", "compose"]
            assert "down" in down_args
            assert "--volumes" in down_args
            assert "--remove-orphans" in down_args

    def test_default_backend_is_native(self):
        """DockerClusterManager defaults to native backend."""
        mgr = DockerClusterManager()
        assert mgr.backend == "native"


class TestDockerComposeRelativeMounts:
    def test_no_repo_root_env_var_in_compose(self):
        """docker-compose.yml should not use ${REPO_ROOT} for build context."""
        import yaml

        compose_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "docker-compose.yml"
        with Path(compose_path).open() as f:
            compose = yaml.safe_load(f)
        for svc_name, svc in compose.get("services", {}).items():
            build = svc.get("build", {})
            if isinstance(build, dict):
                context = build.get("context", "")
                assert "${REPO_ROOT}" not in context, f"Service {svc_name} build.context still uses ${{REPO_ROOT}}"

    def test_no_artifact_dir_env_var_in_volumes(self):
        """docker-compose.yml should not use ${ARTIFACT_DIR} in volumes."""
        import yaml

        compose_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "docker-compose.yml"
        with Path(compose_path).open() as f:
            compose = yaml.safe_load(f)
        for svc_name, svc in compose.get("services", {}).items():
            for vol in svc.get("volumes", []):
                assert "${ARTIFACT_DIR}" not in str(vol), f"Service {svc_name} volume still uses ${{ARTIFACT_DIR}}"

    def test_build_context_is_relative(self):
        """docker-compose.yml build contexts should be relative (.) or valid paths."""
        import yaml

        compose_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "docker-compose.yml"
        with Path(compose_path).open() as f:
            compose = yaml.safe_load(f)
        for svc_name, svc in compose.get("services", {}).items():
            build = svc.get("build", {})
            if isinstance(build, dict):
                context = build.get("context", "")
                assert context == "." or not context.startswith("${"), (
                    f"Service {svc_name} build.context should be relative, got: {context}"
                )


class TestEntrypointsSelfContained:
    def test_controller_entrypoint_has_no_external_imports(self):
        """controller_entrypoint.py should only import stdlib + pytest + pytest-xdist."""
        import ast

        entrypoint_path = (
            Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "controller_entrypoint.py"
        )
        tree = ast.parse(Path(entrypoint_path).read_text())
        allowed = {
            "os",
            "shlex",
            "shutil",
            "socket",
            "subprocess",
            "sys",
            "pathlib",
            "pytest",
            "execnet",
            "time",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    assert name in allowed, f"worker_entrypoint.py imports external module: {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                assert top in allowed, f"worker_entrypoint.py imports from external module: {node.module}"


class TestDockerfilesRelativeContext:
    def test_controller_dockerfile_no_absolute_repo_paths(self):
        """controller.Dockerfile COPY source paths should be relative to build context."""

        dockerfile_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "controller.Dockerfile"
        content = Path(dockerfile_path).read_text()
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("COPY"):
                parts = stripped.split()
                # Last part is destination (can be absolute in container)
                # Check only source paths (all except last)
                for part in parts[1:-1]:
                    assert not part.startswith("/") or part.startswith("--"), (
                        f"Dockerfile COPY source uses absolute path: {part}"
                    )

    def test_worker_dockerfile_no_absolute_repo_paths(self):
        """worker.Dockerfile COPY source paths should be relative to build context."""
        dockerfile_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "worker.Dockerfile"
        content = Path(dockerfile_path).read_text()
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("COPY"):
                parts = stripped.split()
                for part in parts[1:-1]:
                    assert not part.startswith("/") or part.startswith("--"), (
                        f"Dockerfile COPY source uses absolute path: {part}"
                    )
