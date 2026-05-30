# Quickstart: Async Feature File Collection

**Feature**: 022-async-feature-collection
**Date**: 2026-05-11

## What This Feature Does

Speeds up `pytest` test collection for projects with many `.feature` files by reading files concurrently and parsing Gherkin in parallel across CPU cores — instead of one at a time.

## Usage

**No action required.** The feature activates automatically when `aiofiles` is installed:

```bash
uv pip install aiofiles
pytest --collect-only
```

Feature files are accumulated during pytest's normal directory walk and processed in a single concurrent batch on first access. No CLI flags, no ini options, no configuration.

## If aiofiles Is Not Installed

Collection falls back to the existing synchronous (one-at-a-time) path. No errors, no degradation from current behavior.

## Verification

To confirm the feature is active, run `pytest --collect-only` and check that collection completes. Compare timing on a project with 10+ feature files:

```bash
# Without batching (aiofiles not installed)
time pytest --collect-only  # baseline

# With batching (aiofiles installed)
time pytest --collect-only  # should be measurably faster
```

## What Does NOT Change

- The set of discovered tests is identical (same scenarios, markers, parametrization).
- Feature file discovery order stays deterministic (globbing is synchronous).
- `@scenario()` decorators in Python files are unaffected.
- `--disable-feature-autoload`, `--feature-base-dir`, `--feature-base-url` work as before.

## Limitations

- Single feature file (N=1): no speed benefit (no concurrency to exploit).
- Very large feature files (>10MB): serialization cost to send content to worker processes may offset parse parallelism benefit.
- CPU-bound Gherkin parsing is the primary target; I/O benefit requires `aiofiles`.
