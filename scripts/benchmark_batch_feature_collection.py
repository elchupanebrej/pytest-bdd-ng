#!/usr/bin/env python3
"""Compare serial and spawn feature collection without a timing pass/fail gate."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest


FEATURE_NODE_ID = re.compile(r"\.(?:feature|gherkin)(?:\.md)?::")


def _collect(project_root: Path, feature_root: Path, threshold: int) -> tuple[float, list[str]]:
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH", "")
    pythonpath_parts = [str(project_root / "src")]
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    environment["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    environment.pop("PYTEST_ADDOPTS", None)

    command = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "pytest_cuke.plugin",
        "--rootdir",
        str(feature_root.parent),
        "--collect-only",
        "-q",
        "--cuke-autoload",
        "--cuke-features-dir=features",
        f"--cuke-batch-threshold={threshold}",
        str(feature_root),
    ]
    started = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=feature_root.parent,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise RuntimeError(f"collection exited {result.returncode}:\n{result.stdout}\n{result.stderr}")
    node_ids = [line.strip() for line in result.stdout.splitlines() if FEATURE_NODE_ID.search(line)]
    return elapsed, node_ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", type=int, default=100, help="number of generated feature files (default: 100)")
    parser.add_argument("--repeats", type=int, default=3, help="paired measurements per strategy (default: 3)")
    arguments = parser.parse_args()
    if arguments.files < 1 or arguments.repeats < 1:
        parser.error("--files and --repeats must both be positive")

    project_root = Path(__file__).resolve().parents[1]
    serial_samples: list[float] = []
    batch_samples: list[float] = []
    with tempfile.TemporaryDirectory(prefix="pytest-cuke-batch-benchmark-") as temporary_root:
        consumer_root = Path(temporary_root)
        feature_root = consumer_root / "features"
        feature_root.mkdir()
        (consumer_root / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\ncuke_autoload = true\ncuke_features_dir = 'features'\n",
            encoding="utf-8",
        )
        for index in range(arguments.files):
            (feature_root / f"benchmark-{index:05d}.feature").write_text(
                f"Feature: Benchmark {index}\n  Scenario: Scenario {index}\n",
                encoding="utf-8",
            )

        expected_ids: list[str] | None = None
        for _ in range(arguments.repeats):
            serial_seconds, serial_ids = _collect(project_root, feature_root, arguments.files + 1)
            batch_seconds, batch_ids = _collect(project_root, feature_root, 1)
            if expected_ids is None:
                expected_ids = serial_ids
            if serial_ids != batch_ids or serial_ids != expected_ids:
                raise RuntimeError("serial and batch collection produced different scenario identities")
            serial_samples.append(serial_seconds)
            batch_samples.append(batch_seconds)

        print(
            json.dumps(
                {
                    "feature_files": arguments.files,
                    "scenario_items": len(expected_ids or []),
                    "repeats": arguments.repeats,
                    "environment": {
                        "python": platform.python_version(),
                        "implementation": platform.python_implementation(),
                        "platform": platform.platform(),
                        "cpu_count": os.cpu_count(),
                        "pytest": pytest.__version__,
                        "aiofiles_available": importlib.util.find_spec("aiofiles") is not None,
                    },
                    "strategies": {
                        "serial": {"threshold": arguments.files + 1, "seconds": serial_samples},
                        "spawn_batch": {"threshold": 1, "seconds": batch_samples},
                    },
                    "serial_median_seconds": statistics.median(serial_samples),
                    "batch_median_seconds": statistics.median(batch_samples),
                    "timing_gate": False,
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
