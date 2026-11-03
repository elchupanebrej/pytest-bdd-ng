"""BDD step definitions for testing development scripts and architecture CLIs."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from pytest_cuke import given, parsers, then, when


def _extract_docstring(step: Any) -> str:
    if hasattr(step, "doc_string") and step.doc_string:
        return step.doc_string.content
    if hasattr(step, "argument") and hasattr(step.argument, "doc_string") and step.argument.doc_string:
        return step.argument.doc_string.content
    return ""


@given(parsers.parse('Mock file "{filename}" with content:'))
def mock_file_with_content(testdir: Any, filename: str, step: Any) -> None:
    """Write content to a file in the test directory."""
    content = _extract_docstring(step)
    target = Path(str(testdir.tmpdir)) / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


@when(parsers.parse("run `{command}`"), target_fixture="renderer_result")
def run_command(testdir: Any, command: str, request: Any) -> subprocess.CompletedProcess[str]:
    """Execute a CLI command within the testdir sandbox."""
    command_args = shlex.split(command)
    if command_args and command_args[0] == "python":
        command_args[0] = sys.executable
    env = dict(os.environ)
    repo_root = getattr(request.config, "rootpath", getattr(request.config, "rootdir", Path.cwd()))
    env["PYTHONPATH"] = os.pathsep.join(
        filter(
            None,
            [
                str(Path(repo_root) / "src"),
                str(Path(repo_root) / "scripts"),
                env.get("PYTHONPATH", ""),
            ],
        )
    )
    return subprocess.run(
        command_args,
        check=False,
        capture_output=True,
        text=True,
        cwd=str(testdir.tmpdir),
        env=env,
    )


@then(parsers.parse("the command exit code is {exit_code:d}"))
def check_command_exit_code(renderer_result: subprocess.CompletedProcess[str], exit_code: int) -> None:
    """Verify the exit code of the last executed command."""
    assert renderer_result.returncode == exit_code, (
        f"Expected exit code {exit_code}, got {renderer_result.returncode}\n"
        f"STDOUT:\n{renderer_result.stdout}\n"
        f"STDERR:\n{renderer_result.stderr}"
    )


@then(parsers.parse('File "{file_path}" contains the line "{line}"'))
def file_contains_line(testdir: Any, file_path: str, line: str) -> None:
    """Verify that a file in the test directory contains the specified line/substring."""
    output_path = Path(str(testdir.tmpdir)) / file_path
    assert output_path.exists(), f"File does not exist: {output_path}"
    content = output_path.read_text(encoding="utf-8")
    assert line in content, f"Expected substring '{line}' not found in {file_path}.\nActual content:\n{content}"
