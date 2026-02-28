#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${ROOT_DIR}/.tmp/reports"
mkdir -p "${REPORT_DIR}"

cd "${ROOT_DIR}"
conda run -n pytest-bdd-ng-py314 python -m pytest tests/e2e/test_e2e.py \
  --messages-ndjson=.tmp/messages.ndjson \
  --cucumber-html=.tmp/reports/messages-e2e.html

echo "Report generated at ${REPORT_DIR}/messages-e2e.html"
