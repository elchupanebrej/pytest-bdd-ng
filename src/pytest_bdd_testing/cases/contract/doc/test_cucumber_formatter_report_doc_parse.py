"""Provide test cucumber formatter report doc parse helpers."""

from pathlib import Path

from pytest_bdd.script.validate_feature_headings import parse_gherkin_document


def test_cucumber_formatter_report_doc_is_parseable() -> None:
    """Verify cucumber formatter report doc is parseable."""
    feature_path = (
        Path(__file__).resolve().parents[5] / "features" / "07 Report" / "09 Cucumber formatter reports.feature.md"
    )

    parsed_document = parse_gherkin_document(feature_path)

    assert parsed_document["feature"]["name"] == "Cucumber formatter reports"
    assert parsed_document["feature"]["children"]


def test_cucumber_formatter_report_doc_mentions_live_stream_and_controller_ownership() -> None:
    """Verify cucumber formatter report doc mentions live stream and controller ownership."""
    feature_path = (
        Path(__file__).resolve().parents[5] / "features" / "07 Report" / "09 Cucumber formatter reports.feature.md"
    )

    contents = feature_path.read_text(encoding="utf-8")

    assert "live incremental message stream" in contents
    assert "workers forward messages to the controller/main process" in contents
    assert "authority renders formatter output" in contents


def test_cucumber_formatter_report_doc_does_not_require_manual_capture_flags() -> None:
    """Verify cucumber formatter report doc does not require manual capture flags."""
    feature_path = (
        Path(__file__).resolve().parents[5] / "features" / "07 Report" / "09 Cucumber formatter reports.feature.md"
    )

    contents = feature_path.read_text(encoding="utf-8")

    assert "--capture=no" not in contents
    assert " -s" not in contents
