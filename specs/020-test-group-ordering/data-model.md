# Data Model: Test Group Ordering

**Feature**: 020-test-group-ordering
**Date**: 2026-05-05

## Entities

### GroupConfig

Project-level test-group configuration read from pytest ini-style configuration.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `groups` | `list[str]` | Non-empty; each entry is a valid pytest marker identifier; duplicates warn and collapse to first occurrence | Ordered group names; list position determines execution ordinal |
| `default` | `str` | Must be in `groups`; invalid value warns and falls back to first group | Group assigned when no group signal is resolved |
| `paths` | `list[GroupPathMapping]` | Patterns are repo-relative glob or path-prefix patterns; target group must be in `groups` | Optional path-to-group mappings that override directory naming convention |

**Pytest ini source keys**:
- `test_group_order`: line-list or argument-list of group names in execution order.
- `test_group_default`: string default group.
- `test_group_paths`: line-list of `pattern = group` mappings.

**Validation rules**:
- Unknown path mapping value: warn and ignore that entry.
- Invalid or missing default group: warn and use the first configured group.
- Duplicate group name: warn and keep the first occurrence for ordering.
- Empty group list: warn and use a deterministic fallback configuration chosen by the adapter.
- Group name that clashes with a pytest built-in marker: warn; collection continues.
- Malformed path mapping line: warn and ignore that entry.

---

### GroupAssignment

The resolved group for one collected pytest item. This is transient runtime state.

| Field | Type | Description |
|-------|------|-------------|
| `item_nodeid` | `str` | Pytest node ID |
| `group_name` | `str` | Resolved configured group name |
| `ordinal` | `int` | 1-based order value passed to `pytest-order` |
| `resolution_source` | `Literal["dir_convention", "path_pattern", "conftest_marker", "test_marker", "default"]` | Source that supplied the winning assignment |

---

### GroupMarkerSignal

A pytest marker that participates in group resolution.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Marker name that must be present in `GroupConfig.groups` |
| `ordinal` | `int` | Group order derived from `GroupConfig.groups` |
| `source` | `Literal["conftest_marker", "test_marker"]` | Where the signal was observed |

Only configured group names create `GroupMarkerSignal` values. All other pytest markers are ignored by the resolver and do not require ignore lists.

---

### GroupPathMapping

One configured mapping from a pytest ini path mapping line to a group.

| Field | Type | Description |
|-------|------|-------------|
| `pattern` | `str` | Repo-relative glob or path-prefix pattern |
| `group_name` | `str` | Configured group assigned when the pattern matches |

If multiple mappings match at the same level, the deterministic implementation rule is "last matching mapping wins" so projects can place broad mappings first and overrides later.

---

### GroupOrderingUtility

Reusable source module under `src/pytest_bdd/util/test_group_ordering.py`.

| Function | Responsibility |
|----------|----------------|
| `register_group_config_options(parser)` | Register custom pytest ini options with `parser.addini(...)` |
| `read_group_config(config)` | Read group config through `config.getini(...)` |
| `validate_group_config(raw_config)` | Return normalized `GroupConfig` plus warnings |
| `resolve_group_assignment(item, group_config)` | Resolve one item using the cascade |
| `apply_order_marker(item, assignment)` | Apply `pytest.mark.order(assignment.ordinal)` without sorting |

Function names are planning targets, not a frozen public API. The implementation may choose equivalent names if the responsibilities remain separated and testable.

---

### RuntimeGroupBarrierObservation

Acceptance-test observation used to verify xdist runtime barriers.

| Field | Type | Description |
|-------|------|-------------|
| `item_nodeid` | `str` | Pytest node ID |
| `group_name` | `str` | Resolved configured group |
| `event` | `Literal["start", "finish"]` | Runtime event type |
| `timestamp` | `float` | Monotonic timestamp captured by the validation fixture/plugin |

The validation passes when every later-group `start` timestamp is greater than or equal to every earlier-group `finish` timestamp.

## State Transitions

```text
Pytest starts
        |
        v
Adapter registers custom pytest ini options
        |
        v
Collected pytest item
        |
        v
Directory naming convention matches configured group?
        |
        v
Configured path mapping matches?
        |
        v
Inherited conftest marker whose name is in GroupConfig.groups?
        |
        v
Test-file/function marker whose name is in GroupConfig.groups?
        |
        v
No group signal found? Use GroupConfig.default
        |
        v
Create GroupAssignment
        |
        v
Adapter applies pytest.mark.order(N)
        |
        v
pytest-order performs collection ordering
        |
        v
Runtime validation confirms local/xdist group barriers
```

## Configuration Example

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

```python
import pytest

pytestmark = pytest.mark.slow

@pytest.mark.external
def test_requires_external_service():
    ...
```
