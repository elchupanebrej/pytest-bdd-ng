Feature: Synchronizing packaged Cucumber Messages schemas
  The installed cuke command can sync pinned upstream JSON schemas into a stable
  package layout, report drift without writes, and preserve existing data on failure.

  Scenario: Sync local upstream-shaped schemas to the runtime schema layout
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "schema-fixture/jsonschema/Envelope.json" contains:
      """json
      {"$id":"Envelope.json","type":"object","properties":{"version":{"type":"string"}}}
      """
    And consumer file "schema-fixture/jsonschema/TestCase.json" contains:
      """json
      {"$id":"TestCase.json","type":"object","required":["id","pickleId"]}
      """
    And consumer file "schema-fixture/jsonschema/README.md" contains:
      """text
      Non-schema files in the upstream jsonschema folder are ignored.
      """
    When I run command "cuke" with arguments "sync messages schemas --schema-path schema-output --source-dir schema-fixture"
    Then the command should exit with code 0
    And schema sync output should name cuke-messages 0.1.0 and upstream tag v24.0.1
    And schema output "schema-output" should match source tree "schema-fixture"

  Scenario: A clean check reports the pinned source and leaves schemas unchanged
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "schema-fixture/jsonschema/Envelope.json" contains:
      """json
      {"$id":"Envelope.json","type":"object"}
      """
    And consumer file "schema-fixture/jsonschema/TestCase.json" contains:
      """json
      {"$id":"TestCase.json","type":"object"}
      """
    When I run command "cuke" with arguments "sync messages schemas --schema-path schema-output --source-dir schema-fixture"
    Then the command should exit with code 0
    When I snapshot consumer directory "schema-output" for schema sync
    And I run command "cuke" with arguments "sync messages schemas --schema-path schema-output --source-dir schema-fixture --check"
    Then the command should exit with code 0
    And schema sync output should name cuke-messages 0.1.0 and upstream tag v24.0.1
    And consumer directory "schema-output" should match its schema sync snapshot

  Scenario: A drift check lists changed, missing, and extra schemas in sorted order without writes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And a local schema sync fixture has sorted changed, missing, and extra entries
    When I snapshot consumer directory "schema-output" for schema sync
    And I run command "cuke" with arguments "sync messages schemas --schema-path schema-output --source-dir schema-fixture --check"
    Then the command should exit with a non-zero code
    And schema sync output should list changed, missing, and extra files in sorted groups
    And consumer directory "schema-output" should match its schema sync snapshot

  Scenario: Invalid source JSON leaves the previously synchronized schema tree unchanged
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "schema-fixture/jsonschema/Envelope.json" contains:
      """json
      {"$id":"Envelope.json","type":"object","source":"valid"}
      """
    When I run command "cuke" with arguments "sync messages schemas --schema-path schema-output --source-dir schema-fixture"
    Then the command should exit with code 0
    And schema output "schema-output" should match source tree "schema-fixture"
    And consumer file "schema-fixture/jsonschema/Broken.json" contains:
      """text
      { this is not valid JSON
      """
    When I snapshot consumer directory "schema-output" for schema sync
    And I run command "cuke" with arguments "sync messages schemas --schema-path schema-output --source-dir schema-fixture"
    Then the command should exit with a non-zero code
    And the command output should contain "Broken.schema.json"
    And consumer directory "schema-output" should match its schema sync snapshot

  Scenario: The installed wheel exposes its default schema through the runtime helper
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "test_runtime_schema.py" contains:
      """python
      from pytest_cuke.model.message_schemas import load_message_schema


      def test_default_envelope_schema_is_packaged_and_loadable():
          schema = load_message_schema("Envelope")
          assert schema["$id"] == "Envelope.json"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload -q test_runtime_schema.py"
    Then pytest should exit with code 0
    And pytest output should include "1 passed"
