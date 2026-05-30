# 07-03: Rewrite DEVELOPMENT.rst with comprehensive developer guide

## Objective

Replace DEVELOPMENT.rst with a comprehensive developer guide covering architecture, conventions, testing strategy, BDD workflow, CI matrix, and plugin development lifecycle.

## What Was Done

- Replaced DEVELOPMENT.rst with 587-line comprehensive developer guide (was 239 lines)
- Added new sections:
  - Architecture Overview (feature collection, parsing, runtime model, step definitions, plugin system, Cucumber Messages bridge)
  - Core Patterns (StashBound pattern with full example, attrs library usage, plugin class standard, no-return-None rule, specific exception handling)
  - Testing Strategy (unit, feature, E2E/BDD, message tests with commands)
  - BDD Workflow (ATDD process from feature writing to GSD planning)
  - Plugin Development Lifecycle (step-by-step guide with code examples)
  - CI Matrix (Python versions, pytest versions, platforms, gates)
- Preserved existing content:
  - Prerequisites (Python 3.10+, uv, added Go 1.21+ note)
  - Installation (uv sync workflow with extras explanation)
  - Running Tests (tox workflow, make targets, quick test commands)
  - Development Workflow (feature branch, test, pre-commit, commit/push)
  - Release Workflow (GitHub Actions, build, twine check)
  - Project Tooling (CLI entry points, module commands, shell helpers, available commands)
- All content uses RST formatting throughout
- Cross-references to `docs/internal/` and `src/pytest_bdd/model/stash_access.py`

## Verification

- `uv run pytest tests/doc/test_development_rst.py::test_development_rst_required_sections -x --tb=short` PASSED
- Line count: 587 (minimum 200 required)
- All required keywords present: StashBound, attrs, plugin class, test, Architecture

## Requirements Met

- [x] DOC-02: DEVELOPMENT.rst updated with current conventions
- [x] D-05: Comprehensive rewrite, not minimal update
- [x] D-06: Includes architecture overview, plugin development lifecycle, testing strategy, BDD workflow, CI matrix, StashBound pattern, attrs usage, plugin class standard
- [x] D-07: Replaced insufficient current file with full developer guide
