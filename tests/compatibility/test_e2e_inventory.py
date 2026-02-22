from pathlib import Path

import pytest

from pytest_bdd.compatibility.matrix import (
    discover_feature_scenario_ids,
    discover_user_facing_test_scenario_ids,
)

pytestmark = [pytest.mark.e2e_convert_candidate]


def test_discovers_feature_scenario_ids(tmp_path: Path):
    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "Feature base dir.feature.md").write_text("Feature: Base dir\n", encoding="utf-8")

    ids = discover_feature_scenario_ids(tmp_path / "features")

    assert "feature-base-dir" in ids


def test_discovers_user_facing_tests_from_tests_feature_folder(tmp_path: Path):
    user_facing_dir = tmp_path / "tests" / "feature"
    user_facing_dir.mkdir(parents=True)
    (user_facing_dir / "test_no_scenario.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    (user_facing_dir / "test_other.py").write_text("def test_y():\n    pass\n", encoding="utf-8")

    ids = discover_user_facing_test_scenario_ids(tmp_path / "tests")

    assert "no-scenario" in ids
    assert "other" not in ids


def test_deferred_conversion_notes_are_complete():
    inventory = Path("specs/002-e2e-test-conversion/e2e-migration-inventory.md").read_text(encoding="utf-8")
    assert "| Deferred conversion | 0 |" in inventory


def _iter_markdown_table_rows(markdown_text: str, prefix: str):
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if line.startswith(prefix):
            yield [cell.strip() for cell in line.strip("|").split("|")]


def test_category_parity_matrix_has_required_fields_and_consistent_verdicts():
    parity_audit = Path("specs/002-e2e-test-conversion/conversion-parity-audit.md").read_text(encoding="utf-8")
    marker = "## Category Parity Matrix (T013-T032)"
    assert marker in parity_audit
    matrix_text = parity_audit.split(marker, maxsplit=1)[1]
    matrix_text = matrix_text.split("\n## ", maxsplit=1)[0]

    rows = list(_iter_markdown_table_rows(matrix_text, "| T0"))
    assert rows, "Category parity matrix rows are missing"

    for row in rows:
        task_id, happy, failure, boundary, category_parity, _notes = row[:6]
        assert task_id.startswith("T0")
        assert happy in {"yes", "no"}
        assert failure in {"yes", "no"}
        assert boundary in {"yes", "no"}
        assert category_parity in {"yes", "no"}

        all_categories_covered = happy == "yes" and failure == "yes" and boundary == "yes"
        if category_parity == "yes":
            assert all_categories_covered


def test_inventory_marker_policy_is_synchronized_with_classification_metadata():
    inventory = Path("specs/002-e2e-test-conversion/e2e-migration-inventory.md").read_text(encoding="utf-8")

    for row in _iter_markdown_table_rows(inventory, "| `tests/"):
        source_path, *_rest = row
        classification = row[5]
        marker = row[6].strip("`")
        unblock_condition = row[9]
        target_cycle = row[10]

        assert source_path.startswith("`tests/")
        if classification == "retain_technical":
            assert marker == "e2e_retain_technical"
            assert target_cycle == "reviewed-each-cycle"
        elif classification == "deferred_conversion":
            assert marker == "e2e_deferred_conversion"
            assert unblock_condition
            assert unblock_condition != "n/a"
            assert target_cycle == "next-feature-cycle"
        else:
            assert marker == "e2e_convert_candidate"
