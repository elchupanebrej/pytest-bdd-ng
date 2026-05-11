"""Provide test docker wsl2 helpers."""

from __future__ import annotations

import subprocess  # noqa: S404
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.support.cucumber_formatters import materialize_fake_node_runtime
from tests.support.docker import (
    _alpine_wsl2_available,
    _ensure_docker_cli_in_alpine,
    _resolve_tool_path,
    _start_docker_desktop,
    _wait_for_docker,
    docker_daemon_available,
    require_docker_daemon,
)
from tests.support.docker_cluster import DockerClusterManager, DockerTimeouts


def test_prefers_path_lookup():
    """Verify prefers path lookup."""
    with patch("tests.support.docker.shutil.which", return_value=r"C:\tools\docker.exe"):
        assert _resolve_tool_path("docker") == r"C:\tools\docker.exe"


def test_uses_windows_wsl_fallback_when_path_missing():
    """Verify uses windows wsl fallback when path missing."""
    with (
        patch("tests.support.docker.shutil.which", return_value=None),
        patch("tests.support.docker.os.name", "nt"),
        patch.dict("tests.support.docker.os.environ", {"SystemRoot": r"C:\Windows"}, clear=False),
        patch("tests.support.docker.Path.exists", return_value=True),
    ):
        assert _resolve_tool_path("wsl").lower().endswith(r"system32\wsl.exe")


def test_uses_windows_docker_fallback_when_path_missing():
    """Verify uses windows docker fallback when path missing."""
    with (
        patch("tests.support.docker.shutil.which", return_value=None),
        patch("tests.support.docker.os.name", "nt"),
        patch.dict("tests.support.docker.os.environ", {"ProgramFiles": r"C:\Program Files"}, clear=False),
        patch("tests.support.docker.Path.exists", side_effect=[True, False]),
    ):
        assert _resolve_tool_path("docker").lower().endswith(r"docker\docker\resources\bin\docker.exe")


def test_returns_true_when_alpine_wsl2_found():
    """Verify returns true when alpine wsl2 found."""
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


def test_returns_false_when_alpine_not_present():
    """Verify returns false when alpine not present."""
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


def test_returns_false_when_wsl_not_found():
    """Verify returns false when wsl not found."""
    with patch("tests.support.docker._resolve_tool_path", return_value=None):
        assert _alpine_wsl2_available() is False


def test_returns_false_when_wsl_command_fails():
    """Verify returns false when wsl command fails."""
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


def test_returns_false_when_alpine_version_1():
    """Verify returns false when alpine version 1."""
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


def test_starts_docker_desktop_successfully():
    """Verify starts docker desktop successfully."""
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


def test_returns_true_when_docker_ready_immediately_native():
    """Verify returns true when docker ready immediately native."""
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


def test_returns_true_when_docker_ready_immediately_wsl2():
    """Verify returns true when docker ready immediately wsl2."""
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


def test_polls_until_ready_native():
    """Verify polls until ready native."""
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
            "tests.support.docker.subprocess.run",
            side_effect=[fail_result, fail_result, success_result],
        ) as mock_run,
        patch("tests.support.docker.time.sleep"),
    ):
        assert _wait_for_docker("native", timeout=5) is True
        assert mock_run.call_count == 3


def test_polls_until_ready_wsl2():
    """Verify polls until ready wsl2."""
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
            "tests.support.docker.subprocess.run",
            side_effect=[fail_result, fail_result, success_result],
        ) as mock_run,
        patch("tests.support.docker.time.sleep"),
    ):
        assert _wait_for_docker("wsl2", timeout=5) is True
        assert mock_run.call_count == 3


def test_returns_false_on_timeout():
    """Verify returns false on timeout."""
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


def test_does_nothing_when_docker_cli_exists():
    """Verify does nothing when docker cli exists."""
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


def test_installs_docker_cli_when_missing():
    """Verify installs docker cli when missing."""
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


def test_fails_when_installation_fails():
    """Verify fails when installation fails."""
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


def test_returns_native_when_native_docker_works():
    """Verify returns native when native docker works."""
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


