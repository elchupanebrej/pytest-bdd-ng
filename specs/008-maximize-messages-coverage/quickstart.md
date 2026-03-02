# Quickstart: Maximize Messages Capability Coverage

## 1. Prepare environment

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 tox -l
```

## 2. Verify mandatory scope list

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
wc -l specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt
```

Expected outcome:
- The mandatory scope file exists and lists `323` capability IDs.

## 3. Generate capability inventory from approved baseline

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.model.coverage.inventory \
  --schema-dir messages/jsonschema/src \
  --baseline-release v32.current \
  --output /tmp/messages-capabilities.json
```

Expected outcome:
- Inventory output contains one entry per relevant capability.
- No duplicate capability IDs.

## 4. Run dedicated mandatory audit suite and emit NDJSON

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
mkdir -p /tmp/pytest-bdd-ng-messages-audit
PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/messages_coverage/test_mandatory_attachments.py -q \
  -p no:pytest-bdd-gherkin-message-reporter \
  -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
  --messages-ndjson /tmp/pytest-bdd-ng-messages-audit/messages-mandatory.ndjson \
  --messages-coverage
```

Expected outcome:
- Dedicated suite executes independently from the main suite.
- `/tmp/pytest-bdd-ng-messages-audit/messages-mandatory.ndjson` is created.
- Run summary is `3 passed`.

## 5. Generate governance report with strict mandatory enforcement

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance report \
  --messages-file /tmp/pytest-bdd-ng-messages-audit/messages-mandatory.ndjson \
  --baseline-release v32.current \
  --schema specs/008-maximize-messages-coverage/contracts/governance-report.schema.json \
  --decisions specs/008-maximize-messages-coverage/contracts/capability-decisions.json \
  --mandatory-capabilities-file specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt \
  --require-mandatory-implemented \
  --require-fully-governed \
  --output /tmp/pytest-bdd-ng-messages-audit/governance-governed.json
```

Expected outcome:
- Report conforms to governance schema.
- `blocked_capabilities == 0`.
- `mandatory_scope_violations == 0`.
- Every ID from `mandatory-hook-capability-ids.txt` is reported as `Implemented`.

## 6. Dedicated regression slice (executed)

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1 conda run -n pytest-bdd-ng-py314 python -m pytest \
  tests/messages_coverage -q
```

Observed result during feature implementation:
- `4 passed`
- strict governance summary values:
  - `mandatory_capabilities_total = 323`
  - `mandatory_capabilities_implemented = 323`
  - `mandatory_scope_violations = 0`
  - `blocked_capabilities = 0`

## 7. Execute baseline drift check

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance diff \
  --previous-baseline v32.previous \
  --current-baseline v32.current \
  --previous-governance /tmp/governance-prev.json \
  --current-governance /tmp/pytest-bdd-ng-messages-audit/governance-governed.json \
  --output /tmp/baseline-diff.json
```

Expected outcome:
- `baseline-diff.json` lists added/changed/removed capability IDs.
- Non-empty deltas trigger governance review before release sign-off.
