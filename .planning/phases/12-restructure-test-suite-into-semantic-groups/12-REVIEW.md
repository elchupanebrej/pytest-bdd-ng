---
phase: 12
phase_name: restructure-test-suite-into-semantic-groups
status: findings
files_reviewed: 17
depth: standard
reviewed_at: "2026-05-19"
findings:
  critical: 0
  warning: 5
  info: 6
  total: 11
---

# Code Review — Phase 12: Restructure Test Suite into Semantic Groups

## Summary

17 files reviewed at **standard** depth. No critical (blocking) bugs found. Five warnings
requiring attention; six informational notes. Overall code quality is high — the phase
delivered a clean semantic classification structure.

---

## Findings

### WR-001 — `docker_cluster.py`: Module-level singleton `cluster_manager` leaks across test sessions

**File:** `src/pytest_bdd/testing/docker_cluster.py` · **Line:** 292
**Severity:** Warning

`cluster_manager = DockerClusterManager()` is instantiated at import time. `atexit.register(self.cleanup)` is called in `__init__`, meaning every test process that imports this module registers an atexit hook. In pytest this can fire during teardown of a completely different test session or when collected via `--collect-only`, potentially tearing down clusters that are still needed.

**Fix:** Lazy-initialize the singleton behind a function; only register `atexit` when `get_cluster` is first called.

```python
# Before
cluster_manager = DockerClusterManager()

# After
_cluster_manager: DockerClusterManager | None = None

def get_cluster_manager() -> DockerClusterManager:
    global _cluster_manager
    if _cluster_manager is None:
        _cluster_manager = DockerClusterManager()
    return _cluster_manager
```

Update all call sites from `cluster_manager.<method>` → `get_cluster_manager().<method>`.

---

### WR-002 — `docker_cluster.py`: `_run_wsl_cmd` passes `env` to both `subprocess.run` kwarg and the inline `env` prepend — double-injection risk

**File:** `src/pytest_bdd/testing/docker_cluster.py` · **Lines:** 43–53
**Severity:** Warning

```python
env_overrides = [f"{key}={value}" for key, value in env.items() if os.environ.get(key) != value]
if env_overrides:
    command_args = ["env", *env_overrides, *command_args]
return subprocess.run([wsl_bin, "-d", "Alpine", "--", *command_args], ..., env=env)
```

The `env` dict is passed **both** as `subprocess.run(env=env)` (which sets the child process environment) and as shell `env KEY=VALUE …` prepend inside WSL. For keys already in `env`, the WSL `env` call is a no-op, but the filter `os.environ.get(key) != value` uses the *outer* `os.environ`, not the `env` dict that subprocess will actually see. If `env` differs from `os.environ` for a key, the override check may silently skip injecting it.

