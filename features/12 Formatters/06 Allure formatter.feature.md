# Feature: Allure-Cucumber Converter
  This feature documents the Allure-Cucumber Converter's ability to convert
  Cucumber Messages NDJSON files to Allure3 JSON result files, and the pytest-native
  plugin that generates Allure results during the test run.

## Scenario: Convert a minimal valid NDJSON to Allure results
  * Given File "messages.ndjson" with content:

    ```json lines
    {"testRunStarted":{"id":"run-1","timestamp":{"seconds":0,"nanos":0}}}
    {"pickle":{"id":"pk-pass","name":"Passing","language":"en","astNodeIds":[],"tags":[],"uri":"features/sample.feature","steps":[{"id":"ps-pass-1","text":"a passing step","astNodeIds":[]}]}}
    {"testCase":{"id":"tc-pass","pickleId":"pk-pass","testSteps":[{"id":"step-pass-1","pickleStepId":"ps-pass-1"}]}}
    {"testCaseStarted":{"id":"case-pass","testCaseId":"tc-pass","attempt":0,"timestamp":{"seconds":1,"nanos":0}}}
    {"testStepStarted":{"testStepId":"step-pass-1","testCaseStartedId":"case-pass","timestamp":{"seconds":1,"nanos":0}}}
    {"testStepFinished":{"testStepId":"step-pass-1","testCaseStartedId":"case-pass","timestamp":{"seconds":2,"nanos":0},"testStepResult":{"status":"PASSED","duration":{"seconds":1,"nanos":0}}}}
    {"testCaseFinished":{"testCaseStartedId":"case-pass","timestamp":{"seconds":2,"nanos":0},"willBeRetried":false}}
    {"testRunFinished":{"success":true,"timestamp":{"seconds":3,"nanos":0}}}
    ```
  * When run `python -m pytest_bdd.plugin.allure_formatter.cli messages.ndjson --output allure-results`
  * Then renderer command exits with code 0
  * And Directory "allure-results" contains Allure result JSON files
  * And Allure result files validate against the Allure3 events schema
  * And Allure result files in "allure-results" include scenario statuses:

    | scenario | status |
    |----------|--------|
    | Passing  | passed |

## Scenario: Convert NDJSON with multiple scenarios
  * Given File "messages.ndjson" with content:

    ```json lines
    {"testRunStarted":{"id":"run-1","timestamp":{"seconds":0,"nanos":0}}}
    {"pickle":{"id":"pk-one","name":"First scenario","language":"en","astNodeIds":[],"tags":[],"uri":"features/sample.feature","steps":[{"id":"ps-one","text":"first step","astNodeIds":[]}]}}
    {"testCase":{"id":"tc-one","pickleId":"pk-one","testSteps":[{"id":"step-one","pickleStepId":"ps-one"}]}}
    {"testCaseStarted":{"id":"case-one","testCaseId":"tc-one","attempt":0,"timestamp":{"seconds":1,"nanos":0}}}
    {"testStepStarted":{"testStepId":"step-one","testCaseStartedId":"case-one","timestamp":{"seconds":1,"nanos":0}}}
    {"testStepFinished":{"testStepId":"step-one","testCaseStartedId":"case-one","timestamp":{"seconds":2,"nanos":0},"testStepResult":{"status":"PASSED","duration":{"seconds":1,"nanos":0}}}}
    {"testCaseFinished":{"testCaseStartedId":"case-one","timestamp":{"seconds":2,"nanos":0},"willBeRetried":false}}
    {"pickle":{"id":"pk-two","name":"Second scenario","language":"en","astNodeIds":[],"tags":[],"uri":"features/sample.feature","steps":[{"id":"ps-two","text":"second step","astNodeIds":[]}]}}
    {"testCase":{"id":"tc-two","pickleId":"pk-two","testSteps":[{"id":"step-two","pickleStepId":"ps-two"}]}}
    {"testCaseStarted":{"id":"case-two","testCaseId":"tc-two","attempt":0,"timestamp":{"seconds":3,"nanos":0}}}
    {"testStepStarted":{"testStepId":"step-two","testCaseStartedId":"case-two","timestamp":{"seconds":3,"nanos":0}}}
    {"testStepFinished":{"testStepId":"step-two","testCaseStartedId":"case-two","timestamp":{"seconds":4,"nanos":0},"testStepResult":{"status":"PASSED","duration":{"seconds":1,"nanos":0}}}}
    {"testCaseFinished":{"testCaseStartedId":"case-two","timestamp":{"seconds":4,"nanos":0},"willBeRetried":false}}
    {"testRunFinished":{"success":true,"timestamp":{"seconds":5,"nanos":0}}}
    ```
  * When run `python -m pytest_bdd.plugin.allure_formatter.cli messages.ndjson --output allure-results`
  * Then renderer command exits with code 0
  * And Directory "allure-results" contains "2" Allure result JSON files
  * And Directory "allure-results" contains a container JSON file referencing the results
  * And Allure container files in "allure-results" reference all result UUIDs

