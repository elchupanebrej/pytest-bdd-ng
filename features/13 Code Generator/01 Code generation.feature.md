# Feature: Code generation
  Verify that code generation can gather missing artifacts, author target files, print scaffolds, and cooperate with runtime step policies.

## Scenario: Gather missing artifacts as NDJSON
* Given a BDD module with one missing scenario binding and one missing step
* When I gather missing code-generation events
* Then the missing-code NDJSON includes binding and step-definition events

## Scenario: Bind a feature idempotently
* Given a BDD module with one missing scenario binding and one missing step
* When I bind the feature to a target file twice
* Then the target file has one idempotent scenarios binding

## Scenario: Generate inert missing step skeletons
* Given a BDD module with one missing scenario binding and one missing step
* When I generate missing step skeletons into a target file
* Then the target file contains inert underscore step skeletons

## Scenario: Mock-run validates bindings without executing lifecycle code
* Given a scenario with hook and body probes
* When I run pytest in mock-run mode
* Then mock-run passes without executing hooks or step bodies

## Scenario: Mock-run emits IDE bootstrap messages without executing bodies
* Given an IDE bootstrap scenario with launch and binding probes
* When I run pytest mock-run with message reporting
* Then IDE bootstrap messages include launch handles, source identities, matched step bindings, and no probes

## Scenario: Mock-run emits missing-step diagnostics for code authoring
* Given an IDE bootstrap scenario with a missing step and one available definition
* When I run pytest mock-run with message reporting
* Then IDE bootstrap diagnostics include the missing step and scoped available definitions

## Scenario: Mock-run reports duplicate source bindings
* Given an IDE bootstrap scenario bound from two pytest modules
* When I run pytest mock-run with message reporting
* Then IDE bootstrap diagnostics include one duplicate binding warning grouped by source identity

## Scenario: Not implemented steps can be treated as passed work in progress
* Given a not implemented step scenario
* When I run pytest with WIP status passed
* Then the not implemented scenario passes without executing the step body

## Scenario: Tolerant ignored failures let scenarios continue
* Given a tolerant step scenario
* When I run pytest with ignored tolerant status
* Then the tolerant scenario passes and later steps still run
