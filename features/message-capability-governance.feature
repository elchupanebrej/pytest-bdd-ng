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
