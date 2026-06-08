from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]


@pytest.mark.contract
def test_development_rst_required_sections() -> None:
    content = (ROOT / "DEVELOPMENT.rst").read_text(encoding="utf-8")
    required = ["StashBound", "attrs", "plugin class", "test", "Architecture"]
    for keyword in required:
        assert keyword in content, f"DEVELOPMENT.rst missing required section keyword: {keyword!r}"


@pytest.mark.contract
def test_development_rst_documents_phase15_cross_platform_make_api() -> None:
    content = (ROOT / "DEVELOPMENT.rst").read_text(encoding="utf-8")
    required = [
        "Cross-Platform Setup",
        "Canonical Make Commands",
        "tox-backed",
        "test-platform-native",
        "test-platform-linux",
        "test-platform-windows",
        "test-platform-macos",
        "TEST_LINUX_ARGS",
        "TEST_WINDOWS_ARGS",
        "FAIL_FAST",
        "ARTIFACT_MODE=collect",
        "REPORT_MODE=skip",
        "WINDOWS_TOX_BACKEND_COMMAND",
        "PowerShell",
        "WSL2",
    ]
    for keyword in required:
        assert keyword in content, f"DEVELOPMENT.rst missing Phase 15 docs keyword: {keyword!r}"
