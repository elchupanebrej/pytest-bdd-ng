# Feature: Allure Schema Field Coverage
  Verify that pytest-bdd-ng can produce Allure3 schema fields from explicit CLI inputs:
    1. During a live pytest-bdd run with `--allure-cucumber-out`
    2. During post-hoc import with `--allure-cucumber-messages-in`

  This feature keeps GAP-03 evidence executable through real command-line options
  and concrete examples of input files and generated output fields.

## Scenario: Live pytest CLI run produces TestResult schema fields
* Given File "pytest.toml" with content:

    ```toml
    [pytest]
    disable_feature_autoload = true
    ```
* And File "schema_live.feature" with content:

    ```gherkin
    @schema @live
    Feature: Live Allure schema surface

      Scenario: Passing surface with attachment
        When I attach text evidence "live log"
        Then outcome is "pass"

      Scenario: Failing surface with status details
        When I attach text evidence "failure log"
        Then assertion fails with message "expected schema proof"
    ```
* And File "conftest.py" with content:

    ```python
    from pytest_bdd import parsers, then, when


    @when(parsers.parse('I attach text evidence "{value}"'))
    def _attach_text(attach, value):
        attach(value, media_type="text/plain", file_name=f"{value}.txt")


    @then(parsers.parse('outcome is "{outcome}"'))
    def _outcome(outcome):
        assert outcome == "pass"


    @then(parsers.parse('assertion fails with message "{message}"'))
    def _assertion_fails(message):
        raise AssertionError(message)
    ```
* And File "test_schema_live.py" with content:

    ```python
    from pytest_bdd import scenarios


    test = scenarios("schema_live.feature")
    ```
* When run pytest

    | cli_args | --allure-cucumber-out | allure-live-results | test_schema_live.py |
    |----------|-----------------------|---------------------|---------------------|

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 1      |

* And Directory "allure-live-results" contains Allure result JSON files
* And Allure result files validate against the Allure3 events schema
* And Allure result files in "allure-live-results" contain JSON field groups:

    | object        | fields                                                            |
    |---------------|-------------------------------------------------------------------|
    | result        | uuid,name,status,statusDetails,start,stop,labels,steps,parameters |
    | statusDetails | message,trace                                                     |
    | labels[]      | name,value                                                        |
    | steps[]       | name,status,start,stop                                            |
    | parameters[]  | name,value                                                        |

## Scenario: Post-hoc pytest CLI import produces TestResult schema fields
* Given File "messages.ndjson" with content:

    ```json lines
    {"testRunStarted":{"id":"run-1","timestamp":{"seconds":0,"nanos":0}}}
    {"pickle":{"id":"pk-pass","name":"imported passing scenario","language":"en","astNodeIds":[],"tags":[{"name":"@schema","astNodeId":"tag-pass"}],"uri":"features/schema.feature","steps":[{"id":"ps-pass-1","text":"outer step","astNodeIds":[]},{"id":"ps-pass-2","text":"inner step","astNodeIds":[]}]}}
    {"testCase":{"id":"tc-pass","pickleId":"pk-pass","testSteps":[{"id":"step-pass-1","pickleStepId":"ps-pass-1"},{"id":"step-pass-2","pickleStepId":"ps-pass-2"}]}}
    {"testCaseStarted":{"id":"case-pass","testCaseId":"tc-pass","attempt":0,"timestamp":{"seconds":1,"nanos":0}}}
    {"testStepStarted":{"testStepId":"step-pass-1","testCaseStartedId":"case-pass","timestamp":{"seconds":1,"nanos":0}}}
    {"testStepFinished":{"testStepId":"step-pass-1","testCaseStartedId":"case-pass","timestamp":{"seconds":1,"nanos":500000000},"testStepResult":{"status":"PASSED","duration":{"seconds":0,"nanos":500000000}}}}
    {"attachment":{"testCaseStartedId":"case-pass","testStepId":"step-pass-1","fileName":"log.txt","mediaType":"text/plain","body":"log data","contentEncoding":"IDENTITY","timestamp":{"seconds":1,"nanos":600000000}}}
    {"testStepStarted":{"testStepId":"step-pass-2","testCaseStartedId":"case-pass","timestamp":{"seconds":2,"nanos":0}}}
    {"testStepFinished":{"testStepId":"step-pass-2","testCaseStartedId":"case-pass","timestamp":{"seconds":2,"nanos":500000000},"testStepResult":{"status":"PASSED","duration":{"seconds":0,"nanos":500000000}}}}
    {"testCaseFinished":{"testCaseStartedId":"case-pass","timestamp":{"seconds":3,"nanos":0},"willBeRetried":false}}
    {"pickle":{"id":"pk-fail","name":"imported failing scenario","language":"en","astNodeIds":[],"tags":[{"name":"@schema","astNodeId":"tag-fail"}],"uri":"features/schema.feature","steps":[{"id":"ps-fail-1","text":"failing step","astNodeIds":[]}]}}
    {"testCase":{"id":"tc-fail","pickleId":"pk-fail","testSteps":[{"id":"step-fail-1","pickleStepId":"ps-fail-1"}]}}
    {"testCaseStarted":{"id":"case-fail","testCaseId":"tc-fail","attempt":0,"timestamp":{"seconds":4,"nanos":0}}}
    {"testStepStarted":{"testStepId":"step-fail-1","testCaseStartedId":"case-fail","timestamp":{"seconds":4,"nanos":0}}}
    {"testStepFinished":{"testStepId":"step-fail-1","testCaseStartedId":"case-fail","timestamp":{"seconds":5,"nanos":0},"testStepResult":{"status":"FAILED","duration":{"seconds":1,"nanos":0},"message":"AssertionError: expected schema proof"}}}
    {"testCaseFinished":{"testCaseStartedId":"case-fail","timestamp":{"seconds":5,"nanos":0},"willBeRetried":false}}
    {"testRunFinished":{"success":false,"timestamp":{"seconds":6,"nanos":0}}}
    ```
