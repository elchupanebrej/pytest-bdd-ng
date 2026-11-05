from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="coverage-child-consumer-", dir=os.environ.get("PROOF_TMP", "/tmp/opencode")))
DIST = WORK / "dist"
INSTRUMENTED = WORK / "venv-instrumented"
UNINSTRUMENTED = WORK / "venv-uninstrumented"
CONSUMER = WORK / "consumer"
DRIVER = WORK / "driver"
COVERAGE_PIN = "coverage==7.17.1"
UV = shutil.which("uv")
WINDOWS_GIT = Path("/mnt/c/Program Files/Git/bin/git.exe")
GIT = str(WINDOWS_GIT) if WINDOWS_GIT.is_file() else shutil.which("git")


def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "COVERAGE_FILE",
        "COVERAGE_PROCESS_START",
        "COVERAGE_PROCESS_CONFIG",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    ):
        env.pop(name, None)
    return env


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(
    cmd: list[object],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    quiet: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    rendered = [str(part) for part in cmd]
    print("$ " + " ".join(rendered), flush=True)
    result = subprocess.run(rendered, cwd=cwd, env=env, capture_output=True, text=True)
    if result.stdout and not quiet:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n", flush=True)
    if result.stderr and not quiet:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr, flush=True)
    if check and result.returncode != 0:
        raise SystemExit(f"command failed with exit {result.returncode}: {' '.join(rendered)}")
    return result


def coverage_env(base: Path) -> dict[str, str]:
    env = clean_env()
    env["COVERAGE_FILE"] = str(base)
    return env


def coverage_config(base: Path) -> Path:
    config = CONSUMER / "cov.ini"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "[run]\n"
        "patch = subprocess\n"
        "parallel = true\n"
        "branch = true\n"
        "source = pytest_cuke\n"
        f"data_file = {base}\n"
        "\n"
        "[report]\n"
        "precision = 2\n",
        encoding="utf-8",
    )
    return config


def write_consumer() -> None:
    parent_dir = CONSUMER / "parent"
    child_dir = CONSUMER / "child"
    parent_dir.mkdir(parents=True)
    child_dir.mkdir(parents=True)
    (CONSUMER / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ntestpaths = ['parent']\n", encoding="utf-8"
    )
    (parent_dir / "test_parent.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "import os\n"
        "import re\n"
        "import subprocess\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "CONSUMER = Path(__file__).resolve().parents[1]\n"
        "CHILD = CONSUMER / 'child'\n"
        "\n"
        "\n"
        "def run_child(name: str, expected: int) -> None:\n"
        "    script = CHILD / name\n"
        "    result = subprocess.run(\n"
        "        [sys.executable, '-m', 'pytest', '-q', '-s', '-p', 'no:cacheprovider', str(script)],\n"
        "        cwd=str(CHILD),\n"
        "        env=os.environ.copy(),\n"
        "        capture_output=True,\n"
        "        text=True,\n"
        "    )\n"
        "    sys.stdout.write(result.stdout)\n"
        "    sys.stderr.write(result.stderr)\n"
        "    match = re.search(r'^CHILD_PID=(\\d+)$', result.stdout, re.MULTILINE)\n"
        "    if match:\n"
        "        (CONSUMER / f'{name}.pid').write_text(match.group(1), encoding='utf-8')\n"
        "    assert result.returncode == expected, (result.returncode, expected, result.stdout, result.stderr)\n"
        "\n"
        "\n"
        "def test_parent_launches_passing_child() -> None:\n"
        "    print(f'OUTER_PID={os.getpid()}')\n"
        "    run_child('test_pass.py', 0)\n"
        "\n"
        "\n"
        "def test_parent_preserves_failing_child_exit() -> None:\n"
        "    run_child('test_fail.py', 1)\n",
        encoding="utf-8",
    )
    (child_dir / "test_pass.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "import os\n"
        "\n"
        "from pytest_cuke import parsers\n"
        "\n"
        "\n"
        "def test_child_exclusive_product_line() -> None:\n"
        "    print(f'CHILD_PID={os.getpid()}')\n"
        "    parser = parsers.parse('the number is {number:d}')\n"
        "    assert parser.parse_arguments(None, 'the number is 7') == {'number': 7}\n",
        encoding="utf-8",
    )
    (child_dir / "test_fail.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "import os\n"
        "\n"
        "\n"
        "def test_intentional_child_failure() -> None:\n"
        "    print(f'CHILD_PID={os.getpid()}')\n"
        "    assert False, 'intentional child failure'\n",
        encoding="utf-8",
    )
    (DRIVER).mkdir()
    (DRIVER / "driver.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "import os\n"
        "import subprocess\n"
        "import sys\n"
        "\n"
        "child = os.environ['UNINSTRUMENTED_CHILD']\n"
        "python = os.environ['UNINSTRUMENTED_PYTHON']\n"
        "process = subprocess.Popen(\n"
        "    [python, '-m', 'pytest', '-q', '-s', '-p', 'no:cacheprovider', child],\n"
        "    cwd=os.path.dirname(child),\n"
        "    env=os.environ.copy(),\n"
        "    stdout=subprocess.PIPE,\n"
        "    stderr=subprocess.PIPE,\n"
        "    text=True,\n"
        ")\n"
        "out, err = process.communicate()\n"
        "sys.stdout.write(out)\n"
        "sys.stderr.write(err)\n"
        "print(f'UNINSTRUMENTED_CHILD_PID={process.pid}')\n"
        "sys.exit(process.returncode)\n",
        encoding="utf-8",
    )


