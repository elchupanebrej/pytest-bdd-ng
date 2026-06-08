"""Unit tests for FeatureBatchParser and _parse_feature_file."""

from __future__ import annotations

from pathlib import Path

import pytest
from cucumber_messages import GherkinDocument
from gherkin.errors import CompositeParserException

from pytest_bdd.collector_batch import FeatureBatchParser, _parse_feature_file

SAMPLE_FEATURE = b"""Feature: Test feature
  Scenario: Test scenario
    Given a step
    When another step
    Then a result
"""

MALFORMED_FEATURE = b"""Not a gherkin file at all"""

FEATURE_TEXT = b"""Feature: Test feature
  Scenario: Test scenario
    Given a step
"""


# ── FeatureBatchParser state machine tests ──────────────────────────────

pytestmark = [pytest.mark.unit]


def test_register_appends_and_returns_count() -> None:
    parser = FeatureBatchParser()
    count = parser.register(Path("/fake/file1.feature"))
    assert count == 1
    count = parser.register(Path("/fake/file2.feature"))
    assert count == 2
    assert len(parser._pending) == 2


def test_register_after_flush_parses_dynamically(tmp_path: Path) -> None:
    parser = FeatureBatchParser()
    parser.register(Path("/fake/file.feature"))
    parser.flush()

    f = tmp_path / "late.feature"
    f.write_bytes(FEATURE_TEXT)
    count = parser.register(f)
    assert count == 0
    doc = parser.get(f)
    assert doc is not None
    assert doc.feature is not None
    assert doc.feature.name == "Test feature"


def test_has_pending_before_flush() -> None:
    parser = FeatureBatchParser()
    assert not parser.has_pending()
    parser.register(Path("/fake/file.feature"))
    assert parser.has_pending()


def test_has_pending_after_flush() -> None:
    parser = FeatureBatchParser()
    parser.register(Path("/fake/file.feature"))
    parser.flush()
    assert not parser.has_pending()


def test_get_before_flush_raises() -> None:
    parser = FeatureBatchParser()
    parser.register(Path("/fake/file.feature"))
    with pytest.raises(RuntimeError, match="flushed"):
        parser.get(Path("/fake/file.feature"))


def test_get_after_flush_with_no_cache_returns_none() -> None:
    parser = FeatureBatchParser()
    parser.register(Path("/fake/file.feature"))
    parser.flush()
    result = parser.get(Path("/fake/file.feature"))
    assert result is None


def test_get_returns_cached_doc() -> None:
    parser = FeatureBatchParser()
    path = Path("/fake/file.feature")
    doc = GherkinDocument(comments=[], uri=None, feature=None)
    parser.register(path)
    parser._cache[path] = doc  # type: ignore[assignment] — type narrowing workaround for mypy
    parser.flush()
    result = parser.get(path)
    assert result is doc


def test_empty_pending_flush_returns_zero() -> None:
    parser = FeatureBatchParser()
    count = parser.flush()
    assert count == 0


def test_flush_is_idempotent() -> None:
    parser = FeatureBatchParser()
    parser.register(Path("/fake/file.feature"))
    parser.flush()
    count = parser.flush()
    assert count == 0


def test_flush_sets_flushed_flag() -> None:
    parser = FeatureBatchParser()
    parser.register(Path("/fake/file.feature"))
    assert not parser._flushed
    parser.flush()
    assert parser._flushed


def test_single_file_flush_returns_one() -> None:
    parser = FeatureBatchParser()
    path = Path("/fake/file.feature")
    doc = GherkinDocument(comments=[], uri=None, feature=None)
    parser.register(path)
    parser._cache[path] = doc  # type: ignore[assignment] — type narrowing workaround for mypy
    parser.flush()
    result = parser.get(path)
    assert result is doc


def test_multiple_files_all_cached() -> None:
    parser = FeatureBatchParser()
    paths = [Path(f"/fake/file{i}.feature") for i in range(3)]
    docs = {p: GherkinDocument(comments=[], uri=str(p), feature=None) for i, p in enumerate(paths)}
    for p in paths:
        parser.register(p)
    for p, d in docs.items():
        parser._cache[p] = d  # type: ignore[assignment] — type narrowing workaround for mypy
    parser.flush()
    for p in paths:
        assert parser.get(p) is docs[p]


# ── Flush pipeline integration tests ────────────────────────────────────


def test_flush_with_real_files(tmp_path: Path) -> None:
    """Register real feature files, flush, and verify cached parsed docs."""
    files = []
    for i in range(3):
        f = tmp_path / f"test_{i}.feature"
        f.write_bytes(FEATURE_TEXT)
        files.append(f)

    parser = FeatureBatchParser()
    for f in files:
        parser.register(f)

    count = parser.flush()
    assert count == 3

    for f in files:
        doc = parser.get(f)
        assert doc is not None
        assert doc.feature is not None
        assert len(doc.feature.children) == 1


# ── Parse worker function tests ─────────────────────────────────────────


def test_valid_gherkin_returns_document() -> None:
    path = Path("/fake/valid.feature")
    result_path, document = _parse_feature_file(path, SAMPLE_FEATURE)
    assert result_path == path
    assert document is not None
    assert document.feature is not None
    assert len(document.feature.children) == 1
    assert document.feature.children[0].scenario.name == "Test scenario"


def test_malformed_gherkin_raises() -> None:
    path = Path("/fake/broken.feature")
    with pytest.raises(CompositeParserException):
        _parse_feature_file(path, MALFORMED_FEATURE)
