#!/usr/bin/env python3
"""Report the strict runtime type-check policy, then invoke that policy."""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class TypecheckConfigurationError(RuntimeError):
    """A required checker or typing dependency is missing or inconsistent."""


def _read_policy(config_path: Path) -> tuple[str, str, tuple[str, ...], bytes]:
    config_content = config_path.read_bytes()
    try:
        config_text = config_content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise TypecheckConfigurationError("pyproject.toml must be UTF-8 encoded.") from error

    def section_body(section_name: str) -> str:
        section_header = f"[{section_name}]"
        try:
            section_start = config_text.index(section_header) + len(section_header)
        except ValueError as error:
            raise TypecheckConfigurationError(f"pyproject.toml is missing [{section_name}].") from error
        next_section = config_text.find("\n[", section_start)
        return config_text[section_start:] if next_section < 0 else config_text[section_start:next_section]

    def quoted_value(body: str, key: str) -> str | None:
        match = re.search(rf"^\s*{re.escape(key)}\s*=\s*\"([^\"]+)\"\s*$", body, re.MULTILINE)
        return match.group(1) if match else None

    policy = section_body("tool.pytest-cuke.typecheck")
    checker_version = quoted_value(policy, "checker_version")
    source_scope = quoted_value(policy, "source_scope")
    required_match = re.search(r"^\s*required_distributions\s*=\s*\[([^\]]*)\]", policy, re.MULTILINE)
    required_distributions = re.findall(r'"([^\"]+)"', required_match.group(1)) if required_match else None
    optional_dependencies = section_body("project.optional-dependencies")
    testtypes_match = re.search(r"^\s*testtypes\s*=\s*\[([^\]]*)\]", optional_dependencies, re.MULTILINE)
    testtypes_distributions = set(re.findall(r'"([^\"]+)"', testtypes_match.group(1))) if testtypes_match else set()
    mypy_config = section_body("tool.mypy")
    configured_scope_match = re.search(r"^\s*files\s*=\s*\[([^\]]*)\]", mypy_config, re.MULTILINE)
    configured_scope = re.findall(r'"([^\"]+)"', configured_scope_match.group(1)) if configured_scope_match else []
    configured_plugins_match = re.search(r"^\s*plugins\s*=\s*\[([^\]]*)\]", mypy_config, re.MULTILINE)
    configured_plugins = (
        re.findall(r'"([^\"]+)"', configured_plugins_match.group(1)) if configured_plugins_match else []
    )
    strict_mode = re.search(r"^\s*strict\s*=\s*true\s*$", mypy_config, re.MULTILINE) is not None
    if checker_version is None or source_scope is None:
        raise TypecheckConfigurationError("pyproject.toml is missing the pytest-cuke typecheck policy.")
    if required_distributions is None:
        raise TypecheckConfigurationError("pyproject.toml has an invalid required_distributions policy.")
    if not set(required_distributions).issubset(testtypes_distributions):
        missing_testtypes = sorted(set(required_distributions).difference(testtypes_distributions))
        raise TypecheckConfigurationError(
            f"The testtypes extra is missing required pinned distributions: {missing_testtypes!r}."
        )
    if configured_scope != [source_scope]:
        raise TypecheckConfigurationError(
            f"Mypy source scope {configured_scope!r} does not match the declared scope {[source_scope]!r}."
        )
    if not strict_mode or "pydantic.mypy" not in configured_plugins:
        raise TypecheckConfigurationError("Mypy must use strict mode and the configured Pydantic plugin.")
    return checker_version, source_scope, tuple(required_distributions), config_content


def _validate_distributions(
    checker_version: str,
    required_distributions: tuple[str, ...],
    version_lookup: Callable[[str], str] = importlib.metadata.version,
) -> str:
    try:
        installed_mypy = version_lookup("mypy")
    except importlib.metadata.PackageNotFoundError as error:
        raise TypecheckConfigurationError(
            "Mypy is not installed for this Python interpreter. Install the project testtypes extra "
            "and rerun `uv run --extra testtypes python -m mypy --config-file pyproject.toml`."
        ) from error
    if installed_mypy != checker_version:
        raise TypecheckConfigurationError(
            f"Mypy {installed_mypy} is installed, but this project requires {checker_version}; "
            "install the pinned testtypes extra."
        )
    for distribution in required_distributions:
        name, version_separator, expected_version = distribution.partition("==")
        if not version_separator or not expected_version:
            raise TypecheckConfigurationError(
                f"Required typing distribution {distribution!r} must use an exact == version."
            )
        try:
            installed_version = version_lookup(name)
        except importlib.metadata.PackageNotFoundError as error:
            raise TypecheckConfigurationError(
                f"Required typing distribution {name!r} is missing. "
                "Install the project testtypes extra before running the runtime type gate."
            ) from error
        if installed_version != expected_version:
            raise TypecheckConfigurationError(
                f"Required typing distribution {name!r} must be version {expected_version}; "
                f"found {installed_version}. Install the pinned testtypes extra."
            )
    try:
        plugin_spec = importlib.util.find_spec("pydantic.mypy")
    except (ImportError, ModuleNotFoundError, ValueError):
        plugin_spec = None
    if plugin_spec is None:
        raise TypecheckConfigurationError(
            "The configured Pydantic Mypy plugin is missing; install the project testtypes extra."
        )
    return installed_mypy


def _scope_identity(project_root: Path, source_scope: str) -> tuple[int, str]:
    scope_path = project_root / source_scope
    source_files = sorted(path.relative_to(project_root).as_posix() for path in scope_path.rglob("*.py"))
    if not source_files:
        raise TypecheckConfigurationError(f"The declared runtime source scope is empty: {source_scope}")
    digest = hashlib.sha256("\n".join(source_files).encode("utf-8")).hexdigest()
    return len(source_files), digest


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    config_path = project_root / "pyproject.toml"
    try:
        checker_version, source_scope, required_distributions, config_bytes = _read_policy(config_path)
        installed_mypy = _validate_distributions(checker_version, required_distributions)
        source_count, source_digest = _scope_identity(project_root, source_scope)
    except TypecheckConfigurationError as error:
        print(f"Typecheck configuration error: {error}", file=sys.stderr)
        return 2

    config_digest = hashlib.sha256(config_bytes).hexdigest()
    print(f"MYPY_EXECUTABLE={sys.executable}", flush=True)
    print(f"MYPY_VERSION={installed_mypy}", flush=True)
    print(f"MYPY_CONFIG={config_path}", flush=True)
    print(f"MYPY_CONFIG_SHA256={config_digest}", flush=True)
    print(f"MYPY_REQUIRED_DISTRIBUTIONS={','.join(required_distributions)}", flush=True)
    print(f"MYPY_SCOPE={source_scope}", flush=True)
    print(f"MYPY_SCOPE_PY_FILES={source_count}", flush=True)
    print(f"MYPY_SCOPE_SHA256={source_digest}", flush=True)
    command = [sys.executable, "-m", "mypy", "--config-file", str(config_path)]
    environment = os.environ.copy()
    # The executable and all arguments are fixed by project policy.
    return subprocess.run(command, cwd=project_root, env=environment, check=False).returncode  # noqa: S603


if __name__ == "__main__":
    raise SystemExit(main())