def test_returns_wsl2_when_native_fails_but_wsl2_works():
    """Verify returns wsl2 when native fails but wsl2 works."""
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


def test_returns_false_when_both_fail_and_desktop_not_available():
    """Verify returns false when both fail and desktop not available."""
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


def test_returns_backend_when_available():
    """Verify returns backend when available."""
    with patch("tests.support.docker.docker_daemon_available", return_value=(True, "native")):
        result = require_docker_daemon()
        assert result == "native"


def test_refreshes_cached_probe_before_checking_environment():
    """Verify refreshes cached probe before checking environment."""
    availability_probe = Mock(return_value=(True, "native"))
    availability_probe.cache_clear = Mock()
    with patch("tests.support.docker.docker_daemon_available", availability_probe):
        result = require_docker_daemon()
        assert result == "native"
        availability_probe.cache_clear.assert_called_once_with()


def test_fails_when_docker_desktop_not_installed():
    """Verify fails when docker desktop not installed."""
    with (
        patch("tests.support.docker.docker_daemon_available", return_value=(False, None)),
        patch("tests.support.docker._resolve_tool_path", return_value=None),
        pytest.raises(pytest.fail.Exception, match="Docker Desktop not installed"),
    ):
        require_docker_daemon()


def test_fails_when_wsl2_alpine_not_found():
    """Verify fails when wsl2 alpine not found."""
    with (
        patch("tests.support.docker.docker_daemon_available", return_value=(False, None)),
        patch("tests.support.docker._resolve_tool_path", return_value="/usr/bin/docker"),
        patch("tests.support.docker._alpine_wsl2_available", return_value=False),
        pytest.raises(pytest.fail.Exception, match="WSL2 Alpine dist not found"),
    ):
        require_docker_daemon()


def test_default_values():
    """Verify default values."""
    timeouts = DockerTimeouts()
    assert timeouts.startup_poll == 60
    assert timeouts.compose_up == 300
    assert timeouts.compose_exec == 300
    assert timeouts.compose_cp == 30
    assert timeouts.compose_down == 30
    assert timeouts.alpine_install == 60
    assert timeouts.overall_session == 900


def test_overall_session_gte_sum_of_per_step():
    """Verify overall session gte sum of per step."""
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


def test_custom_values():
    """Verify custom values."""
    timeouts = DockerTimeouts(compose_up=60, compose_exec=120)
    assert timeouts.compose_up == 60
    assert timeouts.compose_exec == 120
    assert timeouts.startup_poll == 60  # default preserved


def test_constructs_wsl_command_correctly():
    """Verify constructs wsl command correctly."""
    result = subprocess.CompletedProcess(
        args=["wsl", "-d", "Alpine", "--", "docker", "compose", "up", "-d"],
        returncode=0,
        stdout="",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster._resolve_tool_path", return_value="/usr/bin/wsl"),
        patch("tests.support.docker_cluster.subprocess.run", return_value=result) as mock_run,
    ):
        from tests.support.docker_cluster import _run_wsl_cmd  # noqa: PLC0415 -- optional docker import in test

        _run_wsl_cmd(["docker", "compose", "up", "-d"], timeout=120)
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "wsl" in call_args[0][0][0].lower()
        assert call_args[0][0][1:5] == ["-d", "Alpine", "--", "docker"]
        assert call_args.kwargs["timeout"] == 120


def test_passes_env_and_capture_settings():
    """Verify passes env and capture settings."""
    result = subprocess.CompletedProcess(
        args=["wsl", "-d", "Alpine", "--", "docker", "info"],
        returncode=0,
        stdout="Server Version: 24.0\n",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster._resolve_tool_path", return_value="/usr/bin/wsl"),
        patch("tests.support.docker_cluster.subprocess.run", return_value=result) as mock_run,
    ):
        from tests.support.docker_cluster import _run_wsl_cmd  # noqa: PLC0415 -- optional docker import in test

        _run_wsl_cmd(["docker", "info"], timeout=60)
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["capture_output"] is True
        assert call_kwargs["text"] is True


