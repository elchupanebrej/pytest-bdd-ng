@typecheck
Feature: Strict Mypy covers every runtime module
  The project uses one strict, pinned checker policy for the complete runtime
  source tree, with error codes that protect public runtime changes.

  Scenario: An untyped runtime definition is rejected
    Given runtime source probe "untyped_definition" contains:
      """python
      def normalize(value):
          return value
      """
    When I run the authoritative runtime Mypy gate
    Then the runtime type gate should fail with diagnostic "no-untyped-def"

  Scenario: An unconstrained generic is rejected
    Given runtime source probe "unconstrained_generic" contains:
      """python
      def normalize(values: list) -> list:
          return values
      """
    When I run the authoritative runtime Mypy gate
    Then the runtime type gate should fail with diagnostic "type-arg"

  Scenario: An untyped call is rejected even when its caller is typed
    Given runtime source probe "untyped_call" contains:
      """python
      def get_value():
          return 1


      def use_value() -> int:
          return get_value()
      """
    When I run the authoritative runtime Mypy gate
    Then the runtime type gate should fail with diagnostic "no-untyped-call"

  Scenario: A typed runtime module passes and reports the resolved policy
    Given runtime source probe "typed_control" contains:
      """python
      def normalize(value: str) -> str:
          return value.strip()
      """
    When I run the authoritative runtime Mypy gate
    Then the runtime type gate should pass with visible policy identity

  Scenario: The gate explains when Mypy is not installed
    When I run the type-check adapter without Mypy installed
    Then the type-check adapter should explain that Mypy is missing
