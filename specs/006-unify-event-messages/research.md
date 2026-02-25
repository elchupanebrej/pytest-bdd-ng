<!-- markdownlint-disable MD013 -->

# Research: Unify Event Message Reporting

## Decision 1: Canonical message reporter is the single event-construction authority

- Decision: Treat canonical Cucumber message envelope emission as the only event-construction source, and derive all legacy/user-facing reporting outputs from that stream.
- Rationale: This removes dual-path drift, enforces one lifecycle model, and makes ordering/linkage validation deterministic.
- Alternatives considered:
  - Keep separate message and legacy construction paths: rejected because existing inconsistency comes from path divergence.
  - Replace legacy outputs entirely: rejected because the spec requires retaining legacy outputs in-scope.

## Decision 2: Correlation identifiers are unique per scenario execution attempt

- Decision: Assign unique correlation IDs per scenario attempt, including retries and parallel-worker executions.
- Rationale: Attempt-level uniqueness prevents collisions and orphan linkage in retried/xdist runs.
- Alternatives considered:
  - Scenario-definition-level identifiers: rejected because retries would alias separate executions.
  - Worker-local uniqueness only: rejected because cross-worker aggregation would be ambiguous.

## Decision 3: Emission failures are blocking only when message reporting is enabled

- Decision: Fail execution on message emission/serialization errors only when message output is explicitly requested.
- Rationale: This protects artifact integrity for reporting workflows while avoiding unrelated run failures when reporting is not in use.
- Alternatives considered:
  - Always fail: rejected due unnecessary disruption for non-reporting runs.
  - Never fail: rejected because enabled reporting would silently produce invalid/partial artifacts.

## Decision 4: MyPy validation must directly cover message-construction code paths

- Decision: Include message-building modules in strict type-validation workflow and reduce suppressions that hide incorrect message construction.
- Rationale: Static typing is required by the spec to catch invalid field assignment before runtime.
- Alternatives considered:
  - Runtime-only validation via parser/converter: rejected because it detects issues later and misses some construction-time errors.
  - Keep broad `type: ignore` suppressions: rejected because suppressions mask the target defect class.

## Decision 5: Protocol compatibility scope is latest-version only

- Decision: Validate and support only the latest supported message protocol version in this feature.
- Rationale: Narrowing protocol scope keeps contract surface deterministic and avoids broad backward-compatibility work not requested in this feature.
- Alternatives considered:
  - Current + previous compatibility window: rejected per accepted clarification.
  - Best-effort all historical versions: rejected due high complexity and weak determinism.

## Decision 6: Resolve duplicate prefix conflicts by renumbering only collisions

- Decision: Keep non-conflicting historical prefix numbers unchanged, but rename colliding directories to the next available number and enforce unique monotonic numbering for new specs.
- Rationale: This resolves prerequisite-script ambiguity with minimal repository churn.
- Alternatives considered:
  - Full repository reindex of all specs: rejected due high risk and widespread path churn.
  - Allow duplicates and weaken script checks: rejected because it preserves ambiguity and future instability.

## Decision 7: Contract artifact uses design-time OpenAPI for validation operations

- Decision: Represent event-stream validation and prefix-audit operations as a design-time OpenAPI contract under `specs/.../contracts/`.
- Rationale: This matches existing repository planning patterns and provides deterministic schema for downstream validation tasks.
- Alternatives considered:
  - No explicit contract artifact: rejected because constitution requires explicit deterministic contract definition.
  - GraphQL schema: rejected because existing feature plans and tooling use OpenAPI-style design contracts.

## Clarification Resolution Status

- Outstanding `NEEDS CLARIFICATION` items in plan technical context: **none**.
