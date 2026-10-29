"""Compatibility configuration, matrix construction, and tox-target expansion."""

from __future__ import annotations

import configparser
import itertools
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from attrs import frozen

from pytest_cuke.compatibility.runtime_compat import (
    MIN_SUPPORTED_PYTEST,
    MIN_SUPPORTED_PYTHON,
    REASON_COMPATIBLE,
    REASON_EOL_PYTEST,
    REASON_EOL_PYTHON,
    REASON_PYTEST_UNAVAILABLE,
    REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST,
    REASON_PYTHON_UNAVAILABLE,
    CompatibilityMatrixEntry,
    _format_pytest_version,
    _format_python_version,
    _is_python_version_supported_by_pytest,
    _parse_pytest_factor,
    _parse_python_factor,
)
from pytest_cuke.compatibility.tomllib import TOMLDecodeError, loads

DEFAULT_FEATURE_PATTERNS = ("**/*.feature", "**/*.gherkin", "**/*.feature.md", "**/*.gherkin.md")
DEFAULT_TEST_PATTERNS = ("**/*.py",)
DEFAULT_TOX_ENV_TEMPLATE = "py{python}-pytest{pytest}-coverage-{platform}"
DEFAULT_EXECUTION_TARGETS = ("lin", "mac", "win")
FactorNormalizer = Callable[[str], str]


class CompatibilityConfigurationError(ValueError):
    """A configuration file cannot define a useful compatibility inventory."""


@frozen
class ToxTarget:
    """A concrete environment expanded from an INI tox env_list."""

    name: str
    python_factor: str
    pytest_factor: str
    execution_target: str | None


@frozen
class CompatibilityConfig:
    """Normalized matrix and migration-audit settings for one project."""

    config_path: Path
    project_root: Path
    features_directory: str
    python_factors: tuple[str, ...]
    pytest_factors: tuple[str, ...]
    execution_targets: tuple[str, ...]
    tox_env_template: str | None
    tox_targets: tuple[ToxTarget, ...]
    feature_patterns: tuple[str, ...]
    test_patterns: tuple[str, ...]
    threshold_percent: int
    compatibility_source: str


def load_compatibility_config(
    config_path: Path | str | None = None,
    *,
    require_matrix: bool = True,
) -> CompatibilityConfig:
    """Load the active pyproject configuration or an explicit TOML/legacy INI file."""
    selected_path = _resolve_config_path(config_path)
    try:
        raw_text = selected_path.read_text(encoding="utf-8")
    except OSError as error:
        raise CompatibilityConfigurationError(f"cannot read configuration {selected_path}: {error}") from error

    if selected_path.suffix.casefold() == ".toml":
        try:
            document = loads(raw_text)
        except TOMLDecodeError as error:
            raise CompatibilityConfigurationError(f"invalid TOML configuration {selected_path}: {error}") from error
        return _load_toml_config(selected_path, document, require_matrix=require_matrix)
    if selected_path.suffix.casefold() == ".ini":
        return _load_ini_config(selected_path, raw_text)
    raise CompatibilityConfigurationError(
        f"unsupported configuration format {selected_path.suffix!r}; use a TOML or INI file"
    )


def _resolve_config_path(config_path: Path | str | None) -> Path:
    if config_path is not None:
        path = Path(config_path).expanduser().resolve()
        if not path.is_file():
            raise CompatibilityConfigurationError(f"configuration file does not exist: {path}")
        return path

    for parent in (Path.cwd().resolve(), *Path.cwd().resolve().parents):
        candidate = parent / "pyproject.toml"
        if candidate.is_file():
            return candidate
    raise CompatibilityConfigurationError(
        "no active pyproject.toml found; run from a project directory or pass --config PATH"
    )


