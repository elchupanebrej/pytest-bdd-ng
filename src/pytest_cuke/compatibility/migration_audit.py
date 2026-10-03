"""Semantic inventory and coverage audit for scenario migration."""

from __future__ import annotations

import ast
import unicodedata
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from attrs import frozen

from pytest_cuke.compatibility.matrix import DEFAULT_FEATURE_PATTERNS, DEFAULT_TEST_PATTERNS, CompatibilityConfig
from pytest_cuke.compatibility.runtime_compat import MigrationCoverageSummary
from pytest_cuke.parser import ParserRegistration, default_parser_registry

if TYPE_CHECKING:
    from collections.abc import Iterable


class MigrationAuditError(ValueError):
    """The configured migration inventory cannot be scanned reliably."""


@frozen
class MigrationAuditResult:
    """Coverage summary plus its normalized identities and duplicate registrations."""

    summary: MigrationCoverageSummary
    feature_scenario_ids: tuple[str, ...]
    user_facing_test_scenario_ids: tuple[str, ...]
    duplicate_scenario_ids: tuple[str, ...]
    identity_kind: str = "feature-path-and-scenario-title"

    def to_payload(self) -> dict[str, object]:
        """Return the stable JSON contract used by the installed CLI."""
        return {
            "totalUserFacingScenarios": self.summary.total_user_facing_scenarios,
            "userFacingInFeatures": self.summary.user_facing_in_features,
            "coveragePercent": self.summary.coverage_percent,
            "thresholdPercent": self.summary.threshold_percent,
            "thresholdMet": self.summary.threshold_met,
            "duplicatesInTests": self.summary.duplicates_in_tests,
            "featureScenarioIds": list(self.feature_scenario_ids),
            "userFacingTestScenarioIds": list(self.user_facing_test_scenario_ids),
            "duplicateScenarioIds": list(self.duplicate_scenario_ids),
            "identityKind": self.identity_kind,
        }


def build_migration_audit(
    config: CompatibilityConfig,
    *,
    features_root: Path | str | None = None,
    tests_root: Path | str | None = None,
    feature_patterns: Iterable[str] | None = None,
    test_patterns: Iterable[str] | None = None,
    threshold_percent: int | None = None,
) -> MigrationAuditResult:
    """Compare parsed feature scenarios with literal Python scenario registrations.

    The denominator is the union of unique feature identities and unique test
    registration identities. A matching wrapper does not add another scenario;
    a feature discovered by autoload counts without a mirror wrapper. Repeated
    Python registrations are tracked separately as duplicates.
    """
    selected_threshold = config.threshold_percent if threshold_percent is None else threshold_percent
    if (
        isinstance(selected_threshold, bool)
        or not isinstance(selected_threshold, int)
        or not 0 <= selected_threshold <= 100
    ):
        raise MigrationAuditError("threshold must be an integer from 0 to 100")

    configured_features_root = Path(config.features_directory).expanduser()
    if not configured_features_root.is_absolute():
        configured_features_root = config.project_root / configured_features_root
    feature_root = _resolve_inventory_root(features_root, configured_features_root, "features")
    tests_dir = _resolve_inventory_root(tests_root, config.project_root / "tests", "tests")
    active_feature_patterns = tuple(feature_patterns or config.feature_patterns or DEFAULT_FEATURE_PATTERNS)
    active_test_patterns = tuple(test_patterns or config.test_patterns or DEFAULT_TEST_PATTERNS)
    feature_ids = _discover_feature_ids(feature_root, config.project_root, active_feature_patterns)
    test_occurrences = _discover_test_registration_ids(
        tests_dir,
        feature_root,
        config.project_root,
        active_test_patterns,
    )
    test_counts = Counter(test_occurrences)
    test_ids = set(test_counts)
    duplicates = {scenario_id for scenario_id, count in test_counts.items() if count > 1}
    duplicate_count = sum(count - 1 for count in test_counts.values() if count > 1)

    total_ids = feature_ids | test_ids
    total = len(total_ids)
    coverage = 100.0 if total == 0 else len(feature_ids) / total * 100.0
    summary = MigrationCoverageSummary(
        total_user_facing_scenarios=total,
        user_facing_in_features=len(feature_ids),
        coverage_percent=round(coverage, 2),
        threshold_percent=selected_threshold,
        threshold_met=coverage >= selected_threshold and duplicate_count == 0,
        duplicates_in_tests=duplicate_count,
    )
    return MigrationAuditResult(
        summary=summary,
        feature_scenario_ids=tuple(sorted(feature_ids)),
        user_facing_test_scenario_ids=tuple(sorted(test_ids)),
        duplicate_scenario_ids=tuple(sorted(duplicates)),
    )


