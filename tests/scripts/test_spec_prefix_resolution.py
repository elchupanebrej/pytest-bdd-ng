from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
COMMON_SCRIPT = ROOT_DIR / ".specify" / "scripts" / "bash" / "common.sh"
CHECK_PREREQUISITES_SCRIPT = ROOT_DIR / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
CREATE_FEATURE_SCRIPT = ROOT_DIR / ".specify" / "scripts" / "bash" / "create-new-feature.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_common_script_contains_prefix_lookup_function() -> None:
    script_text = _read(COMMON_SCRIPT)
    assert "find_feature_dir_by_prefix" in script_text


def test_check_prerequisites_supports_paths_json_mode() -> None:
    script_text = _read(CHECK_PREREQUISITES_SCRIPT)
    assert "--paths-only" in script_text
    assert "FEATURE_DIR" in script_text
    assert "TASKS" in script_text


def test_create_new_feature_contains_monotonic_prefix_logic() -> None:
    script_text = _read(CREATE_FEATURE_SCRIPT)
    assert "check_existing_branches" in script_text
    assert "FEATURE_NUM" in script_text
