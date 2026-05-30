# Contract Fixture: Live Reporting Plugin Boundary

## Purpose

Define the internal boundary between live message-stream orchestration,
formatter-specific reporter plugins, and template-backed generated script
assets.

## Participants

| Participant | Responsibility |
|-------------|----------------|
| Reporting entrypoint | Registers the reporting stack, normalizes CLI/capture behavior, and wires the orchestration modules into pytest. |
| Message-stream plugin | Owns live envelope intake, xdist batch forwarding, controller/worker authority rules, and session lifecycle coordination. |
| Session plugin | Owns formatter-session startup, shutdown, and shared delivery state for the run. |
| Formatter reporter plugin | Implements one supported formatter's request normalization, launch/render policy, and output finalization behavior. |
| Template/resource asset | Checked-in source for any generated helper script that exceeds the inline-script limit. |
| Rendered script artifact | Temporary runtime file produced from a template/resource asset with run-specific values injected. |

## Module Rules

| Rule | Obligation |
|------|------------|
| Stream isolation | Message-stream handling must live outside formatter-specific reporter modules. |
| Formatter isolation | Each supported formatter resolves through its own reporter plugin module. |
| Shared base usage | Shared launch/request helpers may live in common support modules, but they must not collapse formatter-specific rendering logic back into one monolithic plugin. |
| Entry facade | `gherkin_message_reporter/plugin.py` remains a thin registration facade rather than the home for all runtime responsibilities. |
| Template ownership | Generated scripts longer than 20 lines must be rendered from checked-in resource/template assets. |

## Invariants

1. Exactly one message-stream orchestration module owns controller/worker live
   delivery for a run.
2. Formatter-specific rendering logic for one formatter must not be required to
   import implementation logic from another formatter module.
3. Long generated helper scripts are not embedded directly as Python string
   literals inside runtime modules.
4. Temporary rendered script artifacts may be deleted after use, but their
   checked-in template/resource sources remain the canonical implementation.

## Failure Rules

1. If a formatter request cannot be resolved to its dedicated reporter plugin,
   startup must fail with an actionable configuration/runtime error.
2. If a required template/resource asset is missing or cannot be rendered,
   startup must fail rather than silently falling back to an inline script.

## Out of Scope

- Changing the public formatter CLI flag surface
- Worker-local formatter rendering during distributed runs
- Treating test-only helper templates as product runtime modules