def test_inlines_env_overrides_into_wsl_command():
    """Verify inlines env overrides into wsl command."""
    result = subprocess.CompletedProcess(
        args=["wsl", "-d", "Alpine", "--", "env", "PYTEST_REMOTE_MODE=ssh", "docker", "compose", "up", "-d"],
        returncode=0,
        stdout="",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster._resolve_tool_path", return_value="/usr/bin/wsl"),
        patch.dict("tests.support.docker_cluster.os.environ", {"PATH": "/usr/bin"}, clear=False),
        patch("tests.support.docker_cluster.subprocess.run", return_value=result) as mock_run,
    ):
        from tests.support.docker_cluster import _run_wsl_cmd  # noqa: PLC0415 -- optional docker import in test

        _run_wsl_cmd(
            ["docker", "compose", "up", "-d"],
            timeout=120,
            env={"PATH": "/usr/bin", "PYTEST_REMOTE_MODE": "ssh", "COMPOSE_PROJECT_NAME": "pytestbddremotessh"},
        )
        call_args = mock_run.call_args[0][0]
        assert call_args[:5] == ["/usr/bin/wsl", "-d", "Alpine", "--", "env"]
        assert "PYTEST_REMOTE_MODE=ssh" in call_args
        assert "COMPOSE_PROJECT_NAME=pytestbddremotessh" in call_args
        assert call_args[-4:] == ["docker", "compose", "up", "-d"]


def test_returns_completed_process():
    """Verify returns completed process."""
    result = subprocess.CompletedProcess(
        args=["wsl", "-d", "Alpine", "--", "echo", "hello"],
        returncode=0,
        stdout="hello\n",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster._resolve_tool_path", return_value="/usr/bin/wsl"),
        patch("tests.support.docker_cluster.subprocess.run", return_value=result),
    ):
        from tests.support.docker_cluster import _run_wsl_cmd  # noqa: PLC0415 -- optional docker import in test

        returned = _run_wsl_cmd(["echo", "hello"], timeout=30)
        assert returned.returncode == 0
        assert returned.stdout == "hello\n"


def test_wsl2_backend_routes_get_cluster_through_wsl():
    """DockerClusterManager with backend='wsl2' uses _run_wsl_cmd in get_cluster."""
    up_result = subprocess.CompletedProcess(
        args=["wsl", "-d", "Alpine", "--", "docker", "compose", "up", "-d", "--build"],
        returncode=0,
        stdout="",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster._run_wsl_cmd", return_value=up_result) as mock_wsl,
        patch("tests.support.docker_cluster.Path.mkdir"),
    ):
        mgr = DockerClusterManager(backend="wsl2")
        mgr.get_cluster("socket", Path("/fixtures"), Path("/repo"))
        mock_wsl.assert_called_once()
        call_args = mock_wsl.call_args[0][0]
        assert call_args[:2] == ["docker", "compose"]
        assert call_args[-3:] == ["up", "-d", "--build"]
        assert "-f" in call_args


def test_native_backend_uses_subprocess_run_directly():
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
        patch("tests.support.docker_cluster._resolve_tool_path", return_value=r"C:\Docker\docker.exe"),
        patch("tests.support.docker_cluster.Path.mkdir"),
    ):
        mgr = DockerClusterManager(backend="native")
        mgr.get_cluster("socket", Path("/fixtures"), Path("/repo"))
        mock_run.assert_called_once()
        mock_wsl.assert_not_called()
        assert mock_run.call_args[0][0][0].lower().endswith("docker.exe")


def test_wsl2_backend_routes_run_in_controller_through_wsl():
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
        patch("tests.support.docker_cluster.Path.mkdir"),
    ):
        mgr = DockerClusterManager(backend="wsl2")
        mgr.run_in_controller("socket", Path("/fixtures"), Path("/repo"), "success-live", "")
        assert mock_wsl.call_count == 2
        exec_args = mock_wsl.call_args_list[1][0][0]
        assert "exec" in exec_args