def _load_toml_config(config_path: Path, document: Any, *, require_matrix: bool) -> CompatibilityConfig:
    if not isinstance(document, dict):
        raise CompatibilityConfigurationError(f"{config_path}: expected a TOML table at the document root")
    tool = document.get("tool", {})
    package = tool.get("pytest-cuke", {}) if isinstance(tool, dict) else {}
    if not isinstance(package, dict):
        raise CompatibilityConfigurationError(f"{config_path}: [tool.pytest-cuke] must be a table")
    compatibility = package.get("compatibility")
    if compatibility is None and not require_matrix:
        compatibility = {}
    if not isinstance(compatibility, dict):
        raise CompatibilityConfigurationError(
            f"{config_path}: add [tool.pytest-cuke.compatibility] with python-factors and pytest-factors"
        )
    audit = package.get("migration-audit", {})
    if not isinstance(audit, dict):
        raise CompatibilityConfigurationError(f"{config_path}: [tool.pytest-cuke.migration-audit] must be a table")

    python_factors = (
        _normalize_list(
            compatibility.get("python-factors"),
            field_name="python-factors",
            config_path=config_path,
            normalizer=normalize_python_factor,
        )
        if "python-factors" in compatibility
        else []
    )
    pytest_factors = (
        _normalize_list(
            compatibility.get("pytest-factors"),
            field_name="pytest-factors",
            config_path=config_path,
            normalizer=normalize_pytest_factor,
        )
        if "pytest-factors" in compatibility
        else []
    )
    if require_matrix and (not python_factors or not pytest_factors):
        raise CompatibilityConfigurationError(
            f"{config_path}: [tool.pytest-cuke.compatibility] needs non-empty python-factors and pytest-factors"
        )
    execution_targets = _normalize_target_list(
        compatibility.get("execution-targets", list(DEFAULT_EXECUTION_TARGETS)), config_path
    )
    tox_env_template = compatibility.get("tox-env-template", DEFAULT_TOX_ENV_TEMPLATE)
    if tox_env_template is not None and not isinstance(tox_env_template, str):
        raise CompatibilityConfigurationError(f"{config_path}: tox-env-template must be a string")
    if tox_env_template:
        _validate_tox_template(tox_env_template, config_path)
    else:
        tox_env_template = None

    feature_patterns = _normalize_pattern_list(
        audit.get("feature-patterns", list(DEFAULT_FEATURE_PATTERNS)), "feature-patterns", config_path
    )
    test_patterns = _normalize_pattern_list(
        audit.get("test-registration-patterns", list(DEFAULT_TEST_PATTERNS)),
        "test-registration-patterns",
        config_path,
    )
    threshold_percent = _normalize_threshold(audit.get("threshold-percent", 80), config_path)
    features_directory = _toml_features_directory(document, config_path)
    compatibility_source = compatibility.get("compatibility-source", "pytest-metadata")
    if not isinstance(compatibility_source, str) or not compatibility_source.strip():
        raise CompatibilityConfigurationError(f"{config_path}: compatibility-source must be a non-empty string")

    return CompatibilityConfig(
        config_path=config_path,
        project_root=config_path.parent,
        features_directory=features_directory,
        python_factors=tuple(sorted(set(python_factors), key=_python_sort_key)),
        pytest_factors=tuple(sorted(set(pytest_factors), key=_pytest_sort_key)),
        execution_targets=execution_targets,
        tox_env_template=tox_env_template,
        tox_targets=(),
        feature_patterns=feature_patterns,
        test_patterns=test_patterns,
        threshold_percent=threshold_percent,
        compatibility_source=compatibility_source.strip(),
    )


