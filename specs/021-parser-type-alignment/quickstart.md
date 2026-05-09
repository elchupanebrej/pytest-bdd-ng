# Quickstart: Parser Type Alignment

**Date**: 2026-05-09
**Feature**: 021-parser-type-alignment

## Verification Commands

After refactoring, verify correctness with:

```bash
# Run existing parser-related tests
uv run python -m pytest tests/ -k "parser" -q

# Run full test suite (spot check for regressions)
uv run python -m pytest tests/compatibility -q

# Run mypy on the changed files
uv run mypy src/pytest_bdd/parser.py src/pytest_bdd/compatibility/parser.py

# Run ruff lint
uv run ruff check src/pytest_bdd/parser.py src/pytest_bdd/compatibility/parser.py
```

## Expected Changes

| File | Lines Changed | What Changes |
|------|--------------|--------------|
| `src/pytest_bdd/parser.py` | ~20 lines | Import change, cast removal, type annotation fixes |
| `src/pytest_bdd/compatibility/parser.py` | ~2 lines | ParserProtocol return type updated |

## What Should NOT Change

- No test modifications needed
- No runtime behavior changes
- No new dependencies
- Downstream consumers unchanged
