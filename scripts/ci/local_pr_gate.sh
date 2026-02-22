#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-pytest-bdd-ng-py314}"

echo "[1/4] pre-commit"
conda run -n "$ENV_NAME" pre-commit run --all-files

echo "[2/4] e2e tests"
conda run -n "$ENV_NAME" python -m pytest -q tests/e2e

echo "[3/4] workflow matrix sanity"
if [ -f .github/workflows/tests.yml ]; then
  echo "ERROR: legacy workflow .github/workflows/tests.yml exists"
  exit 1
fi
if rg -n '"3\.9"|"pypy3\.9"' .github/workflows/*.yml; then
  echo "ERROR: unsupported 3.9 matrix entries found in workflows"
  exit 1
fi

echo "[4/4] dependency marker sanity"
if ! rg -n '"jq;platform_system!=\x27Windows\x27"' pyproject.toml >/dev/null; then
  echo "ERROR: jq dependency marker for Windows exclusion is missing in pyproject.toml"
  exit 1
fi

echo "local_pr_gate: PASS"
