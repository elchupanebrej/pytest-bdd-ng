# Quickstart: Test Group Ordering

**Feature**: 020-test-group-ordering
**Date**: 2026-06-10

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

Add project-specific groups to pytest ini-style configuration. The repository uses seven semantic groups matching the test organization:

```toml
[tool.pytest.ini_options]
addopts = "-p pytester --order-scope=session"
markers = [
    "unit: pure in-process module tests",
    "integration: local plugin, parser, runtime, pytester, and subprocess-light flows",
    "contract: golden files, boundary contracts, schema contracts, and formatter parity contracts",
    "e2e: full executable user workflows and feature-doc driven acceptance tests",
    "compat: Python, pytest, dependency, and platform compatibility checks",
    "perf: benchmarks and expensive performance probes",
    "external: Docker, browser, and host-platform harnesses or acceptance wrappers",
    "order: execution ordering marker from pytest-order",
]
test_group_default = "integration"
test_group_order = ["unit", "integration", "contract", "e2e", "compat", "perf", "external"]
test_group_paths = [
    "src/pytest_bdd_testing/cases/unit/** = unit",
    "src/pytest_bdd_testing/cases/integration/** = integration",
    "src/pytest_bdd_testing/cases/contract/** = contract",
    "src/pytest_bdd_testing/cases/e2e/** = e2e",
    "src/pytest_bdd_testing/cases/compat/** = compat",
    "src/pytest_bdd_testing/cases/perf/** = perf",
    "src/pytest_bdd_testing/cases/external/** = external",
]
```

## 3. Run the Full Suite

```bash
uv run python -m pytest
```

Expected group order:

```text
unit -> integration -> contract -> e2e -> compat -> perf -> external
```

Failures or skips in an earlier group must not prevent later groups from running.

## 4. Run a Single Group

```bash
uv run python -m pytest -m unit
uv run python -m pytest -m integration
uv run python -m pytest -m contract
uv run python -m pytest -m e2e
uv run python -m pytest -m compat
uv run python -m pytest -m perf
uv run python -m pytest -m external
```

Pytest collects the suite, applies the configured group markers during collection, and then deselects non-matching groups through normal `-m` marker filtering.

Current collect-only validation counts (out of 1,932 total tests):

```text
unit: 1,011 selected, 921 deselected
integration: 320 selected, 1,612 deselected
contract: 246 selected, 1,686 deselected
e2e: 230 selected, 1,702 deselected
compat: 45 selected, 1,887 deselected
perf: 1 selected, 1,931 deselected
external: 79 selected, 1,853 deselected
```

In the current local Python 3.14 environment, collect-only commands without `-s` can hit an unrelated pytest capture teardown `FileNotFoundError`. Use `-s` for validation until that capture issue is fixed:

```bash
uv run --extra full python -m pytest -m unit --collect-only -q -s
uv run --extra full python -m pytest -m integration --collect-only -q -s
uv run --extra full python -m pytest -m contract --collect-only -q -s
uv run --extra full python -m pytest -m e2e --collect-only -q -s
uv run --extra full python -m pytest -m compat --collect-only -q -s
uv run --extra full python -m pytest -m perf --collect-only -q -s
uv run --extra full python -m pytest -m external --collect-only -q -s
```

## 5. Override a Test's Group

Use only configured group names as group markers. Other pytest markers continue to work normally and are ignored by the grouping resolver.

```python
import pytest

pytestmark = pytest.mark.compat


@pytest.mark.external
def test_requires_external_service(): ...


@pytest.mark.skip(reason="example")
def test_skip_marker_does_not_change_group(): ...
```

## 6. Verify Ordering

```bash
uv run python -m pytest --collect-only -q
```

The collected order should show all `unit` assignments before `integration`, then `contract`, `e2e`, `compat`, `perf`, and `external`. The adapter accomplishes this by applying `pytest.mark.order(N)` and leaving collection sorting to `pytest-order`.

Use `uv run --extra full python -m pytest --collect-only -q -s` in the current local environment for the same capture workaround described above.

## 7. Verify xdist Runtime Barriers

Run the acceptance validation that records start/finish events while xdist is active:

```bash
uv run python -m pytest -n auto src/pytest_bdd_testing/cases/unit/unit/test_group_ordering.py -q
```

The validation must prove that no later-group test starts before all earlier-group tests finish. Collection-only output is not sufficient for this check.

## 8. Measure Collection Overhead

Compare wall-clock time for `pytest --collect-only` with grouping disabled and enabled in the same environment:

```bash
uv run python -m pytest --collect-only -q
```

The grouping-enabled run must add no more than 2 seconds of collection-phase overhead.
