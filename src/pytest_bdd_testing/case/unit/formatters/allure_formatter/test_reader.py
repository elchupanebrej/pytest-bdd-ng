"""Unit tests for the NDJSON reader module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.plugin.allure_formatter.converter.reader import read_envelopes

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.unit]


class TestReader:
    """Tests for read_envelopes function."""

    def test_parses_single_envelope(self, tmp_path: Path) -> None:
        """Single valid JSON line yields one projection."""
        ndjson = tmp_path / "messages.ndjson"
        ndjson.write_text(
            json.dumps({"testRunStarted": {"id": "r1", "timestamp": {"seconds": 0, "nanos": 0}}}) + "\n",
            encoding="utf-8",
        )
        projections = list(read_envelopes(ndjson))
        assert len(projections) == 1

    def test_parses_multiple_envelopes(self, tmp_path: Path) -> None:
        """Multiple valid JSON lines yield multiple projections."""
        ndjson = tmp_path / "messages.ndjson"
        lines = [
            json.dumps({"testRunStarted": {"id": "r1", "timestamp": {"seconds": 0, "nanos": 0}}}),
            json.dumps(
                {
                    "testCaseStarted": {
                        "id": "c1",
                        "testCaseId": "tc1",
                        "attempt": 0,
                        "timestamp": {"seconds": 1, "nanos": 0},
                    },
                },
            ),
            json.dumps({"testRunFinished": {"success": True, "timestamp": {"seconds": 2, "nanos": 0}}}),
        ]
        ndjson.write_text("\n".join(lines) + "\n", encoding="utf-8")
        projections = list(read_envelopes(ndjson))
        assert len(projections) == 3

    def test_skips_empty_lines(self, tmp_path: Path) -> None:
        """Empty and blank lines are skipped without error."""
        ndjson = tmp_path / "messages.ndjson"
        ndjson.write_text(
            "\n\n" + json.dumps({"testRunStarted": {"id": "r1", "timestamp": {"seconds": 0, "nanos": 0}}}) + "\n\n\n",
            encoding="utf-8",
        )
        projections = list(read_envelopes(ndjson))
        assert len(projections) == 1

    def test_raises_on_malformed_json(self, tmp_path: Path) -> None:
        """Malformed JSON raises ValueError with line context."""
        ndjson = tmp_path / "messages.ndjson"
        ndjson.write_text("not valid json\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Malformed JSON"):
            list(read_envelopes(ndjson))

    def test_handles_empty_file(self, tmp_path: Path) -> None:
        """Empty file yields no projections."""
        ndjson = tmp_path / "messages.ndjson"
        ndjson.write_text("", encoding="utf-8")
        projections = list(read_envelopes(ndjson))
        assert projections == []
