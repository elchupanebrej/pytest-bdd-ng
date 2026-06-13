"""

Debug MCP option and discovery tests.
"""

from __future__ import annotations

import json
from pathlib import Path

from pytest_bdd.plugin.debug_mcp import entrypoint as debug_mcp_entrypoint
from pytest_bdd.plugin.debug_mcp.state import DebugMcpState


def _run_debug_mcp(testdir, *args, ini: str = ""):
    testdir.monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    if ini:
        testdir.makeini(f"[pytest]\n{ini}")
    testdir.makepyfile(
        test_sample="""\
        def test_passes():
            assert True
        """,
    )
    return testdir.runpytest_inprocess(*args, plugins=[debug_mcp_entrypoint])


def _session_json(testdir) -> dict[str, object]:
    path = Path(str(testdir.tmpdir)) / ".pytest_cache" / "mcp-pdb" / "session.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_debug_mcp_is_inert_by_default(testdir) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    result = _run_debug_mcp(testdir)

    assert result.ret == 0
    assert not (Path(str(testdir.tmpdir)) / ".pytest_cache" / "mcp-pdb" / "session.json").exists()


def test_debug_mcp_registers_enable_option_without_legacy_alias(testdir) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    enabled = _run_debug_mcp(testdir, "--mcp-pdb-on-fail")
    assert enabled.ret == 0

    legacy = _run_debug_mcp(testdir, "--mcp-pdb")
    assert legacy.ret != 0
    legacy.stderr.fnmatch_lines(["*unrecognized arguments: --mcp-pdb*"])


def test_debug_mcp_writes_fixed_port_session_discovery(testdir) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    result = _run_debug_mcp(testdir, "--mcp-pdb-on-fail", "--mcp-pdb-port=43210")

    assert result.ret == 0
    discovery = _session_json(testdir)
    assert discovery["status"] == "waiting_for_failure"
    assert discovery["host"] == "127.0.0.1"
    assert discovery["mcp_pdb"] == {"host": "127.0.0.1", "port": 43210}
    assert discovery["sidecar"]["host"] == "127.0.0.1"
    assert isinstance(discovery["sidecar"]["port"], int)
    assert discovery["active_failure"] is None
    result.stdout.fnmatch_lines(["*debug-mcp session * mcp-pdb=127.0.0.1:43210 sidecar=127.0.0.1:*"])


def test_debug_mcp_allocates_port_when_missing(testdir) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    result = _run_debug_mcp(testdir, ini="mcp_pdb_on_fail = true\n")

    assert result.ret == 0
    discovery = _session_json(testdir)
    assert discovery["mcp_pdb"]["host"] == "127.0.0.1"
    assert isinstance(discovery["mcp_pdb"]["port"], int)
    assert discovery["mcp_pdb"]["port"] > 0


def test_debug_mcp_warns_for_public_host(testdir) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    result = _run_debug_mcp(testdir, "--mcp-pdb-on-fail", "--mcp-pdb-host=0.0.0.0")

    assert result.ret == 0
    result.stdout.fnmatch_lines(["*trusted environment warning*non-local host*"])


def test_debug_mcp_stores_state_in_config_stash(testdir) -> None:
    """
    Test target:
    Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
    testdir.monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    testdir.makeconftest(
        """\
        from pytest_bdd.plugin.debug_mcp.state import DebugMcpState


        def pytest_sessionfinish(session):
            state = DebugMcpState.from_stash(session.config.stash)
            assert state.options.enabled is True
            assert state.mcp_pdb_endpoint.port == 43211
        """,
    )
    testdir.makepyfile(
        test_sample="""\
        def test_passes():
            assert True
        """,
    )

    result = testdir.runpytest_inprocess("--mcp-pdb-on-fail", "--mcp-pdb-port=43211", plugins=[debug_mcp_entrypoint])

    assert result.ret == 0


def test_debug_mcp_rejects_invalid_port(testdir) -> None:
    """
    Test target:
    Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
    Integration test
    Test scenario:
    Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
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
    result = _run_debug_mcp(testdir, "--mcp-pdb-on-fail", "--mcp-pdb-port=70000")

    assert result.ret != 0
    result.stderr.fnmatch_lines(["*mcp_pdb_port must be an integer from 1 to 65535*"])
    assert DebugMcpState.STASH_KEY == "pytest_bdd.debug_mcp.state"
