# Quickstart: Test Group Ordering

**Feature**: 020-test-group-ordering
**Date**: 2026-05-05

## Prerequisites

- `pytest-order` installed in the test environment.
- `pyproject.toml` declares group names, marker registration, path mappings, and `pytest-order` options in `[tool.pytest.ini_options]`.
- Existing tests remain in their current directories.

## 1. Install `pytest-order`

Add `pytest-order` to the test dependency set used by local pytest and tox environments.

```toml
[project.optional-dependencies]
test = [
    "pytest-order",
]
```

## 2. Configure Groups

Add project-specific groups to pytest ini-style configuration. The initial example uses five generic cost tiers.

```toml
[tool.pytest.ini_options]
markers = [
    "instant: smallest in-process tests",
    "fast: normal fast tests",
    "medium: moderate integration tests",
    "slow: expensive local tests",
    "external: tests requiring external services",
    "order: execution ordering marker from pytest-order",
]
addopts = "--order-scope=session"
test_group_order = ["instant", "fast", "medium", "slow", "external"]
test_group_default = "fast"
test_group_paths = [
    "tests/unit/** = instant",
    "tests/model/** = instant",
    "tests/args/** = fast",
    "tests/hook/** = fast",
    "tests/steps/** = fast",
    "tests/feature/** = medium",
    "tests/gherkin_integration/** = medium",
    "tests/library/** = medium",
    "tests/struct_bdd/** = medium",
    "tests/allure_/** = slow",
    "tests/compatibility/** = slow",
    "tests/contract/** = slow",
    "tests/doc/** = slow",
    "tests/generation/** = slow",
    "tests/messages/** = slow",
    "tests/messages_coverage/** = slow",
    "tests/scripts/** = slow",
    "tests/e2e/** = external",
]
```

## 3. Run the Full Suite

```bash
uv run python -m pytest
```

Expected group order:

```text
instant -> fast -> medium -> slow -> external
```

Failures or skips in an earlier group must not prevent later groups from running.

## 4. Run a Single Group

```bash
uv run python -m pytest -m instant
uv run python -m pytest -m fast
uv run python -m pytest -m medium
uv run python -m pytest -m slow
uv run python -m pytest -m external
```

Pytest collects the suite, applies the configured group markers during collection, and then deselects non-matching groups through normal `-m` marker filtering.

Current collect-only validation counts:

```text
instant: 25 selected, 748 deselected
fast: 204 selected, 569 deselected
medium: 115 selected, 658 deselected
slow: 265 selected, 508 deselected
external: 164 selected, 609 deselected
```

In the current local Python 3.14 environment, collect-only commands without `-s` can hit an unrelated pytest capture teardown `FileNotFoundError`. Use `-s` for validation until that capture issue is fixed:

```bash
uv run --extra full python -m pytest -m instant --collect-only -q -s
uv run --extra full python -m pytest -m fast --collect-only -q -s
uv run --extra full python -m pytest -m medium --collect-only -q -s
uv run --extra full python -m pytest -m slow --collect-only -q -s
uv run --extra full python -m pytest -m external --collect-only -q -s
```

## 5. Override a Test's Group

Use only configured group names as group markers. Other pytest markers continue to work normally and are ignored by the grouping resolver.

```python
import pytest

pytestmark = pytest.mark.slow

@pytest.mark.external
def test_requires_external_service():
    ...

@pytest.mark.skip(reason="example")
def test_skip_marker_does_not_change_group():
    ...
```

## 6. Verify Ordering

```bash
uv run python -m pytest --collect-only -q
```

The collected order should show all `instant` assignments before `fast`, then `medium`, `slow`, and `external`. The adapter must accomplish this by applying `pytest.mark.order(N)` and leaving collection sorting to `pytest-order`.

Use `uv run --extra full python -m pytest --collect-only -q -s` in the current local environment for the same capture workaround described above.

## 7. Verify xdist Runtime Barriers

Run the acceptance validation that records start/finish events while xdist is active:

```bash
uv run python -m pytest -n auto tests/unit/test_group_ordering.py -q
```

The validation must prove that no later-group test starts before all earlier-group tests finish. Collection-only output is not sufficient for this check.

## 8. Measure Collection Overhead

Compare wall-clock time for `pytest --collect-only` with grouping disabled and enabled in the same environment:

```bash
uv run python -m pytest --collect-only -q
```

The grouping-enabled run must add no more than 2 seconds of collection-phase overhead.
