#!/usr/bin/env bash
# suspect-zones.sh - map changed paths to Suspect Zones (issue #210).
#
# Reference implementation of the diff-affected arm of the Suspect Zone rule:
#     SUSPECT = diff-affected  UNION  --lf  UNION  durations-tail
#
# Reads changed paths from stdin (one per line) and prints the pytest paths
# to run (one per line, deduplicated, relative to the checkout root). Prints
# `FULL` when narrowing is unsafe (conftest or pytest config changed) - run
# the whole suite in that case. Output is never empty: unknown paths fall
# back wide to `tests/unit` + `tests/feature`.
#
# Usage:
#   BASE=$(git merge-base HEAD origin/main)
#   { git diff --name-only "$BASE"...HEAD; git ls-files --others --exclude-standard; } \
#     | scripts/suspect-zones.sh
#   pytest $(git diff --name-only "$BASE"...HEAD | scripts/suspect-zones.sh) --ff -q --durations=10
#
# If the output contains `FULL`, run the full suite (`pytest tests`) instead
# of the printed zones.
#
# `git ls-files --others --exclude-standard` adds untracked files (unlike
# `git status --porcelain`, it never quotes paths that contain spaces).
# Portable to macOS bash 3.2: de-duplication is done with awk, first-seen order.
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
    # Shared fixtures / config: narrowing is unsafe, run everything.
    conftest.py|*/conftest.py|pytest.ini|pyproject.toml|tox.ini|setup.cfg)
      full ;;

    # src/pytest_bdd: one row per module family, extended from the research
    # seed table to match this repo's test layout.
    src/pytest_bdd/parser.py|src/pytest_bdd/parsers.py|src/pytest_bdd/parsers/*|\
    src/pytest_bdd/scenario_locator.py|src/pytest_bdd/markdown_parser.js|src/pytest_bdd/markdown_token_matcher.py)
      emit "tests/unit/parser"; emit "tests/args"; emit "tests/feature" ;;
    src/pytest_bdd/model/message_*|src/pytest_bdd/message_plugin.py)
      emit "tests/unit/message"; emit "tests/messages"; emit "tests/unit/plugins" ;;
    src/pytest_bdd/model/*)
      emit "tests/unit/model"; emit "tests/unit/parser"; emit "tests/feature" ;;
    src/pytest_bdd/plugin.py|src/pytest_bdd/collector.py)
      emit "tests/unit/bootstrap"; emit "tests/unit/execution"; emit "tests/feature"; emit "tests/e2e" ;;
    src/pytest_bdd/runner.py|src/pytest_bdd/scenario.py)
      emit "tests/unit/execution"; emit "tests/feature"; emit "tests/e2e"; emit "tests/generation" ;;
    src/pytest_bdd/compatibility/*)
      emit "tests/unit/compatibility" ;;
    src/pytest_bdd/reporting.py|src/pytest_bdd/cucumber_json.py|src/pytest_bdd/gherkin_terminal_reporter.py)
      emit "tests/unit/reporting"; emit "tests/feature" ;;
    src/pytest_bdd/allure_logging.py)
      emit "tests/unit/reporting"; emit "tests/allure_" ;;
    src/pytest_bdd/generation.py|src/pytest_bdd/template/*)
      emit "tests/generation"; emit "tests/unit/plugins" ;;
    src/pytest_bdd/hook.py|src/pytest_bdd/hooks.py)
      emit "tests/hook"; emit "tests/unit/execution"; emit "tests/test_hooks.py" ;;
    src/pytest_bdd/struct_bdd/*)
      emit "tests/struct_bdd"; emit "tests/unit/plugins"; emit "tests/unit/parser"; emit "tests/unit/compatibility" ;;
    src/pytest_bdd/steps.py|src/pytest_bdd/steps/*)
      emit "tests/unit/steps"; emit "tests/steps"; emit "tests/feature" ;;
    src/pytest_bdd/script/*)
      emit "tests/doc" ;;
    src/pytest_bdd/testing_utils.py)
      emit "tests/e2e"; emit "tests/unit" ;;
    src/pytest_bdd/util/*|src/pytest_bdd/types/*|src/pytest_bdd/const.py|src/pytest_bdd/exceptions.py|\
    src/pytest_bdd/utils.py|src/pytest_bdd/webloc.py|src/pytest_bdd/packaging.py|src/pytest_bdd/mimetype.py|\
    src/pytest_bdd/mimetypes.py|src/pytest_bdd/npm_resource.py|src/pytest_bdd/warning_types.py)
      emit "tests/unit/core"; emit "tests/unit/execution" ;;
    src/pytest_bdd/*)
      emit "tests/unit"; emit "tests/feature" ;;  # unknown module: wide, not empty

    # Fixture assets owned by a known test dir.
    features/*)
      emit "tests/e2e" ;;  # tests/e2e/test_e2e.py collects scenarios("features")
    testdata/allure_/*)
      emit "tests/allure_" ;;
    tests/*.feature|tests/*.feature.md|tests/*/*.feature|tests/*/*.feature.md|tests/*/*.gherkin)
      emit "$(dirname "$path")" ;;  # fixture next to the tests that read it

    # Changed tests: run the owning directory; root-level support files
    # (e.g. tests/slow-tests.txt) affect the whole tree.
    tests/*)
      dir="$(dirname "$path")"
      if [[ "$dir" != tests ]]; then
        emit "$dir"
      elif [[ "$(basename "$path")" == test_*.py ]]; then
        emit "$path"
      else
        emit "tests"
      fi ;;

    # Vendored submodules with a known consumer.
    gherkin|gherkin/*)
      emit "tests/gherkin_integration" ;;
    compatibility-kit|compatibility-kit/*)
      emit "tests/messages" ;;

    # Docs-only changes.
    docs/*|*.rst|*.md|README*|CHANGELOG*|AUTHORS*|LICENSE*)
      emit "tests/doc" ;;

    # Feature asset with no known owning test dir: wide, not empty.
    *.feature|*.feature.md|*.gherkin)
      emit "tests/unit"; emit "tests/feature" ;;

    # Unknown path: wide fallback, never empty.
    *)
      emit "tests/unit"; emit "tests/feature" ;;
  esac
done

if [[ "$FULL" -eq 1 ]]; then
  echo "FULL"
fi
} | awk '!seen[$0]++'