def _load_ini_config(config_path: Path, raw_text: str) -> CompatibilityConfig:
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    try:
        parser.read_string(raw_text, source=str(config_path))
    except configparser.Error as error:
        raise CompatibilityConfigurationError(f"invalid INI configuration {config_path}: {error}") from error
    if not parser.has_section("tox"):
        raise CompatibilityConfigurationError(f"{config_path}: expected a [tox] section with env_list")
    raw_env_list = parser.get("tox", "env_list", fallback=parser.get("tox", "envlist", fallback=""))
    if not raw_env_list.strip():
        raise CompatibilityConfigurationError(f"{config_path}: [tox] env_list is empty")

    expanded_names: set[str] = set()
    for line in raw_env_list.replace(",", "\n").splitlines():
        expression = line.strip()
        if expression:
            expanded_names.update(_expand_tox_expression(expression, config_path))

    targets: dict[str, ToxTarget] = {}
    python_factors: set[str] = set()
    pytest_factors: set[str] = set()
    for name in sorted(expanded_names):
        python_match = re.search(r"(?:^|-)(?:py|pypy)(\d{2,3})(?:-|$)", name)
        pytest_match = re.search(r"(?:^|-)pytest(latest|\d{2,3})(?:-|$)", name)
        if python_match is None or pytest_match is None:
            continue
        python_factor = normalize_python_factor(python_match.group(1))
        pytest_factor = normalize_pytest_factor(pytest_match.group(1))
        target = _execution_target_for_name(name)
        python_factors.add(python_factor)
        pytest_factors.add(pytest_factor)
        targets[name] = ToxTarget(name, python_factor, pytest_factor, target)

    if not python_factors or not pytest_factors:
        raise CompatibilityConfigurationError(
            f"{config_path}: [tox] env_list must contain pyNNN and pytestNNN/latest factors"
        )

    compatibility = _ini_options(parser, "pytest-cuke-compatibility")
    audit = _ini_options(parser, "pytest-cuke-migration-audit")
    configured_targets = _comma_or_newline_list(compatibility.get("execution_targets", ""))
    execution_targets = _normalize_target_list(
        configured_targets
        or sorted({target.execution_target for target in targets.values() if target.execution_target})
        or ["lin"],
        config_path,
    )
    feature_patterns = _normalize_pattern_list(
        _comma_or_newline_list(audit.get("feature_patterns", "")) or DEFAULT_FEATURE_PATTERNS,
        "feature_patterns",
        config_path,
    )
    test_patterns = _normalize_pattern_list(
        _comma_or_newline_list(audit.get("test_registration_patterns", "")) or DEFAULT_TEST_PATTERNS,
        "test_registration_patterns",
        config_path,
    )
    raw_threshold = audit.get("threshold_percent", "80")
    try:
        ini_threshold = int(raw_threshold)
    except ValueError as error:
        raise CompatibilityConfigurationError(
            f"{config_path}: threshold_percent must be an integer from 0 to 100"
        ) from error
    threshold_percent = _normalize_threshold(ini_threshold, config_path)
    compatibility_source = compatibility.get("compatibility_source", "tox-ini-factors")
    if not compatibility_source.strip():
        raise CompatibilityConfigurationError(f"{config_path}: compatibility_source cannot be empty")
    features_directory = parser.get(
        "pytest",
        "cuke_features_dir",
        fallback=parser.get("tool:pytest", "cuke_features_dir", fallback="features"),
    ).strip()
    if not features_directory:
        raise CompatibilityConfigurationError(f"{config_path}: cuke_features_dir cannot be empty")

    return CompatibilityConfig(
        config_path=config_path,
        project_root=config_path.parent,
        features_directory=features_directory,
        python_factors=tuple(sorted(python_factors, key=_python_sort_key)),
        pytest_factors=tuple(sorted(pytest_factors, key=_pytest_sort_key)),
        execution_targets=execution_targets,
        tox_env_template=None,
        tox_targets=tuple(targets[name] for name in sorted(targets)),
        feature_patterns=feature_patterns,
        test_patterns=test_patterns,
        threshold_percent=threshold_percent,
        compatibility_source=compatibility_source.strip(),
    )


def _ini_options(parser: configparser.ConfigParser, section: str) -> dict[str, str]:
    if not parser.has_section(section):
        return {}
    return dict(parser.items(section))


def _toml_features_directory(document: dict[str, Any], config_path: Path) -> str:
    tool = document.get("tool", {})
    pytest = tool.get("pytest", {}) if isinstance(tool, dict) else {}
    if not isinstance(pytest, dict):
        raise CompatibilityConfigurationError(f"{config_path}: [tool.pytest] must be a table")
    ini_options = pytest.get("ini_options", {})
    if not isinstance(ini_options, dict):
        raise CompatibilityConfigurationError(f"{config_path}: [tool.pytest.ini_options] must be a table")
    value = ini_options.get("cuke_features_dir", "features")
    if not isinstance(value, str) or not value.strip():
        raise CompatibilityConfigurationError(f"{config_path}: cuke_features_dir must be a non-empty string")
    return value.strip()


