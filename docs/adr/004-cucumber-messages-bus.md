# ADR-004: Cucumber Messages Protocol as Canonical Reporting Bus

**Status:** Accepted
**Date:** 2026-06-08
**Deciders:** pytest-bdd-ng core team

## Context

pytest-bdd-ng needs a reporting mechanism that is interoperable with the broader Cucumber ecosystem. Reporting plugins (JSON, JUnit, pretty-print, progress, usage, snippets) need a common event stream to consume. Without a standard protocol, each plugin must independently hook into pytest events, parse scenario state, and format output — leading to duplicated logic and inconsistent behavior.

The Cucumber ecosystem has standardized on the Cucumber Messages protocol (NDJSON-encoded Protocol Buffers) as its inter-component communication format. This protocol defines a rich set of message types (Envelope, GherkinDocument, Pickle, TestCaseStarted, TestStepFinished, etc.) that capture the entire BDD lifecycle.

## Decision

**Use the Cucumber Messages NDJSON protocol as the canonical reporting bus.** All formatter plugins consume `Envelope` messages via the `gherkin_message_reporter` lifecycle bridge. The bridge converts internal pytest-bdd runtime state into standardized Cucumber Messages and streams them as NDJSON.

Key aspects:
- The `gherkin_message_reporter` core plugin acts as the single producer of Cucumber Messages, driven by pytest-bdd lifecycle hooks
- All formatter plugins consume `Envelope` messages rather than accessing pytest internals directly
- The NDJSON stream can be captured to file (`--cucumber-json-output`) or piped to external tools
- External Cucumber tools (Cucumber Reports, CI/CD dashboards) can consume the output directly

## Consequences

### Positive
- Interoperable with the Cucumber ecosystem — reports can be consumed by Cucumber Reports, Jenkins Cucumber plugin, and other standard tooling
- Single source of truth for reporting events — formatters don't duplicate lifecycle tracking
- New formatters only need to consume `Envelope` messages, not understand pytest-bdd internals
- NDJSON format is streamable — reports appear in real-time, not just at suite completion
- Protocol supports extension via `meta` messages for pytest-bdd-specific data

### Negative
- NDJSON streaming adds complexity over simple file output — requires the `gherkin_message_reporter` lifecycle bridge and transport runtime
- Formatters must understand the Cucumber Messages schema rather than a simpler pytest-bdd-specific API
- The message bridge introduces an indirection layer that can complicate debugging

### Neutral
- Python implementation uses `cucumber-messages` library for type-safe message construction
- JavaScript formatter bridge (`live_formatter_bridge.mjs`) consumes the same NDJSON stream for Node.js-based formatters
