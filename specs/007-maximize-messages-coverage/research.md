# Research Notes: Maximize Messages Capability Coverage

## Schema Location Strategy
- **Decision**: Use `importlib.resources` to locate the `Envelope.json` schema and fallback to `git` for test-only discovery when the package isn't installed.
- **Rationale**: Relative path resolution based on module location (`__file__`) is prohibited by the technical constraints. `importlib.resources` is the Pythonic standard for accessing packaged artifacts, ensuring resilience in `tox` and `wheel` deployments.
- **Alternatives considered**: Setting an explicit environment variable (`PLUGIN_PATH`), which was specifically forbidden in the spec constraints.

## Validation Failure Handling
- **Decision**: Missing coverage or structurally invalid fields in emitted payloads will immediately raise hard failures during validation tests.
- **Rationale**: User explicitly selected the "Hard failure" mode to strictly enforce compliance and prevent coverage gaps from slipping into the codebase unnoticed.
- **Alternatives considered**: Emitting a diagnostic warning (better for gradual adoption) or reporting gaps only in the final governance JSON.

## Tracing Overhead
- **Decision**: Dynamic runtime traceability is active only when the `--messages-coverage` CLI flag is passed.
- **Rationale**: Deep structural inspection and set-building across all emitted `cucumber-messages` payloads introduce I/O and CPU overhead. An opt-in flag ensures normal test suite runs are fast while providing developers the means to verify coverage when needed.
- **Alternatives considered**: Default-active tracing, which risks degrading the developer experience for large test suites.

## Inventory Generation from Schema
- **Decision**: Use the JSON Schema files in `messages/jsonschema/src/` as the canonical source for the capability inventory.
- **Rationale**: These schemas define the official structure of the `messages` protocol and are language-agnostic. By parsing these, we can programmatically identify every payload kind and every field (including nested ones) that `pytest-bdd-ng` could potentially emit.

## Exhaustive Validation
- **Decision**: Integrate the `jsonschema` library into the message validation flow.
- **Rationale**: Manual validation is error-prone and hard to maintain as the protocol evolves. `jsonschema` provides a robust, standardized way to ensure emitted payloads exactly match the official specification.

## Step Matching Structural Integrity
- **Decision**: Enhance `_build_step_match_arguments_lists` to use precise offsets and capture nested groups.
- **Rationale**: The current implementation uses `.find()`, which is ambiguous for repeated values and doesn't capture nested capture groups. Structural integrity requires exact matching.