def _normalize_list(value: Any, *, field_name: str, config_path: Path, normalizer: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise CompatibilityConfigurationError(f"{config_path}: {field_name} must be a non-empty array of versions")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise CompatibilityConfigurationError(f"{config_path}: each {field_name} item must be a string")
        try:
            normalized.append(normalizer(item))
        except ValueError as error:
            raise CompatibilityConfigurationError(
                f"{config_path}: invalid {field_name} item {item!r}: {error}"
            ) from error
    return normalized


def _normalize_target_list(value: Any, config_path: Path) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise CompatibilityConfigurationError(f"{config_path}: execution-targets must be a non-empty array")
    targets = tuple(sorted({str(item).strip().casefold() for item in value if str(item).strip()}))
    invalid = sorted(set(targets) - {"lin", "mac", "win"})
    if invalid:
        raise CompatibilityConfigurationError(
            f"{config_path}: unsupported execution target(s) {', '.join(invalid)}; use lin, mac, or win"
        )
    if not targets:
        raise CompatibilityConfigurationError(f"{config_path}: execution-targets cannot be empty")
    return targets


def _normalize_pattern_list(value: Any, field_name: str, config_path: Path) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise CompatibilityConfigurationError(f"{config_path}: {field_name} must be a non-empty array")
    if any(not isinstance(item, str) for item in value):
        raise CompatibilityConfigurationError(f"{config_path}: {field_name} entries must be strings")
    patterns = tuple(sorted({item.strip().replace("\\", "/") for item in value if item.strip()}))
    if not patterns:
        raise CompatibilityConfigurationError(f"{config_path}: {field_name} cannot be empty")
    if any(Path(pattern).is_absolute() for pattern in patterns):
        raise CompatibilityConfigurationError(f"{config_path}: {field_name} patterns must be relative to their root")
    return patterns


def _normalize_threshold(value: Any, config_path: Path) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise CompatibilityConfigurationError(f"{config_path}: threshold-percent must be an integer from 0 to 100")
    return value


def _validate_tox_template(template: str, config_path: Path) -> None:
    fields = {match.group(1) for match in re.finditer(r"\{([^{}]+)\}", template)}
    required = {"python", "pytest"}
    if not required.issubset(fields) or not ({"target", "platform"} & fields):
        missing = sorted(required - fields)
        if not ({"target", "platform"} & fields):
            missing.append("target or platform")
        raise CompatibilityConfigurationError(
            f"{config_path}: tox-env-template must include {{{', '.join(missing)}}} placeholder(s)"
        )
    try:
        template.format(python="310", pytest="70", platform="lin", target="lin")
    except (KeyError, ValueError) as error:
        raise CompatibilityConfigurationError(f"{config_path}: invalid tox-env-template: {error}") from error


def _expand_tox_expression(expression: str, config_path: Path) -> tuple[str, ...]:
    opening = expression.find("{")
    if opening < 0:
        if "}" in expression:
            raise CompatibilityConfigurationError(f"{config_path}: unmatched closing brace in tox env {expression!r}")
        return (expression,)
    closing = expression.find("}", opening + 1)
    if closing < 0 or "{" in expression[opening + 1 : closing]:
        raise CompatibilityConfigurationError(f"{config_path}: malformed factor expression {expression!r}")
    choices = [choice.strip() for choice in expression[opening + 1 : closing].split(",")]
    if not choices or any(not choice for choice in choices):
        raise CompatibilityConfigurationError(f"{config_path}: empty tox factor in {expression!r}")
    return tuple(
        expanded
        for choice in choices
        for expanded in _expand_tox_expression(expression[:opening] + choice + expression[closing + 1 :], config_path)
    )


def _execution_target_for_name(name: str) -> str | None:
    token = name.rsplit("-", 1)[-1].casefold()
    return {"lin": "lin", "linux": "lin", "mac": "mac", "macos": "mac", "win": "win", "windows": "win"}.get(token)


def _comma_or_newline_list(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,\n]", value) if part.strip()]


def normalize_python_factor(value: str) -> str:
    """Return tox's compact Python factor for a dotted or compact version."""
    normalized = value.strip().casefold()
    match = re.fullmatch(r"(?:py)?(\d{2,3})", normalized)
    if match:
        factor = match.group(1)
        if _parse_python_factor(factor) is not None:
            return factor
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.\d+)?", normalized)
    if match is None:
        raise ValueError("expected a Python version such as 3.10 or factor 310")
    major, minor = int(match.group(1)), int(match.group(2))
    if major > 9 or minor > 99:
        raise ValueError("the compatibility policy only supports one-digit Python major versions")
    factor = f"{major}{minor:02d}" if minor >= 10 else f"{major}{minor}"
    if _parse_python_factor(factor) is None:
        raise ValueError("unsupported Python factor")
    return factor


