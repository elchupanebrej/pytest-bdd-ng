# ADR-001: Use `attrs` over stdlib `dataclass`

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** pytest-bdd-ng core team

## Context

Python 3.7 introduced `@dataclass` as a standard library approach to data classes.
When pytest-bdd-ng was initiated (Phase 2), both `attrs` and `dataclass` were viable
options for data-holding classes. The project needed a consistent convention for
classes like `LifecycleObjectRef`, `StepRun`, and configuration objects.

`attrs` provides several features that `dataclass` lacks:
- `slots=True` for memory-efficient instance storage
- Rich validator infrastructure without third-party dependencies
- Fine-grained control over equality, hashing, and ordering
- Optional converters with cooperative multiple-inheritance support

The `dataclass` module has improved since Python 3.7 (added `slots=True` in 3.10,
`kw_only` in 3.10), but `attrs` still offers a superset of functionality and works
consistently across our entire Python 3.10-3.14 support matrix.

## Decision

We will use `attrs` (`@define(slots=True)`) as the canonical data class library
for all data-holding classes in pytest-bdd-ng. The pattern is:

```python
from attrs import define, field


@define(slots=True)
class LifecycleObjectRef:
    kind: LifecycleKind
    object_id: str
    name: str | None = None
```

This replaces stdlib `@dataclass` in all contexts. `field()` is used instead of
`dataclasses.field()` for attribute configuration.

## Consequences

### Positive
- Consistent `slots=True` usage across all data classes reduces memory footprint
- `attrs` validators provide richer validation than dataclass `__post_init__`
- `mypy` plugin support for `attrs` handles type checking of `@define` classes
- Validator, converter, and factory patterns are uniform across the codebase
- No version-dependent feature gaps (works identically on 3.10-3.14)

### Negative
- Adds `attrs` as a mandatory dependency (21 KB wheel, pure Python)
- Contributors familiar with stdlib `dataclass` need to learn `attrs` API
- `attrs`-specific decorators (`@define` vs `@dataclass`) are visual noise for those expecting stdlib

### Neutral
- `attrs` and `dataclass` are syntactically similar for basic use cases
- Both libraries interoperate with type checkers through PEP-compliant mechanisms
- IDE support (autocomplete, type hints) is equivalent for both
