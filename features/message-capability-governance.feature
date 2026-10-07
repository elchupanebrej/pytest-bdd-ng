Feature: Govern Cucumber Messages runtime capabilities
  Capability reports identify whether observations came from a real pytest run
  or from a synthetic Messages fixture.

  Scenario: A runtime report consumes a fresh installed pytest Messages artifact
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the capability governance sample step passes")
      def capability_governance_sample_step():
          pass
      """
    And consumer file "features/capability-governance.feature" contains:
      """gherkin
      Feature: Capability governance sample
        Scenario: The runtime sample step passes
          Given the capability governance sample step passes
      """
    And repository file "specs/message-capability-governance/decisions-v28-0-0.json" is copied to consumer file "decisions-v28-0-0.json"
    And repository file "specs/message-capability-governance/mandatory-v28-0-0.txt" is copied to consumer file "mandatory-v28-0-0.txt"
    And repository file "specs/message-capability-governance/runtime-required-v28-0-0.txt" is copied to consumer file "runtime-required-v28-0-0.txt"
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=runtime-messages.ndjson -q"
    Then pytest should exit with code 0
    And consumer artifact "runtime-messages.ndjson" should be a valid Cucumber Messages stream for 1 passed scenario and 1 passed steps
    When I run command "cuke" with arguments "messages capabilities report --messages-file runtime-messages.ndjson --input-kind runtime --decisions decisions-v28-0-0.json --mandatory-capabilities-file mandatory-v28-0-0.txt --runtime-required-capabilities-file runtime-required-v28-0-0.txt --require-fully-governed --require-runtime-required-covered --format json"
    Then the command should exit with code 0
    And the command JSON should include:
      """json
      {
        "observations": {
          "source_kind": "runtime"
        }
      }
      """
    And the capability report should cover IDs from consumer files "mandatory-v28-0-0.txt" and "runtime-required-v28-0-0.txt"
    When I run command "cuke" with arguments "messages capabilities report --messages-file runtime-messages.ndjson --input-kind runtime --decisions decisions-v28-0-0.json --mandatory-capabilities-file mandatory-v28-0-0.txt --runtime-required-capabilities-file runtime-required-v28-0-0.txt --format markdown"
    Then the command should exit with code 0
    And the command output should contain "# Cucumber Messages capability report (28.0.0)"
    And the command output should contain "Observation source: `runtime`"
    And the command output should contain "## Observed fields"
    And the Markdown capability report should list observations and decisions in stable order
    When I run command "cuke" with arguments "messages capabilities report --messages-file runtime-messages.ndjson --input-kind runtime --decisions decisions-v28-0-0.json --mandatory-capabilities-file mandatory-v28-0-0.txt --runtime-required-capabilities-file runtime-required-v28-0-0.txt --require-non-runtime-classified --format json"
    Then the command should exit with code 1
    And the report should show the v28 non-runtime classification for "attachment.test_run_started_id" and actionable unresolved IDs

  Scenario: A synthetic Messages fixture remains labeled as synthetic
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "synthetic-messages.ndjson" contains:
      """ndjson
      {"meta":{"protocolVersion":"28.0.0","implementation":{"name":"synthetic-fixture","version":"1.0"},"runtime":{"name":"python","version":"3.14"},"os":{"name":"Linux","version":"fixture"},"cpu":{"name":"x86_64"}}}
      {"pickle":{"id":"synthetic-pickle","uri":"features/synthetic.feature","name":"Synthetic scenario","language":"en","steps":[{"id":"synthetic-pickle-step","astNodeIds":["synthetic-ast-step"],"type":"Context","text":"the synthetic capability step"}],"tags":[],"astNodeIds":["synthetic-ast-scenario"]}}
      {"testCase":{"id":"synthetic-test-case","pickleId":"synthetic-pickle","testSteps":[{"id":"synthetic-test-step","pickleStepId":"synthetic-pickle-step"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"synthetic-attempt","testCaseId":"synthetic-test-case","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"synthetic-attempt","testStepId":"synthetic-test-step","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"synthetic-attempt","testStepId":"synthetic-test-step","testStepResult":{"duration":{"seconds":0,"nanos":1},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1}}}
      {"testCaseFinished":{"testCaseStartedId":"synthetic-attempt","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    When I run command "cuke" with arguments "messages capabilities report --messages-file synthetic-messages.ndjson --input-kind synthetic --format json"
    Then the command should exit with code 0
    And the command JSON should include:
      """json
      {
        "observations": {
          "source_kind": "synthetic"
        }
      }
      """
    And consumer file "mandatory-capabilities.txt" contains:
      """text
      test_run_started.id
      """
    And consumer file "runtime-required-capabilities.txt" contains:
      """text
      test_run_started.id
      """
    When I run command "cuke" with arguments "messages capabilities report --messages-file synthetic-messages.ndjson --input-kind synthetic --mandatory-capabilities-file mandatory-capabilities.txt --runtime-required-capabilities-file runtime-required-capabilities.txt --require-runtime-required-covered --format json"
    Then the command should exit with code 1
    And the command JSON should include:
      """json
      {
        "gates": {
          "failures": [
            "require-runtime-required-covered: missing runtime observations for: test_run_started.id"
          ],
          "passed": false
        },
        "observations": {
          "source_kind": "synthetic"
        },
        "scope": {
          "mandatory_capability_ids": [
            "test_run_started.id"
          ],
          "runtime_required_capability_ids": [
            "test_run_started.id"
          ]
        },
        "summary": {
          "runtime_required_covered": 0,
          "runtime_required_missing": 1,
          "runtime_required_total": 1
        }
      }
      """
    When I run command "cuke" with arguments "messages capabilities report --messages-file synthetic-messages.ndjson --input-kind synthetic --mandatory-capabilities-file mandatory-capabilities.txt --require-fully-governed --format json"
    Then the command should exit with code 1
    And the command output should contain "require-fully-governed: missing Implemented decisions for: test_run_started.id"

  Scenario: The public diff exposes inventory and decision changes without rewriting decisions
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "previous-inventory.json" contains:
      """json
      {
        "baseline_release": "27.0.0",
        "capabilities": [
          {
            "capability_id": "testCaseStarted.id",
            "baseline_release": "27.0.0",
            "category": "lifecycle",
            "description": "Previous scenario identifier field.",
            "name": "Scenario Identifier",
            "affects": ["emitted_envelope_payload"],
            "source_reference": "TestCaseStarted.json#/properties/id"
          },
          {
            "capability_id": "test_case_started.id",
            "baseline_release": "27.0.0",
            "category": "lifecycle",
            "description": "Previous scenario identifier field.",
            "name": "Scenario Identifier",
            "affects": ["emitted_envelope_payload"],
            "source_reference": "TestCaseStarted.json#/properties/id"
          },
          {
            "capability_id": "test_case_started.attempt",
            "baseline_release": "27.0.0",
            "category": "lifecycle",
            "description": "Previous attempt field.",
            "name": "Attempt",
            "affects": ["emitted_envelope_payload"],
            "source_reference": "TestCaseStarted.json#/properties/attempt"
          }
        ]
      }
      """
    And consumer file "current-inventory.json" contains:
      """json
      {
        "baseline_release": "28.0.0",
        "capabilities": [
          {
            "capability_id": "test_case_started.id",
            "baseline_release": "28.0.0",
            "category": "lifecycle",
            "description": "Updated scenario identifier field.",
            "name": "Scenario Identifier",
            "affects": ["emitted_envelope_payload"],
            "source_reference": "TestCaseStarted.json#/properties/id"
          },
          {
            "capability_id": "test_case_started.timestamp.seconds",
            "baseline_release": "28.0.0",
            "category": "lifecycle",
            "description": "Scenario start time in seconds.",
            "name": "Timestamp Seconds",
            "affects": ["emitted_envelope_payload"],
            "source_reference": "TestCaseStarted.json#/properties/timestamp/properties/seconds"
          }
        ]
      }
      """
    And consumer file "previous-decisions.json" contains:
      """json
      {
        "decisions": [
          {
            "capabilityId": "testCaseStarted.id",
            "releaseTarget": "next-release",
            "status": "implemented",
            "rationale": "The existing scenario ID is emitted."
          }
        ]
      }
      """
    And consumer file "current-decisions.json" contains:
      """json
      {
        "decisions": [
          {
            "capability_id": "test_case_started.id",
            "release_target": "next-release",
            "status": "Implemented",
            "comment": "The scenario ID continues to be emitted."
          }
        ]
      }
      """
    When I remember the exact bytes of consumer file "current-decisions.json"
    And I run command "cuke" with arguments "messages capabilities diff --previous-baseline 27.0.0 --current-baseline 28.0.0 --previous previous-inventory.json --current current-inventory.json --previous-decisions previous-decisions.json --current-decisions current-decisions.json"
    Then the command should exit with code 0
    And the command JSON should include:
      """json
      {
        "added_capability_ids": ["test_case_started.timestamp.seconds"],
        "added_decision_ids": [],
        "changed_capability_ids": ["test_case_started.id"],
        "changed_decision_ids": ["test_case_started.id@next-release"],
        "current_baseline": "28.0.0",
        "previous_baseline": "27.0.0",
        "removed_capability_ids": ["test_case_started.attempt"],
        "removed_decision_ids": []
      }
      """
    And consumer file "current-decisions.json" should match its remembered bytes

  Scenario: Invalid governance inputs fail closed and preserve existing output files
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "invalid-messages.ndjson" contains:
      """ndjson
      {"testRunStarted":{}}
      """
    And consumer file "report.json" contains:
      """json
      {"baseline_release":"28.0.0","observations":{"source_kind":"runtime","record_count":1,"capability_ids":[]},"summary":{},"scope":{"mandatory_capability_ids":[],"runtime_required_capability_ids":[]},"decisions":[],"gates":{"passed":true,"failures":[]},"capabilities":[]}
      """
    When I remember the exact bytes of consumer file "report.json"
    And I run command "cuke" with arguments "messages capabilities report --messages-file invalid-messages.ndjson --input-kind runtime --output report.json --format json"
    Then the command should exit with code 2
    And the command output should contain "invalid Messages envelope at line 1"
    And consumer file "report.json" should match its remembered bytes
    And consumer file "missing-comment-decisions.json" contains:
      """json
      {"decisions":[{"capability_id":"attachment.test_run_started_id","release_target":"28.0.0","status":"Not-Applicable"}]}
      """
    And consumer file "normalized-decisions.json" contains:
      """json
      {"decisions":[]}
      """
    When I remember the exact bytes of consumer file "normalized-decisions.json"
    And I run command "cuke" with arguments "messages capabilities validate-decision --input missing-comment-decisions.json --output normalized-decisions.json"
    Then the command should exit with code 2
    And the command output should contain "status Not-Applicable requires a non-empty comment"
    And consumer file "normalized-decisions.json" should match its remembered bytes
    And consumer file "contradictory-decisions.json" contains:
      """json
      {"decisions":[{"capabilityId":"testCaseStarted.id","releaseTarget":"28.0.0","status":"Implemented","comment":"First terminal decision."},{"capability_id":"test_case_started.id","release_target":"28.0.0","status":"Pending","comment":"Conflicting terminal decision."}]}
      """
    When I remember the exact bytes of consumer file "normalized-decisions.json"
    And I run command "cuke" with arguments "messages capabilities validate-decision --input contradictory-decisions.json --output normalized-decisions.json"
    Then the command should exit with code 2
    And the command output should contain "conflicting terminal statuses for test_case_started.id@28.0.0"
    And consumer file "normalized-decisions.json" should match its remembered bytes
    And consumer file "invalid-schemas/Envelope.json" contains:
      """json
      {"type":}
      """
    And consumer file "inventory.json" contains:
      """json
      {"baseline_release":"28.0.0","capabilities":[],"inventory_version":1,"summary":{"total":0,"relevant":0,"out_of_scope":0}}
      """
    When I remember the exact bytes of consumer file "inventory.json"
    And I run command "cuke" with arguments "messages capabilities sync --baseline-release 28.0.0 --schema-dir invalid-schemas --output inventory.json"
    Then the command should exit with code 2
    And the command output should contain "cannot read schema"
    And consumer file "inventory.json" should match its remembered bytes
    And consumer file "alias-schemas/Envelope.json" contains:
      """json
      {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
          "TestRunStarted": {
            "type": "object",
            "properties": {
              "timestamp": {
                "type": "object",
                "properties": {
                  "seconds": {"type": "integer"}
                }
              }
            }
          }
        }
      }
      """
    When I remember the exact bytes of consumer file "alias-schemas/Envelope.json"
    And I run command "cuke" with arguments "messages capabilities sync --baseline-release 28.0.0 --schema-dir alias-schemas --output alias-schemas/Envelope.json"
    Then the command should exit with code 2
    And the command output should contain "resolves to input file"
    And consumer file "alias-schemas/Envelope.json" should match its remembered bytes
