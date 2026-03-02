# User Guide: Messages Coverage and Governance (Features 007/008)

This guide explains how to use the `messages` coverage and governance capabilities introduced by
features **007** and **008**.

## What 007 and 008 Provide

Feature **007** focuses on:
- Schema-driven capability inventory generation from `messages/jsonschema/src/Envelope.json`
- Runtime field coverage tracking (opt-in)
- Hard-fail validation for invalid message stream structure

Feature **008** extends this with:
- Deterministic outcome mapping and governance status vocabulary
- Governance report schema validation
- Release-facing checklist and baseline drift workflows

## Prerequisites

Run from repository root:

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
```

Use the project environment:

```bash
conda run -n pytest-bdd-ng-py314 tox -l
```

## Important: Message Reporter Plugin Is Explicit

The gherkin message reporter is not auto-loaded via `pytest11`.
Load it explicitly when you need `--messages-ndjson`, `--cucumber-html`, or `--messages-coverage`:

```bash
-p pytest_bdd.plugin.gherkin_message_reporter.entrypoint
```

If your local environment still has old entry-point metadata and you get duplicate plugin registration
errors, use:

```bash
-p no:pytest-bdd-gherkin-message-reporter -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint
```

## Workflow A (007): Coverage Validation

### 1) Generate capability inventory

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.model.coverage.inventory \
  --schema-dir messages/jsonschema/src \
  --baseline-release v32.current \
  --output /tmp/messages-capabilities.json
```

### 2) Run message-producing tests with coverage enabled

```bash
conda run -n pytest-bdd-ng-py314 pytest tests/messages -q \
  -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
  --messages-ndjson=/tmp/messages.ndjson \
  --messages-coverage
```

### 3) Generate governance report from runtime evidence

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance report \
  --messages-file /tmp/messages.ndjson \
  --baseline-release v32.current \
  --output /tmp/governance.json \
  --schema specs/008-maximize-messages-coverage/contracts/governance-report.schema.json
```

## Workflow B (008): Release Governance and Drift

### 1) Produce checklist-style governance output

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance checklist \
  --capabilities /tmp/messages-capabilities.json \
  --decisions /tmp/decisions.json \
  --format markdown \
  --output /tmp/governance-checklist.md
```

### 2) Compare baseline snapshots (diff)

From capability snapshots:

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance diff \
  --previous-baseline v32.previous \
  --current-baseline v32.current \
  --previous /tmp/capabilities-prev.json \
  --current /tmp/capabilities-current.json \
  --output /tmp/baseline-diff.json
```

From governance reports:

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance diff \
  --previous-baseline v32.previous \
  --current-baseline v32.current \
  --previous-governance /tmp/governance-prev.json \
  --current-governance /tmp/governance-current.json \
  --output /tmp/baseline-diff.json
```

## Recommended Validation Slice

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest tests/contract/test_messages_capability_coverage_contract.py \
  tests/messages/test_message_capability_inventory.py \
  tests/messages/test_coverage.py \
  tests/messages/test_message_outcome_mapping.py \
  tests/messages/test_message_validation.py \
  tests/messages/test_governance.py \
  tests/messages/test_message_governance_checklist.py \
  tests/messages/test_message_baseline_diff.py -q
```

## Dedicated Coverage Audit Suite

The dedicated audit suite is intentionally separated from the main test suite.
It enforces this acceptance criterion:

- each capability is either observed as `Implemented`, or
- explicitly governed by a non-implemented decision with required evidence fields.

Run it with:

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
scripts/run_messages_coverage_audit.sh
```

The suite entry point is:

```text
tests/messages_coverage/test_full_capability_governance.py
```

Decision baseline used by the suite:

```text
specs/008-maximize-messages-coverage/contracts/capability-decisions.json
```

## Expected Outputs

- `/tmp/messages-capabilities.json`: schema-derived capability inventory
- `/tmp/messages.ndjson`: runtime message stream
- `/tmp/governance.json`: governance report with summary + capability decisions
- `/tmp/governance-checklist.md`: reviewer-facing checklist
- `/tmp/baseline-diff.json`: added/changed/removed capability IDs

## Troubleshooting

- `unrecognized arguments: --messages-ndjson`:
  load plugin with `-p pytest_bdd.plugin.gherkin_message_reporter.entrypoint`.
- Duplicate plugin registration error:
  add `-p no:pytest-bdd-gherkin-message-reporter` before explicit plugin load.
- Governance report schema validation failure:
  use `--schema specs/008-maximize-messages-coverage/contracts/governance-report.schema.json`.