def test_native_backend_uses_stable_compose_project_name_for_up_and_exec():
    """Verify native backend uses stable compose project name for up and exec."""
    up_result = subprocess.CompletedProcess(
        args=["docker", "compose", "up", "-d", "--build"],
        returncode=0,
        stdout="",
        stderr="",
    )
    exec_result = subprocess.CompletedProcess(
        args=["docker", "compose", "exec", "controller"],
        returncode=0,
        stdout="",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster.subprocess.run", side_effect=[up_result, exec_result]) as mock_run,
        patch("tests.support.docker_cluster._resolve_tool_path", return_value=r"C:\Docker\docker.exe"),
        patch("tests.support.docker_cluster.Path.mkdir"),
    ):
        mgr = DockerClusterManager(backend="native")
        mgr.run_in_controller("ssh", Path("/fixtures"), Path("/repo"), "success", "")

        up_env = mock_run.call_args_list[0].kwargs["env"]
        exec_env = mock_run.call_args_list[1].kwargs["env"]

        assert up_env["COMPOSE_PROJECT_NAME"] == "pytestbddremotessh"
        assert exec_env["COMPOSE_PROJECT_NAME"] == up_env["COMPOSE_PROJECT_NAME"]


def test_compose_up_sets_remote_mode_for_cluster_services():
    """Verify compose up sets remote mode for cluster services."""
    up_result = subprocess.CompletedProcess(
        args=["docker", "compose", "up", "-d", "--build"],
        returncode=0,
        stdout="",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster.subprocess.run", return_value=up_result) as mock_run,
        patch("tests.support.docker_cluster._resolve_tool_path", return_value=r"C:\Docker\docker.exe"),
        patch("tests.support.docker_cluster.Path.mkdir"),
    ):
        mgr = DockerClusterManager(backend="native")
        mgr.get_cluster("ssh", Path("/fixtures"), Path("/repo"))

        up_env = mock_run.call_args.kwargs["env"]

        assert up_env["PYTEST_REMOTE_MODE"] == "ssh"


def test_run_in_controller_uses_compose_mounted_artifacts_directory():
    """Verify run in controller uses compose mounted artifacts directory."""
    up_result = subprocess.CompletedProcess(
        args=["docker", "compose", "up", "-d", "--build"],
        returncode=0,
        stdout="",
        stderr="",
    )
    exec_result = subprocess.CompletedProcess(
        args=["docker", "compose", "exec", "controller"],
        returncode=0,
        stdout="",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster.subprocess.run", side_effect=[up_result, exec_result]),
        patch("tests.support.docker_cluster._resolve_tool_path", return_value=r"C:\Docker\docker.exe"),
        patch("tests.support.docker_cluster.Path.mkdir"),
    ):
        mgr = DockerClusterManager(backend="native")
        _, artifact_dir = mgr.run_in_controller("ssh", Path("/fixtures"), Path("/repo"), "success", "")

        assert artifact_dir == Path("/fixtures") / "artifacts"


def test_run_in_controller_disables_tty_for_compose_exec():
    """Verify run in controller disables tty for compose exec."""
    up_result = subprocess.CompletedProcess(
        args=["docker", "compose", "up", "-d", "--build"],
        returncode=0,
        stdout="",
        stderr="",
    )
    exec_result = subprocess.CompletedProcess(
        args=["docker", "compose", "exec", "controller"],
        returncode=0,
        stdout="",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster.subprocess.run", side_effect=[up_result, exec_result]) as mock_run,
        patch("tests.support.docker_cluster._resolve_tool_path", return_value=r"C:\Docker\docker.exe"),
        patch("tests.support.docker_cluster.Path.mkdir"),
    ):
        mgr = DockerClusterManager(backend="native")
        mgr.run_in_controller("ssh", Path("/fixtures"), Path("/repo"), "success", "")

        exec_args = mock_run.call_args_list[1][0][0]

        assert "exec" in exec_args
        assert "-T" in exec_args


