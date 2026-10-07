from __future__ import annotations

from pathlib import Path

import pytest

from pytest_cuke.formatter_api import FormatterAsset, FormatterRequest


@pytest.mark.parametrize("path", ["../outside.txt", "/absolute.txt", "C:/absolute.txt", "C:relative.txt"])
def test_formatter_asset_rejects_paths_outside_its_temporary_directory(path: str) -> None:
    with pytest.raises(ValueError, match="safe relative path"):
        FormatterAsset(path=path, content="data")


def test_formatter_request_rejects_invalid_command_and_timeout() -> None:
    with pytest.raises(ValueError, match="argv command"):
        FormatterRequest(name="broken", command=("python", "\x00script"))

    with pytest.raises(ValueError, match="positive, finite"):
        FormatterRequest(name="broken", command=("python",), timeout_seconds=float("inf"))

    with pytest.raises(ValueError, match="no greater than"):
        FormatterRequest(name="broken", command=("python",), timeout_seconds=1 << 5000)


def test_formatter_request_requires_an_asset_when_using_asset_placeholder() -> None:
    with pytest.raises(ValueError, match="without runtime assets"):
        FormatterRequest(name="broken", command=("node", "{asset_dir}/formatter.mjs"))


def test_formatter_request_accepts_file_output_and_safe_assets(tmp_path: Path) -> None:
    request = FormatterRequest(
        name="example",
        command=("node", "{asset_dir}/formatter.mjs"),
        output_path=tmp_path / "report.txt",
        runtime_assets=(FormatterAsset("formatter.mjs", "process.exit(0)"),),
    )

    assert request.output_path == tmp_path / "report.txt"
    assert request.runtime_assets[0].path == "formatter.mjs"
