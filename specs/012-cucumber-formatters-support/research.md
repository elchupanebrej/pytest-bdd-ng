# Phase 0: Research

## Objective

Resolve the implementation strategy for exposing supported `cucumber-js`
formatters through pytest CLI flags while preserving deterministic NDJSON-based
reporting, fail-fast validation, and consistent dependency handling.

## Decision 1: Render only from the final canonical NDJSON stream

- **Decision**: Formatter rendering will run only after the canonical NDJSON
  stream has been finalized, including xdist consolidation when distributed
  execution is active.
- **Rationale**: Built-in cucumber formatters consume a complete event stream.
  Rendering after session completion avoids partial reports, stdout races with
  pytest's own terminal output, and duplicate work across xdist workers.
- **Alternatives considered**:
  - Stream formatter output live during test execution: rejected because it
    complicates xdist consolidation and produces nondeterministic terminal
    interleaving.
  - Reconstruct formatter-specific summaries directly in Python: rejected
    because it would diverge from the official cucumber formatter behavior.

## Decision 2: Enforce terminal-output formatter exclusivity before test execution

- **Decision**: At most one terminal-output formatter request may be active in
  a run. If the user passes more than one of `summary`, `progress`,
  `progress-bar`, `snippets`, `pretty`, or `usage` in stdout mode, pytest must
  fail before test execution with a clear configuration error.
- **Rationale**: The spec explicitly excludes terminal reporter interaction.
  Failing during configuration is easier to understand and test than allowing
  one formatter to silently override another.
- **Alternatives considered**:
  - Last flag wins: rejected because ordering-based behavior is implicit and
    hard to discover.
  - First flag wins: rejected for the same reason and because it still hides a
    user mistake.
  - Merge multiple terminal formatters: rejected because it expands scope into
    output composition and ordering semantics that the spec explicitly excludes.

## Decision 3: Treat file output directories as caller-owned

- **Decision**: File-based formatters must fail with a clear filesystem error
  when the requested parent directory does not exist. The reporter must not
  create directories automatically.
- **Rationale**: This keeps report emission predictable in CI, prevents silent
  writes into unintended locations, and matches the clarified fail-fast policy
  in the spec.
- **Alternatives considered**:
  - Auto-create parent directories: rejected because it hides configuration
    errors and can create unreviewed filesystem side effects.
  - Downgrade to warning and skip one formatter: rejected because it yields
    partially successful runs that are harder to diagnose.

## Decision 4: Resolve npm packages locally first, then auto-provision globally

- **Decision**: The reporter should first try to resolve formatter packages
  from the active Node.js environment. If the required package is missing, it
  may attempt `npm install -g` for `@cucumber/cucumber` or
  `@cucumber/pretty-formatter`. If installation still fails, the reporter must
  emit a manual-install hint and fail the formatter request.
- **Rationale**: Local resolution keeps compatibility with deterministic
  project-managed Node environments, while global auto-provisioning preserves
  the zero-config workflow requested for ad hoc runs.
- **Alternatives considered**:
  - Require preinstalled packages only: rejected because it worsens usability
    compared to the existing HTML reporter behavior.
  - Install into repository-local `node_modules` automatically: rejected
    because it mutates the project workspace and package metadata.
  - Use a temp-only cache: rejected because the current desired behavior is to
    reuse packages across runs on the same machine.

## Decision 5: Model formatter behavior from a stable flag-to-package mapping

- **Decision**: Treat each formatter as a static mapping of pytest option
  destination, CLI flag, formatter identifier, npm package, and output mode.
  Built-in formatters (`summary`, `progress`, `progress-bar`, `json`, `junit`,
  `usage`, `usage-json`, `snippets`) resolve through `@cucumber/cucumber`;
  `pretty` resolves through `@cucumber/pretty-formatter`.
- **Rationale**: A declarative mapping keeps validation logic, render planning,
  and tests aligned and makes it straightforward to express output-mode rules
  such as `stdout`, `path`, and `optional_path`.
- **Alternatives considered**:
  - Hardcode per-flag behavior in multiple branches: rejected because it makes
    validation and future maintenance error-prone.
  - Model `pretty` as a built-in formatter: rejected because it comes from a
    separate npm package and needs distinct dependency handling.

## Decision 6: Keep legacy `--cucumberjson` outside the new formatter contract

- **Decision**: The legacy `--cucumberjson` plugin path remains a separate
  compatibility surface. `--cucumber-json` belongs to the gherkin
  message-reporter-backed formatter flow defined by this feature.
- **Rationale**: The repository already differentiates the legacy plugin from
  the newer message-based formatter flow. Preserving that split keeps backward
  compatibility explicit and prevents accidental option alias overlap.
- **Alternatives considered**:
  - Merge legacy and new JSON paths into one option family: rejected because it
    obscures compatibility expectations and makes xdist/reporting ownership less
    explicit.

## Decision 7: Treat same normalized file output paths as conflicting requests

- **Decision**: If two file-based formatter requests resolve to the same
  normalized path, the run should fail as a configuration conflict.
- **Rationale**: FR-006 allows multiple outputs only when they do not conflict.
  Reusing one path for different formatter payloads is nondeterministic and can
  silently overwrite data.
- **Alternatives considered**:
  - Last writer wins: rejected because it hides misconfiguration.
  - Allow shared paths only for matching formatter types: rejected because the
    feature does not require cross-run append or reuse semantics.
