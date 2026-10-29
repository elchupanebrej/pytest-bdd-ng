#!/usr/bin/env bash
# Map changed paths to the pytest-cuke test zones (issue #210).
#
# Reads changed paths from stdin and prints pytest paths relative to the
# checkout root. Prints FULL when a shared fixture or project config changes.
# Unknown paths fall back to the unit and integration suites.
#
# Usage:
#   BASE=$(git merge-base HEAD origin/rewrite-from-2.3.1)
#   { git diff --name-only "$BASE"...HEAD; git ls-files --others --exclude-standard; } \
#     | scripts/suspect-zones.sh
#   pytest $(git diff --name-only "$BASE"...HEAD | scripts/suspect-zones.sh) -q
#
# Portable to macOS bash 3.2: de-duplication uses awk in first-seen order.
set -euo pipefail

FULL=0

emit() {
  printf '%s\n' "$1"
}

full() { FULL=1; }

{
while IFS= read -r path; do
  path="${path%$'\r'}"
  [[ -n "$path" ]] || continue
  case "$path" in
    # Shared fixtures or config make targeted selection unsafe.
    conftest.py|*/conftest.py|pytest.ini|pyproject.toml|tox.ini|setup.cfg)
      full ;;

    config/env-matrix.yaml|scripts/env_matrix.py|scripts/run_env_matrix_cell.py|scripts/aggregate_env_evidence.py)
      emit "tests/unit/compatibility/test_environment_matrix.py"
      emit "features/compatibility/environment-inventory.feature"
      emit "features/compatibility/environment-proof-aggregation.feature" ;;

    src/pytest_cuke/message_plugin.py|src/pytest_cuke/model/message_*)
      emit "tests/unit/message"
      emit "tests/contract/messages"
      emit "tests/unit/plugins"
      emit "features/cucumber-messages-reporting-spine.feature"
      emit "features/message-worker-consolidation.feature" ;;
    src/pytest_cuke/model/*)
      emit "tests/unit/model"
      emit "tests/unit/parser"
      emit "tests/integration/features" ;;
    src/pytest_cuke/parser.py|src/pytest_cuke/parsers/*|src/pytest_cuke/gherkin_builder.py|\
    src/pytest_cuke/feature_sources.py|src/pytest_cuke/batch_collection.py|\
    src/pytest_cuke/markdown_parser.js|src/pytest_cuke/markdown_token_matcher.py|\
    src/pytest_cuke/scenario_locator.py|src/pytest_cuke/parser_backend.py)
      emit "tests/unit/parser"
      emit "tests/integration/step-parsing"
      emit "tests/integration/features" ;;
    src/pytest_cuke/plugin.py|src/pytest_cuke/collector.py|src/pytest_cuke/scenario.py)
      emit "tests/unit/bootstrap"
      emit "tests/unit/execution"
      emit "tests/contract"
      emit "tests/integration/features"
      emit "features/pytest-cuke-bootstrap.feature" ;;
    src/pytest_cuke/runner.py)
      emit "tests/unit/execution"
      emit "tests/integration/features"
      emit "features" ;;
    src/pytest_cuke/compatibility/*)
      emit "tests/unit/compatibility"
      emit "features/compatibility" ;;
    src/pytest_cuke/reporting.py|src/pytest_cuke/cucumber_json*|\
    src/pytest_cuke/cucumber_junit*|src/pytest_cuke/cucumber_pretty.py|\
    src/pytest_cuke/cucumber_progress*|src/pytest_cuke/cucumber_summary.py|\
    src/pytest_cuke/cucumber_snippets.py|src/pytest_cuke/cucumber_usage*)
      emit "tests/unit/reporting"
      emit "tests/unit/plugins"
      emit "tests/integration/features"
      emit "features/live-cucumber-json.feature"
      emit "features/live-cucumber-junit-xml.feature" ;;
    src/pytest_cuke/allure_*.py|src/pytest_cuke/native_allure*.py|src/pytest_cuke/allure_*/)
      emit "tests/unit/reporting"
      emit "tests/integration/allure"
      emit "features/allure-message-conversion.feature"
      emit "features/native-allure-reporting.feature" ;;
    src/pytest_cuke/generation.py|src/pytest_cuke/generation_command.py|\
    src/pytest_cuke/generation_*.py)
      emit "tests/integration/generation"
      emit "tests/unit/generation"
      emit "tests/unit/plugins" ;;
    src/pytest_cuke/hook.py|src/pytest_cuke/hooks.py)
      emit "tests/integration/hooks"
      emit "tests/unit/execution" ;;
    src/pytest_cuke/struct_bdd/*)
      emit "tests/integration/struct-bdd"
      emit "tests/unit/plugins"
      emit "tests/unit/parser"
      emit "tests/unit/compatibility"
      emit "features/compatibility/optional-struct-bdd-extra.feature" ;;
    src/pytest_cuke/steps.py|src/pytest_cuke/steps/*)
      emit "tests/unit/steps"
      emit "tests/integration/steps"
      emit "tests/integration/features" ;;
    src/pytest_cuke/script/*)
      emit "tests/unit/docs" ;;
    src/pytest_cuke/debug_mcp/*)
      emit "tests/unit/plugins"
      emit "tests/unit/runtime"
      emit "features/debug-mcp-failure-inspection.feature"
      emit "features/debug-mcp-xdist-worker-discovery.feature" ;;
    src/pytest_cuke/util/*|src/pytest_cuke/types.py|src/pytest_cuke/const.py|\
    src/pytest_cuke/exceptions.py|src/pytest_cuke/utils.py|src/pytest_cuke/webloc.py|\
    src/pytest_cuke/packaging.py|src/pytest_cuke/mimetype.py|src/pytest_cuke/mimetypes.py|\
    src/pytest_cuke/npm_resource.py|src/pytest_cuke/warning_types.py)
      emit "tests/unit/core"
      emit "tests/unit/execution" ;;
    src/pytest_cuke/*)
      emit "tests/unit"
      emit "tests/integration" ;;  # unknown module: broad, not empty

    # Autoloaded feature files are directly runnable pytest targets.
    features/*)
      emit "$path" ;;

    # Shared BDD step definitions support features collected from the root.
    tests/e2e/*|tests/support/*)
      emit "features" ;;
    tests/*.feature|tests/*.feature.md|tests/*/*.feature|tests/*/*.feature.md|tests/*/*.gherkin)
      emit "$(dirname "$path")" ;;

    # Fixture assets are consumed by contract and integration tests.
    tests/data/*|tests/fixtures/*)
      emit "tests/contract"
      emit "tests/integration" ;;
    tests/*)
      dir="$(dirname "$path")"
      if [[ "$dir" != tests ]]; then
        emit "$dir"
      elif [[ "$(basename "$path")" == test_*.py ]]; then
        emit "$path"
      else
        emit "tests"
      fi ;;

    docs/*|*.rst|*.md|README*|CHANGES*|AUTHORS*|LICENSE*)
      emit "tests/unit/docs" ;;

    *.feature|*.feature.md|*.gherkin)
      emit "tests/unit"
      emit "tests/integration/features" ;;

    *)
      emit "tests/unit"
      emit "tests/integration" ;;
  esac
done

if [[ "$FULL" -eq 1 ]]; then
  echo "FULL"
fi
} | awk '!seen[$0]++'
