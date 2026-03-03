# Quickstart: Runtime-Pure Messages Coverage Governance

## 1. Prepare environment

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 tox -l
```

Expected outcome:
- Toolchain and tox environments are available.

## 2. Generate canonical capability inventory

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.model.coverage.inventory \
  --schema-dir messages/jsonschema/src \
  --baseline-release v32.current \
  --output /tmp/messages-capabilities.json
```

Expected outcome:
- Canonical inventory is generated.
- Capability IDs are unique and normalized.

## 3. Execute dedicated real-runtime evidence suite

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
mkdir -p /tmp/pytest-bdd-ng-messages-audit
PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/messages_coverage/test_mandatory_attachments.py -q \
  -p no:pytest-bdd-gherkin-message-reporter \
  -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
  --messages-ndjson /tmp/pytest-bdd-ng-messages-audit/messages-runtime.ndjson
```

Expected outcome:
- Dedicated suite runs separately from the main suite.
- NDJSON contains only real emitted runtime events.
- No synthetic probe payloads are injected.

## 4. Produce post-factum governance report

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
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

Expected outcome:
- Report schema validation succeeds.
- Runtime-required coverage is complete.
- Non-runtime capabilities are either runtime-covered or explicitly classified.

## 5. Validate hard-limit exception quality

Review `specs/008-maximize-messages-coverage/contracts/capability-decisions.json` and verify every `Non-Implementable` entry has:
- hard technical impossibility rationale (not implementation backlog),
- reproducible evidence references,
- decision owner,
- review timestamp for current release cycle,
- `recheck_trigger`.

Expected outcome:
- Every exception is auditable and technically justified.

## 6. Run governance-focused suites

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/messages_coverage -q
```

Expected outcome:
- Dedicated audit suite passes.
- Failures point to missing runtime-required evidence or invalid governance decisions.

## 7. Run complete end-to-end regression and HTML report

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/e2e -q \
  -p no:pytest-bdd-gherkin-message-reporter \
  -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
  --cucumber-html /tmp/pytest-bdd-ng-e2e-report.html
```

Expected outcome:
- E2E suite passes.
- HTML report is generated at `/tmp/pytest-bdd-ng-e2e-report.html`.

## 8. Baseline drift check (weekly cadence)

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance diff \
  --previous-baseline v32.previous \
  --current-baseline v32.current \
  --previous-governance /tmp/governance-prev.json \
  --current-governance /tmp/pytest-bdd-ng-messages-audit/governance-runtime.json \
  --output /tmp/baseline-diff.json
```

Expected outcome:
- Added/changed/removed capability IDs are explicit.
- Any drift is routed through governance review before release sign-off.
