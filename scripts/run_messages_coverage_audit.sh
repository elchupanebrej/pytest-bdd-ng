#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"
export PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1

conda run -n pytest-bdd-ng-py314 python -m pytest tests/messages_coverage -q
