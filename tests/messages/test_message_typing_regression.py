from __future__ import annotations

import importlib.util
import subprocess  # noqa: S404
import sys
import textwrap
from typing import TYPE_CHECKING

import pytest
from cucumber_messages import Envelope as Message  # type:ignore[attr-defined]
from cucumber_messages import TestRunStarted as _TestRunStarted  # type:ignore[attr-defined]


def build_valid_envelope() -> Message:
    return Message(test_run_started=_TestRunStarted())


if TYPE_CHECKING:
    # This block is intentionally unreachable at runtime and exists for MyPy-regression checks.
    # MyPy should reject non-dataclass payload assignments to known envelope payload fields.
    _INVALID_ENVELOPE_ASSIGNMENT: Message = Message(test_run_started="invalid-payload-type")


@pytest.mark.skipif(importlib.util.find_spec("mypy") is None, reason="mypy is not installed in this environment")
def test_mypy_rejects_invalid_envelope_assignment(tmp_path) -> None:
    source = tmp_path / "invalid_message_assignment.py"
    source.write_text(
        textwrap.dedent(
            """\
            from cucumber_messages import Envelope as Message

            invalid: Message = Message(test_run_started="invalid-payload-type")
            """
        ),
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "mypy", "--config-file", "pyproject.toml", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "error:" in result.stdout or "error:" in result.stderr