**Fix:** Compare against `os.environ` only for keys *not* already in `env`, or remove the `env` subprocess kwarg when using the shell-level `env` prepend (WSL inherits the caller's environment by default).

---

### WR-003 — `docker.py`: `docker_daemon_available` cache not invalidated before probe in `require_docker_daemon`

**File:** `src/pytest_bdd/testing/docker.py` · **Lines:** 219–222
**Severity:** Warning

```python
cache_clear = getattr(docker_daemon_available, "cache_clear", None)
if callable(cache_clear):
    cache_clear()
available, backend = docker_daemon_available()
```

`require_docker_daemon` deliberately clears `lru_cache` before probing, but this means every call to `require_docker_daemon()` re-runs a full docker probe (potentially spawning subprocesses). In a session with many docker-gated tests this adds significant overhead.

**Fix:** Clear only when necessary (e.g., only on first fixture request per session). Consider a session-scoped pytest fixture that calls `require_docker_daemon` once and stores the result, rather than clearing the cache on every call.

---

### WR-004 — `conftest.py` (e2e): Hardcoded `tests/e2e/` relative import in `_run_remote_xdist`

**File:** `tests/cases/e2e/conftest.py` · **Line:** 248
**Severity:** Warning

```python
from tests.cases.external.e2e.test_xdist_remote_message_aggregation import (
    _run_remote_xdist_compose,
)
```

Importing a private symbol (`_run_remote_xdist_compose`) from a test module couples conftest to internal implementation. If `test_xdist_remote_message_aggregation.py` is restructured or the private helper renamed, this import silently breaks.

**Fix:** Extract `_run_remote_xdist_compose` into a helper module in `src/pytest_bdd/testing/` or `tests/assets/` so the API is stable and intentionally shared.

---

### WR-005 — `cucumber_formatters.py`: `install_formatter_hook_registry` returns the pluginmanager but signature says nothing (no return type annotation)

**File:** `src/pytest_bdd/testing/cucumber_formatters.py` · **Lines:** 409–445
**Severity:** Warning

The function creates a `_HookProxy` instance, attaches it to `config.pluginmanager.hook`, and returns `pluginmanager`. The return type is not annotated. More importantly, if `config` already has a real `pluginmanager` (which will have a real `hook`), replacing `pluginmanager.hook` with `_HookProxy()` silently discards all other hooks registered on the real pluginmanager. This is safe in test harnesses but dangerous if called outside of a fully mocked context.

**Fix:** Add `-> SimpleNamespace` return annotation. Add a guard or assertion that `config` is a test-only object (e.g., `assert not isinstance(pluginmanager, pluggy.PluginManager)`).

---

### IN-001 — `pytest_results.py`: `attach_command_result_outputs` docstring placed after code body

**File:** `src/pytest_bdd/testing/pytest_results.py` · **Lines:** 37–41
**Severity:** Info

```python
def attach_command_result_outputs(...) -> None:
    # Nested pytest/docker helper runs are harness diagnostics...
    """Handle attach command result outputs."""
```

The module-level comment precedes the docstring, which inverts the conventional ordering (docstring first, then implementation comments). The docstring `"""Handle attach command result outputs."""` is also not descriptive — it merely restates the function name.

**Suggested fix:**
```python
def attach_command_result_outputs(...) -> None:
    """Attach subprocess/pytester result streams as Cucumber Attachment envelopes.

    Keeps nested pytest/docker diagnostics out of the primary terminal reporter
    so the outer cucumber formatter remains the only writer during test execution.
    """
```

---

### IN-002 — `message_stream_assertions.py`: `unfold_message` iterates `UNFOLDABLE_ATTRS` but raises `ValueError` on empty envelope — no distinction between truly empty and unknown attribute

**File:** `tests/cases/contract/messages/message_stream_assertions.py` · **Lines:** 54–67
**Severity:** Info

If a new envelope type is added to `cucumber_messages` but not added to `UNFOLDABLE_ATTRS`, `unfold_message` raises `ValueError: Empty envelope was given` with no hint about the unknown attribute. This makes debugging new protocol additions harder.

**Suggested fix:** Inspect unknown non-None attributes and include them in the error:
```python
unknown = [attr for attr in dir(message) if not attr.startswith("_") and attr not in UNFOLDABLE_ATTRS and getattr(message, attr) is not None]
if unknown:
    raise ValueError(f"Unknown envelope attributes: {unknown}. Update UNFOLDABLE_ATTRS.")
raise ValueError("Empty envelope was given")
```

---

### IN-003 — `worker.Dockerfile`: Uses `python:3.14-slim` (pre-release at time of writing) — may introduce instability

**File:** `tests/assets/docker/remote_xdist/worker.Dockerfile` · **Line:** 1
**Severity:** Info

`python:3.14-slim` may be a release candidate / pre-release image. Pre-release images can change their package availability or behaviour. Prefer pinning to a concrete digest (`python:3.14-slim@sha256:…`) or using the latest stable release if 3.14 is not yet GA.

---

### IN-004 — `test_e2e.py`: `pytest_plugins` uses string module paths (`"tests.e2e.steps_*"`) referencing a `tests/e2e/` tree

**File:** `tests/cases/e2e/e2e/test_e2e.py` · **Lines:** 237–248
**Severity:** Info

```python
pytest_plugins = [
    "tests.e2e.steps_go_parser",
    ...
]
```

`tests.e2e.*` is the **legacy** test path that Phase 12 is moving away from. After the restructure, these should reference `tests.cases.e2e.steps_*` to remain consistent with the new semantic tree. If the legacy paths are still needed for compatibility during transition, a comment should explain when they will be removed.

---

### IN-005 — `test_e2e_loader_shape.py`: `E2E_ROOTS` includes legacy `tests/e2e/` as a fallback

**File:** `tests/cases/unit/test_e2e_loader_shape.py` · **Line:** 9
**Severity:** Info

```python
E2E_ROOTS = (REPO_ROOT / "tests" / "cases" / "e2e", REPO_ROOT / "tests" / "e2e")
```

The legacy root is still scanned. Once all tests have migrated to `tests/cases/e2e`, this fallback should be removed to prevent false negatives (tests in the legacy location would still pass the shape guard even after the migration).

---

### IN-006 — `run_messages_coverage_audit.sh`: Hardcoded fake CI metadata (GITHUB_SHA=`deadbeef…`)

**File:** `scripts/run_messages_coverage_audit.sh` · **Lines:** 25–35
**Severity:** Info

Hardcoded values like `GITHUB_SHA=deadbeefdeadbeefdeadbeefdeadbeefdeadbeef` and `GITHUB_RUN_NUMBER=42` are used as CI metadata. These are intentionally fake (the comment says "Populate CI metadata fields from real runtime environment variables"), but actual environment variables are never read — the script always exports its own hardcoded values even when run in real CI where `GITHUB_SHA` etc. are already set.

**Suggested fix:** Use parameter expansion to fall through to real env vars:
```bash
export GITHUB_RUN_NUMBER="${GITHUB_RUN_NUMBER:-42}"
export GITHUB_SHA="${GITHUB_SHA:-deadbeefdeadbeefdeadbeefdeadbeefdeadbeef}"
```

---

## Verdict

| Severity | Count |
|----------|-------|
| Critical | 0     |
| Warning  | 5     |
| Info     | 6     |
| **Total**| **11**|

No blockers. Five warnings should be addressed before this phase is closed; WR-001 (singleton atexit) and WR-004 (private cross-module import) carry the highest practical risk.
