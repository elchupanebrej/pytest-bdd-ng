"""Distribution artifacts must contain every runtime namespace package."""

from __future__ import annotations

import subprocess
import shutil
import tarfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


def test_sdist_contains_runtime_namespace_packages(tmp_path: Path) -> None:
    """
    Verify a source distribution contains runtime namespace packages.

    Test target:
        Ensure the published source distribution can load all runtime plugin and compatibility modules.
    Test type:
        Contract test
    Test scenario:
        Given a source distribution is built, when its archive contents are inspected, then runtime namespace
        packages are present.
    BDD reference:
        None
    Fixtures:
        - tmp_path: Isolated output directory for the generated archive.
    Mocks:
        - None
    Side effects:
        Builds a temporary source distribution outside the repository tree.
    Reduction:
        The archive contents are the smallest seam that reproduces installation-time import failures.
    Escalation:
        Testing only the editable checkout would miss packaging omissions.
    Atomicity:
        The assertions cover one coherent distribution contract.
    Autonomy:
        No sibling test verifies runtime namespace package inclusion in the sdist.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=2
        #test-eval:assertions_clarity=5
    """
    uv_path = shutil.which("uv")
    assert uv_path is not None  # pylint: disable=S101  # test environment contract

    subprocess.run(
        [uv_path, "build", "--sdist", "--out-dir", str(tmp_path)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    archive = next(tmp_path.glob("*.tar.gz"))
    with tarfile.open(archive, "r:gz") as source_distribution:
        members = set(source_distribution.getnames())

    assert any(name.endswith("/src/pytest_bdd/compatibility/parser.py") for name in members)
    assert any(name.endswith("/src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py") for name in members)
    assert any(name.endswith("/src/pytest_bdd/util/other.py") for name in members)


def test_tox_exposes_source_tree_for_test_support_packages() -> None:
    """
    Verify tox can import the source-only test support package after sdist installation.

    Test target:
        Keep tox collection able to load tests that are intentionally excluded from the product distribution.
    Test type:
        Contract test
    Test scenario:
        Given tox installs only the product sdist, when it collects repository tests, then the source tree is on the
        import path for test support packages.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None.
    Reduction:
        The tox environment contract is the smallest seam that reproduces collection-time test-support imports.
    Escalation:
        An end-to-end tox run would add setup time without changing this configuration assertion.
    Atomicity:
        The assertion covers the source-path contract for tox.
    Autonomy:
        No sibling test verifies test-support importability from tox.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    tox_text = (REPO_ROOT / "tox.ini").read_text(encoding="utf-8")

    assert "PYTHONPATH = {tox_root}/src" in tox_text
