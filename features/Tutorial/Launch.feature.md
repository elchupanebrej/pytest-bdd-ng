# Feature: Simple project tests that use pytest-cuke could be run via pytest
    Project per se: https://github.com/elchupanebrej/pytest-bdd-ng/tree/rewrite-from-2.3.1/examples/tutorial

## Scenario: Catalog example with simplest steps

* Given Copy path from "examples/tutorial" to test path "tutorial"
* When I run pytest with arguments "--rootdir=tutorial tutorial/tests"

* Then pytest outcome must contain tests with statuses:
    | passed |
    |--------|
    | 1      |
