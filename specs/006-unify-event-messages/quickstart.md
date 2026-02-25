<!-- markdownlint-disable MD013 -->

# Quickstart: Validate Unified Event Message Reporting

## 1. Prepare environment

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pip install -e '.[test,testtypes]'
```

Expected:
- Editable install is available for reporter/message validation.

## 2. Validate canonical message stream behavior

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest -q \
  tests/messages/test_messages.py \
  tests/feature/test_report.py \
  tests/feature/test_gherkin_terminal_reporter.py \
  tests/hook/test_reporting_context_snapshot_unit.py
```

Expected:
- Message stream remains parseable and lifecycle ordering assertions pass.
- Scenario/terminal report outputs remain consistent with canonical events.

## 3. Validate compatibility behavior for failure diagnostics

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 python -m pytest -q tests/compatibility/test_failure_messages.py
```

Expected:
- Failure and error message behavior remains deterministic under compatibility checks.

## 4. Validate MyPy message-construction coverage

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest-mypy
```

Expected:
- Message-construction paths pass static type validation with no new message-related type failures.

## 5. Validate spec-prefix uniqueness prerequisite behavior

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
.specify/scripts/bash/check-prerequisites.sh --json --paths-only
```

Expected:
- Exactly one feature directory resolves for the active prefix.
- No duplicate-prefix error is reported.

## 5a. Prefix-conflict remediation workflow

If `check-prerequisites.sh --json` reports `PREFIX_AUDIT.status` as `fail`:

1. Identify each conflict tuple from `PREFIX_AUDIT.conflicts`.
2. Keep the intended active directory name unchanged when it already matches the current branch.
3. Rename the extra conflicting directories to the next available numeric prefix.
4. Re-run:

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
.specify/scripts/bash/check-prerequisites.sh --json
```

Expected:
- `PREFIX_AUDIT.status` becomes `pass`.
- `FEATURE_DIR` resolves deterministically for the current feature prefix.

## 6. Run contributor quality gate

```bash
cd /Users/goloveshkokonstantin/Projects/pytest-bdd-ng
conda run -n pytest-bdd-ng-py314 pre-commit run --all-files
```

Expected:
- Pre-commit hooks pass with no unresolved issues.

## 7. Latest execution results (2026-02-25)

- Command:

```bash
conda run -n pytest-bdd-ng-py314 python -m pytest -q \
  tests/messages/test_messages.py \
  tests/messages/test_message_attachments.py \
  tests/messages/test_message_validation.py \
  tests/messages/test_message_typing_regression.py \
  tests/feature/test_report.py \
  tests/feature/test_gherkin_terminal_reporter.py \
  tests/feature/test_cucumber_json.py \
  tests/contract/test_event_message_reporting_contract.py \
  tests/scripts/test_spec_prefix_resolution.py \
  tests/hook/test_hook.py::test_message_hook_signature_uses_event_envelope_annotation
```

  Result: `40 passed in 7.56s`

- Command:

```bash
conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest-mypy
```

  Result: `FAIL` (repository-wide pre-existing mypy issues remain; command reported 11 errors in 5 files).

- Command:

```bash
conda run -n pytest-bdd-ng-py314 tox -e py314-pytestlatest-mypy-messages
```

  Result: `PASS` (`Success: no issues found in 7 source files`).

- Command:

```bash
conda run -n pytest-bdd-ng-py314 pre-commit run --all-files
```

  Result: `FAIL` (repository-wide hooks reported existing markdown and mypy/lint issues outside this feature scope; some files were auto-formatted by hooks).
