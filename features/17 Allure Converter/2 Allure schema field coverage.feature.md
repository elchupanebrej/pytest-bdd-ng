# Feature: Allure Schema Field Coverage
  Verify that pytest-bdd-ng can produce every field in the Allure3 events schema
  via the converter model in two ways:
    1. During a live pytest-bdd run (dynamic generation)
    2. Via generated NDJSON consumed by the plugin (post-hoc conversion)

  This feature ensures GAP-03 compliance: every schema field has evidence
  of being producible through the implemented model.

## Scenario: Live run produces all TestResult fields
  Given a pytest-bdd test suite configured to generate all allure fields
  When the test suite runs successfully
  Then the allure-results directory contains test result files
  And every result file validates against the Allure3 events schema
  And result files contain all required TestResult fields
  And result files contain populated StatusDetails fields
  And result files contain populated Label fields
  And result files contain populated Attachment fields
  And result files contain populated StepResult fields
  And result files contain populated Parameter fields

## Scenario: Post-hoc NDJSON conversion produces all fields
  Given a pytest-bdd test suite that generates a cucumber messages NDJSON file
  When the allure-cucumber converter processes the NDJSON file
  Then the output directory contains test result files
  And every result file validates against the Allure3 events schema
  And result files contain all required TestResult fields
  And result files contain populated Label fields
  And result files contain populated Attachment fields
  And result files contain populated StepResult fields
  And result files contain populated Parameter fields
  And a container file is produced that references all results

## Scenario: Container file contains all fixture fields
  Given a pytest-bdd test suite with before/after fixtures
  When the test suite runs successfully
  Then the allure-results directory contains container files
  And container files contain populated befores fixtures
  And container files contain populated afters fixtures
  And container files validate against the Allure3 events schema
