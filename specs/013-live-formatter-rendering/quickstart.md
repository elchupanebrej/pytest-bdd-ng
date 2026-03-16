# Quickstart: Live Formatter Rendering

## Preconditions

- Use the repository development environment, for example:
  `conda run -n pytest-bdd-ng-py314 ...`
- Ensure `node` and `npm` are available on `PATH` when running formatter
  validations.
- Ensure `pytest-xdist` is installed before running distributed validation
  slices.
- Terminal formatter validations must use the real CLI path without adding
  `-s` or `--capture=no`; pytest-bdd-ng switches capture automatically when a
  terminal formatter flag is active.
- If you launch manual live-output checks through `conda run`, add
  `--live-stream` so conda does not buffer formatter output.

## Architecture Guardrails

- The reporter root must remain a narrow coordination boundary rather than
  owning formatter request resolution, service-graph assembly, xdist role
  selection, and runtime asset preparation directly.
- The pytest entrypoint must configure and unconfigure reporting through one
  explicit public lifecycle contract and must not fall back to duck typing over
  private runtime state.
- Runtime services must use explicit direct collaborator dependencies rather
  than reporter-backed service-locator accessors.
- Standalone NDJSON replay must use a first-class application service boundary
  rather than synthetic pytest `Config` or pluginmanager stand-ins.
- Each supported formatter must resolve through its own formatter plugin module
  or formatter-owned collaborators; shared support code may provide reusable
  primitives only.
- Supported runtime paths must use one canonical formatter discovery source per
  execution mode; package-scan fallback is not an accepted supported path.
- Generated helper scripts longer than 20 lines must be rendered from
  checked-in resource/template assets rather than embedded as Python string
  literals.

## Focused Validation Slices

### 1. Contract slice

Validate public CLI behavior and formatter request normalization:

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/contract/test_cucumber_formatter_cli_contract.py -q
```

### 2. Hook and lifecycle slice

Validate explicit entrypoint and runtime lifecycle behavior:

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/hook/test_gherkin_reporter_context_lifecycle.py -q
```

Expected observation:

- The reporting runtime starts and stops through one explicit lifecycle
  contract.
- Terminal-output ownership is activated and restored without duck-typed
  fallback against private runtime state.

### 3. Single-process live formatter slice

Validate that active formatters consume the live stream during a standard run:

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_cucumber_formatters.py -q
```

Manual smoke command for visible live terminal output:

```bash
PYTHONPATH=src conda run --live-stream -n pytest-bdd-ng-py314 python -m pytest \
  /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_report_doc_cucumber_formatters.py \
  --cucumber-summary
```

Expected observation:

- Console formatter scenarios show visible formatter output before the run is
  fully finished.
- For validation runs designed to satisfy the feature success criteria, record
  total elapsed time and confirm the first visible formatter output appears
  before 25% of that elapsed time.
- File formatter scenarios still produce complete final artifacts from the same
  live session.

### 4. Standalone replay boundary slice

Validate that replay uses the supported standalone service boundary:

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/compatibility/test_render_cucumber_formatters.py -q
```

Expected observation:

- Replay accepts canonical NDJSON and normalized formatter requests without
  building a synthetic pytest runtime.
- Replay reuses the same formatter inventory and runtime assets as the live
  runtime.

### 5. Distributed controller-only slice

Validate worker forwarding and controller-owned rendering behavior:

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_xdist_message_aggregation.py -k live_formatter_stream -q
```

Expected observation:

- Only one live formatter session is observed for the run.
- Worker-originated envelopes are present inside that controller-owned live
  stream.
- Controller-only rendering remains the only supported distributed rendering
  authority.

### 6. Documentation-backed slice

Keep user-facing reporting examples aligned with behavior:

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/e2e/test_report_doc_cucumber_formatters.py -q
```

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest \
  /Users/goloveshkokonstantin/Projects/pytest-bdd-ng/tests/doc/test_cucumber_formatter_report_doc_parse.py -q
```

## Distributed Gateway Note

If validation needs to cover non-native distributed gateway targets, use the
repository Docker workflow in line with the constitution requirement for
non-native platform testing.

## Validation Notes

- 2026-03-14: planning artifacts updated to require a narrow reporter root, one
  explicit entrypoint lifecycle contract, explicit service dependencies, a
  first-class standalone rendering service, formatter-owned behavior, and one
  canonical discovery source per execution mode.
- 2026-03-14: `tests/contract/test_cucumber_formatter_cli_contract.py tests/hook/test_gherkin_reporter_context_lifecycle.py -q` -> `41 passed`
- 2026-03-14: `tests/contract/test_cucumber_formatter_cli_contract.py tests/contract/test_standalone_rendering_boundary_contract.py tests/compatibility/test_render_cucumber_formatters.py tests/hook/test_gherkin_reporter_context_lifecycle.py tests/model/test_cucumber_formatter_adapter.py -q` -> `57 passed`
- 2026-03-14: `tests/e2e/test_cucumber_formatters.py tests/e2e/test_cucumber_formatters_feature.py tests/e2e/test_report_doc_cucumber_formatters.py tests/e2e/test_xdist_message_aggregation.py tests/e2e/test_xdist_remote_message_aggregation.py tests/e2e/test_xdist_html_reporting.py tests/messages/test_xdist_remote_transport.py tests/hook/test_live_formatter_output_relay.py tests/compatibility/test_e2e_inventory.py tests/compatibility/test_e2e_no_duplicates.py -q` -> `55 passed, 9 skipped`
- 2026-03-14: `tests/doc/test_cucumber_formatter_report_doc_parse.py tests/e2e/test_report_doc_gathering_html.py -q` -> `4 passed`
- 2026-03-14: `PYTHONPATH=src:. conda run --live-stream -n pytest-bdd-ng-py314 python -m pytest docs/tutorial/tests -p no:pytest-bdd-gherkin-message-reporter -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint --cucumber-html .tmp/reports/tutorial-books.html -q` -> `1 passed`
- 2026-03-14: `python .codex/skills/tox-test-matrix/scripts/run_tox_matrix.py --env py314-ruff` -> `OK`
- 2026-03-14: `python .codex/skills/tox-test-matrix/scripts/run_tox_matrix.py --env py314-pytestlatest-gherkinlatest-xdist-coverage-mac` -> `687 passed, 19 skipped`
- 2026-03-12: `tests/contract/test_cucumber_formatter_cli_contract.py tests/compatibility/test_render_cucumber_formatters.py tests/doc/test_cucumber_formatter_report_doc_parse.py -q` -> `11 passed`
- 2026-03-12: `tests/e2e/test_cucumber_formatters.py tests/e2e/test_cucumber_formatters_feature.py -q` -> `29 passed`
- 2026-03-12: `tests/e2e/test_xdist_message_aggregation.py tests/messages/test_xdist_remote_transport.py tests/hook/test_live_formatter_output_relay.py -q` -> `10 passed`
- 2026-03-12: `tests/e2e/test_e2e.py -q` -> `99 passed`
- 2026-03-12: `tests/compatibility/test_e2e_inventory.py tests/compatibility/test_e2e_no_duplicates.py tests/compatibility/test_e2e_classification.py tests/e2e/test_xdist_html_reporting.py -q` -> `10 passed`
- 2026-03-12: `python .codex/skills/tox-test-matrix/scripts/run_tox_matrix.py --env py314-ruff` -> `OK`
- 2026-03-12: `python .codex/skills/tox-test-matrix/scripts/run_tox_matrix.py --env py314-pytestlatest-gherkinlatest-xdist-coverage-mac` -> `673 passed, 19 skipped`
