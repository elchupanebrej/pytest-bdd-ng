# language: en
@feature-tag
Feature: Source navigation
  A feature description.
  # Keep this source comment.
  Background: feature context
    Given origin
  @rule-tag
  Rule: a rule
    Background: rule context
      Given rule origin
    @scenario-tag
    Scenario Outline: row <value>
      Given phrase <value>
        ```text/plain
        body <value>
        ```
      And grid
        | key | value   |
        | a   | <value> |
      When act
      Then done
      @examples-tag
      Examples: values
        | value |
        | one   |
        | two   |
