"""Run one inventory cell and record the exact tox/runtime evidence."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from env_matrix import load_cells
from environment_evidence import (
    OPTIONAL_VERSION_KEYS,
    SYSTEM_TOOL_VERSION_KEYS,
    TEST_EVIDENCE_GROUPS,
    evidence_group,
    required_optional_versions,
    required_system_tool_versions,
    system_tool_version_command,
)

_OPTIONAL_PACKAGES = ("pytest", *OPTIONAL_VERSION_KEYS)
_VERSION_PATTERN = re.compile(r"(?<![\w.])v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?(?![\w.])")
_GO_VERSION_PATTERN = re.compile(r"\bgo\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?\b")


def _write_console_text(
    text: str,
    *,
    stream: Any | None = None,
    end: str = "\n",
    flush: bool = False,
) -> None:
    destination = stream if stream is not None else sys.stdout
    encoding = getattr(destination, "encoding", None)
    if encoding:
        text = text.encode(encoding, errors="backslashreplace").decode(encoding)
    destination.write(text)
    destination.write(end)
    if flush:
        destination.flush()


def _installed_versions(python: Path) -> dict[str, Any]:
    package_names = json.dumps(_OPTIONAL_PACKAGES)
    query = "\n".join(
        (
            "import importlib.metadata as metadata, json, platform",
            f"names = {package_names}",
            "installed = {dist.metadata['Name'].casefold(): dist.version for dist in metadata.distributions()}",
            "versions = {name: installed.get(name.casefold()) for name in names}",
            "payload = {'python': platform.python_version(),",
            "'runtime': platform.python_implementation(), 'packages': versions}",
            "print(json.dumps(payload))",
        )
    )
    # The executable is resolved from the selected tox environment.
    result = subprocess.run(  # noqa: S603
        [str(python), "-c", query], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise RuntimeError(f"cannot inspect tox environment with {python}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def _system_tool_evidence(
    tox_environment: str,
    platform_name: str = sys.platform,
    *,
    project_root: Path | None = None,
) -> tuple[dict[str, str | None], dict[str, dict[str, Any] | None]]:
    versions: dict[str, str | None] = dict.fromkeys(SYSTEM_TOOL_VERSION_KEYS, None)
    commands: dict[str, dict[str, Any] | None] = dict.fromkeys(SYSTEM_TOOL_VERSION_KEYS, None)
    for tool in required_system_tool_versions(tox_environment):
        executable_name, arguments = system_tool_version_command(tool, platform_name)
        if tool == "uv":
            executable = _tox_uv_executable(project_root or Path.cwd(), tox_environment, platform_name)
        else:
            executable = shutil.which(executable_name)
        if executable is None:
            continue
        argv = [executable, *arguments]
        commands[tool] = {"executable": executable, "argv": argv}
        try:
            # The tool and arguments come from the fixed evidence contract.
            result = subprocess.run(  # noqa: S603
                argv, capture_output=True, text=True, check=False, timeout=120
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode != 0:
            continue
        output = f"{result.stdout}\n{result.stderr}"
        version_pattern = _GO_VERSION_PATTERN if tool == "go" else _VERSION_PATTERN
        match = version_pattern.search(output)
        if match:
            versions[tool] = match.group()
    return versions, commands


def _tox_uv_executable(project_root: Path, tox_environment: str, platform_name: str) -> str | None:
    """Resolve uv only from the formatter environment whose evidence is being recorded."""
    environment_root = project_root / ".tox" / tox_environment
    if platform_name in {"win32", "windows"}:
        candidate = environment_root / "Scripts" / "uv.exe"
    else:
        candidate = environment_root / "bin" / "uv"
    try:
        resolved_environment = environment_root.resolve(strict=True)
        resolved_candidate = candidate.resolve(strict=True)
        resolved_candidate.relative_to(resolved_environment)
    except (OSError, ValueError):
        return None
    return str(resolved_candidate)


def _system_tool_versions(tox_environment: str) -> dict[str, str | None]:
    """Return only captured versions for callers that do not need invocation details."""
    versions, _commands = _system_tool_evidence(tox_environment)
    return versions


def _python_in_tox_environment(project_root: Path, env_name: str) -> Path:
    environment = project_root / ".tox" / env_name
    executable = "python.exe" if os.name == "nt" else "python"
    scripts_dir = "Scripts" if os.name == "nt" else "bin"
    python = environment / scripts_dir / executable
    if not python.is_file():
        raise RuntimeError(f"tox environment {env_name!r} has no Python executable at {python}")
    return python


def _test_counts(output: str) -> dict[str, int] | None:
    for line in reversed(output.splitlines()):
        counts = re.findall(r"\b(\d+)\s+(passed|failed|errors?|skipped|xfailed|xpassed)\b", line)
        if counts:
            summary: dict[str, int] = {}
            for count, outcome in counts:
                key = "error" if outcome in {"error", "errors"} else outcome
                summary[key] = summary.get(key, 0) + int(count)
            return summary
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", required=True)
    parser.add_argument("--cell", required=True)
    parser.add_argument(
        "--tox-env",
        help="run only this tox environment from the selected inventory cell",
    )
    parser.add_argument("--inventory", type=Path, default=Path("config/env-matrix.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sha", default=os.environ.get("GITHUB_SHA"))
    args = parser.parse_args()

    if not args.sha:
        _write_console_text(
            "run-env-matrix: pass --sha or set GITHUB_SHA so evidence is tied to an exact commit",
            stream=sys.stderr,
        )
        return 2
    tox = shutil.which("tox")
    if tox is None:
        _write_console_text(
            "run-env-matrix: tox is not installed; run `python -m pip install 'pytest-cuke[env-matrix]'`",
            stream=sys.stderr,
        )
        return 2

    try:
        cells = load_cells(args.inventory, args.job)
    except RuntimeError as error:
        _write_console_text(f"run-env-matrix: {error}", stream=sys.stderr)
        return 2
    selected = next((cell for cell in cells if cell.get("id") == args.cell), None)
    if selected is None:
        _write_console_text(f"run-env-matrix: cell {args.cell!r} is not part of job {args.job!r}", stream=sys.stderr)
        return 2
    if args.tox_env and args.tox_env not in selected["tox_envs"]:
        _write_console_text(
            f"run-env-matrix: tox environment {args.tox_env!r} is not part of cell {args.cell!r}",
            stream=sys.stderr,
        )
        return 2
    tox_environments = [args.tox_env] if args.tox_env else selected["tox_envs"]

    project_root = args.inventory.resolve().parent.parent
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tox_results_dir = output_path.parent / "tox-results"
    tox_results_dir.mkdir(parents=True, exist_ok=True)
    environment_records: list[dict[str, Any]] = []
    overall_status = "passed"
    for env_name in tox_environments:
        result_json = tox_results_dir / f"{env_name}.json"
        remote_runtime_path = tox_results_dir / f"{env_name}.remote-workers.json"
        command = [tox, "run", "--result-json", str(result_json), "-e", env_name]
        command_environment = os.environ.copy()
        command_environment["PYTHONUTF8"] = "1"
        if args.job == "remote":
            remote_runtime_path.unlink(missing_ok=True)
            command_environment["PYTEST_CUKE_REMOTE_RUNTIME_EVIDENCE"] = str(remote_runtime_path)
        if args.job == "native-go-parser":
            command_environment["PYTEST_CUKE_BUILD_GO"] = "off"
        _write_console_text(f"Running {' '.join(command)}", flush=True)
        # The command is built from the validated inventory's tox environment name.
        run = subprocess.run(  # noqa: S603
            command,
            cwd=project_root,
            env=command_environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if run.stdout:
            _write_console_text(run.stdout, end="" if run.stdout.endswith("\n") else "\n", flush=True)
        if run.stderr:
            _write_console_text(
                run.stderr,
                stream=sys.stderr,
                end="" if run.stderr.endswith("\n") else "\n",
                flush=True,
            )
        if run.returncode:
            overall_status = "failed"

        output = run.stdout + "\n" + run.stderr
        test_counts = _test_counts(output)
        selected_tests = sum(test_counts.values()) if test_counts else None
        passed_tests = test_counts.get("passed", 0) if test_counts else None
        environment_group = evidence_group(args.job, env_name)
        if environment_group in TEST_EVIDENCE_GROUPS:
            if selected_tests is None or selected_tests < 1:
                overall_status = "failed"
                _write_console_text(
                    f"run-env-matrix: {env_name} selected no tests; refusing to record an empty acceptance run",
                    stream=sys.stderr,
                )
            elif passed_tests is None or passed_tests < 1:
                overall_status = "failed"
                _write_console_text(
                    f"run-env-matrix: {env_name} selected no tests that passed; "
                    "all selected tests may have been skipped or expected to fail",
                    stream=sys.stderr,
                )

        system_tool_versions, system_tool_commands = _system_tool_evidence(env_name, project_root=project_root)
        environment_record: dict[str, Any] = {
            "git_sha": args.sha,
            "job": args.job,
            "cell": args.cell,
            "group": environment_group,
            "tox_environment": env_name,
            "command": command,
            "selected_tests": selected_tests,
            "passed_tests": passed_tests,
            "system_tool_versions": system_tool_versions,
            "system_tool_commands": system_tool_commands,
            "outcome": "passed" if run.returncode == 0 else "failed",
            "returncode": run.returncode,
            "platform": platform.platform(),
            "platform_name": sys.platform,
            "result_json": result_json.as_posix(),
        }
        if args.job == "remote":
            try:
                remote_payload = json.loads(remote_runtime_path.read_text(encoding="utf-8"))
                if remote_payload.get("schema_version") != 1 or not isinstance(remote_payload.get("runs"), list):
                    raise ValueError("remote worker evidence has an unsupported schema or missing runs")
                environment_record["remote_worker_runs"] = remote_payload["runs"]
            except (OSError, json.JSONDecodeError, AttributeError, ValueError) as error:
                environment_record["remote_worker_evidence_error"] = str(error)
                environment_record["outcome"] = "failed"
                overall_status = "failed"
        try:
            runtime_evidence = _installed_versions(_python_in_tox_environment(project_root, env_name))
            packages = runtime_evidence.pop("packages")
            environment_record.update(runtime_evidence)
            environment_record["pytest"] = packages.pop("pytest", None)
            environment_record["optional_versions"] = packages
            missing_optional = [
                package for package in required_optional_versions(env_name) if not packages.get(package)
            ]
            if missing_optional:
                environment_record["outcome"] = "failed"
                environment_record["missing_optional_packages"] = missing_optional
                overall_status = "failed"
                _write_console_text(
                    f"run-env-matrix: {env_name} is missing required optional package(s): "
                    f"{', '.join(missing_optional)}",
                    stream=sys.stderr,
                )
            missing_system_tools = [
                tool
                for tool in required_system_tool_versions(env_name)
                if not environment_record["system_tool_versions"].get(tool)
            ]
            if missing_system_tools:
                environment_record["outcome"] = "failed"
                environment_record["missing_system_tools"] = missing_system_tools
                overall_status = "failed"
                _write_console_text(
                    f"run-env-matrix: {env_name} is missing a version for required system tool(s): "
                    f"{', '.join(missing_system_tools)}",
                    stream=sys.stderr,
                )
            missing_system_tool_commands = [
                tool
                for tool in required_system_tool_versions(env_name)
                if not environment_record["system_tool_commands"].get(tool)
            ]
            if missing_system_tool_commands:
                environment_record["outcome"] = "failed"
                environment_record["missing_system_tool_commands"] = missing_system_tool_commands
                overall_status = "failed"
                _write_console_text(
                    f"run-env-matrix: {env_name} is missing a resolved version command for required system tool(s): "
                    f"{', '.join(missing_system_tool_commands)}",
                    stream=sys.stderr,
                )
        except (OSError, RuntimeError, json.JSONDecodeError) as error:
            environment_record["runtime_evidence_error"] = str(error)
            environment_record["outcome"] = "failed"
            overall_status = "failed"
        if result_json.is_file():
            try:
                environment_record["tox_result"] = json.loads(result_json.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                environment_record["tox_result_error"] = str(error)
                environment_record["outcome"] = "failed"
                overall_status = "failed"
        else:
            environment_record["tox_result_error"] = "tox did not write the requested result JSON"
            environment_record["outcome"] = "failed"
            overall_status = "failed"
        environment_records.append(environment_record)

    evidence = {
        "schema_version": 1,
        "git_sha": args.sha,
        "job": args.job,
        "cell": args.cell,
        "outcome": overall_status,
        "environments": environment_records,
    }
    output_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_console_text(f"Environment evidence written to {output_path}")
    return 0 if overall_status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
