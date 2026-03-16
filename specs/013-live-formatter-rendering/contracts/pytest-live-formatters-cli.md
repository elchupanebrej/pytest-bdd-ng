# Contract: Pytest Live Formatters CLI

## Purpose

Define the public pytest CLI behavior for cucumber formatter requests once live
incremental rendering is enabled.

## Supported Request Surface

The existing formatter flags remain the public activation surface. When any of
these flags are requested, the formatter joins the live execution stream for the
run instead of depending on a separate post-run-only replay step.

| Flag | Output target | Live-stream obligation |
|------|---------------|------------------------|
| `--cucumber-summary` | Console | Must consume the live stream during the run and may emit most visible output near the end. |
| `--cucumber-progress` | Console | Must consume the live stream during the run and may emit visible progress incrementally. |
| `--cucumber-progress-bar` | Console | Must consume the live stream during the run and may emit visible progress incrementally. |
| `--cucumber-snippets` | Console | Must consume the live stream during the run. |
| `--cucumber-pretty` | Console | Must consume the live stream during the run. |
| `--cucumber-usage[=path]` | Console or file | Must consume the live stream during the run; visible output timing depends on formatter behavior and target. |
| `--cucumber-json=path` | File | Must consume the live stream during the run and finalize the file output when the session closes. |
| `--cucumber-junit=path` | File | Must consume the live stream during the run and finalize the file output when the session closes. |
| `--cucumber-usage-json=path` | File | Must consume the live stream during the run and finalize the file output when the session closes. |

## Behavioral Guarantees

1. Active formatter requests consume execution envelopes while pytest is still
   running.
2. A formatter may choose when visible output appears, but it must not switch to
   an entirely separate post-run-only message source.
3. Final formatter outputs must remain consistent with the completed run.
4. Existing formatter flag names and argument shapes remain stable.
5. Internal plugin decomposition, explicit lifecycle contracts, formatter-owned
   behavior, or template-backed script rendering must not change the public CLI
   contract exposed by these flags.

## Distributed Execution Rules

1. When distributed execution is active, workers do not render formatter output
   directly.
2. The controller/main reporting authority owns the live formatter session and
   forwards worker-derived events into it.
3. Users observe one coherent live formatter stream from the controller/main
   authority rather than competing worker-local streams.

## Failure Rules

1. If live delivery cannot be established or maintained reliably, users receive
   an actionable error.
2. The system must not silently downgrade formatter requests to a post-run-only
   rendering path.

## Compatibility Surface

- `--messages-ndjson=path` remains the canonical report artifact for replay and
  post-run validation.
- `python -m pytest_bdd.script.render_cucumber_formatters` remains a supported
  compatibility entrypoint for replaying an existing canonical NDJSON stream
  through the standalone rendering service boundary.