## Scenario: Handle empty NDJSON gracefully
  * Given File "messages.ndjson" with content:

    ```json lines
    ```
  * When run `python -m pytest_bdd.plugin.allure_formatter.cli messages.ndjson --output allure-results`
  * Then renderer command exits with code 0
  * And Directory "allure-results" contains "0" Allure result JSON files

## Scenario: CLI rejects nonexistent input file
  * When run `python -m pytest_bdd.plugin.allure_formatter.cli missing.ndjson --output allure-results`
  * Then renderer command exits with non-zero code
  * And the renderer terminal output includes:

    | *missing.ndjson* |
    |------------------|

## Scenario: Runtime plugin generates Allure results during pytest run
  * Given File "pytest.toml" with content:

    ```toml
    [pytest]
    disable_feature_autoload = true
    ```
  * And File "sample.feature" with content:

    ```gherkin
    Feature: Sample
      Scenario: Passing
        Given a passing step
    ```
  * And File "conftest.py" with content:

    ```python
    from pytest_bdd import given

    @given("a passing step")
    def _():
      pass
    ```
  * And File "test_sample.py" with content:

    ```python
    from pytest_bdd import scenarios

    test = scenarios("sample.feature")
    ```
  * When run pytest

    | cli_args | --allure-cucumber-out | allure-output | test_sample.py |
    |----------|-----------------------|---------------|----------------|

  * Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |
  * And Directory "allure-output" contains Allure result JSON files
  * And Allure result files validate against the Allure3 events schema
  * When run docker

    | image   | allure3-local:latest                              |
    |---------|---------------------------------------------------|
    | command | allure generate /allure-results -o /allure-report |
    | volume  | allure-output:/allure-results:ro                  |
    | volume  | allure-report:/allure-report                      |
  * Then Directory "allure-report" contains Allure HTML report with index.html
  * And Allure HTML report contains scenario name "Passing"

## Scenario: Live mode generates Allure results without NDJSON file
  * Given File "pytest.toml" with content:

    ```toml
    [pytest]
    disable_feature_autoload = true
    ```
  * And File "live.feature" with content:

    ```gherkin
    Feature: Live mode test
      Scenario: Passing live
        Given a passing step
    ```
  * And File "conftest.py" with content:

    ```python
    from pytest_bdd import given

    @given("a passing step")
    def _():
      pass
    ```
  * And File "test_live.py" with content:

    ```python
    from pytest_bdd import scenarios

    test = scenarios("live.feature")
    ```
  * When run pytest

    | cli_args | --allure-cucumber-out | allure-live-output | test_live.py |
    |----------|-----------------------|--------------------|--------------|
  * Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |

  * And Directory "allure-live-output" contains Allure result JSON files
  * And Allure result files validate against the Allure3 events schema

