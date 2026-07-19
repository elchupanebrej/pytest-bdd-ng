# Plan 17-02 Summary: Migrate GitHub CI to use Makefile

## Accomplishments
- Refactored `.github/workflows/main.yml` to call `make env-install-npm`, `make tox`, `make check-message-schemas`, and `make dist-check` instead of duplicating command bodies directly in the workflow.
- Replaced the manual pip/uv installation steps in `main.yml` with the official `astral-sh/setup-uv@v6` action.
- Scoped the visible `Install PyPi dependencies` step to Python 3.14 only to install `codecov`, keeping it separate from the clean Makefile-driven flow.
- Updated the contract test in `tests/cases/contract/generation/test_template_packaging.py` to assert that the workflow calls `make check-message-schemas` instead of the raw Python script command.
- Verified that all modified files pass the `pre-commit` hooks and all contract tests pass successfully.