def normalize_pytest_factor(value: str) -> str:
    """Return tox's compact pytest factor, preserving patch factors and latest."""
    normalized = value.strip().casefold()
    if normalized == "latest":
        return normalized
    match = re.fullmatch(r"(?:pytest)?(\d{2,3})", normalized)
    if match:
        factor = match.group(1)
        if _parse_pytest_factor(factor) is not None:
            return factor
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?", normalized)
    if match is None:
        raise ValueError("expected a pytest version such as 8.0, 6.2.5, or latest")
    major, minor, patch = (int(match.group(1)), int(match.group(2)), int(match.group(3) or 0))
    if major > 9 or minor > 9 or patch > 9:
        raise ValueError("the compatibility policy only supports single-digit version components")
    factor = f"{major}{minor}" if patch == 0 else f"{major}{minor}{patch}"
    if _parse_pytest_factor(factor) is None:
        raise ValueError("unsupported pytest factor")
    return factor


def classify_pair(python_factor: str, pytest_factor: str) -> tuple[bool, bool, str]:
    """Return upstream compatibility, project support, and a stable reason code."""
    normalized_python = _safe_normalize(normalize_python_factor, python_factor)
    normalized_pytest = _safe_normalize(normalize_pytest_factor, pytest_factor)
    if normalized_python is None:
        return False, False, REASON_PYTHON_UNAVAILABLE
    if normalized_pytest is None:
        return False, False, REASON_PYTEST_UNAVAILABLE

    python_version = _parse_python_factor(normalized_python)
    pytest_version = _parse_pytest_factor(normalized_pytest)
    if python_version is None:
        return False, False, REASON_PYTHON_UNAVAILABLE
    if pytest_version is None:
        return False, False, REASON_PYTEST_UNAVAILABLE

    project_supported = python_version >= MIN_SUPPORTED_PYTHON and pytest_version >= MIN_SUPPORTED_PYTEST
    if pytest_version < MIN_SUPPORTED_PYTEST:
        return False, False, REASON_EOL_PYTEST

    policy_key = "latest" if normalized_pytest == "latest" else f"{pytest_version[0]}{pytest_version[1]}"
    upstream_compatible = _is_python_version_supported_by_pytest(python_version, policy_key)
    if upstream_compatible is None:
        return False, False, REASON_PYTEST_UNAVAILABLE
    if python_version < MIN_SUPPORTED_PYTHON:
        return upstream_compatible, False, REASON_EOL_PYTHON
    if not upstream_compatible:
        return False, project_supported, REASON_PYTHON_NOT_SUPPORTED_BY_PYTEST
    if not project_supported:
        return True, False, REASON_EOL_PYTHON
    return True, True, REASON_COMPATIBLE


def build_matrix(config: CompatibilityConfig) -> list[CompatibilityMatrixEntry]:
    """Build a stable, complete Python-by-pytest factor matrix from project config."""
    entries: list[CompatibilityMatrixEntry] = []
    for python_factor, pytest_factor in itertools.product(config.python_factors, config.pytest_factors):
        compatible, supported, reason = classify_pair(python_factor, pytest_factor)
        tox_names = _tox_names_for_pair(config, python_factor, pytest_factor) if compatible and supported else ()
        entries.append(
            CompatibilityMatrixEntry(
                python_version=_format_python_version(python_factor),
                pytest_version=_format_pytest_version(pytest_factor),
                is_compatible=compatible,
                is_supported=supported,
                reason_code=reason,
                execution_targets=config.execution_targets,
                compatibility_source=config.compatibility_source,
                tox_env_name=tox_names[0] if tox_names else None,
            )
        )
    return entries


