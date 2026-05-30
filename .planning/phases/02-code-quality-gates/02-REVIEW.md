---
phase: 02-code-quality-gates
reviewed: 2026-05-19T00:00:00Z
depth: standard
files_reviewed: 25
files_reviewed_list:
  - src/pytest_bdd/.ruff/rules/quality_gates.py
  - src/pytest_bdd/_ruff/rules/quality_gates.py
  - src/pytest_bdd/collector_batch.py
  - src/pytest_bdd/feature_locator.py
  - src/pytest_bdd/model/execution_message_adapter.py
  - src/pytest_bdd/model/message_capability_inventory.py
  - src/pytest_bdd/model/message_consolidation.py
  - src/pytest_bdd/model/message_extension.py
  - src/pytest_bdd/model/message_outcome_mapping.py
  - src/pytest_bdd/model/message_registry.py
  - src/pytest_bdd/model/message_transport.py
  - src/pytest_bdd/model/message_validation.py
  - src/pytest_bdd/model/scenario_run.py
  - src/pytest_bdd/model/stash_access.py
  - src/pytest_bdd/parsers.py
  - src/pytest_bdd/plugin/scenario_test_collector/entrypoint.py
  - src/pytest_bdd/plugin/scenario_test_collector/plugin.py
  - src/pytest_bdd/scenario.py
  - src/pytest_bdd/scenario_locator.py
  - src/pytest_bdd/script/bdd_tree_to_rst.py
  - src/pytest_bdd/script/validate_feature_headings.py
  - src/pytest_bdd/types/__init__.py
  - src/pytest_bdd/types/failure_reasons.py
  - src/pytest_bdd/util/tests_group_ordering.py
  - src/pytest_bdd/util/webloc.py
findings:
  critical: 0
  warning: 5
  info: 5
  total: 10
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-05-19T00:00:00Z
**Depth:** standard
**Files Reviewed:** 25
**Status:** issues_found

## Summary

Reviewed 25 source files across the `src/pytest_bdd/` directory at standard depth. No critical (security or data-loss) issues found. 5 warnings and 5 info items identified. Key concerns: event loop resource leak in `scenario_locator.py`, duplicate docstring in `parsers.py`, potentially fragile dict key access in `message_transport.py`, and a lock cleanup that can mask exceptions in `tests_group_ordering.py`.

Clean files (no issues found): `.ruff/rules/quality_gates.py`, `_ruff/rules/quality_gates.py`, `feature_locator.py`, `model/execution_message_adapter.py`, `model/message_capability_inventory.py`, `model/message_outcome_mapping.py`, `model/message_registry.py`, `model/message_validation.py`, `model/scenario_run.py`, `model/stash_access.py`, `plugin/scenario_test_collector/entrypoint.py`, `plugin/scenario_test_collector/plugin.py`, `script/bdd_tree_to_rst.py`, `script/validate_feature_headings.py`, `types/__init__.py`, `types/failure_reasons.py`, `util/webloc.py`

## Warnings

### WR-01: Event loop not closed on exception in _fetch_feature_responses

**File:** `src/pytest_bdd/scenario_locator.py:291-296`
**Issue:** The method creates a new asyncio event loop but does not wrap `run_until_complete()` in `try/finally`. If `self.fetch_all(urls)` raises an exception, `loop.close()` is never called, leaking the event loop and potentially holding resources.

**Fix:**
```python
def _fetch_feature_responses(self, urls: Sequence[str]) -> list[tuple[str, str] | BaseException]:
    loop = asyncio.new_event_loop()
    try:
        responses = loop.run_until_complete(self.fetch_all(urls))
        # Wait 250 ms for the underlying SSL connections to close
        loop.run_until_complete(asyncio.sleep(0.250))
        return responses
    finally:
        loop.close()
```

### WR-02: Duplicate docstring on arguments property

**File:** `src/pytest_bdd/parsers.py:613-614`
**Issue:** The `arguments` property in `cucumber_regular_expression` has two consecutive docstrings with identical text `"""Initialize the cucumber regular expression."""`. The second one is dead code — only the first is used by Python. Both are copy-paste artifacts from the `__init__` method.

**Fix:**
```python
@property
def arguments(self) -> Collection[str]:
    """Get argument names from the compiled regular expression."""
    return [*re_compile(self.pattern).groupindex.keys()]
```

### WR-03: Potential KeyError on missing worker_id in transport payloads

**File:** `src/pytest_bdd/model/message_transport.py:125,176`
**Issue:** Both `WorkerChunkBatch.from_dict` (line 125) and `WorkerCompletionManifest.from_dict` (line 176) access `payload["worker_id"]` via direct key indexing. Other fields use `.get()` with defaults. A malformed or corrupted JSON payload missing the `worker_id` key will raise `KeyError` with a cryptic message instead of a descriptive error. Since these methods process data received from remote workers (potentially across network boundaries), input validation is important.

**Fix:**
```python
# Line 125
worker_id = payload.get("worker_id")
if worker_id is None:
    raise ValueError("Missing required field 'worker_id' in batch payload")
return cls(
    worker_id=str(worker_id),
    ...
)
```
Apply the same pattern at line 176 for `WorkerCompletionManifest.from_dict`.

