from __future__ import annotations

from pathlib import Path

import pytest

from pytest_cuke.source_editor import SourceEditError, update_source_file


def _identity_formatter(source: str, path: Path) -> str:
    del path
    return source


def test_update_preserves_existing_bytes_and_crlf_with_utf8_bom(tmp_path: Path) -> None:
    target = tmp_path / "steps.py"
    original = b"\xef\xbb\xbf# hand-written comment\r\nvalue = 'kept'\r\n"
    target.write_bytes(original)

    result = update_source_file(
        target, "@given('caf\\u00e9')\ndef generated():\n    pass", formatter=_identity_formatter
    )

    updated = target.read_bytes()
    assert result.changed is True
    assert updated.startswith(original)
    assert updated.count(b"\xef\xbb\xbf") == 1
    assert b"\r\n" in updated[len(original) :]
    assert b"\n" not in updated[len(original) :].replace(b"\r\n", b"")


def test_preview_validates_and_returns_a_diff_without_writing(tmp_path: Path) -> None:
    target = tmp_path / "steps.py"
    original = b"value = 1\n"
    target.write_bytes(original)

    result = update_source_file(target, "value = 2", preview=True, formatter=_identity_formatter)

    assert result.changed is True
    assert "+value = 2" in result.diff
    assert "value = 1" in result.diff
    assert target.read_bytes() == original


def test_successful_update_is_idempotent_when_no_source_is_proposed(tmp_path: Path) -> None:
    target = tmp_path / "steps.py"
    original = b"value = 1\n"
    target.write_bytes(original)

    result = update_source_file(target, "", formatter=_identity_formatter)

    assert result.changed is False
    assert result.diff == ""
    assert target.read_bytes() == original


def test_formatter_failure_rolls_back_by_default(tmp_path: Path) -> None:
    target = tmp_path / "steps.py"
    original = b"value = 1\n"
    target.write_bytes(original)

    def fail_formatter(source: str, path: Path) -> str:
        raise RuntimeError("formatter failed")

    with pytest.raises(SourceEditError, match="formatter failed"):
        update_source_file(target, "value = 2", formatter=fail_formatter)

    assert target.read_bytes() == original


def test_keep_on_error_retains_the_attempted_edit_and_still_raises(tmp_path: Path) -> None:
    target = tmp_path / "steps.py"
    original = b"value = 1\n"
    target.write_bytes(original)

    def fail_formatter(source: str, path: Path) -> str:
        raise RuntimeError("formatter failed")

    with pytest.raises(SourceEditError, match="formatter failed"):
        update_source_file(target, "value = 2", formatter=fail_formatter, keep_on_error=True)

    assert target.read_bytes().startswith(original)
    assert target.read_bytes().endswith(b"value = 2\n")


def test_validation_failure_rolls_back_and_keep_on_error_retains_candidate(tmp_path: Path) -> None:
    target = tmp_path / "steps.py"
    original = b"value = 1\n"
    target.write_bytes(original)

    with pytest.raises(SourceEditError, match="invalid Python"):
        update_source_file(target, "if :", formatter=_identity_formatter)
    assert target.read_bytes() == original

    with pytest.raises(SourceEditError, match="invalid Python"):
        update_source_file(target, "if :", formatter=_identity_formatter, keep_on_error=True)
    assert target.read_bytes().startswith(original)
    assert target.read_bytes().endswith(b"if :\n")


def test_invalid_existing_target_is_never_replaced(tmp_path: Path) -> None:
    target = tmp_path / "steps.py"
    original = b"if :\n"
    target.write_bytes(original)

    with pytest.raises(SourceEditError, match="existing target is not valid Python"):
        update_source_file(target, "value = 2", formatter=_identity_formatter, keep_on_error=True)

    assert target.read_bytes() == original
