# Contract: Pytest Cucumber Formatter CLI

## Scope

Defines the public pytest CLI contract for cucumber formatter support exposed by
`pytest-bdd-ng`.

## Supported Flags

| Flag | Formatter ID | Package | Output Mode |
|------|--------------|---------|-------------|
| `--cucumber-summary` | `summary` | `@cucumber/cucumber` | terminal |
| `--cucumber-progress` | `progress` | `@cucumber/cucumber` | terminal |
| `--cucumber-progress-bar` | `progress-bar` | `@cucumber/cucumber` | terminal |
| `--cucumber-json=PATH` | `json` | `@cucumber/cucumber` | file |
| `--cucumber-junit=PATH` | `junit` | `@cucumber/cucumber` | file |
| `--cucumber-usage[=PATH]` | `usage` | `@cucumber/cucumber` | terminal when no path is provided; file when a path is provided |
| `--cucumber-usage-json=PATH` | `usage-json` | `@cucumber/cucumber` | file |
| `--cucumber-snippets` | `snippets` | `@cucumber/cucumber` | terminal |
| `--cucumber-pretty` | `pretty` | `@cucumber/pretty-formatter` | terminal |

## Selection Rules

- File-based formatter flags may be combined in one run.
- At most one terminal-output formatter may be active in one run.
- `--cucumber-usage` without a path counts as a terminal-output formatter.
- `--cucumber-usage=PATH` counts as a file-output formatter.
- Two file-based formatter requests must not resolve to the same normalized
  path.
- Formatter rendering consumes the canonical NDJSON stream produced for the
  logical pytest run.

## Validation Rules

- If more than one terminal-output formatter flag is active, pytest must fail
  before test execution with a clear configuration error.
- If a file-based formatter path points into a missing parent directory, pytest
  must fail with a clear filesystem error.
- If multiple file-based formatters target the same normalized path, pytest
  must fail with a clear configuration error.
- The reporter must not create missing output directories automatically.
- If no Node.js runtime is available when formatter rendering is requested,
  pytest must fail with a clear diagnostic.

## Dependency Resolution Rules

- The reporter first tries to resolve required npm packages from the active
  Node.js environment.
- Missing packages may be auto-provisioned via global `npm install -g`.
- If auto-provisioning fails, the error must name the missing package and
  instruct the user how to install it manually.
- Legacy `--cucumberjson` compatibility remains outside this contract; this
  contract covers the message-reporter-backed `--cucumber-json` path only.

## Output Timing Rules

- Formatter output is derived only after the final canonical NDJSON stream is
  available.
- Under xdist, rendering uses the consolidated logical run rather than
  worker-local fragments.
- Terminal formatter output may appear after pytest finishes executing tests
  because rendering is post-run.

## Validation Requirements

- Acceptance tests must cover each supported formatter flag.
- Acceptance tests must cover the terminal conflict error case.
- Acceptance tests must cover the missing-directory error case.
- Validation must confirm that xdist-derived outputs represent the consolidated
  run.
- Validation must confirm that legacy `--cucumberjson` behavior is not
  redefined by this contract.
