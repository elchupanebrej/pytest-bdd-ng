# Contract: Standalone Rendering Boundary

## Purpose

Define the supported application boundary for replaying an existing canonical
NDJSON message stream into formatter outputs outside a live pytest session.

## Participants

| Participant | Responsibility |
|-------------|----------------|
| Standalone CLI entrypoint | Parses replay arguments, validates input paths, and invokes the standalone rendering service. |
| Standalone rendering service | Accepts canonical NDJSON plus normalized formatter requests and produces formatter outputs. |
| Formatter discovery catalog | Resolves the supported formatter inventory for standalone replay through one canonical discovery policy. |
| Formatter plugin | Owns formatter-specific request and runtime-asset behavior used by replay. |
| Canonical NDJSON artifact | Input evidence stream replayed into formatter outputs. |
| Rendered runtime assets | Temporary JS assets required to execute formatter rendering under Node.js. |

## Boundary Inputs

| Input | Type | Rules |
|-------|------|-------|
| `messages_path` | absolute path | Must point to an existing canonical NDJSON file. |
| `formatter_requests` | list of normalized requests | Must use the same request model as live rendering. |
| `catalog` | formatter discovery inventory | Must come from the standalone discovery policy defined for this feature. |

## Boundary Outputs

| Output | Type | Rules |
|--------|------|-------|
| `render_result` | structured success or failure result | Must report success, exit semantics, missing dependencies, and rendered formatter set. |
| formatter files | file artifacts | Must match the requested output targets and remain consistent with the replayed NDJSON. |
| terminal output | stdout | Must reflect the requested terminal formatter behavior for replay mode. |

## Invariants

1. Standalone replay must use the same `FormatterRequest` normalization model as
   live runtime rendering.
2. Standalone replay must not require a synthetic pytest `Config` object.
3. Standalone replay must not require ad hoc construction of a pytest
   `PytestPluginManager` merely to imitate an in-process pytest runtime.
4. Formatter discovery for standalone replay must use one explicit supported
   catalog path.
5. Canonical NDJSON remains the only supported replay input artifact.

## Failure Rules

1. Missing replay input files must fail with an actionable error.
2. Missing formatter runtime assets or packages must fail through the structured
   render result rather than through hidden pytest-runtime assumptions.
3. Replay must not silently switch to package-scan formatter discovery when the
   supported standalone catalog path is unavailable.

## Out of Scope

- Starting a live pytest session
- Reconstructing a fake pytest runtime with synthetic `Config` objects
- Supporting replay from non-canonical ad hoc message formats