def test_run_in_controller_uses_explicit_exec_env_values():
    """Verify run in controller uses explicit exec env values."""
    up_result = subprocess.CompletedProcess(
        args=["docker", "compose", "up", "-d", "--build"],
        returncode=0,
        stdout="",
        stderr="",
    )
    exec_result = subprocess.CompletedProcess(
        args=["docker", "compose", "exec", "controller"],
        returncode=0,
        stdout="",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster.subprocess.run", side_effect=[up_result, exec_result]) as mock_run,
        patch("tests.support.docker_cluster._resolve_tool_path", return_value=r"C:\Docker\docker.exe"),
        patch("tests.support.docker_cluster.Path.mkdir"),
    ):
        mgr = DockerClusterManager(backend="native")
        mgr.run_in_controller("ssh", Path("/fixtures"), Path("/repo"), "success-live", "gw1")

        exec_args = mock_run.call_args_list[1][0][0]

        assert "PYTEST_REMOTE_MODE=ssh" in exec_args
        assert "PYTEST_BDD_TRANSPORT_FAIL_WORKERS=gw1" in exec_args
        assert "VERIFY_EXPECT_CONTROLLER_ONLY=1" in exec_args
        assert "PYTEST_REMOTE_FAKE_NODE_ROOT=/artifacts/fake-node-runtime" in exec_args


def test_wsl2_backend_routes_cleanup_through_wsl():
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
        patch("tests.support.docker_cluster.Path.mkdir"),
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


def test_default_backend_is_native():
    """DockerClusterManager defaults to native backend."""
    mgr = DockerClusterManager()
    assert mgr.backend == "native"


def test_session_timer_starts_on_first_cluster_use():
    """Verify session timer starts on first cluster use."""
    up_result = subprocess.CompletedProcess(
        args=["docker", "compose", "up", "-d", "--build"],
        returncode=0,
        stdout="",
        stderr="",
    )
    with (
        patch("tests.support.docker_cluster.subprocess.run", return_value=up_result),
        patch("tests.support.docker_cluster._resolve_tool_path", return_value=r"C:\Docker\docker.exe"),
        patch("tests.support.docker_cluster.Path.mkdir"),
        patch("tests.support.docker_cluster.time.monotonic", return_value=1000.0),
    ):
        mgr = DockerClusterManager(backend="native", timeouts=DockerTimeouts(overall_session=1))
        assert mgr._session_start is None

        mgr.get_cluster("ssh", Path("/fixtures"), Path("/repo"))

        assert mgr._session_start == pytest.approx(1000.0)


def test_local_images_have_build_config():
    """docker-compose.yml local-tagged services should be buildable without registry pulls."""
    import yaml  # noqa: PLC0415 -- optional docker import in test

    compose_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "docker-compose.yml"
    with Path(compose_path).open(encoding="utf-8") as f:
        compose = yaml.safe_load(f)

    for svc_name, svc in compose.get("services", {}).items():
        image = svc.get("image", "")
        if isinstance(image, str) and image.endswith(":local"):
            assert "build" in svc, f"Service {svc_name} uses a local image tag without a build config"


def test_remote_xdist_builds_use_repo_root_context():
    """remote xdist Dockerfiles copy repo-root files, so compose builds must use the repo root as context."""
    import yaml  # noqa: PLC0415 -- optional docker import in test

    compose_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "docker-compose.yml"
    with Path(compose_path).open(encoding="utf-8") as f:
        compose = yaml.safe_load(f)

    expected_context = "../../../.."
    for svc_name in ("controller", "proxy", "worker1", "worker2"):
        build = compose["services"][svc_name]["build"]
        assert build["context"] == expected_context, f"Service {svc_name} should build from repo root context"


def test_no_repo_root_env_var_in_compose():
    """docker-compose.yml should not use ${REPO_ROOT} for build context."""
    import yaml  # noqa: PLC0415 -- optional docker import in test

    compose_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "docker-compose.yml"
    with Path(compose_path).open(encoding="utf-8") as f:
        compose = yaml.safe_load(f)
    for svc_name, svc in compose.get("services", {}).items():
        build = svc.get("build", {})
        if isinstance(build, dict):
            context = build.get("context", "")
            assert "${REPO_ROOT}" not in context, f"Service {svc_name} build.context still uses ${{REPO_ROOT}}"


