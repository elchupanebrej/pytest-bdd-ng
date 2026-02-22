from pathlib import Path

from pytest_bdd.compatibility.matrix import build_migration_coverage_summary


def test_duplicate_user_facing_scenarios_are_detected(tmp_path: Path):
    tests_feature_dir = tmp_path / "tests" / "feature"
    tests_feature_dir.mkdir(parents=True)
    (tests_feature_dir / "test_no_scenario.py").write_text("def test_x():\n    pass\n", encoding="utf-8")

    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "no-scenario.feature.md").write_text("Feature: no scenario\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.duplicates_in_tests == 1
    assert summary.threshold_met is False


def test_no_duplicates_when_user_facing_tests_removed(tmp_path: Path):
    feature_dir = tmp_path / "features" / "Feature"
    feature_dir.mkdir(parents=True)
    (feature_dir / "only-doc.feature.md").write_text("Feature: only doc\n", encoding="utf-8")

    summary = build_migration_coverage_summary(tmp_path / "tests", tmp_path / "features", threshold_percent=80)

    assert summary.duplicates_in_tests == 0
    assert summary.threshold_met is True


def test_inventory_keeps_non_removable_retained_and_deferred_tests():
    inventory = Path("specs/002-e2e-test-conversion/e2e-migration-inventory.md").read_text(encoding="utf-8")

    assert "`tests/e2e/test_e2e.py`" in inventory
    assert "`tests/e2e/allure/test_e2e_allure.py`" in inventory
    assert "e2e_retain_technical" in inventory

    assert "`tests/feature/test_outline.py`" in inventory
    assert "`tests/feature/test_http.py`" in inventory
    assert "`tests/struct_bdd/test_deserialization.py`" in inventory
    assert "| Deferred conversion | 0 |" in inventory


def _iter_inventory_rows(inventory_text: str):
    for raw_line in inventory_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("| `tests/"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 11:
            continue
        yield cells


def test_fr_006b_restoration_required_rows_must_keep_source_until_parity_is_recorded():
    inventory = Path("specs/002-e2e-test-conversion/e2e-migration-inventory.md").read_text(encoding="utf-8")

    restoration_rows = []
    for cells in _iter_inventory_rows(inventory):
        source_path = cells[0].strip("`")
        restoration_required = cells[7]
        if restoration_required.startswith("yes"):
            restoration_rows.append(source_path)
            assert Path(source_path).exists(), (
                f"{source_path} is marked restoration_required={restoration_required!r} "
                "but the pytest source file is missing"
            )
