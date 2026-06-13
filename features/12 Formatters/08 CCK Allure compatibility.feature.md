# Feature: CCK Allure Compatibility
  Validate that pytest-bdd-ng's allure-formatter converter correctly renders
  all Cucumber Compatibility Kit samples as Allure HTML reports.

  The CCK (Cucumber Compatibility Kit) provides standardized NDJSON files
  that represent expected Cucumber message streams. This feature validates
  that our converter can process these files and produce valid, renderable
  Allure HTML reports.

## Background:
* Given the CCK sample "minimal" is available
* And the allure-formatter converter processes the sample
* And the Allure HTML report is generated via Docker

## Scenario: Allure report renders scenario names
* When the report is served via HTTP
* And the browser navigates to the report
* Then the scenario name "cukes" is visible

## Scenario: Allure report renders step names
* When the report is served via HTTP
* And the browser navigates to the report
* Then the step "I have 42 cukes in my belly" is visible

## Scenario: Allure report renders test status
* When the report is served via HTTP
* And the browser navigates to the report
* Then the test status "passed" is visible