def _resolve_inventory_root(value: Path | str | None, default: Path, label: str) -> Path:
    root = Path(default if value is None else value).expanduser()
    if not root.is_absolute():
        root = default.parent / root
    if value is None and not root.exists():
        return root.resolve()
    try:
        resolved = root.resolve(strict=True)
    except OSError as error:
        raise MigrationAuditError(f"invalid {label} root {root}: {error}") from error
    if not resolved.is_dir():
        raise MigrationAuditError(f"invalid {label} root {resolved}: expected a directory")
    return resolved


def _discover_feature_ids(root: Path, project_root: Path, patterns: Iterable[str]) -> set[str]:
    ids: set[str] = set()
    for path in _discover_paths(root, patterns, "features", project_root):
        parser = default_parser_registry.get_parser_for_path(path)
        if parser is None:
            raise MigrationAuditError(
                f"no pytest-cuke parser is registered for feature inventory file {path}; "
                "use a supported feature suffix or register its parser"
            )
        if isinstance(parser, ParserRegistration):
            parser = parser.resolve()
        try:
            feature = parser.parse(path, uri=path.as_posix())
        except Exception as error:
            raise MigrationAuditError(f"cannot parse feature inventory file {path}: {error}") from error
        feature_path = _identity_path(path, root, project_root)
        for scenario in feature.all_scenarios:
            scenario_name = _normalize_scenario_name(getattr(scenario, "name", ""))
            if not scenario_name:
                continue
            ids.add(f"{feature_path}::{scenario_name}")
    return ids


def _discover_test_registration_ids(
    root: Path,
    features_root: Path,
    project_root: Path,
    patterns: Iterable[str],
) -> list[str]:
    ids: list[str] = []
    for path in _discover_paths(root, patterns, "tests", project_root):
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise MigrationAuditError(f"cannot read test inventory file {path}: {error}") from error
        try:
            tree = ast.parse(source, filename=path.as_posix())
        except SyntaxError as error:
            raise MigrationAuditError(
                f"cannot parse Python test inventory file {path}:{error.lineno}: {error.msg}"
            ) from error
        registration_names, module_aliases = _registration_imports(tree)
        collector = _TopLevelRegistrationCollector(registration_names, module_aliases)
        collector.visit(tree)
        for node in collector.calls:
            ids.extend(
                _identities_for_registration(
                    node,
                    features_root=features_root,
                    project_root=project_root,
                )
            )
    return ids


class _TopLevelRegistrationCollector(ast.NodeVisitor):
    """Collect active module/class registrations while skipping nested examples."""

    def __init__(self, names: set[str], module_aliases: set[str]) -> None:
        self.names = names
        self.module_aliases = module_aliases
        self.calls: list[ast.Call] = []

    def visit_Call(self, node: ast.Call) -> None:
        if _is_registration_call(node.func, self.names, self.module_aliases):
            self.calls.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for statement in node.body:
            self.visit(statement)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        del node


def _discover_paths(root: Path, patterns: Iterable[str], label: str, project_root: Path) -> list[Path]:
    paths: dict[str, Path] = {}
    for pattern in patterns:
        if Path(pattern).is_absolute():
            raise MigrationAuditError(f"{label} inventory pattern must be relative to {root}: {pattern}")
        normalized_pattern = _pattern_relative_to_root(pattern, label, root, project_root)
        try:
            for candidate in root.glob(normalized_pattern):
                if candidate.is_file():
                    resolved = candidate.resolve()
                    paths[resolved.as_posix().casefold()] = resolved
        except (OSError, ValueError) as error:
            raise MigrationAuditError(f"invalid {label} inventory pattern {pattern!r} under {root}: {error}") from error
    return [paths[key] for key in sorted(paths)]


def _pattern_relative_to_root(pattern: str, label: str, root: Path, project_root: Path) -> str:
    """Accept active-project, conventional-root, and inventory-root patterns."""
    normalized = pattern.replace("\\", "/").removeprefix("./")
    prefixes = [f"{label}/"]
    try:
        project_relative_root = root.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        project_relative_root = ""
    if project_relative_root and project_relative_root != ".":
        prefixes.append(f"{project_relative_root.rstrip('/')}/")
    for prefix in sorted(prefixes, key=len, reverse=True):
        if normalized.casefold().startswith(prefix.casefold()):
            return normalized[len(prefix) :]
    return normalized


