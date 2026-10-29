"""Batch controls exercised by installed pytest consumers."""
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("arguments,spawned", [
    (["--cuke-batch-threshold=1"], True),
    (["--cuke-batch-threshold=1", "--cuke-disable-batch-collection"], False),
    (["--cuke-batch-threshold=1", "-o", "cuke_disable_batch_collection=true"], False),
    (["-o", "cuke_batch_threshold=0"], False),
    (["-o", "cuke_batch_threshold=-1"], False),
])
def test_batch_controls(tmp_path, arguments, spawned):
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    features = tmp_path / "features"
    features.mkdir()
    for name in ("first", "second"):
        (features / (name + ".feature")).write_text(
            "Feature: " + name + "\n  Scenario: smoke\n    Given a passing step\n"
        )
    (tmp_path / "conftest.py").write_text(
        "from pathlib import Path\nimport multiprocessing\nfrom pytest_cuke import given\n"
        "_get_context = multiprocessing.get_context\n"
        "def observe_context(method=None):\n"
        "    Path('spawn-observed').write_text(str(method))\n"
        "    return _get_context(method)\n"
        "multiprocessing.get_context = observe_context\n"
        "@given('a passing step')\ndef passing(): pass\n"
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "features", "--cuke-parser=python",
         "--confcutdir=.", "-c", "pytest.ini", "-q", *arguments],
        cwd=tmp_path, capture_output=True, text=True, timeout=90, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 passed" in result.stdout
    assert (tmp_path / "spawn-observed").exists() is spawned


@pytest.mark.parametrize("arguments", [
    ["--cuke-batch-threshold=0"], ["--cuke-batch-threshold=-1"],
    ["-o", "cuke_batch_threshold=invalid"],
])
def test_invalid_threshold_is_usage_error(tmp_path, arguments):
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--confcutdir=.", "-c", "pytest.ini", *arguments],
        cwd=tmp_path, capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 4, result.stdout + result.stderr
    assert "INTERNALERROR" not in result.stdout + result.stderr
