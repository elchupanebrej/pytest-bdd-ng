# Feature: Tag expression edge cases
  Verify tag expression handling of boundary inputs, single tags, and deeply nested expressions.

## Scenario: Empty tag expression evaluates to True
* Given Tag expression ""
* Then Tag expression evaluates to True for marks "['smoke']"
* And Tag expression evaluates to True for marks "['slow']"
* And Tag expression evaluates to True for marks "[]"

## Scenario: Single tag expression
* Given Tag expression "smoke"
* Then Tag expression evaluates to True for marks "['smoke', 'login']"
* And Tag expression evaluates to False for marks "['slow', 'login']"

## Scenario: Triple AND expression
* Given Tag expression "smoke and login and regression"
* Then Tag expression evaluates to True for marks "['smoke', 'login', 'regression']"
* And Tag expression evaluates to False for marks "['smoke', 'login']"

## Scenario: Deeply nested parentheses
* Given Tag expression "((smoke and not slow) or (login and not slow)) and regression"
* Then Tag expression evaluates to True for marks "['smoke', 'regression']"
* And Tag expression evaluates to True for marks "['login', 'regression']"
* And Tag expression evaluates to False for marks "['smoke', 'slow', 'regression']"
