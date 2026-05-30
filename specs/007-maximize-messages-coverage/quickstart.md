# Quickstart: Maximize Messages Capability Coverage

## Setup
Ensure dependencies are installed:

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 pip install jsonschema
uv sync --extra test
```

## Generate Capability Inventory
Generate the base inventory from the provided schema:

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.model.coverage.inventory --schema-dir messages/jsonschema/src
uv run python -m pytest_bdd.model.coverage.inventory --schema-dir messages/jsonschema/src
```

## Run Messages with Coverage Tracing
Execute tests to populate tracking context:

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 pytest tests/messages/ \
#   -p no:pytest-bdd-gherkin-message-reporter \
#   -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
#   --messages-ndjson=messages.ndjson \
#   --messages-coverage
uv run pytest tests/messages/ \
  -p no:pytest-bdd-gherkin-message-reporter \
  -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
  --messages-ndjson=messages.ndjson \
  --messages-coverage
```

## Generate Governance Artifact
Evaluate tracked coverage against the schema inventory:

```bash
# Legacy workflow:
# conda run -n pytest-bdd-ng-py314 python -m pytest_bdd.script.message_capability_governance report \
#   --messages-file messages.ndjson \
#   --output governance.json
uv run python -m pytest_bdd.script.message_capability_governance report \
  --messages-file messages.ndjson \
  --output governance.json
```
