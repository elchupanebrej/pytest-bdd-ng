from pathlib import Path, PureWindowsPath
from types import SimpleNamespace

from gherkin.ast_builder import AstBuilder
from gherkin.parser import Parser
from messages import GherkinDocument
import pytest

from pytest_cuke.heading_scanner import (
    HeadingValidationScanError,
    _relative_document_path,
    build_baseline_audit,
    discover_feature_documents,
    heading_type_for_keyword,
    run_heading_validation_scan,
)
from pytest_cuke.heading_validation import (
    EMPTY_HEADING_TITLE_CODE,
    HeadingType,
    ParsedHeadingRecord,
    default_heading_validation_policy,
    heading_validation_policy_payload,
    validate_heading_records,
)
from pytest_cuke.compatibility.parser import ParsedFeature
from pytest_cuke.parser import ParserRegistration, ParserRegistry
from pytest_cuke.utils import IdGenerator


def test_default_policy_payload_keeps_the_public_field_names() -> None:
    assert heading_validation_policy_payload() == {
        "policy_id": "feature-heading-policy-v1",
        "enforced_heading_types": ["feature", "scenario", "scenario_outline"],
        "trim_whitespace": True,
        "empty_name_is_violation": True,
        "snippet_text_excluded": True,
    }


def test_policy_reports_only_empty_enforced_semantic_titles() -> None:
    records = [
        ParsedHeadingRecord("example.feature", HeadingType.FEATURE, "  ", 1),
        ParsedHeadingRecord("example.feature", HeadingType.SCENARIO, None, 4),
    ]

    violations = validate_heading_records(records)

    assert [(violation.path, violation.line, violation.code) for violation in violations] == [
        ("example.feature", 1, EMPTY_HEADING_TITLE_CODE),
        ("example.feature", 4, EMPTY_HEADING_TITLE_CODE),
    ]
    assert all(violation.raw_name in ("  ", None) for violation in violations)


@pytest.mark.parametrize(
    ("keyword", "language", "expected"),
    [
        ("Example", "en", HeadingType.SCENARIO),
        ("Scenario", "en", HeadingType.SCENARIO),
        ("Scenario Template", "en", HeadingType.SCENARIO_OUTLINE),
        ("Exemple", "fr", HeadingType.SCENARIO),
        ("Plan du scénario", "fr", HeadingType.SCENARIO_OUTLINE),
    ],
)
def test_heading_type_uses_gherkin_dialect_keywords(keyword: str, language: str, expected: HeadingType) -> None:
    assert heading_type_for_keyword(keyword, language) is expected


def test_recursive_discovery_deduplicates_patterns_and_sorts_paths(tmp_path: Path) -> None:
    root = tmp_path / "features"
    (root / "nested").mkdir(parents=True)
    (root / "z.feature").write_text("Feature: Z\n", encoding="utf-8")
    (root / "nested" / "a.gherkin.md").write_text("# Feature: A\n", encoding="utf-8")

    documents = discover_feature_documents(
        root,
        ("**/*.feature", "**/*.gherkin.md", "**/*.feature", "**/*"),
    )

    assert [path.relative_to(root).as_posix() for path in documents] == [
        "nested/a.gherkin.md",
        "z.feature",
    ]


def test_windows_relative_paths_are_serialized_with_posix_separators() -> None:
    root = PureWindowsPath(r"C:\workspace\features")
    document = root / "nested" / "valid.feature"

    assert _relative_document_path(document, root) == "nested/valid.feature"


def test_scan_and_baseline_payloads_share_policy_and_run_identity(tmp_path: Path) -> None:
    root = tmp_path / "features"
    root.mkdir()
    (root / "blank.feature").write_text("Feature:   \n  Scenario: \n", encoding="utf-8")

    run = run_heading_validation_scan(root)
    baseline = build_baseline_audit(root)

    assert run.documents_scanned == 1
    assert run.status == "fail"
    assert [(item.line, item.heading_type) for item in run.violations] == [
        (1, HeadingType.FEATURE),
        (2, HeadingType.SCENARIO),
    ]
    assert baseline.policy_id == default_heading_validation_policy().policy_id
    assert baseline.record_id == f"baseline-audit-{baseline.run_id}"
    assert baseline.violations_count == 2
    assert baseline.compliant is False


@pytest.mark.parametrize(
    ("root_path", "kind"),
    [
        ("missing", "invalid_root"),
    ],
)
def test_scan_reports_invalid_root_as_a_structured_failure(tmp_path: Path, root_path: str, kind: str) -> None:
    with pytest.raises(HeadingValidationScanError) as raised:
        run_heading_validation_scan(tmp_path / root_path)

    assert raised.value.kind == kind


def test_scan_distinguishes_parse_and_io_failures(tmp_path: Path) -> None:
    root = tmp_path / "features"
    root.mkdir()
    (root / "broken.feature").write_text(
        "Feature: Broken\n  Scenario: Invalid\n    Given a step\n    Invalid syntax without keyword\n",
        encoding="utf-8",
    )

    with pytest.raises(HeadingValidationScanError, match="parse error") as parse_error:
        run_heading_validation_scan(root)

    assert parse_error.value.kind == "parse_error"

    (root / "broken.feature").unlink()
    (root / "invalid.feature").write_bytes(b"Feature: Invalid\n\xff")
    with pytest.raises(HeadingValidationScanError) as io_error:
        run_heading_validation_scan(root)

    assert io_error.value.kind == "io_error"


def test_heading_scan_passes_pytest_config_to_legacy_parser(tmp_path: Path) -> None:
    root = tmp_path / "features"
    root.mkdir()
    source = "Feature:   \n  Scenario: \n"
    feature_path = root / "invalid.feature"
    feature_path.write_text(source, encoding="utf-8")
    config = SimpleNamespace(pytest_cuke_id_generator=IdGenerator())
    calls: list[tuple[object, Path, str]] = []

    class ConfigAwareLegacyParser:
        id_generator: IdGenerator | None = None

        def parse(self, parser_config: object, path: Path, uri: str, **kwargs: object) -> ParsedFeature:
            calls.append((parser_config, path, uri))
            document = Parser(AstBuilder(id_generator=self.id_generator)).parse(path.read_text(encoding="utf-8"))
            document["uri"] = uri
            return ParsedFeature(
                gherkin_document=GherkinDocument.model_validate(document),
                filename=path.as_posix(),
                raw_data=path.read_text(encoding="utf-8"),
            )

    registry = ParserRegistry()
    registry.register(".feature", ParserRegistration.legacy(ConfigAwareLegacyParser))

    run = run_heading_validation_scan(root, parser_registry=registry, config=config)

    assert run.documents_scanned == 1
    assert run.status == "fail"
    assert calls == [(config, feature_path, feature_path.as_posix())]


def test_heading_scan_reports_missing_config_for_legacy_parser(tmp_path: Path) -> None:
    root = tmp_path / "features"
    root.mkdir()
    (root / "feature.feature").write_text("Feature: Name\n", encoding="utf-8")

    class ConfigAwareLegacyParser:
        id_generator: IdGenerator | None = None

        def parse(self, parser_config: object, path: Path, uri: str, **kwargs: object) -> ParsedFeature:
            raise AssertionError("legacy parser must not be called without pytest Config")

    registry = ParserRegistry()
    registry.register(".feature", ParserRegistration.legacy(ConfigAwareLegacyParser))

    with pytest.raises(HeadingValidationScanError, match="pytest Config is required") as error:
        run_heading_validation_scan(root, parser_registry=registry)

    assert error.value.kind == "parse_error"