## Scenario: Runtime plugin renders full pytest-bdd feature surface in an Allure report
  * Given File "pytest.toml" with content:

    ```toml
    [pytest]
    disable_feature_autoload = true
    ```
  * And File "full_surface.feature" with content:
    ```gherkin
    @allure-ui @feature-tag
    Feature: Local Allure full surface
      Feature description propagated to Allure.

      Background:
        Given shared context

      Rule: Rule level reporting
        Rule description propagated to Allure.

        Background:
          Given rule context

        @pass @attachments
        Scenario: Passing full surface
          Scenario description propagated to Allure.
          When I attach text evidence "pass evidence"
          And I attach binary evidence "pass.bin"
          And I receive table data
            | key | value |
            | foo | bar   |
          And I receive doc string
            """text/plain
            pass docstring
            """
          Then outcome is "pass"

        @assertion
        Scenario: Failing assertion surface
          When I attach text evidence "assert evidence"
          Then assertion fails with message "expected proof"

        @exception
        Scenario: Failing exception surface
          When I attach text evidence "exception evidence"
          Then exception fails with message "runtime proof"

        @outline
        Scenario Outline: Outline status surface
          Outline description propagated to Allure.
          When I attach text evidence "<name> evidence"
          Then outcome is "<outcome>"

          @examples-tag
          Examples: Status examples
            | name         | outcome |
            | outline pass | pass    |
    ```

  * And File "conftest.py" with content:
    ```python
    from pytest_bdd import given, parsers, then, when


    @given("shared context")
    def _shared_context():
        return "shared"


    @given("rule context")
    def _rule_context():
        return "rule"


    @when(parsers.parse('I attach text evidence "{value}"'))
    def _attach_text(attach, value):
        attach(value, media_type="text/plain;charset=UTF-8", file_name=f"{value}.txt")


    @when(parsers.parse('I attach binary evidence "{filename}"'))
    def _attach_binary(attach, filename):
        attach(b"binary evidence", media_type="application/octet-stream", file_name=filename)


    @when("I receive table data")
    def _receive_table():
        return "table"


    @when("I receive doc string")
    def _receive_doc_string():
        return "docstring"


    @then(parsers.parse('outcome is "{outcome}"'))
    def _outcome(outcome):
        assert outcome == "pass"


    @then(parsers.parse('assertion fails with message "{message}"'))
    def _assertion_fails(message):
        raise AssertionError(message)


    @then(parsers.parse('exception fails with message "{message}"'))
    def _exception_fails(message):
        raise RuntimeError(message)
    ```

  * And File "test_full_surface.py" with content:
    ```python
    from pytest_bdd import scenarios

    test = scenarios("full_surface.feature")
    ```
  * When run pytest

    | cli_args | --messages-ndjson | messages.ndjson | --allure-cucumber-out | allure-full-results | test_full_surface.py |
    |----------|-------------------|-----------------|-----------------------|---------------------|----------------------|

  * Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 2      | 2      |

  * And the local allure-cucumber plugin generated results for "4" scenarios
  * When run docker

    | image   | allure3-local:latest                                        |
    |---------|-------------------------------------------------------------|
    | command | allure generate /allure-full-results -o /allure-full-report |
    | volume  | allure-full-results:/allure-full-results:ro                 |
    | volume  | allure-full-report:/allure-full-report                      |

  * Then Directory "allure-full-report" contains Allure HTML report with index.html
  * When the Allure report is opened in a browser
  * Then the Allure report shows "4" tests
  * And the Allure report shows scenario statuses:

    | scenario                  | status |
    |---------------------------|--------|
    | Passing full surface      | passed |
    | Failing assertion surface | failed |
    | Failing exception surface | failed |
    | Outline status surface    | passed |

  * And the Allure report shows step counts:

    | scenario                  | steps |
    |---------------------------|-------|
    | Passing full surface      | 7     |
    | Failing assertion surface | 4     |
    | Failing exception surface | 4     |
    | Outline status surface    | 4     |

  * And the Allure report shows tags:

    | scenario                  | tags                                           |
    |---------------------------|------------------------------------------------|
    | Passing full surface      | @allure-ui,@feature-tag,@pass,@attachments     |
    | Failing assertion surface | @allure-ui,@feature-tag,@assertion             |
    | Failing exception surface | @allure-ui,@feature-tag,@exception             |
    | Outline status surface    | @allure-ui,@feature-tag,@outline,@examples-tag |

  * And the Allure report shows descriptions and structured arguments
  * And the Allure report shows failure messages:

    | scenario                  | message        |
    |---------------------------|----------------|
    | Failing assertion surface | expected proof |
    | Failing exception surface | runtime proof  |

## Scenario: Convert existing NDJSON file to Allure report via CLI
  * Given File "existing-messages.ndjson" with content:

    ```json lines
    {"testRunStarted":{"id":"run-1","timestamp":{"seconds":0,"nanos":0}}}
    {"pickle":{"id":"pk-existing","name":"Passing","language":"en","astNodeIds":[],"tags":[],"uri":"features/sample.feature","steps":[{"id":"ps-existing-1","text":"a passing step","astNodeIds":[]}]}}
    {"testCase":{"id":"tc-existing","pickleId":"pk-existing","testSteps":[{"id":"step-existing-1","pickleStepId":"ps-existing-1"}]}}
    {"testCaseStarted":{"id":"case-existing","testCaseId":"tc-existing","attempt":0,"timestamp":{"seconds":1,"nanos":0}}}
    {"testStepStarted":{"testStepId":"step-existing-1","testCaseStartedId":"case-existing","timestamp":{"seconds":1,"nanos":0}}}
    {"testStepFinished":{"testStepId":"step-existing-1","testCaseStartedId":"case-existing","timestamp":{"seconds":2,"nanos":0},"testStepResult":{"status":"PASSED","duration":{"seconds":1,"nanos":0}}}}
    {"testCaseFinished":{"testCaseStartedId":"case-existing","timestamp":{"seconds":2,"nanos":0},"willBeRetried":false}}
    {"testRunFinished":{"success":true,"timestamp":{"seconds":3,"nanos":0}}}
    ```
  * When run `python -m pytest_bdd.plugin.allure_formatter.cli existing-messages.ndjson --output allure-cli-output`
  * Then renderer command exits with code 0
  * And Directory "allure-cli-output" contains Allure result JSON files
  * And Directory "allure-cli-output" contains a container JSON file referencing the results
  * When run docker

    | image   | allure3-local:latest                              |
    |---------|---------------------------------------------------|
    | command | allure generate /allure-results -o /allure-report |
    | volume  | allure-cli-output:/allure-results:ro              |
    | volume  | allure-cli-report:/allure-report                  |

  * Then Directory "allure-cli-report" contains Allure HTML report with index.html
  * And Allure HTML report contains scenario name "Passing"
