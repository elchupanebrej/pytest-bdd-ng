#!/usr/bin/env bash
set -euo pipefail

# Why this dedicated audit exists:
# docs/messages-coverage-user-guide.md
# That guide documents the runtime-pure messages coverage/governance flow that
# this script orchestrates for CI and local maintainer runs.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUDIT_DIR="${ROOT_DIR}/.tmp/messages-coverage-audit"
MESSAGES_FILE="${AUDIT_DIR}/messages-runtime.ndjson"
REPORT_FILE="${AUDIT_DIR}/governance-runtime.json"
SCHEMA_FILE="${ROOT_DIR}/specs/008-maximize-messages-coverage/contracts/governance-report.schema.json"
DECISIONS_FILE="${ROOT_DIR}/specs/008-maximize-messages-coverage/contracts/capability-decisions.json"
MANDATORY_SCOPE_FILE="${ROOT_DIR}/specs/008-maximize-messages-coverage/mandatory-hook-capability-ids.txt"
RUNTIME_REQUIRED_FILE="${ROOT_DIR}/specs/008-maximize-messages-coverage/runtime-required-capability-ids.txt"

cd "${ROOT_DIR}"
export PYTEST_BDD_RUN_MESSAGES_COVERAGE_AUDIT=1

mkdir -p "${AUDIT_DIR}"
rm -f "${MESSAGES_FILE}" "${REPORT_FILE}"

# Populate CI metadata fields from real runtime environment variables.
export CI=true
export GITHUB_ACTIONS=true
export GITHUB_RUN_NUMBER=42
export GITHUB_RUN_ID=4242
export GITHUB_REF_NAME=coverage-audit
export GITHUB_REF=refs/heads/coverage-audit
export GITHUB_REF_TYPE=branch
export GITHUB_SHA=deadbeefdeadbeefdeadbeefdeadbeefdeadbeef
export GITHUB_SERVER_URL=https://github.com
export GITHUB_REPOSITORY=pytest-dev/pytest-bdd-ng

run_message_capture() {
  uv run --with pytest -m pytest \
    "$1" -q \
    -p no:pytest-bdd-gherkin-message-reporter \
    -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
    --messages-ndjson "${MESSAGES_FILE}"
}

run_expected_failure_capture() {
  set +e
  uv run --with pytest -m pytest \
    "$1" -q \
    -p no:pytest-bdd-gherkin-message-reporter \
    -p pytest_bdd.plugin.gherkin_message_reporter.entrypoint \
    --messages-ndjson "${MESSAGES_FILE}"
  local rc=$?
  set -e
  if [ "$rc" -eq 0 ]; then
    echo "Expected probe to fail but it passed: $1"
    exit 1
  fi
}

run_message_capture tests/messages_coverage/test_mandatory_attachments.py
# Additional real run with tag ref ensures meta.ci.git.tag is observed from runtime CI metadata.
GITHUB_REF=refs/tags/v32.0.0 GITHUB_REF_NAME=v32.0.0 GITHUB_REF_TYPE=tag run_message_capture tests/messages_coverage/test_mandatory_attachments.py
run_expected_failure_capture tests/messages_coverage/probes/test_failing_step_runtime.py
run_expected_failure_capture tests/messages_coverage/probes/test_undefined_parameter_runtime.py
run_expected_failure_capture tests/messages_coverage/probes/test_parse_error_runtime.py

uv run --with pytest-bdd-ng python -m pytest_bdd.script.message_capability_governance report \
  --messages-file "${MESSAGES_FILE}" \
  --baseline-release "v32.current" \
  --schema "${SCHEMA_FILE}" \
  --decisions "${DECISIONS_FILE}" \
  --mandatory-capabilities-file "${MANDATORY_SCOPE_FILE}" \
  --runtime-required-capabilities-file "${RUNTIME_REQUIRED_FILE}" \
  --require-runtime-required-covered \
  --require-non-runtime-classified \
  --require-fully-governed \
  --output "${REPORT_FILE}"

cat "${REPORT_FILE}"
