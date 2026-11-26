"""Contract checks for the #409 parity evidence ledger."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[3] / "docs" / "parity" / "ledger.json"
LEDGER_MD = LEDGER.with_suffix(".md")
CATEGORIES = {
    "proven analogue",
    "agreed replacement/addition",
    "agreed exclusion",
    "unproven gap",
}


def _ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_row_identities_and_category_counts_match() -> None:
    ledger = _ledger()
    rows = ledger["rows"]
    assert len(rows) == 219
    assert len({(row["path"], row["line"]) for row in rows}) == 219
    assert [row["id"] for row in rows] == list(range(1, 220))
    assert {row["category"] for row in rows} <= CATEGORIES
    counts = Counter(row["category"] for row in rows)
    assert ledger["counts"] == {"total": 219, **{category: counts[category] for category in CATEGORIES}}


def test_agreed_rows_cite_a_resolvable_numbered_decision() -> None:
    ledger = _ledger()
    decisions = {decision["id"] for decision in ledger["decisions"]}
    agreed = [row for row in ledger["rows"] if row["category"].startswith("agreed")]
    assert agreed
    for row in agreed:
        assert row["decision"] in decisions, row["path"]
        for extra in row.get("also", []):
            assert extra in decisions, row["path"]


def test_unproven_rows_carry_a_reason_and_no_borrowed_evidence() -> None:
    ledger = _ledger()
    unproven = [row for row in ledger["rows"] if row["category"] == "unproven gap"]
    for row in unproven:
        assert row["reason"] and row["reason"].strip(), row["path"]
        assert row["evidence"] is None
        assert row["probe"] is None


def test_proven_rows_have_probe_and_observation() -> None:
    ledger = _ledger()
    for row in ledger["rows"]:
        if row["category"] != "proven analogue":
            continue
        assert row["probe"], row["path"]
        assert row["command"], row["path"]
        assert row["exit"] is not None, row["path"]
        assert row["result"], row["path"]


def test_parity_flag_agrees_with_the_statement() -> None:
    ledger = _ledger()
    unproven = [row for row in ledger["rows"] if row["category"] == "unproven gap"]
    assert ledger["full_parity_claimed"] is False
    assert "No full parity is claimed" in ledger["parity_statement"]
    for row in unproven:
        assert str(row["id"]) in ledger["parity_statement"]


def test_ledger_binds_the_proof_ref_and_wheel() -> None:
    ledger = _ledger()
    assert ledger["final_revision"] == {
        "repo": "elchupanebrej/pytest-bdd-ng",
        "ref": "parity/cycle-2-proof",
        "sha": "8ea8a5fd5b48a25f9c8d395b388858fefa107676",
        "resolvable": True,
        "resolvable_via": "git ls-remote origin parity/cycle-2-proof",
    }
    assert ledger["wheel"]["built_from"] == ledger["final_revision"]["sha"]
    assert ledger["wheel"]["filename"] == "pytest_cuke-2.3.1-py3-none-any.whl"
    assert len(ledger["wheel"]["sha256"]) == 64
    assert len(ledger["former_unexecuted_rows"]) == 16
    assert len(ledger["nested_docstring_rows"]) == 2


def test_markdown_projection_matches_the_json() -> None:
    ledger = _ledger()
    markdown = LEDGER_MD.read_text(encoding="utf-8")

    assert f"> **{ledger['parity_statement']}**" in markdown

    counts = ledger["counts"]
    for category, count in counts.items():
        if category == "total":
            continue
        assert re.search(rf"^\| {re.escape(category)} \| {count} \|$", markdown, re.MULTILINE), category
    agreed = counts["agreed replacement/addition"] + counts["agreed exclusion"]
    assert f"## Unproven gaps ({counts['unproven gap']})" in markdown
    assert f"## Agreed replacements and exclusions ({agreed})" in markdown

    for decision in ledger["decisions"]:
        assert f"| `{decision['id']}` |" in markdown, decision["id"]

    matrix = markdown.split("## Matrix: 219 external declarations", 1)[1]
    for row in ledger["rows"]:
        match = re.search(rf"^\| {row['id']} \| (.+)$", matrix, re.MULTILINE)
        assert match, row["id"]
        line = match.group(0)
        assert f"| {row['category']} |" in line, row["id"]
        if row["category"].startswith("agreed"):
            assert f"decision {row['decision']}" in line, row["id"]
