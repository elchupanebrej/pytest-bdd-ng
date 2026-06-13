"""

Provide test startup imports helpers.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path


def _assert_import_does_not_load(module: str, blocked_modules: tuple[str, ...]) -> None:
    code = textwrap.dedent(
        f"""
        import importlib
        import sys

        before = set(sys.modules)
        importlib.import_module({module!r})
        loaded = [
            name
            for name in {blocked_modules!r}
            if name in sys.modules and name not in before
        ]
        if loaded:
            raise SystemExit("loaded blocked modules: " + ", ".join(loaded))
        """,
    )
    env = os.environ.copy()
    src_path = str((Path(__file__).resolve().parents[5] / "src").resolve())
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [src_path, env.get("PYTHONPATH")]))
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_message_validation_import_does_not_build_schema_validator_dependencies() -> None:
    """
    Verify message validation import does not build schema validator dependencies.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    _assert_import_does_not_load(
        "pytest_bdd.model.message_validation",
        ("jsonschema", "referencing"),
    )


def test_scenario_locator_import_does_not_load_url_fetch_dependencies() -> None:
    """
    Verify scenario locator import does not load url fetch dependencies.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    _assert_import_does_not_load(
        "pytest_bdd.scenario_locator",
        ("aiohttp", "certifi"),
    )
