# ADR-008: pytest.config.stash Runtime State

**Status:** Accepted

**Date:** 2026-06-08

**Deciders:** pytest-bdd-ng core team

## Context

pytest-bdd needs session-scoped state shared across multiple plugins without global variables. The state includes the `Run` instance, `ScenarioRun` instances, feature bindings, and other runtime objects. Without a canonical state store, plugins would need to communicate through global singletons or pass objects through pytest hooks, both of which are fragile and hard to test.

## Decision

Use `pytest.config.stash` as the canonical state store for all session-scoped runtime state. `StashBound` subclasses provide typed access to specific stash keys, encapsulating the key name, type checking, and initialization logic.

```python
from pytest_bdd.model.stash_access import StashBound


class Run(StashBound):
    _STASH_KEY = "bdd/run"
```

Each stash-bound type is responsible for its own key namespace (`bdd/run`, `bdd/scenario`, etc.) and provides factory methods (`from_stash`, `ensure_in_stash`) for consistent access patterns.

## Consequences

### Positive

- Type-safe access to runtime state with mypy-compatible return types
- Discoverable — all stash keys are defined as class constants on their respective types
- Avoids global state — state is scoped to the pytest session via config.stash
- Testable — tests can inject mock stash objects without global side effects

### Negative

- Requires `StashBound` boilerplate for each stored type (key constant, class definition)
- Stash keys must be globally unique across plugins
- Runtime errors from missing or wrong-type stash entries surface as `PytestBDDStashLookupError` / `PytestBDDStashTypeMismatchError`

### Neutral

- Pattern is consistent across the entire codebase — all runtime state access follows the same convention
