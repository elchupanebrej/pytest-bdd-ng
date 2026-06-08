# ADR-002: `StashBound` pattern for `pytest.config.stash` access

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** pytest-bdd-ng core team

## Context

pytest-bdd-ng stores session-scoped runtime state in pytest's `config.stash`
(`pytest.Stash`). This includes `Run` (the BDD test run container), `FeatureBatchParser`
(lazy batch parsing), `IdGenerator` (unique ID generation), and reporter state.

Direct `config.stash[key]` access is error-prone:
- **Type safety:** `config.stash` is typed as `Stash[object]`, so retrieved values
  must be cast to the expected type
- **Key collisions:** Multiple plugins storing objects under similar string keys
  risk silent overwrites
- **Initialization ordering:** Plugins must agree on initialization order to
  ensure dependencies are in stash before they're accessed
- **Discoverability:** Finding all stash keys requires grep; no centralized
  registry

Pytest's `config.stash` is the canonical runtime state container (per pytest
plugin conventions), and replacing it would break pytest integration.

## Decision

We will use the `StashBound` abstract base class as the canonical pattern for
`config.stash` access. Every session-scoped object stored in stash extends
`StashBound` (defined in `src/pytest_bdd/model/stash_access.py`).

The pattern provides:

```python
class StashBound:
    STASH_KEY: ClassVar[str] = ""

    @classmethod
    def from_stash(cls, stash: pytest.Stash) -> Self: ...
    @classmethod
    def find_in_stash(cls, stash: pytest.Stash) -> Self | None: ...
    def initialize_in_stash(self, stash: pytest.Stash) -> None: ...
    def set_in_stash(self, stash: pytest.Stash) -> None: ...
```

Backed by `StashAccess` static helpers that operate on `pytest.Stash` with
type-safe retrieval and proper error reporting (`PytestBDDStashLookupError`,
`PytestBDDStashTypeMismatchError`, `PytestBDDStashAlreadyInitializedError`).

## Consequences

### Positive
- Type-safe: `from_stash()` returns the correct type without manual casting
- Key collision prevention: `STASH_KEY` classvar documents and centralizes keys
- Discoverable: grep for `STASH_KEY` or `class StashBound` to find all stash users
- Initialization ordering: `initialize_in_stash()` throws if object already exists
- Consistent error handling: `StashAccess` provides uniform exceptions

### Negative
- Boilerplate: each stored type requires `STASH_KEY`, `from_stash()`, and
  `initialize_in_stash()` even for simple key-value pairs
- Learning curve: contributors must understand `StashBound` before accessing runtime state
- Not auto-enforced: direct `config.stash[key]` access is still possible
  (enforced by BLQ1003 in `plugin_patterns.py`)

### Neutral
- `StashBound` is a project convention, not a pytest upstream feature
- The pattern could be replaced by a typed container library (e.g., `returns.maybe`)
  if pytest-bdd were to adopt functional patterns, but `StashBound` is simpler
