# Contract: Formatter Rendering Boundary

## Scope

Defines the boundary between the Python gherkin message reporter and the Node.js
formatter runtime used to render cucumber formatter outputs.

## Input Contract

The Python side must supply:
- one canonical `messages.ndjson` path for the logical run;
- one validated formatter execution plan;
- zero or one terminal-output formatter request;
- zero or more file-output formatter requests;
- the required npm package list derived from the selected formatters.

The boundary must reject:
- more than one terminal-output formatter request;
- file-output requests whose parent directory does not already exist;
- multiple file-output requests that resolve to the same normalized path;
- missing or unreadable NDJSON input.

## Render Timing Contract

- Rendering starts only after NDJSON finalization.
- Under xdist, rendering starts only after worker fragments have been
  consolidated into the canonical stream.
- The rendering layer must not try to consume worker-local fragment files
  directly.

## Package Resolution Contract

- The Python side is responsible for checking package availability before
  invoking the Node.js renderer.
- `@cucumber/cucumber` provides the built-in formatter implementations.
- `@cucumber/pretty-formatter` provides `pretty`.
- When a required package is absent, the Python side may attempt global
  installation with `npm install -g` before invoking the renderer.

## Output Contract

- Terminal output is passed through to the caller's stdout/stderr for the one
  active terminal formatter, if any.
- File outputs are written only to validated caller-provided paths.
- The renderer must not invent additional output files beyond the requested
  formatter targets.

## Failure Contract

- Launch failures, package-resolution failures, NDJSON parse failures, and
  renderer non-zero exits must surface as explicit diagnostics.
- The Python side must preserve enough context in the error message to identify
  the failing formatter flag or package.
- The boundary must fail the affected run rather than silently degrading to
  partial terminal output or partial file generation.

## Validation Requirements

- Hook-level validation must confirm that session-finish rendering uses the
  finalized NDJSON stream.
- Compatibility validation must confirm that renderer invocation from an
  existing NDJSON stream uses the same selection and dependency rules.
- End-to-end validation must confirm that the boundary stays deterministic for
  both single-process and xdist runs.
- Legacy `--cucumberjson` behavior remains outside this boundary.
