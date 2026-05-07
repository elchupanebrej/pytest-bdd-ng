from __future__ import annotations

import pytest
from attrs import define

from tests.support.pytest_results import (
    attach_command_result_outputs,
    resolve_pytester_run_mode,
    run_quietly,
)


class _CapturedText:
    def __init__(self, value: str) -> None:
        self._value = value

    def str(self) -> str:
        return self._value


class _PytesterLikeResult:
    def __init__(self, *, stdout: str, stderr: str, ret: int) -> None:
        self.stdout = _CapturedText(stdout)
        self.stderr = _CapturedText(stderr)
        self.ret = ret


@define
class _CompletedProcessLikeResult:
    stdout: str
    stderr: str
    returncode: int


def test_attach_command_result_outputs_emits_metadata_stdout_and_stderr() -> None:
    attachments: list[tuple[str, dict[str, str]]] = []

    def _attach(body: str, **kwargs: str) -> None:
        attachments.append((body, kwargs))

    result = _CompletedProcessLikeResult(stdout="stdout-body", stderr="stderr-body", returncode=1)

    attach_command_result_outputs(_attach, result, label="nested-process", command="python -V")

    assert attachments == [
        (
            "label: nested-process\ncommand: python -V\nreturn_code: 1\n",
            {
                "file_name": "nested-process.meta.txt",
                "media_type": "text/plain;charset=UTF-8",
            },
        ),
        (
            "stdout-body",
            {
                "file_name": "nested-process.stdout.txt",
                "media_type": "text/plain;charset=UTF-8",
            },
        ),
        (
            "stderr-body",
            {
                "file_name": "nested-process.stderr.txt",
                "media_type": "text/plain;charset=UTF-8",
            },
        ),
    ]


def test_attach_command_result_outputs_supports_pytester_capture_objects() -> None:
    attachments: list[tuple[str, dict[str, str]]] = []

    def _attach(body: str, **kwargs: str) -> None:
        attachments.append((body, kwargs))

    result = _PytesterLikeResult(stdout="child stdout", stderr="child stderr", ret=0)

    attach_command_result_outputs(_attach, result, label="nested-pytest")

    assert attachments == [
        (
            "label: nested-pytest\nreturn_code: 0\n",
            {
                "file_name": "nested-pytest.meta.txt",
                "media_type": "text/plain;charset=UTF-8",
            },
        ),
        (
            "child stdout",
            {
                "file_name": "nested-pytest.stdout.txt",
                "media_type": "text/plain;charset=UTF-8",
            },
        ),
        (
            "child stderr",
            {
                "file_name": "nested-pytest.stderr.txt",
                "media_type": "text/plain;charset=UTF-8",
            },
        ),
    ]


def test_run_quietly_redirects_harness_stdout_and_stderr() -> None:
    def _noisy_runner() -> str:
        import sys

        sys.stdout.write("runner stdout\n")
        sys.stderr.write("runner stderr\n")
        return "result"

    result, harness_stdout, harness_stderr = run_quietly(_noisy_runner)

    assert result == "result"
    assert harness_stdout == "runner stdout\n"
    assert harness_stderr == "runner stderr\n"


@pytest.mark.parametrize(
    ("options_dict", "expected_mode"),
    [
        ({}, "subprocess"),
        ({"subprocess": ["true"]}, "subprocess"),
        ({"subprocess": ["false"]}, "inprocess"),
        ({"inprocess": ["true"]}, "inprocess"),
        ({"inprocess": ["false"]}, "subprocess"),
        ({"subprocess": ["true"], "inprocess": ["false"]}, "subprocess"),
        ({"subprocess": ["false"], "inprocess": ["true"]}, "inprocess"),
    ],
)
def test_resolve_pytester_run_mode_supports_legacy_and_current_switches(
    options_dict: dict[str, list[str]],
    expected_mode: str,
) -> None:
    assert resolve_pytester_run_mode(options_dict) == expected_mode


def test_resolve_pytester_run_mode_rejects_conflicting_switches() -> None:
    with pytest.raises(ValueError, match="Conflicting pytest invocation mode options"):
        resolve_pytester_run_mode({"subprocess": ["true"], "inprocess": ["true"]})
