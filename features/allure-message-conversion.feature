Feature: Convert saved Cucumber Messages to Allure results
  A saved Cucumber Messages stream can be converted without collecting its
  original feature files or importing consumer test configuration.

  Scenario: Convert one complete saved scenario without loading test sources
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has no Allure Python adapters or Node on PATH
    And consumer file "conftest.py" contains:
      """python
      raise RuntimeError("the converter must not load conftest.py")
      """
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-1","uri":"features/saved.feature","name":"Saved scenario","language":"en","steps":[{"id":"pickle-step-1","astNodeIds":["ast-step-1"],"type":"Context","text":"the saved step"}],"tags":[],"astNodeIds":["ast-scenario-1"]}}

      {"hook":{"id":"hook-1","name":"Before setup","sourceReference":{"uri":"conftest.py","location":{"line":1}}}}
      {"hook":{"id":"hook-2","name":"After cleanup","sourceReference":{"uri":"conftest.py","location":{"line":2}}}}
      {"testCase":{"id":"case-1","pickleId":"pickle-1","testSteps":[{"id":"hook-step-1","hookId":"hook-1"},{"id":"step-1","pickleStepId":"pickle-step-1"},{"id":"after-hook-step-1","hookId":"hook-2"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-1","testCaseId":"case-1","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-1","testStepId":"hook-step-1","timestamp":{"seconds":1700000001,"nanos":100000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-1","testStepId":"hook-step-1","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"PASSED"},"timestamp":{"seconds":1700000001,"nanos":200000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-1","testStepId":"step-1","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-1","testStepId":"step-1","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-1","testStepId":"after-hook-step-1","timestamp":{"seconds":1700000002,"nanos":100000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-1","testStepId":"after-hook-step-1","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":200000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-1","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    And I remember the exact bytes of consumer file "messages.ndjson"
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-results"
    Then the command should exit with code 0
    And the consumer file "features/saved.feature" should not exist
    And consumer file "messages.ndjson" should match its remembered bytes
    And consumer Allure result directory "allure-results" should contain one result for scenario "Saved scenario" with passed step "the saved step" and one linked container
    When I run command "pytest-cuke" with arguments "convert allure messages.ndjson --output allure-results-pytest-cuke"
    Then the command should exit with code 0
    And consumer file "messages.ndjson" should match its remembered bytes
    And consumer Allure result directory "allure-results-pytest-cuke" should contain one result for scenario "Saved scenario" with passed step "the saved step" and one linked container

  Scenario: Reject an incomplete stream without writing partial Allure results
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-incomplete","uri":"features/incomplete.feature","name":"Incomplete scenario","language":"en","steps":[{"id":"pickle-step-incomplete","astNodeIds":["ast-step-incomplete"],"type":"Context","text":"an unfinished step"}],"tags":[],"astNodeIds":["ast-scenario-incomplete"]}}
      {"testCase":{"id":"case-incomplete","pickleId":"pickle-incomplete","testSteps":[{"id":"step-incomplete","pickleStepId":"pickle-step-incomplete"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-incomplete","testCaseId":"case-incomplete","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-incomplete","testStepId":"step-incomplete","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-incomplete","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":false,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-incomplete"
    Then the command should exit with code 2
    And the command output should contain "test steps did not finish"
    And the consumer file "allure-incomplete" should not exist

  Scenario: Reject invalid input and output paths and aggregate skipped statuses
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"testRunStarted":{"timestamp":"not-a-timestamp"}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-schema-invalid"
    Then the command should exit with code 2
    And the command output should contain "invalid Cucumber message in messages.ndjson at line 1"
    And the command output should contain "timestamp"
    And the consumer file "allure-schema-invalid" should not exist
    Given consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-status","uri":"features/statuses.feature","name":"Mixed outcome scenario","language":"en","steps":[{"id":"pickle-step-skipped","astNodeIds":["ast-step-skipped"],"type":"Context","text":"the skipped operation"},{"id":"pickle-step-undefined","astNodeIds":["ast-step-undefined"],"type":"Context","text":"the undefined operation"}],"tags":[],"astNodeIds":["ast-scenario-status"]}}
      {"testCase":{"id":"case-status","pickleId":"pickle-status","testSteps":[{"id":"step-skipped","pickleStepId":"pickle-step-skipped"},{"id":"step-undefined","pickleStepId":"pickle-step-undefined"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-status","testCaseId":"case-status","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-status","testStepId":"step-skipped","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-status","testStepId":"step-skipped","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"SKIPPED"},"timestamp":{"seconds":1700000002,"nanos":100000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-status","testStepId":"step-undefined","timestamp":{"seconds":1700000002,"nanos":200000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-status","testStepId":"step-undefined","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"UNDEFINED"},"timestamp":{"seconds":1700000002,"nanos":300000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-status","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":false,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    And consumer file "blocked-parent" contains:
      """text
      preserve-this-output-blocker
      """
    And I remember the exact bytes of consumer file "blocked-parent"
    When I run command "cuke" with arguments "convert allure messages.ndjson --output blocked-parent/allure-results"
    Then the command should exit with code 2
    And the command output should contain "Allure output path component is not a directory"
    And consumer file "blocked-parent" should match its remembered bytes
    And the consumer file "blocked-parent/allure-results" should not exist
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-status-results"
    Then the command should exit with code 0
    And consumer Allure result directory "allure-status-results" should map "the skipped operation" to skipped and "the undefined operation" to broken, with scenario status broken

  Scenario: malformed-input-fails-and-unknown-extension-is-attached
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {malformed json}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-malformed"
    Then the command should exit with code 2
    And the command output should contain "invalid JSON in messages.ndjson at line 2"
    And the consumer file "allure-malformed" should not exist
    Given consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-1","uri":"features/saved-scenario.feature","name":"saved-scenario","language":"en","steps":[{"id":"pickle-step-1","astNodeIds":["ast-step-1"],"type":"Context","text":"the saved step"}],"tags":[],"astNodeIds":["ast-scenario-1"]}}
      {"vendorAuditExtension":{"event":"record-snapshot","revision":3,"payload":{"record":"Ada-17","visible":true}}}
      {"hook":{"id":"hook-1","name":"Before setup","sourceReference":{"uri":"conftest.py","location":{"line":1}}}}
      {"hook":{"id":"hook-2","name":"After cleanup","sourceReference":{"uri":"conftest.py","location":{"line":2}}}}
      {"testCase":{"id":"case-1","pickleId":"pickle-1","testSteps":[{"id":"hook-step-1","hookId":"hook-1"},{"id":"step-1","pickleStepId":"pickle-step-1"},{"id":"after-hook-step-1","hookId":"hook-2"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-1","testCaseId":"case-1","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-1","testStepId":"hook-step-1","timestamp":{"seconds":1700000001,"nanos":100000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-1","testStepId":"hook-step-1","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"PASSED"},"timestamp":{"seconds":1700000001,"nanos":200000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-1","testStepId":"step-1","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-1","testStepId":"step-1","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-1","testStepId":"after-hook-step-1","timestamp":{"seconds":1700000002,"nanos":100000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-1","testStepId":"after-hook-step-1","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":200000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-1","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-extension"
    Then the command should exit with code 0
    And consumer Allure result directory "allure-extension" should contain one result for scenario "saved-scenario" with passed step "the saved step" and one linked container
    And consumer Allure result directory "allure-extension" should expose the raw event from "messages.ndjson" as an application/json attachment

  Scenario: Convert a pytest-produced outline after its feature source is removed
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, parsers


      @given(parsers.parse("the saved order belongs to {customer}"))
      def saved_order_belongs_to_customer(customer: str) -> None:
          pass
      """
    And consumer file "features/orders.feature" contains:
      """gherkin
      Feature: Saved orders
        @smoke
        Scenario Outline: Save an order for <customer>
          Given the saved order belongs to <customer>

          Examples:
            | customer |
            | Ada      |
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-allure=allure-native --cuke-summary -q"
    Then pytest should exit with code 0
    And consumer artifact "messages.ndjson" should be a valid Cucumber Messages stream for 1 passed scenario and 1 passed steps
    And consumer Allure result directory "allure-native" should preserve scenario "Save an order for Ada", tag "@smoke", and outline parameter "customer" value "Ada"
    When I remove consumer file "features/orders.feature"
    And I remove consumer file "conftest.py"
    Given consumer file "conftest.py" contains:
      """python
      raise RuntimeError("pytest Allure stream import must not load conftest.py")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-allure=allure-imported --cuke-allure-messages-in=messages.ndjson -q"
    Then pytest should exit with code 0
    And consumer Allure result directory "allure-imported" should preserve scenario "Save an order for Ada", tag "@smoke", and outline parameter "customer" value "Ada"
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-converted"
    Then the command should exit with code 0
    And the consumer file "features/orders.feature" should not exist
    And consumer Allure result directory "allure-converted" should preserve scenario "Save an order for Ada", tag "@smoke", and outline parameter "customer" value "Ada"
    And consumer Allure result directories "allure-native" and "allure-converted" should be semantically equivalent

  Scenario: Convert failed step diagnostics and attached evidence
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the operation attaches evidence and fails")
      def operation_attaches_evidence_and_fails(attach):
          attach("identity evidence", media_type="text/plain", file_name="identity.txt")
          attach(b"\x00\xffbinary evidence", media_type="application/octet-stream", file_name="binary.bin")
          raise AssertionError('failure sentinel')
      """
    And consumer file "features/failure-evidence.feature" contains:
      """gherkin
      Feature: Failed scenario evidence
        Scenario: Fail after attaching evidence
          Given the operation attaches evidence and fails
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-summary -q"
    Then pytest should exit with code 1
    And consumer Messages artifact "messages.ndjson" should preserve the failed step diagnostics and attachment correlations
    When I remove consumer file "features/failure-evidence.feature"
    And I remove consumer file "conftest.py"
    And I run command "cuke" with arguments "convert allure messages.ndjson --output allure-results"
    Then the command should exit with code 0
    And the consumer file "features/failure-evidence.feature" should not exist
    And the consumer file "conftest.py" should not exist
    And consumer Allure result directory "allure-results" should preserve failed diagnostics, portable attachments, and a linked container

  Scenario: Convert a described scenario with DocString and DataTable steps
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, when


      @given("the JSON profile is accepted")
      def json_profile_is_accepted(step):
          assert step.doc_string is not None
          assert step.doc_string.media_type == "application/json"
          assert step.doc_string.content == '{"customer": "Ada", "active": true}'


      @when("the profile fields are recorded")
      def profile_fields_are_recorded(step):
          assert step.data_table is not None
          rows = [[cell.value for cell in row.cells] for row in step.data_table.rows]
          assert rows == [
              ["field", "value"],
              ["customer", "Ada"],
              ["active", "true"],
          ]
      """
    And consumer file "features/profile-input.feature" contains:
      """gherkin
      Feature: Profile input reporting
        @smoke
        Scenario: Submit a profile payload and field table
          The request identifies its media type and keeps the field values.
          Given the JSON profile is accepted
            ```application/json
            {"customer": "Ada", "active": true}
            ```
          When the profile fields are recorded
            | field    | value |
            | customer | Ada   |
            | active   | true  |
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-summary -q"
    Then pytest should exit with code 0
    When I remove consumer file "features/profile-input.feature"
    And I remove consumer file "conftest.py"
    And I run command "cuke" with arguments "convert allure messages.ndjson --output allure-results"
    Then the command should exit with code 0
    And the consumer file "features/profile-input.feature" should not exist
    And the consumer file "conftest.py" should not exist
    And consumer Allure result directory "allure-results" should preserve the scenario description, tag, and structured step arguments

  Scenario: Render converted results with Allure 3
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-render","uri":"features/rendered.feature","name":"Rendered scenario","language":"en","steps":[{"id":"pickle-step-render","astNodeIds":["ast-step-render"],"type":"Context","text":"the rendered step"}],"tags":[],"astNodeIds":["ast-scenario-render"]}}
      {"hook":{"id":"hook-render-before","name":"Before setup","sourceReference":{"uri":"conftest.py","location":{"line":1}}}}
      {"hook":{"id":"hook-render-after","name":"After cleanup","sourceReference":{"uri":"conftest.py","location":{"line":2}}}}
      {"testCase":{"id":"case-render","pickleId":"pickle-render","testSteps":[{"id":"hook-render-before-step","hookId":"hook-render-before"},{"id":"step-render","pickleStepId":"pickle-step-render"},{"id":"hook-render-after-step","hookId":"hook-render-after"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-render","testCaseId":"case-render","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-render","testStepId":"hook-render-before-step","timestamp":{"seconds":1700000001,"nanos":100000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-render","testStepId":"hook-render-before-step","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"PASSED"},"timestamp":{"seconds":1700000001,"nanos":200000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-render","testStepId":"step-render","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-render","testStepId":"step-render","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-render","testStepId":"hook-render-after-step","timestamp":{"seconds":1700000002,"nanos":100000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-render","testStepId":"hook-render-after-step","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":200000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-render","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-results"
    Then the command should exit with code 0
    And consumer Allure result directory "allure-results" should contain one result for scenario "Rendered scenario" with passed step "the rendered step" and one linked container
    When I generate an Allure 3 report from consumer result directory "allure-results" into "allure-report"
    Then the Allure 3 renderer should generate the report

  Scenario: Convert multiple pytest-produced scenarios without their source files
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, then, when


      @given("the cart contains a book")
      def cart_contains_a_book():
          pass


      @when("the customer submits the order")
      def customer_submits_the_order():
          pass


      @then("the order has an identifier")
      def order_has_an_identifier():
          pass


      @given("a customer report is requested")
      def customer_report_is_requested():
          pass


      @when("the report is generated")
      def report_is_generated():
          pass


      @then("the report is ready")
      def report_is_ready():
          pass
      """
    And consumer file "features/workflows.feature" contains:
      """gherkin
      Feature: Customer workflows
        Scenario: Submit a book order
          Given the cart contains a book
          When the customer submits the order
          Then the order has an identifier

        Scenario: Generate a customer report
          Given a customer report is requested
          When the report is generated
          Then the report is ready
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    When I remove consumer file "features/workflows.feature"
    And I remove consumer file "conftest.py"
    And I run command "cuke" with arguments "convert allure messages.ndjson --output allure-results"
    Then the command should exit with code 0
    And the consumer file "features/workflows.feature" should not exist
    And the consumer file "conftest.py" should not exist
    And consumer Allure result directory "allure-results" should contain both scenarios with ordered steps and linked containers
