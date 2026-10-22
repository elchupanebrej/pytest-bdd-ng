"""Discover feature documents and apply heading validation to configured parser models."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any, cast

from attrs import frozen
from gherkin.dialect import Dialect

from pytest_cuke.heading_validation import (
    BaselineAuditSummary,
    HeadingType,
    HeadingValidationPolicy,
    HeadingValidationRun,
    HeadingValidationViolation,
    ParsedHeadingRecord,
    default_heading_validation_policy,
    validate_heading_records,
)
from pytest_cuke.parser import ParserRegistration, ParserRegistry, default_parser_registry

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import Protocol

    from pytest_cuke.model import Feature

    class _GherkinDialect(Protocol):
        scenario_keywords: list[str]
        scenario_outline_keywords: list[str]


DEFAULT_INCLUDE_PATTERNS = (
    "**/*.feature",
    "**/*.gherkin",
    "**/*.feature.md",
    "**/*.gherkin.md",
)


@frozen
class HeadingValidationScanError(Exception):
    """A root, discovery, read, or syntax error that prevents a compliant scan result."""

    kind: str
    path: str
    detail: str

    def __str__(self) -> str:
        return f"{self.kind.replace('_', ' ')}: {self.detail}"

    def to_payload(self) -> dict[str, object]:
        return {"kind": self.kind, "path": self.path, "message": str(self)}


class HeadingValidationCollectionError(ValueError):
    """A strict collection rejection with the parsed source location and stable violation code."""

    def __init__(self, violation: HeadingValidationViolation) -> None:
        self.violation = violation
        super().__init__(
            f"{violation.path}:{violation.line}: {violation.message} ({violation.code})",
        )


def heading_type_for_keyword(keyword: str | None, language: str = "en") -> HeadingType | None:
    """Map parser-provided scenario keywords through Gherkin's active dialect metadata."""
    if keyword is None:
        return None
    normalized_keyword = keyword.strip().casefold()
    dialect_for_name = cast("Callable[[str], _GherkinDialect | None]", Dialect.for_name)
    dialect = dialect_for_name(language)
    if dialect is None:
        return None
    scenario_outline_keywords = {candidate.strip().casefold() for candidate in dialect.scenario_outline_keywords}
    if normalized_keyword in scenario_outline_keywords:
        return HeadingType.SCENARIO_OUTLINE
    scenario_keywords = {candidate.strip().casefold() for candidate in dialect.scenario_keywords}
    if normalized_keyword in scenario_keywords:
        return HeadingType.SCENARIO
    return None


def extract_parsed_heading_records(feature: Feature, document_path: str) -> tuple[ParsedHeadingRecord, ...]:
    """Read only semantic Feature and Scenario nodes from the executed parser's immutable model."""
    records = [
        ParsedHeadingRecord(
            document_path=document_path,
            heading_type=HeadingType.FEATURE,
            name_raw=feature.name,
            line=feature.line or 1,
        ),
    ]
    for scenario in feature.all_scenarios:
        heading_type = heading_type_for_keyword(scenario.keyword, feature.language)
        if heading_type is not None:
            records.append(
                ParsedHeadingRecord(
                    document_path=document_path,
                    heading_type=heading_type,
                    name_raw=scenario.name,
                    line=scenario.line or 1,
                ),
            )
    return tuple(records)


def validate_feature_headings(
    feature: Feature,
    document_path: str,
    policy: HeadingValidationPolicy | None = None,
) -> tuple[HeadingValidationViolation, ...]:
    """Validate a feature already parsed for collection without reparsing or inspecting source text."""
    records = extract_parsed_heading_records(feature, document_path)
    return tuple(validate_heading_records(records, policy))


def enforce_feature_heading_policy(
    feature: Feature,
    document_path: str,
    policy: HeadingValidationPolicy | None = None,
) -> None:
    """Reject the first parsed title violation during opt-in strict collection."""
    violations = validate_feature_headings(feature, document_path, policy)
    if violations:
        raise HeadingValidationCollectionError(violations[0])


def discover_feature_documents(
    root_path: Path | str,
    include_patterns: Iterable[str] | None = None,
) -> list[Path]:
    """Recursively find supported documents, deduplicated and sorted by normalized path."""
    resolved_root = _resolve_root(root_path)
    return _discover_resolved_root(resolved_root, include_patterns)