def _registration_imports(tree: ast.Module) -> tuple[set[str], set[str]]:
    names: set[str] = set()
    module_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if _is_registration_module(node.module):
                for alias in node.names:
                    if alias.name in {"scenario", "scenarios"}:
                        names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if _is_registration_module(alias.name):
                    module_aliases.add(alias.asname or alias.name.split(".")[0])
    return names, module_aliases


def _is_registration_module(module: str) -> bool:
    return module in {
        "pytest_cuke",
        "pytest_cuke.scenario",
        "pytest_bdd",
        "pytest_bdd.scenario",
    }


def _is_registration_call(function: ast.expr, names: set[str], module_aliases: set[str]) -> bool:
    if isinstance(function, ast.Name):
        return function.id in names
    if not isinstance(function, ast.Attribute) or function.attr not in {"scenario", "scenarios"}:
        return False
    value = function.value
    if isinstance(value, ast.Name):
        return value.id in module_aliases
    if isinstance(value, ast.Attribute):
        return (
            function.attr == "scenarios"
            and value.attr == "mark"
            and isinstance(value.value, ast.Name)
            and value.value.id == "pytest"
        )
    return False


def _identities_for_registration(
    call: ast.Call,
    *,
    features_root: Path,
    project_root: Path,
) -> list[str]:
    if isinstance(call.func, ast.Name):
        function_name = call.func.id
    elif isinstance(call.func, ast.Attribute):
        function_name = call.func.attr
    else:
        return []
    feature_values = [_literal_string(argument) for argument in call.args]
    keyword_values = {
        keyword.arg: _literal_string(keyword.value) for keyword in call.keywords if keyword.arg is not None
    }
    paths = [value for value in feature_values if value is not None and _looks_like_feature_path(value)]
    feature_name = keyword_values.get("feature_name") if function_name == "scenario" else None
    if feature_name is not None and _looks_like_feature_path(feature_name):
        paths.append(feature_name)
    if not paths:
        return []

    scenario_name = feature_values[1] if function_name == "scenario" and len(feature_values) > 1 else None
    if scenario_name is None:
        scenario_name = keyword_values.get("scenario_name")
    filter_name = keyword_values.get("filter_")
    selected_name = scenario_name or filter_name
    identities: list[str] = []
    for raw_path in paths:
        resolved = _resolve_registered_feature_path(raw_path, features_root, project_root)
        feature_path = _identity_path(resolved, features_root, project_root)
        if selected_name:
            identities.append(f"{feature_path}::{_normalize_scenario_name(selected_name)}")
            continue
        identities.extend(_feature_ids_for_registered_file(resolved, feature_path))
    return [identity for identity in identities if identity.split("::", 1)[-1]]


def _feature_ids_for_registered_file(path: Path, identity_path: str) -> list[str]:
    if not path.is_file():
        return []
    parser = default_parser_registry.get_parser_for_path(path)
    if parser is None:
        return []
    if isinstance(parser, ParserRegistration):
        parser = parser.resolve()
    try:
        feature = parser.parse(path, uri=path.as_posix())
    except Exception:
        return []
    return [
        f"{identity_path}::{_normalize_scenario_name(getattr(scenario, 'name', ''))}"
        for scenario in feature.all_scenarios
        if _normalize_scenario_name(getattr(scenario, "name", ""))
    ]


def _resolve_registered_feature_path(raw_path: str, features_root: Path, project_root: Path) -> Path:
    normalized = raw_path.strip().replace("\\", "/")
    candidate = Path(normalized).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    project_candidate = (project_root / candidate).resolve()
    if project_candidate.exists():
        return project_candidate
    feature_candidate = (features_root / candidate).resolve()
    if feature_candidate.exists():
        return feature_candidate
    return project_candidate


def _identity_path(path: Path, root: Path, project_root: Path) -> str:
    try:
        relative = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        try:
            relative = path.resolve().relative_to(root.resolve())
        except ValueError:
            relative = Path(path.name)
    return relative.as_posix().casefold().lstrip("./")


def _literal_string(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _looks_like_feature_path(value: str) -> bool:
    normalized = value.casefold().replace("\\", "/")
    return normalized.endswith(
        (".feature", ".gherkin", ".feature.md", ".gherkin.md", ".json", ".yaml", ".yml", ".hjson", ".conf")
    )


def _normalize_scenario_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())


__all__ = ["MigrationAuditError", "MigrationAuditResult", "build_migration_audit"]
