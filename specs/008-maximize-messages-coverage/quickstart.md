# Quickstart: Maximize Messages Capability Coverage

## 1. Prepare environment

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 tox -l
```

## 2. Generate capability inventory from approved baseline

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.model.coverage.inventory --schema-dir messages/jsonschema/src
```

Expected outcome:
- Inventory output contains one entry per relevant capability.
- No duplicate capability IDs.

## 3. Run message suite with opt-in coverage tracing

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 pytest tests/messages -q \
  -p no:pytest-bdd-gherkin-message-reporter \
  -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
  --messages-ndjson=messages.ndjson \
  --messages-coverage
```

Expected outcome:
- Test run emits `messages.ndjson`.
- Validation fails immediately on missing required coverage evidence or structural payload mismatch.

## 4. Produce governance checklist artifact

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance report \
  --messages-file messages.ndjson \
  --decisions specs/008-maximize-messages-coverage/contracts/capability-decisions.json \
  --require-fully-governed \
  --output governance.json
```

Expected outcome:
- `governance.json` conforms to `contracts/governance-report.schema.json`.
- Unresolved capabilities are marked as blocker or deferred.

## 5. Execute baseline drift check

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance diff \
  --previous-governance governance-prev.json \
  --current-governance governance.json \
  --output baseline-diff.json
```

Expected outcome:
- `baseline-diff.json` lists `added_capability_ids`, `changed_capability_ids`, and `removed_capability_ids`.
- Non-empty delta lists require governance review before release sign-off.
