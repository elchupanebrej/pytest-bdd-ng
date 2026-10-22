Feature: Semantic heading validation

  Scenario: The CLI identifies an empty parsed scenario title
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    # The consumer file step expands this marker to three spaces.
    And consumer file "features/empty.feature" has content:
      """
      Feature: A feature with a titled heading
        Scenario: {WHITESPACE_TITLE}
          Given a step
      """
    When I run command "cuke" with arguments "validate features --json"
    Then the command should exit with a non-zero code
    And the command output should contain "EMPTY_HEADING_TITLE"

  Scenario: The CLI recognizes localized scenario aliases from the parser
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/empty-french.feature" has content:
      """
      # language: fr
      Fonctionnalité: Titre valide
        Exemple: {WHITESPACE_TITLE}
        Scénario: {WHITESPACE_TITLE}
      """
    When I run command "cuke" with arguments "validate features --json"
    Then the command should exit with a non-zero code
    And the command JSON should include:
      """
      {
        "documents_scanned": 1,
        "status": "fail",
        "violations": [
          {
            "path": "empty-french.feature",
            "line": 3,
            "heading_type": "scenario",
            "code": "EMPTY_HEADING_TITLE"
          },
          {
            "path": "empty-french.feature",
            "line": 4,
            "heading_type": "scenario",
            "code": "EMPTY_HEADING_TITLE"
          }
        ]
      }
      """

  Scenario: The baseline audit emits a compact compliance record
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/valid.feature" has content:
      """
      Feature: Valid feature
        Scenario: Valid scenario
      """
    When I run command "cuke" with arguments "validate features --baseline-audit --json"
    Then the command should exit with code 0
    And the command JSON should include:
      """
      {
        "policy_id": "feature-heading-policy-v1",
        "violations_count": 0,
        "compliant": true
      }
      """
