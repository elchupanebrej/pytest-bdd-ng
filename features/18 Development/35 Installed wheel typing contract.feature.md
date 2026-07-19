# Feature: Installed wheel typing contract

The published wheel must have a 100% Pyright public contract and provide
consumer typing proofs under both venv-local mypy and upstream Pyright.

**Background:**
A freshly built wheel is installed into an isolated venv outside the
source checkout so that checker results reflect the distribution rather
than the local source tree.

---

## Scenario: The wheel installs in a clean external venv and verification asserts isolation

Given a freshly built wheel from the checkout source
When the wheel is installed with mypy and Pyright into a temporary venv outside the repository root
Then the venv python resolves to the temp directory
And mypy resolves under the temp venv
And Pyright resolves under the temp venv
And `pytest_bdd.__file__` resolves to the venv site-packages, not the checkout

---

## Scenario: Consumer typing fixtures prove all six public API families

Given the installed wheel in the external venv
And consumer typing fixtures exist for scenario binding, step decorators, parser types, hooks, reporters/configuration, and re-exports
When mypy checks all valid consumer fixtures
Then every valid fixture passes with exit code zero
When mypy checks all invalid consumer fixtures
Then each invalid fixture is rejected with the expected diagnostic category
When Pyright checks all valid consumer fixtures
Then every valid fixture passes with exit code zero
When Pyright checks all invalid consumer fixtures
Then each invalid fixture is rejected with the expected diagnostic category

---

## Scenario: Pyright verifytypes reports 100% public type completeness

Given the installed wheel in the external venv
When `pyright --verifytypes pytest_bdd --ignoreexternal` runs against the venv
Then the type completeness score is 100%
