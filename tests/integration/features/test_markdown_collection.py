"""Exercise Markdown collection through an installed plugin without Node on PATH."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("feature_path", "configured_root", "arguments", "expected_exit", "expected_outcome"),
    [
        ("doc.feature.md", None, ["doc.feature.md"], 0, "1 passed"),
        ("doc.gherkin.md", None, ["doc.gherkin.md"], 0, "1 passed"),
        ("features/doc.feature.md", None, ["features/doc.feature.md"], 0, "1 passed"),
        ("doc.feature.md", "specs/features", ["doc.feature.md"], 0, "1 passed"),
        ("specs/features/doc.feature.md", "specs/features", ["specs/features"], 0, "1 passed"),
        ("doc.feature.md", None, ["."], 5, None),
        ("doc.feature.md", None, ["--cuke-no-autoload", "doc.feature.md"], 4, "not found"),
        ("doc.feature.md", None, ["--cuke-no-autoload", "test_binding.py"], 0, "1 passed"),
    ],
)
def test_markdown_file_selection_without_node(
    tmp_path, feature_path, configured_root, arguments, expected_exit, expected_outcome
):
    config = "[pytest]\ncuke_autoload = true\ncuke_parser = python\n"
    if configured_root is not None:
        (tmp_path / configured_root).mkdir(parents=True)
        config += f"cuke_features_dir = {configured_root}\n"
    (tmp_path / "pytest.ini").write_text(config, encoding="utf-8")
    feature = tmp_path / feature_path
    feature.parent.mkdir(parents=True, exist_ok=True)
    feature.write_text(
        "# Feature: Markdown\n\n## Scenario: Selected\n* Given the sentinel executes\n", encoding="utf-8"
    )
    (tmp_path / "conftest.py").write_text(
        "from pathlib import Path\n"
        "from pytest_cuke import given\n"
        "@given('the sentinel executes', target_fixture='sentinel')\n"
        "def sentinel():\n"
        "    print('MARKDOWN-CONSUMER-SENTINEL')\n"
        "    Path('sentinel.txt').write_text('executed', encoding='utf-8')\n"
        "    return 'executed'\n",
        encoding="utf-8",
    )
    if "test_binding.py" in arguments:
        (tmp_path / "test_binding.py").write_text(
            "from pathlib import Path\n"
            "from pytest_cuke import scenario\n"
            "@scenario('doc.feature.md', 'Selected', features_base_dir='.')\n"
            "def test_selected():\n"
            "    assert Path('sentinel.txt').read_text(encoding='utf-8') == 'executed'\n",
            encoding="utf-8",
        )
    env = {**os.environ, "PATH": str(Path(sys.executable).parent)}
    assert shutil.which("npm", path=env["PATH"]) is None
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-s", "-q", "--rootdir=.", "-p", "no:cacheprovider", *arguments],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == expected_exit, output
    if expected_outcome is not None:
        assert expected_outcome in output, output
    assert ("MARKDOWN-CONSUMER-SENTINEL" in output) is (expected_exit == 0), output