def _discover_resolved_root(
    resolved_root: Path,
    include_patterns: Iterable[str] | None,
) -> list[Path]:
    try:
        is_directory = resolved_root.is_dir()
    except OSError as error:
        raise HeadingValidationScanError("invalid_root", resolved_root.as_posix(), str(error)) from error
    if not is_directory:
        raise HeadingValidationScanError("invalid_root", resolved_root.as_posix(), "invalid feature root")

    patterns = tuple(include_patterns or DEFAULT_INCLUDE_PATTERNS)
    paths: dict[str, Path] = {}
    for pattern in patterns:
        try:
            matches = resolved_root.glob(pattern)
            for path in matches:
                if path.is_file() and _is_supported_feature_path(path):
                    resolved_path = path.resolve()
                    paths[resolved_path.as_posix()] = resolved_path
        except (OSError, ValueError) as error:
            raise HeadingValidationScanError("discovery_error", resolved_root.as_posix(), str(error)) from error
    return sorted(paths.values(), key=lambda path: path.as_posix())


def run_heading_validation_scan(
    root_path: Path | str,
    include_patterns: Iterable[str] | None = None,
    policy: HeadingValidationPolicy | None = None,
    parser_registry: ParserRegistry | None = None,
    config: Any = None,
) -> HeadingValidationRun:
    """Scan parsed source in deterministic document and violation order."""
    started_at = datetime.now(timezone.utc)
    root = _resolve_root(root_path)
    active_policy = default_heading_validation_policy() if policy is None else policy
    registry = parser_registry or default_parser_registry
    document_paths = _discover_resolved_root(root, include_patterns)
    violations: list[HeadingValidationViolation] = []

    for path in document_paths:
        try:
            parser = registry.get_parser_for_path(path)
            if parser is None:
                raise HeadingValidationScanError("parse_error", path.as_posix(), "no parser is registered")
            if isinstance(parser, ParserRegistration):
                parser = parser.resolve(config)
            feature = parser.parse(path)
        except HeadingValidationScanError:
            raise
        except (OSError, UnicodeError) as error:
            raise HeadingValidationScanError("io_error", path.as_posix(), str(error)) from error
        except Exception as error:
            line = getattr(error, "line", None)
            location = f":{line}" if isinstance(line, int) and line > 0 else ""
            relative_path = _relative_document_path(path, root)
            raise HeadingValidationScanError(
                "parse_error",
                relative_path,
                f"parse error in {relative_path}{location}: {error}",
            ) from error

        relative_path = _relative_document_path(path, root)
        violations.extend(validate_feature_headings(feature, relative_path, active_policy))

    ordered_violations = tuple(
        sorted(violations, key=lambda violation: (violation.path, violation.line, violation.heading_type.value))
    )
    finished_at = datetime.now(timezone.utc)
    run_id = f"heading-scan-{started_at.strftime('%Y%m%d%H%M%S%f')}"
    return HeadingValidationRun(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        documents_scanned=len(document_paths),
        violations=ordered_violations,
    )


def build_baseline_audit(
    root_path: Path | str,
    include_patterns: Iterable[str] | None = None,
    policy: HeadingValidationPolicy | None = None,
    parser_registry: ParserRegistry | None = None,
    config: Any = None,
) -> BaselineAuditSummary:
    """Build the historical compact baseline record from one full parsed scan."""
    active_policy = default_heading_validation_policy() if policy is None else policy
    validation_run = run_heading_validation_scan(
        root_path,
        include_patterns=include_patterns,
        policy=active_policy,
        parser_registry=parser_registry,
        config=config,
    )
    return BaselineAuditSummary(
        record_id=f"baseline-audit-{validation_run.run_id}",
        policy_id=active_policy.policy_id,
        run_id=validation_run.run_id,
        violations_count=len(validation_run.violations),
        compliant=validation_run.status == "pass",
    )


def _relative_document_path(path: PurePath, root: PurePath) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_root(root_path: Path | str) -> Path:
    root = Path(root_path)
    try:
        return root.resolve()
    except OSError as error:
        raise HeadingValidationScanError("invalid_root", root.as_posix(), str(error)) from error


def _is_supported_feature_path(path: Path) -> bool:
    name = path.name.casefold()
    return name.endswith((".feature", ".gherkin", ".feature.md", ".gherkin.md"))


__all__ = [
    "DEFAULT_INCLUDE_PATTERNS",
    "HeadingValidationCollectionError",
    "HeadingValidationScanError",
    "build_baseline_audit",
    "discover_feature_documents",
    "enforce_feature_heading_policy",
    "extract_parsed_heading_records",
    "heading_type_for_keyword",
    "run_heading_validation_scan",
    "validate_feature_headings",
]
