"""Guard Makefile test API and environment target contracts."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_TARGETS = (
    "test",
    "test-all",
    "test-unit",
    "test-integration",
    "test-contract",
    "test-e2e",
    "test-compat",
    "test-perf",
    "test-external",
    "test-slow",
    "test-docker",
    "test-windows",
    "test-posix",
    "env-check",
    "env-check-docker",
    "env-check-windows",
    "env-check-browser",
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
        if line and not line.startswith(("\t", " ")) and ":" in line:
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
    return targets


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
        if not (has_env_check or has_group_command or has_make_group):
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