def test_no_artifact_dir_env_var_in_volumes():
    """docker-compose.yml should not use ${ARTIFACT_DIR} in volumes."""
    import yaml  # noqa: PLC0415 -- optional docker import in test

    compose_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "docker-compose.yml"
    with Path(compose_path).open(encoding="utf-8") as f:
        compose = yaml.safe_load(f)
    for svc_name, svc in compose.get("services", {}).items():
        for vol in svc.get("volumes", []):
            assert "${ARTIFACT_DIR}" not in str(vol), f"Service {svc_name} volume still uses ${{ARTIFACT_DIR}}"


def test_build_context_is_relative():
    """docker-compose.yml build contexts should be relative (.) or valid paths."""
    import yaml  # noqa: PLC0415 -- optional docker import in test

    compose_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "docker-compose.yml"
    with Path(compose_path).open(encoding="utf-8") as f:
        compose = yaml.safe_load(f)
    for svc_name, svc in compose.get("services", {}).items():
        build = svc.get("build", {})
        if isinstance(build, dict):
            context = build.get("context", "")
            assert context == "." or not context.startswith("${"), (
                f"Service {svc_name} build.context should be relative, got: {context}"
            )


def test_controller_entrypoint_has_no_external_imports():
    """controller_entrypoint.py should only import stdlib + pytest + pytest-xdist."""
    import ast  # noqa: PLC0415 -- optional docker import in test

    entrypoint_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "controller_entrypoint.py"
    tree = ast.parse(Path(entrypoint_path).read_text(encoding="utf-8"))
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


def test_controller_entrypoint_waits_for_ssh_command_readiness():
    """Verify controller entrypoint waits for ssh command readiness."""
    entrypoint_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "controller_entrypoint.py"
    content = Path(entrypoint_path).read_text(encoding="utf-8")

    assert "ssh_ready(" in content
    assert '"ssh"' in content
    assert "python3.14" in content
    assert "print(1)" in content


def test_node_and_npm_scripts_use_lf_newlines(tmp_path: Path):
    """Verify node and npm scripts use lf newlines."""
    runtime = materialize_fake_node_runtime(
        tmp_path / "fake-node-runtime",
        preinstalled_packages=("@cucumber/cucumber",),
    )

    node_bytes = (runtime["bin_dir"] / "node").read_bytes()
    npm_bytes = (runtime["bin_dir"] / "npm").read_bytes()

    assert b"\r\n" not in node_bytes
    assert b"\r\n" not in npm_bytes
    assert node_bytes.startswith(b"#!/usr/bin/env python3\n")
    assert npm_bytes.startswith(b"#!/usr/bin/env python3\n")


def test_controller_dockerfile_installs_git_for_gitpython_imports():
    """Verify controller dockerfile installs git for gitpython imports."""
    dockerfile_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "controller.Dockerfile"
    content = Path(dockerfile_path).read_text(encoding="utf-8")

    assert "apt-get install --yes --no-install-recommends" in content
    assert " git" in content or " git \\" in content


def test_worker_dockerfile_installs_git_for_gitpython_imports():
    """Verify worker dockerfile installs git for gitpython imports."""
    dockerfile_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "worker.Dockerfile"
    content = Path(dockerfile_path).read_text(encoding="utf-8")

    assert "apt-get install --yes --no-install-recommends" in content
    assert " git" in content or " git \\" in content


def test_controller_dockerfile_no_absolute_repo_paths():
    """controller.Dockerfile COPY source paths should be relative to build context."""

    dockerfile_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "controller.Dockerfile"
    content = Path(dockerfile_path).read_text(encoding="utf-8")
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


def test_worker_dockerfile_no_absolute_repo_paths():
    """worker.Dockerfile COPY source paths should be relative to build context."""
    dockerfile_path = Path(__file__).parent.parent / "e2e" / "fixtures" / "remote_xdist" / "worker.Dockerfile"
    content = Path(dockerfile_path).read_text(encoding="utf-8")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("COPY"):
            parts = stripped.split()
            for part in parts[1:-1]:
                assert not part.startswith("/") or part.startswith("--"), (
                    f"Dockerfile COPY source uses absolute path: {part}"
                )
