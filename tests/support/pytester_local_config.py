"""Give pytester children a local default feature root without hiding overrides."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

import pytest


_CONFIG_FILES = (
    ("pytest.ini", "pytest"),
    (".pytest.ini", "pytest"),
    ("pyproject.toml", "tool.pytest.ini_options"),
    ("tox.ini", "pytest"),
    ("setup.cfg", "tool:pytest"),
)
_TOML_CONFIG_FILES = (("pytest.toml", "pytest"), (".pytest.toml", "pytest"), *_CONFIG_FILES)
_SECTION_HEADER = re.compile(r"^\s*\[([^]]+)\]")
_FEATURE_ROOT_SETTING = re.compile(r"^\s*cuke_features_dir\s*(?:=|:)", re.IGNORECASE)
_PYTESTER_FIXTURES = frozenset({"pytester", "testdir"})
_WRAPPED_ATTRIBUTE = "_pytest_cuke_local_feature_root_wrapped"
_RUNNING_ATTRIBUTE = "_pytest_cuke_local_feature_root_running"


def _config_section(config_path: Path) -> str:
    if config_path.name == "pyproject.toml":
        if pytest.version_tuple >= (9, 0) and any(
            match.group(1).strip().lower() == "tool.pytest"
            for line in config_path.read_text(encoding="utf-8").splitlines()
            if (match := _SECTION_HEADER.match(line))
        ):
            return "tool.pytest"
        return "tool.pytest.ini_options"
    if config_path.suffix == ".toml":
        return "pytest"
    sections = dict(_TOML_CONFIG_FILES if pytest.version_tuple >= (9, 0) else _CONFIG_FILES)
    return sections.get(config_path.name, "pytest")


def _has_feature_root_setting(config_path: Path, section: str) -> bool:
    active_section = None
    for line in config_path.read_text(encoding="utf-8").splitlines():
        match = _SECTION_HEADER.match(line)
        if match:
            active_section = match.group(1).strip().lower()
        elif active_section == section.lower() and _FEATURE_ROOT_SETTING.match(line):
            return True
    return False


def _add_local_feature_root(config_path: Path, section: str) -> None:
    lines = config_path.read_text(encoding="utf-8").splitlines()
    setting = 'cuke_features_dir = "."' if config_path.suffix == ".toml" else "cuke_features_dir = ."
    section_start = None
    section_end = len(lines)

    for index, line in enumerate(lines):
        match = _SECTION_HEADER.match(line)
        if not match:
            continue
        if section_start is not None:
            section_end = index
            break
        if match.group(1).strip().lower() == section.lower():
            section_start = index

    if section_start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend((f"[{section}]", setting))
    else:
        lines.insert(section_end, setting)

    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _explicit_config_path(arguments: tuple[Any, ...]) -> str | None:
    for index, argument in enumerate(arguments):
        value = str(argument)
        if value in {"-c", "--config-file"} and index + 1 < len(arguments):
            return str(arguments[index + 1])
        if value.startswith("--config-file="):
            return value.partition("=")[2]
        if value.startswith("-c") and not value.startswith("-cache-") and value != "-c":
            return value[2:].lstrip("=")
    return None


def _local_config(project_path: Path) -> Path:
    config_files = _TOML_CONFIG_FILES if pytest.version_tuple >= (9, 0) else _CONFIG_FILES
    for filename, _section in config_files:
        candidate = project_path / filename
        if candidate.is_file():
            return candidate

    config_path = project_path / "pytest.ini"
    config_path.write_text("[pytest]\n", encoding="utf-8")
    return config_path


def _prepare_config(project_path: Path, arguments: tuple[Any, ...]) -> tuple[Path, tuple[Any, ...]] | None:
    explicit_config = _explicit_config_path(arguments)
    if explicit_config is None:
        config_path = _local_config(project_path)
        return config_path, ("-c", str(config_path), *arguments)

    config_path = Path(explicit_config)
    if not config_path.is_absolute():
        config_path = project_path / config_path
    config_path = config_path.resolve()
    try:
        config_path.relative_to(project_path.resolve())
    except ValueError:
        return None
    if not config_path.is_file():
        return None
    return config_path, arguments


def _run_with_local_config(
    pytester: Any,
    original_run: Callable[..., Any],
    *arguments: Any,
    **kwargs: Any,
) -> Any:
    if getattr(pytester, _RUNNING_ATTRIBUTE, False):
        return original_run(*arguments, **kwargs)

    project_path = getattr(pytester, "path", None)
    if project_path is None:
        project_path = pytester.tmpdir
    project_path = Path(str(project_path)).resolve()
    prepared = _prepare_config(project_path, arguments)
    if prepared is None:
        return original_run(*arguments, **kwargs)

    config_path, run_arguments = prepared
    section = _config_section(config_path)
    if not _has_feature_root_setting(config_path, section):
        _add_local_feature_root(config_path, section)

    setattr(pytester, _RUNNING_ATTRIBUTE, True)
    try:
        return original_run(*run_arguments, **kwargs)
    finally:
        setattr(pytester, _RUNNING_ATTRIBUTE, False)


def _wrap_pytester(pytester: Any) -> None:
    if getattr(pytester, _WRAPPED_ATTRIBUTE, False):
        return

    for name in ("runpytest", "runpytest_inprocess", "runpytest_subprocess"):
        original_run = getattr(pytester, name)

        def run_with_local_config(*arguments: Any, _original_run=original_run, **kwargs: Any) -> Any:
            return _run_with_local_config(pytester, _original_run, *arguments, **kwargs)

        setattr(pytester, name, run_with_local_config)

    setattr(pytester, _WRAPPED_ATTRIBUTE, True)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_fixture_setup(fixturedef: Any):
    outcome = yield
    if fixturedef.argname in _PYTESTER_FIXTURES and outcome.excinfo is None:
        _wrap_pytester(outcome.get_result())
