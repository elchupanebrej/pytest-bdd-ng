# Quickstart: Validate Python/Pytest Compatibility Coverage

## Prerequisites

- Python environment with project dependencies installed.
- `tox` available in active environment.
- Project checkout at repository root.

## 1. List available tox environments

```bash
tox -l
```

## 2. Run all compatibility jobs

```bash
tox
```

## 3. Run selected pair checks

Use the matrix runner helper for targeted execution:

```bash
python .codex/skills/tox-test-matrix/scripts/run_tox_matrix.py --contains pytest --contains coverage --dry-run
python .codex/skills/tox-test-matrix/scripts/run_tox_matrix.py --contains py313 --contains pytest83 --contains coverage
```

## 4. Validate pair support behavior

Expected outcomes:
- Compatible pair: test job executes and reports pass/fail.
- Incompatible pair: command fails fast with explicit compatibility reason.
- Unavailable pair artifact: command fails with actionable acquisition guidance.

## 5. Verify documentation alignment

Confirm support policy in contributor docs states:
- support follows pytest compatibility matrix
- no extra library-imposed Python/pytest caps
- commands to run any compatible pair
