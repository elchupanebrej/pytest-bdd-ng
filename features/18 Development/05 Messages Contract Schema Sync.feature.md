# Feature: Messages Contract Schema Sync CLI
  Verify the sync_messages_contract_schemas.py CLI tool detects schema drift against the official Cucumber contract version.

## Scenario: Schema check passes on identical schema set
  * Given Copy path from "src/pytest_bdd/model/message_jsonschema" to test path "message_jsonschema"
  * When run `python -m pytest_bdd.script.sync_messages_contract_schemas --schema-path message_jsonschema`
  * And run `python -m pytest_bdd.script.sync_messages_contract_schemas --check --schema-path message_jsonschema`
  * Then the command exit code is 0

## Scenario: Schema check fails when local schema has drifted
  * Given Copy path from "src/pytest_bdd/model/message_jsonschema" to test path "message_jsonschema"
  * And Mock file "message_jsonschema/Attachment.schema.json" with content:

    ```json
    {
      "type": "object",
      "properties": {
        "driftedProperty": { "type": "string" }
      }
    }
    ```
  * When run `python -m pytest_bdd.script.sync_messages_contract_schemas --check --schema-path message_jsonschema`
  * Then the command exit code is 1
  * And the renderer terminal output includes:
    | Generated Cucumber messages schemas are stale |
    | Attachment.schema.json |
