# User Guide: Messages Coverage and Governance (Features 007/008)

This guide describes the runtime-pure reporting and post-factum governance flow.

## Feature split

- Feature 007: canonical capability inventory, baseline diffing, and governance primitives.
- Feature 008: runtime-pure reporter behavior (real events only), dedicated coverage suite, runtime-required gate, and non-runtime classification gate.

## Principles

- Reporter emits only real runtime events.
- No synthetic probe payloads.
- No test-only substitutions in normal plugin flow.
- Coverage and governance are computed from NDJSON after test execution.

## Prerequisites

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
```

Plugin is loaded explicitly when `--messages-ndjson` or `--cucumber-html` is used:

```bash
-p no:pytest-bdd-gherkin-message-reporter -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint
```

## 1. Generate runtime evidence NDJSON

```bash
mkdir -p /tmp/pytest-bdd-ng-messages-audit
PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/messages_coverage/test_mandatory_attachments.py -q \
  -p no:pytest-bdd-gherkin-message-reporter \
  -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
  --messages-ndjson /tmp/pytest-bdd-ng-messages-audit/messages-runtime.ndjson
```

## 2. Build governance report from NDJSON

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance report \
  --messages-file /tmp/pytest-bdd-ng-messages-audit/messages-runtime.ndjson \
  --baseline-release v32.current \
  --schema specs/008-maximize-messages-coverage/contracts/governance-report.schema.json \
  --decisions specs/008-maximize-messages-coverage/contracts/capability-decisions.json \
  --mandatory-capabilities-file specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt \
  --runtime-required-capabilities-file specs/008-maximize-messages-coverage/runtime-required-capability-ids.txt \
  --require-runtime-required-covered \
  --require-non-runtime-classified \
  --require-fully-governed \
  --output /tmp/pytest-bdd-ng-messages-audit/governance-runtime.json
```

## 3. Read report summary

Important summary keys:

- `runtime_required_total`
- `runtime_required_covered`
- `runtime_required_missing`
- `non_runtime_required_total`
- `non_runtime_covered`
- `non_runtime_classified`
- `blocked_capabilities`
- `mandatory_scope_violations`

Gate expectations:

- Runtime-required capabilities must be covered by real runtime evidence.
- Non-runtime-required capabilities must be covered or explicitly classified.
- Release gate fails when blockers remain.

## 4. One-command audit

```bash
scripts/run_messages_coverage_audit.sh
```

This script runs the dedicated runtime-evidence suite and then executes governance report gating.

## 5. CI workflow

CI uses the same dedicated suite and governance gates in:

```text
.github/workflows/messages-baseline-drift.yml
```

## Troubleshooting

- `unrecognized arguments: --messages-ndjson`:
  load the reporter plugin explicitly.
- Duplicate reporter registration:
  use `-p no:pytest-bdd-gherkin-message-reporter` before explicit plugin load.
- Governance schema validation errors:
  ensure `--schema` points to `specs/008-maximize-messages-coverage/contracts/governance-report.schema.json`.