* When run pytest

    | cli_args  | --allure-cucumber-out | allure-import-results | --allure-cucumber-messages-in | messages.ndjson |
    |-----------|-----------------------|-----------------------|-------------------------------|-----------------|
    | inprocess | true                  |                       |                               |                 |

* Then Directory "allure-import-results" contains Allure result JSON files
* And Allure result files validate against the Allure3 events schema
* And Allure result files in "allure-import-results" contain JSON field groups:

    | object        | fields                                                            |
    |---------------|-------------------------------------------------------------------|
    | result        | uuid,name,status,statusDetails,start,stop,labels,steps,parameters |
    | statusDetails | message                                                           |
    | labels[]      | name,value                                                        |
    | steps[]       | name,status,start,stop                                            |
    | parameters[]  | name,value                                                        |

## Scenario: Post-hoc pytest CLI import produces container schema fields
* Given File "messages.ndjson" with content:

    ```json lines
    {"testRunStarted":{"id":"run-1","timestamp":{"seconds":0,"nanos":0}}}
    {"pickle":{"id":"pk-one","name":"first imported scenario","language":"en","astNodeIds":[],"tags":[],"uri":"features/schema.feature","steps":[{"id":"ps-one","text":"first step","astNodeIds":[]}]}}
    {"testCase":{"id":"tc-one","pickleId":"pk-one","testSteps":[{"id":"step-one","pickleStepId":"ps-one"}]}}
    {"testCaseStarted":{"id":"case-one","testCaseId":"tc-one","attempt":0,"timestamp":{"seconds":1,"nanos":0}}}
    {"testStepStarted":{"testStepId":"step-one","testCaseStartedId":"case-one","timestamp":{"seconds":1,"nanos":0}}}
    {"testStepFinished":{"testStepId":"step-one","testCaseStartedId":"case-one","timestamp":{"seconds":2,"nanos":0},"testStepResult":{"status":"PASSED","duration":{"seconds":1,"nanos":0}}}}
    {"testCaseFinished":{"testCaseStartedId":"case-one","timestamp":{"seconds":2,"nanos":0},"willBeRetried":false}}
    {"pickle":{"id":"pk-two","name":"second imported scenario","language":"en","astNodeIds":[],"tags":[],"uri":"features/schema.feature","steps":[{"id":"ps-two","text":"second step","astNodeIds":[]}]}}
    {"testCase":{"id":"tc-two","pickleId":"pk-two","testSteps":[{"id":"step-two","pickleStepId":"ps-two"}]}}
    {"testCaseStarted":{"id":"case-two","testCaseId":"tc-two","attempt":0,"timestamp":{"seconds":3,"nanos":0}}}
    {"testStepStarted":{"testStepId":"step-two","testCaseStartedId":"case-two","timestamp":{"seconds":3,"nanos":0}}}
    {"testStepFinished":{"testStepId":"step-two","testCaseStartedId":"case-two","timestamp":{"seconds":4,"nanos":0},"testStepResult":{"status":"PASSED","duration":{"seconds":1,"nanos":0}}}}
    {"testCaseFinished":{"testCaseStartedId":"case-two","timestamp":{"seconds":4,"nanos":0},"willBeRetried":false}}
    {"testRunFinished":{"success":true,"timestamp":{"seconds":5,"nanos":0}}}
    ```
* When run pytest

    | cli_args  | --allure-cucumber-out | allure-container-results | --allure-cucumber-messages-in | messages.ndjson |
    |-----------|-----------------------|--------------------------|-------------------------------|-----------------|
    | inprocess | true                  |                          |                               |                 |
* Then Directory "allure-container-results" contains a container JSON file referencing the results
* And Allure container files in "allure-container-results" validate against the Allure3 events schema
* And Allure container files in "allure-container-results" contain JSON field groups:

    | object    | fields             |
    |-----------|--------------------|
    | container | uuid,name,children |
* And Allure container files in "allure-container-results" reference all result UUIDs
