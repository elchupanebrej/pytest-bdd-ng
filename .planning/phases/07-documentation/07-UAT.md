---
status: testing
phase: 07-documentation
source: 07-01-SUMMARY.md, 07-02-SUMMARY.md, 07-03-SUMMARY.md, 07-04-SUMMARY.md
started: 2026-05-15T22:15:00.000Z
updated: 2026-05-15T22:15:00.000Z
---

## Current Test

number: 1
name: Sphinx Installation Verification
expected: |
  Sphinx >= 7.0 installed via `uv sync --extra doc-gen`. Command `uv run python -c "import sphinx; print(sphinx.__version__)"` outputs version >= 7.0.
awaiting: user response

## Tests

### 1. Sphinx Installation Verification
expected: Sphinx >= 7.0 installed via doc-gen extra, napoleon extension enabled in docs/conf.py
result: [pending]

### 2. Docstring Verification Tests Pass
expected: All 8 public API exports have non-empty Google-style docstrings with Args and Returns sections. `uv run pytest tests/doc/test_docstrings.py::test_all_exports_have_docstrings -x --tb=short` passes.
result: [pending]

### 3. DEVELOPMENT.rst Comprehensive Guide
expected: DEVELOPMENT.rst is a 200+ line developer guide with sections: Architecture, StashBound, attrs, plugin class, testing strategy, BDD workflow, CI matrix. `uv run pytest tests/doc/test_development_rst.py::test_development_rst_required_sections -x --tb=short` passes.
result: [pending]

### 4. Migration Guide Content
expected: MIGRATION.md exists at repo root with 10 breaking changes, each with Before/After code examples. Covers target_fixture, parser syntax, example_converters, hook signatures, CLI flags.
result: [pending]

### 5. Deprecation Registry
expected: DEPRECATIONS.md exists at repo root with "Removed in 1.0" and "Deprecated in 2.x" sections. Lists --cucumberjson, Allure as removed; example_converters, <var> syntax, pathlib2, docopt-ng as deprecated. docs/include.rst references both files.
result: [pending]

### 6. Full Doc Test Suite
expected: `uv run pytest tests/doc/ -x --tb=short` passes with all doc-related tests green.
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0

## Gaps

[none yet]
