# Quickstart: E2E Conversion Validation

## 1. Run converted feature scenarios

```bash
python -m pytest -q features
```

## 2. Run technical E2E tests

```bash
python -m pytest -q tests/e2e/test_e2e.py
```

## 3. Verify parity audit status

- Check `conversion-parity-audit.md` for verdict and follow-up fix commit links.
- Check `e2e-migration-inventory.md` for convertibility and migration progress.

## 4. Run pre-commit before committing conversion changes

```bash
pre-commit run --all-files
```
