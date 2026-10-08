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
    When I run command "cuke" with arguments "convert allure messages.ndjson"
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

  Scenario: Preserve an attachment for an unknown Messages test case as an explicit fallback
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-known","uri":"features/known.feature","name":"Known scenario","language":"en","steps":[{"id":"pickle-step-known","astNodeIds":["ast-step-known"],"type":"Context","text":"the known step"}],"tags":[],"astNodeIds":["ast-scenario-known"]}}
      {"testCase":{"id":"case-known","pickleId":"pickle-known","testSteps":[{"id":"step-known","pickleStepId":"pickle-step-known"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-known","testCaseId":"case-known","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-known","testStepId":"step-known","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-known","testStepId":"step-known","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-known","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"attachment":{"body":"{\"testCaseId\":\"case-unknown\",\"event\":\"orphan\"}","contentEncoding":"IDENTITY","fileName":"orphan.json","mediaType":"application/vnd.pytest-bdd.launch+json"}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-unknown-case"
    Then the command should exit with code 0
    And consumer Allure result directory "allure-unknown-case" should preserve JSON attachment "orphan.json" for testCaseId "case-unknown" as an unmapped fallback from "messages.ndjson"

  Scenario: Reject a retry declaration without its next attempt
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-retry","uri":"features/retry.feature","name":"Retry scenario","language":"en","steps":[{"id":"pickle-step-retry","astNodeIds":["ast-step-retry"],"type":"Context","text":"the retryable operation"}],"tags":[],"astNodeIds":["ast-scenario-retry"]}}
      {"testCase":{"id":"case-retry","pickleId":"pickle-retry","testSteps":[{"id":"step-retry","pickleStepId":"pickle-step-retry"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-retry-0","testCaseId":"case-retry","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-retry-0","testStepId":"step-retry","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-retry-0","testStepId":"step-retry","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-retry-0","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":true}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-missing-retry"
    Then the command should exit with code 2
    And the command output should contain "retry"
    And the consumer file "allure-missing-retry" should not exist

  Scenario: Accept a complete retry sequence as two Allure results
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-retry-complete","uri":"features/retry.feature","name":"Retry scenario","language":"en","steps":[{"id":"pickle-step-retry-complete","astNodeIds":["ast-step-retry-complete"],"type":"Context","text":"the retryable operation"}],"tags":[],"astNodeIds":["ast-scenario-retry-complete"]}}
      {"testCase":{"id":"case-retry-complete","pickleId":"pickle-retry-complete","testSteps":[{"id":"step-retry-complete","pickleStepId":"pickle-step-retry-complete"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-retry-0","testCaseId":"case-retry-complete","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-retry-0","testStepId":"step-retry-complete","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-retry-0","testStepId":"step-retry-complete","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"FAILED","message":"first attempt sentinel","exception":{"type":"AssertionError","message":"first attempt sentinel"}},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-retry-0","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":true}}
      {"testCaseStarted":{"attempt":1,"id":"attempt-retry-1","testCaseId":"case-retry-complete","timestamp":{"seconds":1700000004,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-retry-1","testStepId":"step-retry-complete","timestamp":{"seconds":1700000005,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-retry-1","testStepId":"step-retry-complete","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000005,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-retry-1","timestamp":{"seconds":1700000006,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000007,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-retry-results"
    Then the command should exit with code 0
    And consumer Allure result directory "allure-retry-results" should emit two retry attempts for scenario "Retry scenario" with linked containers

  Scenario: Preserve run-finished diagnostics without changing a passing scenario
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-run-diagnostics","uri":"features/run-diagnostics.feature","name":"Run diagnostic scenario","language":"en","steps":[{"id":"pickle-step-run-diagnostics","astNodeIds":["ast-step-run-diagnostics"],"type":"Context","text":"the successful operation"}],"tags":[],"astNodeIds":["ast-scenario-run-diagnostics"]}}
      {"testCase":{"id":"case-run-diagnostics","pickleId":"pickle-run-diagnostics","testSteps":[{"id":"step-run-diagnostics","pickleStepId":"pickle-step-run-diagnostics"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-run-diagnostics","testCaseId":"case-run-diagnostics","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-run-diagnostics","testStepId":"step-run-diagnostics","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-run-diagnostics","testStepId":"step-run-diagnostics","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-run-diagnostics","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":false,"timestamp":{"seconds":1700000004,"nanos":0},"message":"run summary sentinel","exception":{"type":"RuntimeError","message":"run exception sentinel","stackTrace":"Traceback (most recent call last):\n  File \"runner.py\", line 42, in run\nRuntimeError: run exception sentinel"}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-run-diagnostics"
    Then the command should exit with code 0
    And consumer Allure result directory "allure-run-diagnostics" should preserve deterministic run-finished diagnostics from "messages.ndjson" and keep the scenario passed

  Scenario: Preserve a failed run status without run-finished diagnostics
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-run-status-only","uri":"features/run-status.feature","name":"Run status-only scenario","language":"en","steps":[{"id":"pickle-step-run-status-only","astNodeIds":["ast-step-run-status-only"],"type":"Context","text":"the successful operation"}],"tags":[],"astNodeIds":["ast-scenario-run-status-only"]}}
      {"testCase":{"id":"case-run-status-only","pickleId":"pickle-run-status-only","testSteps":[{"id":"step-run-status-only","pickleStepId":"pickle-step-run-status-only"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-run-status-only","testCaseId":"case-run-status-only","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-run-status-only","testStepId":"step-run-status-only","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-run-status-only","testStepId":"step-run-status-only","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-run-status-only","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":false,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-run-status-only"
    Then the command should exit with code 0
    And consumer Allure result directory "allure-run-status-only" should preserve the success-only run-finished JSON and keep the scenario passed

  Scenario: Preserve an unscoped attachment without case metadata as a run-level fallback
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-run-fallback","uri":"features/run-fallback.feature","name":"Run fallback scenario","language":"en","steps":[{"id":"pickle-step-run-fallback","astNodeIds":["ast-step-run-fallback"],"type":"Context","text":"the successful operation"}],"tags":[],"astNodeIds":["ast-scenario-run-fallback"]}}
      {"testCase":{"id":"case-run-fallback","pickleId":"pickle-run-fallback","testSteps":[{"id":"step-run-fallback","pickleStepId":"pickle-step-run-fallback"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-run-fallback","testCaseId":"case-run-fallback","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-run-fallback","testStepId":"step-run-fallback","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-run-fallback","testStepId":"step-run-fallback","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-run-fallback","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"attachment":{"body":"build metadata bytes","contentEncoding":"IDENTITY","fileName":"build-info.txt","mediaType":"text/plain"}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-run-fallback"
    Then the command should exit with code 0
    And consumer Allure result directory "allure-run-fallback" should preserve run-level fallback attachment "Cucumber run-level fallback: build-info.txt" of type "text/plain" with bytes "build metadata bytes"

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
      {"pickle":{"id":"pickle-status","uri":"features/statuses.feature","name":"Mixed outcome scenario","language":"en","steps":[{"id":"pickle-step-skipped","astNodeIds":["ast-step-skipped"],"type":"Context","text":"the skipped operation"},{"id":"pickle-step-undefined","astNodeIds":["ast-step-undefined"],"type":"Context","text":"the undefined operation"},{"id":"pickle-step-ambiguous","astNodeIds":["ast-step-ambiguous"],"type":"Context","text":"the ambiguous operation"},{"id":"pickle-step-pending","astNodeIds":["ast-step-pending"],"type":"Context","text":"the pending operation"},{"id":"pickle-step-unknown","astNodeIds":["ast-step-unknown"],"type":"Context","text":"the unknown operation"}],"tags":[],"astNodeIds":["ast-scenario-status"]}}
      {"testCase":{"id":"case-status","pickleId":"pickle-status","testSteps":[{"id":"step-skipped","pickleStepId":"pickle-step-skipped"},{"id":"step-undefined","pickleStepId":"pickle-step-undefined"},{"id":"step-ambiguous","pickleStepId":"pickle-step-ambiguous"},{"id":"step-pending","pickleStepId":"pickle-step-pending"},{"id":"step-unknown","pickleStepId":"pickle-step-unknown"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-status","testCaseId":"case-status","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-status","testStepId":"step-skipped","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-status","testStepId":"step-skipped","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"SKIPPED"},"timestamp":{"seconds":1700000002,"nanos":100000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-status","testStepId":"step-undefined","timestamp":{"seconds":1700000002,"nanos":200000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-status","testStepId":"step-undefined","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"UNDEFINED"},"timestamp":{"seconds":1700000002,"nanos":300000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-status","testStepId":"step-ambiguous","timestamp":{"seconds":1700000002,"nanos":400000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-status","testStepId":"step-ambiguous","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"AMBIGUOUS"},"timestamp":{"seconds":1700000002,"nanos":500000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-status","testStepId":"step-pending","timestamp":{"seconds":1700000002,"nanos":600000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-status","testStepId":"step-pending","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"PENDING"},"timestamp":{"seconds":1700000002,"nanos":700000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-status","testStepId":"step-unknown","timestamp":{"seconds":1700000002,"nanos":800000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-status","testStepId":"step-unknown","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"UNKNOWN"},"timestamp":{"seconds":1700000002,"nanos":900000000}}}
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
    And consumer Allure result directory "allure-status-results" should map skipped, undefined, ambiguous, pending, and unknown to their Allure statuses with scenario status broken
    When I run command "cuke" with arguments "convert allure messages.ndjson --output xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    Then the command should exit with code 2
    And the command output should contain "cannot write Allure results"
    And the consumer file "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" should not exist

    And consumer directory "readonly-output" exists
    When I remove write permission from consumer directory "readonly-output"
    And I run command "cuke" with arguments "convert allure messages.ndjson --output readonly-output/allure-results"
    Then the command should exit with code 2
    And the command output should contain "cannot write Allure results"
    And consumer directory "readonly-output" should remain empty
    And the consumer file "readonly-output/allure-results" should not exist
    When I restore write permission to consumer directory "readonly-output"

  Scenario: Reject a missing Messages input without creating output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run command "cuke" with arguments "convert allure missing.ndjson --output allure-missing-input"
    Then the command should exit with code 2
    And the command output should contain "cannot read input"
    And the consumer file "allure-missing-input" should not exist

  Scenario: Reject invalid retry history and reversed timestamps without results
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-gap","uri":"features/retry.feature","name":"Retry scenario","language":"en","steps":[{"id":"pickle-step-gap","astNodeIds":["ast-step-gap"],"type":"Context","text":"the retryable operation"}],"tags":[],"astNodeIds":["ast-scenario-gap"]}}
      {"testCase":{"id":"case-gap","pickleId":"pickle-gap","testSteps":[{"id":"step-gap","pickleStepId":"pickle-step-gap"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-gap-0","testCaseId":"case-gap","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-gap-0","testStepId":"step-gap","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-gap-0","testStepId":"step-gap","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-gap-0","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":true}}
      {"testCaseStarted":{"attempt":2,"id":"attempt-gap-2","testCaseId":"case-gap","timestamp":{"seconds":1700000004,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-gap-2","testStepId":"step-gap","timestamp":{"seconds":1700000005,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-gap-2","testStepId":"step-gap","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000005,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-gap-2","timestamp":{"seconds":1700000006,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000007,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-retry-gap"
    Then the command should exit with code 2
    And the consumer file "allure-retry-gap" should not exist
    Given consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-duplicate","uri":"features/retry.feature","name":"Retry scenario","language":"en","steps":[{"id":"pickle-step-duplicate","astNodeIds":["ast-step-duplicate"],"type":"Context","text":"the retryable operation"}],"tags":[],"astNodeIds":["ast-scenario-duplicate"]}}
      {"testCase":{"id":"case-duplicate","pickleId":"pickle-duplicate","testSteps":[{"id":"step-duplicate","pickleStepId":"pickle-step-duplicate"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-duplicate-0a","testCaseId":"case-duplicate","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-duplicate-0a","testStepId":"step-duplicate","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-duplicate-0a","testStepId":"step-duplicate","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-duplicate-0a","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":true}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-duplicate-0b","testCaseId":"case-duplicate","timestamp":{"seconds":1700000004,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-duplicate-0b","testStepId":"step-duplicate","timestamp":{"seconds":1700000005,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-duplicate-0b","testStepId":"step-duplicate","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000005,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-duplicate-0b","timestamp":{"seconds":1700000006,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000007,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-retry-duplicate"
    Then the command should exit with code 2
    And the consumer file "allure-retry-duplicate" should not exist
    Given consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-final","uri":"features/retry.feature","name":"Retry scenario","language":"en","steps":[{"id":"pickle-step-final","astNodeIds":["ast-step-final"],"type":"Context","text":"the retryable operation"}],"tags":[],"astNodeIds":["ast-scenario-final"]}}
      {"testCase":{"id":"case-final","pickleId":"pickle-final","testSteps":[{"id":"step-final","pickleStepId":"pickle-step-final"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-final-0","testCaseId":"case-final","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-final-0","testStepId":"step-final","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-final-0","testStepId":"step-final","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-final-0","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"testCaseStarted":{"attempt":1,"id":"attempt-final-1","testCaseId":"case-final","timestamp":{"seconds":1700000004,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-final-1","testStepId":"step-final","timestamp":{"seconds":1700000005,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-final-1","testStepId":"step-final","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000005,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-final-1","timestamp":{"seconds":1700000006,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000007,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-retry-final-flag"
    Then the command should exit with code 2
    And the consumer file "allure-retry-final-flag" should not exist
    Given consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-reversed","uri":"features/timestamps.feature","name":"Reversed timestamps","language":"en","steps":[{"id":"pickle-step-reversed","astNodeIds":["ast-step-reversed"],"type":"Context","text":"the timestamped operation"}],"tags":[],"astNodeIds":["ast-scenario-reversed"]}}
      {"testCase":{"id":"case-reversed","pickleId":"pickle-reversed","testSteps":[{"id":"step-reversed","pickleStepId":"pickle-step-reversed"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-reversed","testCaseId":"case-reversed","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-reversed","testStepId":"step-reversed","timestamp":{"seconds":1700000003,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-reversed","testStepId":"step-reversed","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-reversed","timestamp":{"seconds":1700000004,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000005,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-reversed-timestamps"
    Then the command should exit with code 2
    And the consumer file "allure-reversed-timestamps" should not exist

    Given consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-retry-time-order","uri":"features/retry.feature","name":"Retry timestamp order","language":"en","steps":[{"id":"pickle-step-retry-time-order","astNodeIds":["ast-step-retry-time-order"],"type":"Context","text":"the retryable operation"}],"tags":[],"astNodeIds":["ast-scenario-retry-time-order"]}}
      {"testCase":{"id":"case-retry-time-order","pickleId":"pickle-retry-time-order","testSteps":[{"id":"step-retry-time-order","pickleStepId":"pickle-step-retry-time-order"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-time-order-0","testCaseId":"case-retry-time-order","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-time-order-0","testStepId":"step-retry-time-order","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-time-order-0","testStepId":"step-retry-time-order","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"FAILED","message":"first attempt sentinel","exception":{"type":"AssertionError","message":"first attempt sentinel"}},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-time-order-0","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":true}}
      {"testCaseStarted":{"attempt":1,"id":"attempt-time-order-1","testCaseId":"case-retry-time-order","timestamp":{"seconds":1700000002,"nanos":900000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-time-order-1","testStepId":"step-retry-time-order","timestamp":{"seconds":1700000004,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-time-order-1","testStepId":"step-retry-time-order","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"PASSED"},"timestamp":{"seconds":1700000004,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-time-order-1","timestamp":{"seconds":1700000005,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":true,"timestamp":{"seconds":1700000006,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-retry-time-order"
    Then the command should exit with code 2
    And the consumer file "allure-retry-time-order" should not exist

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
    And the consumer installs pytest-cuke with its Allure extra in an isolated environment
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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-allure=allure-native -q"
    Then pytest should exit with code 0
    And consumer artifact "messages.ndjson" should be a valid Cucumber Messages stream for 1 passed scenario and 1 passed steps
    And consumer Allure result directory "allure-native" should preserve scenario "Save an order for Ada", tag "@smoke", and outline parameter "customer" value "Ada"
    And consumer Allure result directory "allure-native" should satisfy the result and container required-field contract
    When I remove consumer file "features/orders.feature"
    And I remove consumer file "conftest.py"
    Given consumer file "conftest.py" contains:
      """python
      raise RuntimeError("pytest Allure stream import must not load conftest.py")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-allure=allure-imported --cuke-allure-messages-in=messages.ndjson -q"
    Then pytest should exit with code 0
    And consumer Allure result directory "allure-imported" should preserve scenario "Save an order for Ada", tag "@smoke", and outline parameter "customer" value "Ada"
    And consumer Allure result directory "allure-imported" should satisfy the result and container required-field contract
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-converted"
    Then the command should exit with code 0
    And the consumer file "features/orders.feature" should not exist
    And consumer Allure result directory "allure-converted" should preserve scenario "Save an order for Ada", tag "@smoke", and outline parameter "customer" value "Ada"
    And consumer Allure result directory "allure-converted" should satisfy the result and container required-field contract
    And consumer Allure result directories "allure-native" and "allure-imported" should be semantically equivalent
    And consumer Allure result directories "allure-native" and "allure-converted" should be semantically equivalent
    And consumer Allure result directories "allure-imported" and "allure-converted" should be semantically equivalent
    And consumer Allure result directories "allure-native" and "allure-converted" should preserve no-attempt Messages extensions for their scenarios from "messages.ndjson"

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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 1
    And consumer Messages artifact "messages.ndjson" should preserve the failed step diagnostics and attachment correlations
    When I remove consumer file "features/failure-evidence.feature"
    And I remove consumer file "conftest.py"
    And I run command "cuke" with arguments "convert allure messages.ndjson --output allure-results"
    Then the command should exit with code 0
    And the consumer file "features/failure-evidence.feature" should not exist
    And the consumer file "conftest.py" should not exist
    And consumer Allure result directory "allure-results" should preserve failed diagnostics, portable attachments, and linked containers

  Scenario: Preserve distinct exception and step-result failure messages
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-distinct-failure","uri":"features/distinct-failure.feature","name":"Distinct failure messages","language":"en","steps":[{"id":"pickle-step-distinct-failure","astNodeIds":["ast-step-distinct-failure"],"type":"Context","text":"the operation reports separate failure details"}],"tags":[],"astNodeIds":["ast-scenario-distinct-failure"]}}
      {"testCase":{"id":"case-distinct-failure","pickleId":"pickle-distinct-failure","testSteps":[{"id":"step-distinct-failure","pickleStepId":"pickle-step-distinct-failure"}]}}
      {"testRunStarted":{"timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-distinct-failure","testCaseId":"case-distinct-failure","timestamp":{"seconds":1700000001,"nanos":0}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-distinct-failure","testStepId":"step-distinct-failure","timestamp":{"seconds":1700000002,"nanos":0}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-distinct-failure","testStepId":"step-distinct-failure","testStepResult":{"duration":{"seconds":0,"nanos":1000000},"status":"FAILED","message":"step result detail","exception":{"type":"AssertionError","message":"exception detail"}},"timestamp":{"seconds":1700000002,"nanos":1000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-distinct-failure","timestamp":{"seconds":1700000003,"nanos":0},"willBeRetried":false}}
      {"testRunFinished":{"success":false,"timestamp":{"seconds":1700000004,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-distinct-failure"
    Then the command should exit with code 0
    And consumer Allure result directory "allure-distinct-failure" should combine the exception and step-result messages with a linked container

  Scenario: Convert a Gherkin Background step from saved Messages
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, when


      @given("the shop is open")
      def shop_is_open():
          pass


      @given("the customer is Ada")
      def customer_is_ada():
          pass


      @when("the order is saved")
      def order_is_saved():
          pass
      """
    And consumer file "features/store-order.feature" contains:
      """gherkin
      Feature: Store customer orders
        Background:
          Given the shop is open

        Scenario: Save Ada's order
          Given the customer is Ada
          When the order is saved
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 0
    And consumer artifact "messages.ndjson" should be a valid Cucumber Messages stream for 1 passed scenario and 3 passed steps
    When I remove consumer file "features/store-order.feature"
    And I remove consumer file "conftest.py"
    And I run command "cuke" with arguments "convert allure messages.ndjson --output allure-background"
    Then the command should exit with code 0
    And the consumer file "features/store-order.feature" should not exist
    And the consumer file "conftest.py" should not exist
    And consumer Allure result directory "allure-background" should preserve the Background step before scenario steps and linked containers

  Scenario: Convert a pytest-produced failed Background after deleting its sources
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, when


      @given("the shop is open")
      def shop_is_open():
          pass


      @given("the inventory reconciliation fails")
      def inventory_reconciliation_fails():
          raise AssertionError("background failure sentinel")


      @given("the customer is Ada")
      def customer_is_ada():
          pass


      @when("the order is saved")
      def order_is_saved():
          pass
      """
    And consumer file "features/store-order-failure.feature" contains:
      """gherkin
      Feature: Store customer orders
        Background:
          Given the shop is open
          And the inventory reconciliation fails

        Scenario: Save Ada's order
          Given the customer is Ada
          When the order is saved
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 1
    And consumer Messages artifact "messages.ndjson" should preserve the failed Background step diagnostic and step order
    When I remove consumer file "features/store-order-failure.feature"
    And I remove consumer file "conftest.py"
    And I run command "cuke" with arguments "convert allure messages.ndjson --output allure-background-failure"
    Then the command should exit with code 0
    And the consumer file "features/store-order-failure.feature" should not exist
    And the consumer file "conftest.py" should not exist
    And consumer Allure result directory "allure-background-failure" should preserve the failed Background step diagnostic, order, and linked containers
    And consumer Allure result directory "allure-background-failure" should satisfy the result and container required-field contract

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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    When I remove consumer file "features/workflows.feature"
    And I remove consumer file "conftest.py"
    And consumer file "conftest.py" contains:
      """python
      raise RuntimeError("pytest Allure stream import must not load conftest.py")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-allure=allure-imported --cuke-allure-messages-in=messages.ndjson -q"
    Then pytest should exit with code 0
    When I remove consumer file "conftest.py"
    And I run command "cuke" with arguments "convert allure messages.ndjson --output allure-results"
    Then the command should exit with code 0
    And the consumer file "features/workflows.feature" should not exist
    And the consumer file "conftest.py" should not exist
    And consumer Allure result directory "allure-results" should contain both scenarios with ordered steps and linked containers
    And consumer Allure result directories "allure-imported" and "allure-results" should preserve no-attempt Messages extensions for their scenarios from "messages.ndjson"

  Scenario: Convert Cucumber Messages v28 run hooks into Allure container fixtures
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "messages.ndjson" contains:
      """ndjson
      {"pickle":{"id":"pickle-run-hooks","uri":"features/run-hooks.feature","name":"Run-hook scenario","language":"en","steps":[{"id":"pickle-step-run-hooks","astNodeIds":["ast-step-run-hooks"],"type":"Context","text":"the saved step"}],"tags":[],"astNodeIds":["ast-scenario-run-hooks"]}}
      {"testCase":{"id":"case-run-hooks","pickleId":"pickle-run-hooks","testSteps":[{"id":"step-run-hooks","pickleStepId":"pickle-step-run-hooks"}]}}
      {"hook":{"id":"hook-before-run","name":"Prepare reporting endpoint","sourceReference":{"uri":"conftest.py","location":{"line":10}},"type":"BEFORE_TEST_RUN"}}
      {"hook":{"id":"hook-after-run","name":"Flush audit log","sourceReference":{"uri":"conftest.py","location":{"line":20}},"type":"AFTER_TEST_RUN"}}
      {"testRunStarted":{"id":"run-hooks","timestamp":{"seconds":1700000000,"nanos":0}}}
      {"testRunHookStarted":{"id":"run-hook-before","testRunStartedId":"run-hooks","hookId":"hook-before-run","timestamp":{"seconds":1700000000,"nanos":100000000}}}
      {"testRunHookFinished":{"testRunHookStartedId":"run-hook-before","result":{"duration":{"seconds":0,"nanos":100000000},"status":"PASSED"},"timestamp":{"seconds":1700000000,"nanos":200000000}}}
      {"testCaseStarted":{"attempt":0,"id":"attempt-run-hooks","testCaseId":"case-run-hooks","timestamp":{"seconds":1700000000,"nanos":300000000}}}
      {"testStepStarted":{"testCaseStartedId":"attempt-run-hooks","testStepId":"step-run-hooks","timestamp":{"seconds":1700000000,"nanos":400000000}}}
      {"testStepFinished":{"testCaseStartedId":"attempt-run-hooks","testStepId":"step-run-hooks","testStepResult":{"duration":{"seconds":0,"nanos":100000000},"status":"PASSED"},"timestamp":{"seconds":1700000000,"nanos":500000000}}}
      {"testCaseFinished":{"testCaseStartedId":"attempt-run-hooks","timestamp":{"seconds":1700000000,"nanos":600000000},"willBeRetried":false}}
      {"testRunHookStarted":{"id":"run-hook-after","testRunStartedId":"run-hooks","hookId":"hook-after-run","timestamp":{"seconds":1700000000,"nanos":700000000}}}
      {"attachment":{"body":"after run hook attachment bytes","contentEncoding":"IDENTITY","fileName":"after-run.log","mediaType":"text/plain","testRunHookStartedId":"run-hook-after","timestamp":{"seconds":1700000000,"nanos":800000000}}}
      {"attachment":{"body":"AP8=","contentEncoding":"BASE64","fileName":"after-run.bin","mediaType":"application/octet-stream","testRunHookStartedId":"run-hook-after","timestamp":{"seconds":1700000000,"nanos":850000000}}}
      {"testRunHookFinished":{"testRunHookStartedId":"run-hook-after","result":{"duration":{"seconds":0,"nanos":200000000},"message":"after run hook failure sentinel","status":"FAILED","exception":{"type":"RuntimeError","message":"after run hook failure sentinel","stackTrace":"RuntimeError: after run hook failure sentinel\n  at conftest.py:20"}},"timestamp":{"seconds":1700000000,"nanos":900000000}}}
      {"testRunFinished":{"testRunStartedId":"run-hooks","success":false,"timestamp":{"seconds":1700000001,"nanos":0}}}
      """
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-run-hooks"
    Then the command should exit with code 0
    And consumer Allure result directory "allure-run-hooks" should preserve Cucumber run-hook fixtures and attachment evidence
    And consumer Allure result directory "allure-run-hooks" should satisfy the result and container required-field contract

  Scenario: Preserve pytest-produced v28 run hooks across Allure reporting modes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs pytest-cuke with its Allure extra in an isolated environment
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the pytest session hook scenario passes")
      def session_hook_scenario_passes():
          pass
      """
    And consumer file "features/session-run-hooks.feature" contains:
      """gherkin
      Feature: Session run hooks
        Scenario: Session hook scenario
          Given the pytest session hook scenario passes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-allure=allure-native -q"
    Then pytest should exit with code 0
    And consumer Messages artifact "messages.ndjson" should preserve pytest-generated v28 run hooks around one passed scenario
    And consumer Allure result directory "allure-native" should preserve pytest session run-hook fixtures
    And consumer Allure result directory "allure-native" should satisfy the result and container required-field contract
    When I remove consumer file "features/session-run-hooks.feature"
    And I remove consumer file "conftest.py"
    And I run installed pytest with arguments "--rootdir=. --cuke-allure=allure-imported --cuke-allure-messages-in=messages.ndjson -q"
    Then pytest should exit with code 0
    And consumer Allure result directory "allure-imported" should preserve pytest session run-hook fixtures
    And consumer Allure result directory "allure-imported" should satisfy the result and container required-field contract
    When I run command "cuke" with arguments "convert allure messages.ndjson --output allure-converted"
    Then the command should exit with code 0
    And the consumer file "features/session-run-hooks.feature" should not exist
    And the consumer file "conftest.py" should not exist
    And consumer Allure result directory "allure-converted" should preserve pytest session run-hook fixtures
    And consumer Allure result directory "allure-converted" should satisfy the result and container required-field contract
    And consumer Allure result directories "allure-native" and "allure-imported" should be semantically equivalent
    And consumer Allure result directories "allure-native" and "allure-converted" should be semantically equivalent
    And consumer Allure result directories "allure-imported" and "allure-converted" should be semantically equivalent
