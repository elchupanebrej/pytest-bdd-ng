<!-- markdownlint-disable MD013 -->

# Research: Jinja2 Documentation Generation Migration

## Decision 1: Replace Mako templates with Jinja2 templates under package resources

- Decision: Use `.jinja2` templates in `src/pytest_bdd/template/` for both code generation and documentation generation flows.
- Rationale: One template engine across both flows removes mixed-engine complexity and keeps runtime resolution deterministic.
- Alternatives considered:
  - Keep dual-engine support (Mako + Jinja2): rejected due to maintenance burden and ambiguous behavior.
  - Inline templates in Python modules: rejected due to poor readability and harder reviewability.

## Decision 2: Preserve manual documentation via explicit generated-section markers

- Decision: Keep marker-based replacement for generated content in `docs/features/features.rst`, replacing only the generated block.
- Rationale: This guarantees manual curation outside markers is preserved while allowing deterministic regeneration.
- Alternatives considered:
  - Full-file overwrite on regeneration: rejected because it destroys manual content.
  - Heuristic merge without markers: rejected because behavior is brittle and non-deterministic.

## Decision 3: Define migration parity as semantic parity

- Decision: Enforce semantic parity with baseline generation output; non-functional formatting differences are allowed.
- Rationale: Aligns with approved clarification and avoids brittle byte-level failures with no user value.
- Alternatives considered:
  - Byte-for-byte parity: rejected due to high maintenance cost and low practical value.
  - No parity requirement: rejected because compatibility risk becomes unbounded.

## Decision 4: Enforce stale-doc detection in pre-commit

- Decision: Keep documentation generation/sync checks in pre-commit so stale generated docs fail before commit.
- Rationale: Shortens feedback loop and ensures repository state remains synchronized.
- Alternatives considered:
  - CI-only enforcement: rejected because feedback is delayed.
  - Optional local check: rejected because enforcement would be inconsistent.

## Decision 5: Package only required Jinja2 template assets

- Decision: Include `.jinja2` template assets in package metadata and remove legacy `.mak` assets from runtime packaging paths.
- Rationale: Installed distributions must contain required runtime assets without legacy ambiguity.
- Alternatives considered:
  - Ship both `.mak` and `.jinja2` assets: rejected because it obscures active runtime path.

## Decision 6: Keep `docs/features/features.rst` scoped to generated feature documentation context

- Decision: Restrict `docs/features/features.rst` to feature-file-driven generated navigation and user-facing context; move internal implementation/change-history notes to a separate document.
- Rationale: Aligns with FR-011/FR-012 and keeps generated docs consumer-facing and stable.
- Alternatives considered:
  - Keep internal migration notes in `features.rst`: rejected because it mixes implementation internals with generated-user docs.
  - Remove all explanatory text from `features.rst`: rejected because minimal user-facing context is still useful.

## Decision 7: Validate migration with focused suites before broad matrix runs

- Decision: Use targeted generation/doc/contract tests plus pre-commit as migration acceptance baseline, then run broader matrix checks as follow-up.
- Rationale: Preserves fast feedback for migration-critical behavior while retaining wider compatibility confidence.
- Alternatives considered:
  - Full matrix only on every iteration: rejected due to slower loop and lower iteration speed.

## Clarification Resolution Status

- Outstanding `NEEDS CLARIFICATION` items in plan technical context: **none**.
