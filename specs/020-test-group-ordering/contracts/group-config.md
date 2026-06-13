# Contract: Group Configuration Schema

**Feature**: 020-test-group-ordering
**Contract Type**: Pytest ini configuration interface
**Date**: 2026-05-05

## Overview

This contract defines how projects declare test groups, execution order, default assignment, and path mappings through pytest ini-style configuration. The example names are generic cost tiers for the initial project setup; implementations must support any configured group names.

No `[tool.pytest-bdd-ng.test-groups]` table or separate config file is part of this contract.

## Pytest Ini Options

The adapter must register these options with pytest and read them through pytest's config API.

| Key | Type | Example | Description |
|-----|------|---------|-------------|
| `test_group_order` | `linelist` or `args` | `["instant", "fast", "medium", "slow", "external"]` | Ordered group names. First entry runs first. Names must be valid pytest marker identifiers. |
| `test_group_default` | `string` | `"fast"` | Group assigned to tests with no resolvable group signal. Must be a member of `test_group_order`. |
| `test_group_paths` | `linelist` | `"tests/e2e/** = external"` | Repo-relative glob or path-prefix mappings. Path mappings override directory naming convention. |

## Full `pyproject.toml` Example

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

## Equivalent `pytest.ini` Example

```ini
[pytest]
addopts = --order-scope=session
markers =
    instant: smallest in-process tests
    fast: normal fast tests
    medium: moderate integration tests
    slow: expensive local tests
    external: tests requiring external services
    order: execution ordering marker from pytest-order
test_group_order =
    instant
    fast
    medium
    slow
    external
test_group_default = fast
test_group_paths =
    tests/unit/** = instant
    tests/e2e/** = external
```

## Group Marker Protocol

Only marker names declared in `test_group_order` participate in group resolution. Every other pytest marker is ignored by the grouping resolver.

### 1. Directory Naming Convention

If a path segment exactly matches a configured group name after duplicate group normalization, that group supplies the base assignment:

```text
tests/fast/test_example.py      -> fast, if "fast" is configured
tests/external/test_api.py      -> external, if "external" is configured
```

### 2. Path Mapping

Configured path mappings override directory naming convention:

```ini
test_group_paths =
    tests/legacy_api/** = external
```

### 3. Directory-Level Marker

A configured group marker inherited from `conftest.py` overrides path assignment:

```python
import pytest

pytestmark = pytest.mark.slow
```

### 4. Test-Level Marker

A configured group marker on a test module or function has final precedence:

```python
import pytest

pytestmark = pytest.mark.medium


@pytest.mark.external
def test_requires_external_service(): ...
```

If multiple configured group markers are present at the same cascade level, the latest group in configured order wins.

## Validation Contract

Validation happens at collection/configuration time. Warnings are visible and collection continues.

| Violation | Required Behaviour |
|-----------|--------------------|
| `test_group_order` is empty or missing | Warn and use a deterministic fallback configuration chosen by the adapter. |
| Duplicate group name | Warn and keep the first occurrence. |
| `test_group_default` is missing from `test_group_order` | Warn and use the first configured group. |
| `test_group_paths` value is not in `test_group_order` | Warn and ignore that path mapping. |
| Group name clashes with a pytest built-in marker | Warn; collection continues. |
| Path mapping line is malformed | Warn and ignore that path mapping. |

Non-group pytest markers are not validation errors. They are ignored by group resolution and must not be handled through hardcoded ignore lists.

## pytest-order Integration Contract

The adapter applies `pytest.mark.order(N)` to each collected item, where `N` is the 1-based ordinal of the resolved group:

```text
test_group_order = ["instant", "fast", "medium", "slow", "external"]
instant -> order(1)
fast -> order(2)
medium -> order(3)
slow -> order(4)
external -> order(5)
```

After marker translation, `pytest-order` performs collection ordering. Project code must not call `items.sort(...)`, replace `items[:]`, or otherwise reorder the collected item list directly.

## Runtime Validation Contract

Full-suite validation must include a runtime check, including xdist, that records test start and finish events by resolved group. The validation passes only when every later-group start event occurs after all earlier-group finish events.

Fixture-driven external-resource skips must be validated by a fixture that calls `pytest.skip()`. The skipped test must be reported as a normal pytest skip, and later groups must still run.
