"""Provide test spec prefix resolution helpers."""

from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[4]
COMMON_SCRIPT = ROOT_DIR / ".specify" / "scripts" / "bash" / "common.sh"
CHECK_PREREQUISITES_SCRIPT = ROOT_DIR / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
CREATE_FEATURE_SCRIPT = ROOT_DIR / ".specify" / "scripts" / "bash" / "create-new-feature.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_common_script_contains_prefix_lookup_function() -> None:
    """Verify common script contains prefix lookup function."""
    script_text = _read(COMMON_SCRIPT)
    assert "find_feature_dir_by_prefix" in script_text


def test_check_prerequisites_supports_paths_json_mode() -> None:
    """Verify check prerequisites supports paths json mode."""
    script_text = _read(CHECK_PREREQUISITES_SCRIPT)
    assert "--paths-only" in script_text
    assert "FEATURE_DIR" in script_text
    assert "TASKS" in script_text


def test_create_new_feature_contains_monotonic_prefix_logic() -> None:
    """Verify create new feature contains monotonic prefix logic."""
    script_text = _read(CREATE_FEATURE_SCRIPT)
    assert "check_existing_branches" in script_text
    assert "FEATURE_NUM" in script_text
