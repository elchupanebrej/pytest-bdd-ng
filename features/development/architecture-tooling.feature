Feature: Architecture tooling CLI
  Verify the unified architecture CLI facade (scripts/arch.py) behaves correctly for injection, score collection, and gap analysis.

  Background:
    Given Copy path from "scripts" to test path "scripts"

  Scenario: Inject responsibility template into mockup Python file
    Given Mock file "pyproject.toml" with content:
      """toml
      [tool.architecture.inject_source]
      root = "src/pytest_cuke"
      """
    And Mock file "src/pytest_cuke/sample.py" with content:
      """python
      def hello():
          pass
      """
    When run `python scripts/arch.py inject-source --stub`
    Then the command exit code is 0
    And File "src/pytest_cuke/sample.py" contains the line "Responsibility:"
    And File "src/pytest_cuke/sample.py" contains the line "Reason for existence:"

  Scenario: Collect architecture scores
    Given Mock file "pyproject.toml" with content:
      """toml
      [tool.architecture.collect_scores]
      root = "src/pytest_cuke"
      exclude = []
      """
    And Mock file "src/pytest_cuke/sample.py" with content:
      ```python
      """
      Architecture score:
          #arch-eval:reason_for_existence=4
          #arch-eval:owned_responsibility=4
          #arch-eval:delegation_boundary=4
          #arch-eval:cohesion=4
          #arch-eval:separation=4
          #arch-eval:consumer_clarity=4
          #arch-eval:state_invariants=4
          #arch-eval:entity_fullness=4
          #arch-eval:locational_stability=4
      """
      ```
    When run `python scripts/arch.py collect-scores`
    Then the command exit code is 0
    And File ".planning/tmp/object-map.json" is not empty

  Scenario: Analyze responsibility gaps with markdown output
    Given Mock file "pyproject.toml" with content:
      """toml
      [tool.architecture.analyze_gaps]
      root = "src/pytest_cuke"
      """
    And Mock file "src/pytest_cuke/sample.py" with content:
      ```python
      """
      Responsibility:
          A short mock component for architecture gap analysis testing.
      Reason for existence:
          Tests whether gap analysis works on valid mock files.
      Architecture score:
          #arch-eval:reason_for_existence=2
          #arch-eval:owned_responsibility=2
          #arch-eval:delegation_boundary=2
          #arch-eval:cohesion=2
          #arch-eval:separation=2
          #arch-eval:consumer_clarity=2
          #arch-eval:state_invariants=2
          #arch-eval:entity_fullness=2
          #arch-eval:locational_stability=2
      """
      ```
    When run `python scripts/arch.py analyze-gaps --markdown`
    Then the command exit code is 0
    And File "docs/architecture/RESPONSIBILITY_GAPS.md" is not empty
