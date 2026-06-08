"""Guard Makefile test API and environment target contracts."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
REQUIRED_TARGETS = (
    "test",
    "test-all",
    "test-platform-native",
    "test-platform-linux",
    "test-platform-windows",
    "test-platform-macos",
    "test-unit",
    "test-integration",
    "test-contract",
    "test-e2e",
    "test-compat",
    "test-perf",
    "test-external",
    "test-slow",
    "test-docker",
    "test-docker-linux",
    "test-docker-windows",
    "test-windows",
    "test-posix",
    "env-check",
    "env-check-tox",
    "env-check-powershell",
    "env-check-wsl2",
    "env-check-docker",
    "env-check-docker-linux",
    "env-check-docker-windows",
    "env-check-windows",
    "env-check-browser",
    "validate-test-all-backends",
    "env-install",
    "env-install-docker",
    "env-install-windows",
    "env-install-browser",
)
INSTALL_TARGETS = {"env-install", "env-install-docker", "env-install-windows", "env-install-browser"}
TEST_TARGETS = tuple(target for target in REQUIRED_TARGETS if target.startswith("test"))
MUTATING_COMMAND_RE = re.compile(
    r"\b("
    r"uv\s+sync|"
    r"uv\s+python\s+install|"
    r"pip\s+install|"
    r"npm\s+install|"
    r"playwright\s+install|"
    r"docker\s+(?:build|compose\s+build|pull)"
    r")\b",
)


def _makefile_text() -> str:
    return (REPO_ROOT / "Makefile").read_text(encoding="utf-8")


def _parse_targets(text: str) -> dict[str, dict[str, object]]:
    targets: dict[str, dict[str, object]] = {}
    current_targets: tuple[str, ...] = ()
    for line in text.splitlines():
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            current_targets = ()
            continue

        is_assignment = any(op in line for op in (":=", "+=", "?=", "="))
        is_keyword = line_stripped.startswith(
            ("export", "ifeq", "ifneq", "else", "endif", "include", "define", "undefine", "override"),
        )

        if not line.startswith(("\t", " ")) and ":" in line and not is_assignment and not is_keyword:
            target_part, dependency_part = line.split(":", maxsplit=1)
            current_targets = tuple(target.strip() for target in target_part.split() if target.strip())
            dependencies = tuple(dependency_part.strip().split())
            for target in current_targets:
                targets[target] = {"dependencies": dependencies, "commands": []}
        elif line.startswith("\t"):
            for target in current_targets:
                commands = targets[target]["commands"]
                assert isinstance(commands, list)
                commands.append(line.strip())
        else:
            current_targets = ()
    return targets


def _target_body(targets: dict[str, dict[str, object]], name: str) -> str:
    commands = targets[name]["commands"]
    assert isinstance(commands, list)
    return "\n".join(commands)


def test_makefile_exposes_required_test_api_targets() -> None:
    """Verify Makefile contains the Phase 12 human test API."""
    targets = _parse_targets(_makefile_text())

    assert set(REQUIRED_TARGETS).issubset(targets)


def test_test_targets_do_not_depend_on_env_install_targets() -> None:
    """Verify test targets use validation or group commands, never provisioning."""
    targets = _parse_targets(_makefile_text())

    offenders = {
        target: sorted(set(targets[target]["dependencies"]) & INSTALL_TARGETS)
        for target in TEST_TARGETS
        if target in targets and set(targets[target]["dependencies"]) & INSTALL_TARGETS
    }

    assert offenders == {}


def test_test_targets_run_group_commands_or_environment_checks() -> None:
    """Verify test targets are wired through explicit group commands or env checks."""
    targets = _parse_targets(_makefile_text())
    offenders = []
    for target in TEST_TARGETS:
        assert target in targets
        dependencies = set(targets[target]["dependencies"])
        commands = " ".join(targets[target]["commands"])
        has_env_check = any(dependency.startswith("env-check") for dependency in dependencies)
        has_group_command = bool(re.search(r"pytest .*?(-m|tests/cases/)", commands))
        has_make_group = "$(MAKE)" in commands and "test-" in commands
        has_tox_command = "$(TOX)" in commands and " run " in commands
        has_backend_validation = "validate-test-all-backends" in dependencies
        if not (has_env_check or has_group_command or has_make_group or has_tox_command or has_backend_validation):
            offenders.append(target)

    assert offenders == []


def test_env_check_targets_are_read_only() -> None:
    """Verify env-check targets diagnose setup without install/provision/build-image steps."""
    targets = _parse_targets(_makefile_text())
    offenders = {}
    for target in ("env-check", "env-check-docker", "env-check-windows", "env-check-browser"):
        assert target in targets
        body_without_echo = "\n".join(
            command for command in targets[target]["commands"] if not command.lstrip("@-").startswith("echo ")
        )
        if MUTATING_COMMAND_RE.search(body_without_echo):
            offenders[target] = body_without_echo

    assert offenders == {}


def test_phase15_test_all_validates_backends_before_platform_work() -> None:
    """Verify full cross-platform entrypoint validates before executing subwork."""
    targets = _parse_targets(_makefile_text())
    dependencies = set(targets["test-all"]["dependencies"])
    body = _target_body(targets, "test-all")

    assert "validate-test-all-backends" in dependencies
    for target in (
        "test-platform-native",
        "test-platform-linux",
        "test-platform-windows",
        "test-platform-macos",
    ):
        assert target in body
    assert "render-tox-reports-run" in body
    assert "python -m pytest" not in body


def test_phase15_platform_targets_are_tox_backed_and_arg_isolated() -> None:
    """Verify platform targets use only their matching tox env and arg variables."""
    targets = _parse_targets(_makefile_text())
    expected = {
        "test-platform-native": ("TOX_NATIVE_ENVS", "TEST_NATIVE_ARGS"),
        "test-platform-linux": ("TOX_LINUX_ENVS", "TEST_LINUX_ARGS"),
        "test-platform-windows": ("TOX_WINDOWS_ENVS", "TEST_WINDOWS_ARGS"),
        "test-platform-macos": ("TOX_MACOS_ENVS", "TEST_MACOS_ARGS"),
    }

    for target, (env_var, arg_var) in expected.items():
        body = _target_body(targets, target)
        assert "$(TOX)" in body or target == "test-platform-windows"
        assert env_var in body
        assert arg_var in body


def test_phase15_backend_routing_patterns_are_explicit() -> None:
    """Verify backend routes for PowerShell, WSL2, Docker, and custom Windows backend."""
    makefile = _makefile_text()

    assert "powershell.exe" in makefile
    assert "wsl.exe sh -lc" in makefile
    assert "python:3.14-windowsservercore-ltsc2022" in makefile
    assert "WINDOWS_TOX_BACKEND_COMMAND" in makefile
    assert "env-check-docker-windows" in makefile


def test_phase15_modes_and_argument_variables_are_exported() -> None:
    """Verify collect/fail-fast/report controls and arg variables are public Make inputs."""
    makefile = _makefile_text()

    for variable in (
        "TEST_ALL_ARGS",
        "TEST_NATIVE_ARGS",
        "TEST_LINUX_ARGS",
        "TEST_WINDOWS_ARGS",
        "TEST_MACOS_ARGS",
        "REPORT_ARGS",
        "FAIL_FAST",
        "ARTIFACT_MODE",
        "REPORT_MODE",
    ):
        assert re.search(rf"^{variable} \?=", makefile, re.MULTILINE)
    assert re.search(r"^export .*TEST_LINUX_ARGS.*TEST_WINDOWS_ARGS", makefile, re.MULTILINE)


def test_phase15_legacy_native_docker_routing_variables_removed() -> None:
    """Verify obsolete routing variables do not drift back into validation/docs contract."""
    makefile = _makefile_text()

    assert "NATIVE_TARGETS" not in makefile
    assert "DOCKER_TARGETS" not in makefile


def test_phase17_makefile_targets_and_tox_ci_conditional() -> None:
    """Verify Phase 17 targets and tox CI conditional logic."""
    makefile = _makefile_text()
    targets = _parse_targets(makefile)

    # Check targets exist
    for target in ("tox", "env-install-npm", "check-message-schemas", "validate-github-actions"):
        assert target in targets

    # Test GITHUB_ACTIONS conditional and TOX command
    assert "GITHUB_ACTIONS" in makefile
    assert "uvx --with tox-uv --with tox-gh-actions tox" in makefile
    assert "uvx --with tox-uv tox" in makefile

    # Test env-install-npm target body installs exactly the expected packages with --no-save
    npm_body = _target_body(targets, "env-install-npm")
    assert "npm install" in npm_body
    assert "--no-save" in npm_body
    assert "@cucumber/html-formatter" in npm_body
    assert "cucumber-html-reporter" in npm_body

    # Test validate-github-actions target body checks command -v act, contains install URL, and runs act --validate
    act_body = _target_body(targets, "validate-github-actions")
    assert "command -v act" in act_body
    assert "https://nektosact.com/installation/" in act_body
    assert "act --validate" in act_body

    # Test check-message-schemas target
    schema_body = _target_body(targets, "check-message-schemas")
    assert "sync_messages_contract_schemas" in schema_body
    assert "--check" in schema_body