def expanded_tox_env_names(config: CompatibilityConfig) -> list[str]:
    """Return configured concrete tox names for accepted pairs, in stable order."""
    accepted_pairs = {
        (entry.python_version, entry.pytest_version)
        for entry in build_matrix(config)
        if entry.is_compatible and entry.is_supported
    }
    names: set[str] = set()
    if config.tox_env_template is None:
        for tox_target in config.tox_targets:
            python_version = _format_python_version(tox_target.python_factor)
            pytest_version = _format_pytest_version(tox_target.pytest_factor)
            if (python_version, pytest_version) in accepted_pairs:
                names.add(tox_target.name)
        return sorted(names)

    for python_factor, pytest_factor in itertools.product(config.python_factors, config.pytest_factors):
        if (_format_python_version(python_factor), _format_pytest_version(pytest_factor)) not in accepted_pairs:
            continue
        for target_name in config.execution_targets:
            names.add(
                config.tox_env_template.format(
                    python=python_factor,
                    pytest=pytest_factor,
                    platform=target_name,
                    target=target_name,
                )
            )
    return sorted(names)


def entry_payload(entry: CompatibilityMatrixEntry) -> dict[str, object]:
    """Serialize one matrix entry with stable public JSON field names."""
    return {
        "pythonVersion": entry.python_version,
        "pytestVersion": entry.pytest_version,
        "isCompatible": entry.is_compatible,
        "isSupported": entry.is_supported,
        "reasonCode": entry.reason_code,
        "executionTargets": list(entry.execution_targets),
        "compatibilitySource": entry.compatibility_source,
        "toxEnvName": entry.tox_env_name,
    }


def pair_entry(config: CompatibilityConfig, python_version: str, pytest_version: str) -> CompatibilityMatrixEntry:
    """Classify a command-line pair, including factors absent from the configured grid."""
    python_factor = _safe_normalize(normalize_python_factor, python_version)
    pytest_factor = _safe_normalize(normalize_pytest_factor, pytest_version)
    compatible, supported, reason = classify_pair(python_version, pytest_version)
    tox_names = (
        _tox_names_for_pair(config, python_factor, pytest_factor)
        if compatible and supported and python_factor is not None and pytest_factor is not None
        else ()
    )
    return CompatibilityMatrixEntry(
        python_version=_format_python_version(python_factor) if python_factor else python_version,
        pytest_version=_format_pytest_version(pytest_factor) if pytest_factor else pytest_version,
        is_compatible=compatible,
        is_supported=supported,
        reason_code=reason,
        execution_targets=config.execution_targets,
        compatibility_source=config.compatibility_source,
        tox_env_name=tox_names[0] if tox_names else None,
    )


def _tox_names_for_pair(config: CompatibilityConfig, python_factor: str, pytest_factor: str) -> tuple[str, ...]:
    if config.tox_env_template is None:
        return tuple(
            target.name
            for target in config.tox_targets
            if target.python_factor == python_factor and target.pytest_factor == pytest_factor
        )
    template = config.tox_env_template
    return tuple(
        template.format(
            python=python_factor,
            pytest=pytest_factor,
            platform=target_name,
            target=target_name,
        )
        for target_name in config.execution_targets
    )


def _safe_normalize(normalizer: FactorNormalizer, value: str) -> str | None:
    try:
        return normalizer(value)
    except ValueError:
        return None


def _python_sort_key(factor: str) -> tuple[int, int]:
    return _parse_python_factor(factor) or (0, 0)


def _pytest_sort_key(factor: str) -> tuple[int, int, int]:
    return _parse_pytest_factor(factor) or (0, 0, 0)


__all__ = [
    "DEFAULT_EXECUTION_TARGETS",
    "DEFAULT_FEATURE_PATTERNS",
    "DEFAULT_TEST_PATTERNS",
    "DEFAULT_TOX_ENV_TEMPLATE",
    "CompatibilityConfig",
    "CompatibilityConfigurationError",
    "ToxTarget",
    "build_matrix",
    "classify_pair",
    "entry_payload",
    "expanded_tox_env_names",
    "load_compatibility_config",
    "normalize_pytest_factor",
    "normalize_python_factor",
    "pair_entry",
]
