<!-- markdownlint-disable MD013 -->

# Research: Template-Driven Feature Documentation Ordering

## Decision 1: Keep `bdd_tree_to_rst.py` as the coordinator and move presentation rules into templates

- Decision: Limit `src/pytest_bdd/script/bdd_tree_to_rst.py` to source discovery, tree traversal, relative-path preparation, and deterministic validation; move index wrapper composition, default feature-doc intro text, heading presentation, and related output-structure rules into Jinja2 templates as far as practical.
- Rationale: This matches the approved clarification boundary, reduces logic density in the script without rewriting the generator, and keeps rendering reviewable in template files.
- Alternatives considered:
  - Keep the current mixed script/template split: rejected because it leaves presentation behavior scattered and preserves the current overgrown script.
  - Move nearly all generation logic out of the script at once: rejected because it exceeds the requested “minimal mechanism change” scope.

## Decision 2: Use numeric prefixes in sibling file and directory names as the only ordering source

- Decision: Order each navigation scope by required numeric prefixes in sibling filenames and directory names.
- Rationale: Numeric prefixes satisfy the requested lightweight control mechanism and avoid a separate metadata registry.
- Alternatives considered:
  - Dedicated metadata file for ordering: rejected because it adds a second source of truth.
  - Displayed numbering in generated labels: rejected because the spec requires user-facing labels to stay clean.

## Decision 3: Keep numeric prefixes in generated paths but strip them from reader-facing labels

- Decision: Preserve numeric prefixes in generated page paths and filenames while removing them from section headings, include-page titles, and navigation labels shown to readers.
- Rationale: This keeps the path derivation simple and stable while presenting cleaner documentation to end users.
- Alternatives considered:
  - Strip prefixes from generated paths as well: rejected because it introduces a path-remapping layer and raises compatibility risk.
  - Show prefixes everywhere: rejected because it exposes maintenance-oriented ordering markers to readers.

## Decision 4: Treat missing or duplicate sibling prefixes as deterministic validation errors

- Decision: Require every sibling item in each ordered navigation scope to carry a unique numeric prefix and fail generation when a prefix is missing or duplicated.
- Rationale: The approved clarification explicitly rejects fallback ordering and requires deterministic error behavior instead of ambiguous output.
- Alternatives considered:
  - Fall back to the previous default sort for unnumbered items: rejected because it conflicts with the clarification and hides configuration mistakes.
  - Warn and continue on duplicates: rejected because output would remain ambiguous and non-deterministic.

## Decision 5: Keep `pypandoc` heading shifting as the preferred normalization path for markdown-backed pages

- Decision: Continue to prefer `pypandoc` with `--shift-heading-level-by` for markdown heading normalization when it helps remove custom heading logic from the script, while keeping the spec outcome-focused rather than forcing `pandoc` in every case.
- Rationale: Existing code already uses this conversion path for markdown gherkin pages, and it directly supports the goal of avoiding new script-side heading math.
- Alternatives considered:
  - Replace `pypandoc` heading shifting with hand-written heading-level calculations in Python: rejected because it increases script-side presentation logic.
  - Make `pandoc` mandatory for every page type: rejected because non-markdown include pages do not need it and the clarification does not require a universal dependency path.

## Decision 6: Reuse the repository’s docs-generation contract pattern

- Decision: Represent the feature’s public behavior with a design-time OpenAPI contract under `specs/010-order-rst-docs/contracts/` and validate implementation with focused doc, contract, generation, and contributor-workflow checks.
- Rationale: This matches existing docs-generation governance patterns already used in `specs/004-migrate-jinja2-docs` and keeps compatibility expectations explicit and versioned.
- Alternatives considered:
  - Use only prose notes in the plan: rejected because it weakens deterministic contract coverage.
  - Use a contract file without focused doc-generation tests: rejected because the constitution requires executable validation.

## Clarification Resolution Status

- Outstanding `NEEDS CLARIFICATION` items in plan technical context: **none**.
