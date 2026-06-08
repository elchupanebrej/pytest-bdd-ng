"""Debug MCP option and discovery tests."""

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
    result = _run_debug_mcp(testdir)

    assert result.ret == 0
    assert not (Path(str(testdir.tmpdir)) / ".pytest_cache" / "mcp-pdb" / "session.json").exists()


def test_debug_mcp_registers_enable_option_without_legacy_alias(testdir) -> None:
    enabled = _run_debug_mcp(testdir, "--mcp-pdb-on-fail")
    assert enabled.ret == 0

    legacy = _run_debug_mcp(testdir, "--mcp-pdb")
    assert legacy.ret != 0
    legacy.stderr.fnmatch_lines(["*unrecognized arguments: --mcp-pdb*"])


def test_debug_mcp_writes_fixed_port_session_discovery(testdir) -> None:
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
    result = _run_debug_mcp(testdir, ini="mcp_pdb_on_fail = true\n")

    assert result.ret == 0
    discovery = _session_json(testdir)
    assert discovery["mcp_pdb"]["host"] == "127.0.0.1"
    assert isinstance(discovery["mcp_pdb"]["port"], int)
    assert discovery["mcp_pdb"]["port"] > 0


def test_debug_mcp_warns_for_public_host(testdir) -> None:
    result = _run_debug_mcp(testdir, "--mcp-pdb-on-fail", "--mcp-pdb-host=0.0.0.0")

    assert result.ret == 0
    result.stdout.fnmatch_lines(["*trusted environment warning*non-local host*"])


def test_debug_mcp_stores_state_in_config_stash(testdir) -> None:
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
    result = _run_debug_mcp(testdir, "--mcp-pdb-on-fail", "--mcp-pdb-port=70000")

    assert result.ret != 0
    result.stderr.fnmatch_lines(["*mcp_pdb_port must be an integer from 1 to 65535*"])
    assert DebugMcpState.STASH_KEY == "pytest_bdd.debug_mcp.state"