def fragment_pid(fragment: Path) -> int | None:
    match = re.search(r"\.pid(\d+)\.", fragment.name)
    return int(match.group(1)) if match else None


def fragment_for(fragments: list[Path], pid: int) -> Path | None:
    return next((fragment for fragment in fragments if fragment_pid(fragment) == pid), None)


def json_for_fragment(python: Path, config: Path, fragment: Path, label: str) -> dict[str, object]:
    probe = WORK / "probes" / label
    probe.mkdir(parents=True)
    copied = probe / fragment.name
    shutil.copy2(fragment, copied)
    base = probe / ".coverage"
    env = coverage_env(base)
    run([python, "-m", "coverage", "combine", "--rcfile", str(config), str(copied)], cwd=probe, env=env)
    output = probe / "data.json"
    run([python, "-m", "coverage", "json", "--rcfile", str(config), "-o", str(output)], cwd=probe, env=env)
    return json.loads(output.read_text(encoding="utf-8"))


def product_entry(data: dict[str, object], suffix: str) -> tuple[str, dict[str, object]] | None:
    files = data["files"]
    assert isinstance(files, dict)
    for path, entry in files.items():
        if path.replace("\\", "/").endswith(suffix):
            assert isinstance(entry, dict)
            return path, entry
    return None


def main() -> int:
    if not UV:
        raise SystemExit("uv is required")
    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 or newer is required")

    print(f"WORK={WORK}")
    git_repo = str(REPO)
    if GIT and GIT.endswith(".exe"):
        git_repo = subprocess.run(["wslpath", "-w", str(REPO)], capture_output=True, text=True, check=True).stdout.strip()
    revision = subprocess.run(
        [GIT, "-C", git_repo, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    branch = subprocess.run(
        [GIT, "-C", git_repo, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    token = f"{revision[:12]}-installed-child-{secrets.token_hex(6)}"
    print(f"BRANCH={branch}")
    print(f"REVISION={revision}")
    print(f"TOKEN={token}")

    DIST.mkdir()
    build_env = clean_env()
    build_env["PYTEST_CUKE_BUILD_GO"] = "off"
    run([UV, "build", "--wheel", "--out-dir", DIST, REPO], cwd=REPO, env=build_env, quiet=True)
    wheels = list(DIST.glob("pytest_cuke-*.whl"))
    assert len(wheels) == 1, wheels
    wheel = wheels[0]
    print(f"WHEEL={wheel}")

    for venv in (INSTRUMENTED, UNINSTRUMENTED):
        run([UV, "venv", "--python", sys.executable, venv])
    ipy = venv_python(INSTRUMENTED)
    upy = venv_python(UNINSTRUMENTED)
    run([UV, "pip", "install", "--python", ipy, wheel, COVERAGE_PIN, "pytest"], quiet=True)
    run([UV, "pip", "install", "--python", upy, wheel, "pytest"], quiet=True)

    write_consumer()

    installed = run(
        [ipy, "-c", "import pathlib, pytest_cuke; print(pathlib.Path(pytest_cuke.__file__).resolve())"],
        cwd=CONSUMER,
    ).stdout.strip()
    installed_path = Path(installed)
    print(f"INSTALLED_PRODUCT={installed_path}")
    assert INSTRUMENTED.resolve() in installed_path.parents, installed_path
    assert REPO.resolve() not in installed_path.parents, installed_path

    missing = run(
        [upy, "-c", "import importlib.util; print(importlib.util.find_spec('coverage'))"],
        cwd=CONSUMER,
    ).stdout.strip()
    print(f"UNINSTRUMENTED_COVERAGE_SPEC={missing}")
    assert missing == "None", missing

    base = CONSUMER / f".coverage.{token}"
    config = coverage_config(base)
    env = coverage_env(base)
    outer = run(
        [ipy, "-m", "coverage", "run", "--rcfile", str(config), "-m", "pytest", "-q", "-s", str(CONSUMER / "parent")],
        cwd=CONSUMER,
        env=env,
    )

    raw_fragments = sorted(CONSUMER.glob(f"{base.name}.*"))
    safe_dir = WORK / "fragments"
    safe_dir.mkdir()
    fragments = [Path(shutil.copy2(fragment, safe_dir / fragment.name)) for fragment in raw_fragments]
    for fragment in fragments:
        print(f"FRAGMENT={fragment.name} pid={fragment_pid(fragment)}")
    pass_pid = int((CONSUMER / "test_pass.py.pid").read_text(encoding="utf-8"))
    fail_pid = int((CONSUMER / "test_fail.py.pid").read_text(encoding="utf-8"))
    pass_fragment = fragment_for(fragments, pass_pid)
    fail_fragment = fragment_for(fragments, fail_pid)
    assert pass_fragment is not None, (pass_pid, [f.name for f in fragments])
    assert fail_fragment is not None, (fail_pid, [f.name for f in fragments])
    print(f"CHILD_PASS_PID={pass_pid}")
    print(f"CHILD_FAIL_PID={fail_pid}")

    run([ipy, "-m", "coverage", "combine", "--rcfile", str(config), "--keep"], cwd=CONSUMER, env=env)
    combined_json = CONSUMER / "combined.json"
    run([ipy, "-m", "coverage", "json", "--rcfile", str(config), "-o", str(combined_json)], cwd=CONSUMER, env=env)
    combined = json.loads(combined_json.read_text(encoding="utf-8"))
    combined_entry = product_entry(combined, "pytest_cuke/parsers/parse_parser.py")
    assert combined_entry is not None, sorted(combined["files"])
    combined_path, combined_data = combined_entry

    source = installed_path.parent / "parsers" / "parse_parser.py"
    source_lines = source.read_text(encoding="utf-8").splitlines()
    target_line = 1 + next(
        index for index, line in enumerate(source_lines) if "res = dict(match.named)" in line
    )
    combined_lines = set(combined_data["executed_lines"])
    print(f"PRODUCT_FILE={combined_path}")
    print(f"CHILD_EXCLUSIVE_LINE={target_line}")
    print(f"COMBINED_HAS_LINE={target_line in combined_lines}")
    assert target_line in combined_lines

    parent_match = re.search(r"OUTER_PID=(\d+)", outer.stdout)
    assert parent_match, outer.stdout
    parent_pid = int(parent_match.group(1))

    parent_fragment = fragment_for(fragments, parent_pid)
    assert parent_fragment is not None, (parent_pid, [f.name for f in fragments])
    parent_probe = json_for_fragment(ipy, config, parent_fragment, "parent")
    child_probe = json_for_fragment(ipy, config, pass_fragment, "child-pass")
    parent_entry = product_entry(parent_probe, "pytest_cuke/parsers/parse_parser.py")
    child_entry = product_entry(child_probe, "pytest_cuke/parsers/parse_parser.py")
    parent_has_line = parent_entry is not None and target_line in set(parent_entry[1]["executed_lines"])
    child_has_line = child_entry is not None and target_line in set(child_entry[1]["executed_lines"])
    print(f"PARENT_HAS_LINE={parent_has_line}")
    print(f"CHILD_HAS_LINE={child_has_line}")
    assert not parent_has_line, "parent fragment unexpectedly executed the child-exclusive line"
    assert child_has_line, "child fragment did not execute the child-exclusive line"

    uninstrumented_base = CONSUMER / f".coverage.{token}-uninstrumented"
    uninstrumented_config = coverage_config(uninstrumented_base)
    uninstrumented_env = coverage_env(uninstrumented_base)
    uninstrumented_env["UNINSTRUMENTED_CHILD"] = str(CONSUMER / "child" / "test_pass.py")
    uninstrumented_env["UNINSTRUMENTED_PYTHON"] = str(upy)
    driver_result = run(
        [ipy, "-m", "coverage", "run", "--rcfile", str(uninstrumented_config), str(DRIVER / "driver.py")],
        cwd=DRIVER,
        env=uninstrumented_env,
    )
    uninstrumented_raw = sorted(CONSUMER.glob(f"{uninstrumented_base.name}.*"))
    uninstrumented_safe = WORK / "fragments-uninstrumented"
    uninstrumented_safe.mkdir()
    uninstrumented_fragments = [
        Path(shutil.copy2(fragment, uninstrumented_safe / fragment.name)) for fragment in uninstrumented_raw
    ]
    for fragment in uninstrumented_fragments:
        print(f"UNINSTRUMENTED_FRAGMENT={fragment.name} pid={fragment_pid(fragment)}")
    match = re.search(r"UNINSTRUMENTED_CHILD_PID=(\d+)", driver_result.stdout)
    assert match, driver_result.stdout
    uninstrumented_child_pid = int(match.group(1))
    uninstrumented_child_fragment = fragment_for(uninstrumented_fragments, uninstrumented_child_pid)
    print(f"UNINSTRUMENTED_CHILD_PID={uninstrumented_child_pid}")
    print(f"UNINSTRUMENTED_CHILD_FRAGMENT={uninstrumented_child_fragment}")
    run(
        [ipy, "-m", "coverage", "combine", "--rcfile", str(uninstrumented_config), "--keep"],
        cwd=CONSUMER,
        env=uninstrumented_env,
    )
    uninstrumented_json = CONSUMER / "uninstrumented.json"
    uninstrumented_report = run(
        [ipy, "-m", "coverage", "json", "--rcfile", str(uninstrumented_config), "-o", str(uninstrumented_json)],
        cwd=CONSUMER,
        env=uninstrumented_env,
        check=False,
    )
    print(f"UNINSTRUMENTED_JSON_EXIT={uninstrumented_report.returncode}")
    if uninstrumented_report.returncode == 0:
        uninstrumented_data = json.loads(uninstrumented_json.read_text(encoding="utf-8"))
        uninstrumented_product = product_entry(uninstrumented_data, "pytest_cuke/parsers/parse_parser.py")
    else:
        uninstrumented_product = None
    diagnosis = "measurement_gap" if uninstrumented_child_fragment is None else "silently_passed"
    gate_exit = 2 if diagnosis == "measurement_gap" else 0
    print(f"UNINSTRUMENTED_PRODUCT_EVIDENCE={uninstrumented_product is not None}")
    print(f"DIAGNOSIS={diagnosis}")
    print(f"GATE_EXIT_IF_ENFORCED={gate_exit}")
    assert uninstrumented_child_fragment is None, "uninstrumented child unexpectedly produced a fragment"
    assert uninstrumented_product is None, "uninstrumented child unexpectedly produced product evidence"
    assert diagnosis == "measurement_gap"

    print("RESULT=proof_observed")
    print(f"WORK={WORK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
