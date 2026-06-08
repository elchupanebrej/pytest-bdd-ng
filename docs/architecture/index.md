# Architecture Documentation

This directory contains architectural documentation for the pytest-bdd project,
providing visual and textual descriptions of the system's structure, behavior,
and design patterns.

## Documentation Set

The architecture documentation is organized into distinct aspects, each focusing
on a specific viewpoint of the system:

- [Project Structure](architecture-project-structure.md): High-level organization
  of components and their relationships
- [Data Flow](architecture-data-flow.md): Execution paths and data movement
  through the system
- [Plugin Architecture](architecture-plugin-architecture.md): Extension mechanisms
  and plugin system design
- [Responsibility Object Map](OBJECT_MAP.md): Entity-level responsibility,
  consumers, invariants, and architecture scores generated from source docstrings
- [Responsibility Gaps](RESPONSIBILITY_GAPS.md): Aggregated weak responsibility
  zones and recommended refactoring actions

## How to Use This Documentation

Each document follows a consistent structure:
1. **Overview**: Brief introduction to the architectural aspect being documented
2. **Diagram**: Visual representation using Mermaid syntax
3. **Explanation**: Detailed description of what the diagram shows and key architectural insights
4. **Relationships**: Links to related architectural aspects

## Diagram Notation

All diagrams use [Mermaid](https://mermaid.js.org/) syntax. Refer to the individual documents for specific diagram types and their meanings.

## Navigation Tips

- Start with the Project Structure document to understand the overall system organization
- Proceed to Data Flow to see how information moves through the system
- Explore Plugin Architecture to understand extension mechanisms
- Use cross-links between documents to explore related concepts

## Current Runtime Map

The runtime is organized around pytest collection, Gherkin parsing, scenario
binding, pickle execution, and Cucumber Messages reporting:

- `src/pytest_bdd/scenario.py` exposes `scenario()` and `scenarios()` for
  binding feature scenarios to pytest tests.
- `src/pytest_bdd/collector_batch.py` provides `FeatureBatchParser`, a
  stash-backed parser cache that can batch feature reads and parsing during
  collection.
- `src/pytest_bdd/plugin/scenario_test_collector/` owns feature collection and
  generated pytest items.
- `src/pytest_bdd/plugin/pickle_runner/` owns scenario execution, step dispatch,
  and runtime lifecycle state.
- `src/pytest_bdd/plugin/gherkin_message_reporter/` bridges runtime events into
  Cucumber Messages streams.
- Formatter plugins under `src/pytest_bdd/plugin/cucumber_*` consume those
  messages for JSON, JUnit, pretty, progress, summary, snippets, and usage
  output.

Shared runtime state should be stored through pytest `config.stash` wrappers
instead of global module state.
