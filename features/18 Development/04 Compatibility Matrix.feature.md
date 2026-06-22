# Feature: Compatibility Matrix CLI
  Verify the compatibility_matrix CLI tool calculates environment matrices and compatibility pairs correctly.

## Background:
  * Given Copy path from "tox.ini" to test path "tox.ini"

## Scenario: Check compatibility for a specific Python and pytest version pair
  * When run `python -m pytest_bdd.script.compatibility_matrix --python 314 --pytest latest`
  * Then the command exit code is 0
  * And the renderer terminal output includes:
    | compatible pair |

## Scenario: Reject incompatible pair
  * When run `python -m pytest_bdd.script.compatibility_matrix --python 310 --pytest 6.0`
  * Then the command exit code is 1
  * And the renderer terminal output includes:
    | unsupported pair |

## Scenario: Generate tox environment names from tox.ini
  * Given Mock file "tox.ini" with content:

    ```ini
    [tox]
    envlist = py310-pytest7, py314-pytestlatest
    ```
  * When run `python -m pytest_bdd.script.compatibility_matrix --tox-ini tox.ini`
  * Then the command exit code is 0
  * And the renderer terminal output includes:
    | py310-pytestlatest-coverage-lin |
    | py314-pytestlatest-coverage-lin |
