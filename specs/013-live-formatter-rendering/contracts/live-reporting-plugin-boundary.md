# Contract: Live Reporting Plugin Boundary

## Purpose

Define the internal boundary between the pytest entrypoint, the narrow reporter
coordination root, orchestration services, formatter-specific reporter plugins,
and template-backed generated runtime assets.

## Participants

| Participant | Responsibility |
|-------------|----------------|
| Reporting entrypoint | Registers the reporting stack with pytest and invokes one explicit public lifecycle contract on the reporting runtime. |
| Reporter coordination root | Exposes the public lifecycle contract and owns shared runtime state references without absorbing formatter request resolution or service assembly responsibilities. |
| Pytest/pluggy plugin manager | Discovers and registers live-reporting plugins so orchestration and formatter modules participate through hook callbacks rather than helper dispatch. |
| Message-stream plugin | Owns live envelope intake, xdist batch forwarding, controller or worker authority rules, and stream coordination. |
| Session or lifecycle plugin | Owns formatter-session startup, shutdown, and shared delivery state for the run. |
| Formatter reporter plugin | Owns one supported formatter's request normalization and formatter-specific runtime-asset behavior. |
| Standalone rendering service | Replays canonical NDJSON into formatter outputs outside a live pytest session through an explicit application service boundary. |
| Template/resource asset | Checked-in source for any generated helper script that exceeds the inline-script limit. |
| Rendered script artifact | Temporary runtime file produced from a template/resource asset with run-specific values injected. |

## Module Rules

| Rule | Obligation |
|------|------------|
| Stream isolation | Message-stream handling must live outside formatter-specific reporter modules. |
| Formatter isolation | Each supported formatter resolves through its own reporter plugin module and owns its formatter-specific request or runtime-asset behavior. |
| Shared base usage | Shared support modules may provide reusable primitives, but they must not remain the primary home of formatter-specific behavior for most plugins. |
| Narrow root | `gherkin_message_reporter/plugin.py` remains a narrow coordination boundary rather than the home for request resolution, service-graph assembly, xdist role decisions, or runtime preparation. |
| Public lifecycle contract | The entrypoint interacts with the reporting runtime only through one explicit public lifecycle contract; duck typing against private reporter attributes or private methods is forbidden. |
| Explicit collaborators | Runtime services must declare explicit direct collaborators rather than reaching sibling services through reporter-backed service-locator accessors. |
| Hook participation | Split modules must register as real pytest or pluggy plugins and expose their behavior through hook registration or lifecycle callbacks. |
| State ownership | Mutable live-reporting state must live in plugin instances or pytest-owned runtime objects such as config, request, run, or session state containers. |
| Discovery policy | Supported runtime paths must use one canonical formatter discovery source per execution mode; package-scan fallback is not part of the supported contract. |
| Template ownership | Generated scripts longer than 20 lines must be rendered from checked-in resource/template assets. |

## Invariants

1. Exactly one message-stream orchestration module owns controller or worker
   live delivery for a run.
2. The entrypoint must not need to know private runtime state to configure or
   unconfigure the reporting runtime.
3. Formatter-specific behavior for one formatter must not be required to import
   implementation logic from another formatter module.
4. Service-to-service collaboration must be visible as explicit direct
   dependency wiring rather than implicit sibling lookup through the reporter.
5. Standalone replay must consume the same canonical formatter request model
   and the same runtime assets without constructing a synthetic pytest runtime.
6. Temporary rendered script artifacts may be deleted after use, but their
   checked-in template/resource sources remain the canonical implementation.

## Failure Rules

1. If a formatter request cannot be resolved to its dedicated reporter plugin,
   startup must fail with an actionable configuration or runtime error.
2. If a split module cannot be registered as a pytest or pluggy plugin, startup
   must fail rather than silently downgrading to helper-only execution.
3. If the entrypoint cannot satisfy the explicit public lifecycle contract, the
   runtime must fail rather than falling back to duck typing against private
   fields.
4. If a required template/resource asset is missing or cannot be rendered,
   startup must fail rather than silently falling back to an inline script.
5. If live reporting requires mutable module-level globals or reporter-backed
   service-locator access to coordinate state, startup or validation must fail
   because the runtime ownership contract is broken.

## Out of Scope

- Changing the public formatter CLI flag surface
- Worker-local formatter rendering during distributed runs
- Treating test-only helper templates as product runtime modules
- Supporting package-scan discovery as a first-class runtime path
