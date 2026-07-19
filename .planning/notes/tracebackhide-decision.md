---
title: Decision: module-level `__tracebackhide__` for pytest plugin tracebacks
date: 2026-06-16
context: Exploration session on hiding internal tracebacks from pytest-bdd-ng library
---

## Decision

Chose module-level `__tracebackhide__ = True` in all `src/pytest_bdd/` modules to hide internal library tracebacks from pytest output.

## Reasoning

- User wants to hide all internal frames from pytest-bdd-ng library when BDD steps fail, showing only user code traces.
- Official pytest recommendation is function-local, but module-level is acceptable for library code (not test functions).
- Simplicity: module-level covers all functions in the module without needing to annotate each individually.
- `--full-trace` flag provides escape hatch for debugging internal library issues.

## Tradeoffs considered

1. **Module-level vs function-local**: Module-level hides all frames from the module, which could mask bugs in assertion helpers. However, the library modules are not test functions; they are plugin runtime code.
2. **All internal frames vs targeted**: User chose all internal frames for simplicity, avoiding the need to identify specific frames to hide.
3. **Conditional hiding**: Future consideration for hiding only specific exception types (e.g., `ConfigException`) to keep unexpected bugs visible.

## References

- pytest documentation on `__tracebackhide__`: https://docs.pytest.org/en/stable/example/simple.html#writing-well-integrated-assertion-helpers
- Research findings: function-local pattern, conditional hiding, `--full-trace` override.
