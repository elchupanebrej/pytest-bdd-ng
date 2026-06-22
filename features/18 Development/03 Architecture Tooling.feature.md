# Feature: Architecture Tooling CLI
  Verify the unified architecture CLI facade (scripts/arch.py) behaves correctly for injection, score collection, and gap analysis.

## Background:
  * Given Copy path from "scripts" to test path "scripts"

## Scenario: Inject responsibility template into mockup Python file
  * Given Mock file "pyproject.toml" with content:

    ```toml
    [tool.architecture.inject_source]
    root = "src/pytest_bdd"
    ```
  * And Mock file "src/pytest_bdd/sample.py" with content:

    ```python
    def hello():
        pass
    ```
  * When run `python scripts/arch.py inject-source --stub`
  * Then the command exit code is 0
  * And File "src/pytest_bdd/sample.py" contains the line "Responsibility:"
  * And File "src/pytest_bdd/sample.py" contains the line "Reason for existence:"

## Scenario: Collect architecture scores
  * Given Mock file "pyproject.toml" with content:

    ```toml
    [tool.architecture.collect_scores]
    root = "src/pytest_bdd"
    exclude = []
    ```
  * And Mock file "src/pytest_bdd/sample.py" with content:

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
  * When run `python scripts/arch.py collect-scores`
  * Then the command exit code is 0
  * And File ".planning/tmp/object-map.json" is not empty
