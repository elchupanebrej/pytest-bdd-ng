# Feature: Allure outline reporting
  This feature documents pytest-native Allure-Cucumber result generation for
  scenario outlines.

## Scenario: Outline reporting writes Allure-Cucumber results
* Given Copy path from "src/pytest_bdd_testing/resource/allure_reporting/outline" to test path "."

* When run pytest

    | cli_args | --allure-cucumber-out | allure-output | -k | test_sample |
    |----------|--------------------------|---------------|----|-------------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 2      |

* And Directory "allure-output" contains Allure result JSON files
