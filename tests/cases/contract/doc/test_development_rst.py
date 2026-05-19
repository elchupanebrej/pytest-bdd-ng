from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.contract
def test_development_rst_required_sections() -> None:
    content = (ROOT / "DEVELOPMENT.rst").read_text(encoding="utf-8")
    required = ["StashBound", "attrs", "plugin class", "test", "Architecture"]
    for keyword in required:
        assert keyword in content, f"DEVELOPMENT.rst missing required section keyword: {keyword!r}"
