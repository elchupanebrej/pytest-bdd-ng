# Changelog

All notable changes to this project will be documented in this file.

## [3.0.0] - 2026-08-30

### Architecture & Clean-Room Rewrite (refs #143, #150, #151)
- Complete clean-room rewrite establishing an 8-layer cycle-free DAG architecture.
- Replaced legacy runtime coupling and pytest internals monkeypatching with pure domain models and pytest Stash.
- Architecture Seams 1–6 defining clear boundaries for hooks, parsers, step matching, runtime stash, message serialization, and bootstrap configuration.

### Features & Protocol Compatibility
- **Cucumber Messages v22+**: Modernized NDJSON serialization and streaming protocol (refs #143, #151).
- **Multi-Format Parsers**: Pure Layer L2a AST parser support for Gherkin (`.feature`), Gherkin Markdown (`.feature.md`, `.md`), and Structured BDD (`.bdd.yaml`, `.bdd.json`, `.bdd.toml`) (refs #150).
- **Cucumber Expressions**: Native parser integration alongside Regex and String parsers.
- **Scenario Outlines & Parameterization**: Direct table row expansion and parameterized test generation.
- **Toolchain Quality Gates**: Full automated validation with ruff, deptry, and DAG layer architecture verification.