### WR-04: rmdir in finally block can mask original exceptions

**File:** `src/pytest_bdd/util/tests_group_ordering.py:485-497`
**Issue:** The `_barrier_lock` context manager calls `lock_path.rmdir()` in its `finally` block. If another process removes the lock directory between the `yield` and `rmdir()`, a `FileNotFoundError` is raised from `finally`. This exception replaces any original exception from the `yield` body, making root-cause debugging very difficult in multi-process test scenarios.

**Fix:**
```python
@contextmanager
def _barrier_lock(state_path: Path) -> Iterator[None]:
    lock_path = state_path.with_suffix(".lock")
    while True:
        try:
            lock_path.mkdir()
            break
        except FileExistsError:
            time.sleep(_BARRIER_LOCK_POLL_SECONDS)
    try:
        yield
    finally:
        try:
            lock_path.rmdir()
        except FileNotFoundError:
            pass
```

### WR-05: Module-level mutable state for test name generation

**File:** `src/pytest_bdd/scenario.py:64`
**Issue:** `test_names = get_python_name_generator("")` is a module-level generator instance. At line 462, `test.__name__ = next(iter(test_names))` advances this shared generator. If `scenarios()` with `return_test_decorator=False` is called across multiple modules or from concurrent test collection, name generation order depends on import order and timing, which can cause non-deterministic test names and potential collisions.

**Fix:** Create a fresh generator per call rather than sharing module-level state, or use an instance-scoped counter:
```python
def scenarios(...):
    ...
    if return_test_decorator:
        return decorator

    @decorator
    def test() -> None:
        return Nothing.value_or(None)

    # Use a fresh generator per scenarios() call
    test.__name__ = next(get_python_name_generator(""))
    return test
```

## Info

### IN-01: Overly complex consolidation function

**File:** `src/pytest_bdd/model/message_consolidation.py:318`
**Issue:** `consolidate_message_fragments` carries four noqa suppressions: `# noqa: C901, PLR0912, PLR0914, PLR0915` — targeting McCabe complexity, branch count, local variable count, and statement count respectively. The function handles ID deduplication, structural sorting, execution categorization, and hook resolution all in one ~120-line block. While functionally correct, it is difficult to test in isolation and resistant to safe modification.

**Fix:** Consider extracting the deduplication phases (singular records, phase one, phase two) into separate private functions, and the execution sorting/categorization into its own function. This would also improve testability.

### IN-02: Wildcard import for module patching

**File:** `src/pytest_bdd/model/message_extension.py:9`
**Issue:** `from cucumber_messages import *  # noqa: F403` imports all names from `cucumber_messages` into the module namespace. This is intentional — the module extends/patchs cucumber_messages types in place — but it makes it impossible to audit which names originate from the library vs. this module. The `# noqa: F403` suppression acknowledges the anti-pattern.

**Fix:** If the patching approach must be preserved, document explicitly in a module-level comment which names are being imported and re-exported. Consider explicit imports with `__all__` re-export.

### IN-03: Fragile empty-value check in _get_ini_value

**File:** `src/pytest_bdd/util/tests_group_ordering.py:256`
**Issue:** The check `if value not in ("", [], ()):` uses tuple membership to detect empty values from pytest config. While correct for the expected return types of `config.getini()`, this pattern is fragile — if a future pytest version or config source returns a different empty collection type (e.g., empty `set`, `frozenset`), the check would fail to detect it.

**Fix:** Use a more explicit pattern:
```python
if not value:  # covers None, "", [], (), {}, etc.
    return value
```
Or, since `getini` always returns a value, use:
```python
if value in ("", [], ()):
    pass  # check other sources
```

### IN-04: No startup feedback when aiofiles is unavailable

**File:** `src/pytest_bdd/collector_batch.py:26-31`
**Issue:** The optional `aiofiles` import fails silently — no log message informs the user that async I/O is unavailable and the system is falling back to synchronous reads. While `aiofiles` is correctly declared optional, a user who installs it later may not realize it was never being used in a previous run.

**Fix:** Add a debug-level log message in the except block:
```python
except ImportError:
    _aiofiles_available = False
    logger.debug("aiofiles not installed; async feature file reading disabled")
```

### IN-05: Blocking asyncio event loop creation in synchronous context

**File:** `src/pytest_bdd/scenario_locator.py:292`
**Issue:** `_fetch_feature_responses` calls `asyncio.new_event_loop()` in a synchronous pytest collection hook path. If pytest is already running inside an async context (e.g., pytest-asyncio), creating and running a separate event loop can cause `RuntimeError: Cannot run the event loop while another loop is running`. While the current design assumes synchronous collection, this assumption should be documented.

**Fix:** Add a comment noting the synchronous context assumption. For future-proofing, consider detecting an existing running loop and using it:
```python
try:
    loop = asyncio.get_running_loop()
    # Fall back to running in a thread or using sync HTTP client
except RuntimeError:
    loop = asyncio.new_event_loop()
```

---

_Reviewed: 2026-05-19T00:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
