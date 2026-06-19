# Feature: Allure scenario reporting
  This feature documents pytest-native Allure-Cucumber result generation for
  regular scenarios.

## Scenario: Scenario reporting writes Allure-Cucumber results
* Given Copy path from "src/pytest_bdd_testing/resource/allure_reporting/simple_scenario" to test path "."

* When run pytest

    | cli_args | --allure-cucumber-out | allure-output | -k | test_sample.py |
    |----------|--------------------------|---------------|----|----------------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |

* And Directory "allure-output" contains Allure result JSON files
