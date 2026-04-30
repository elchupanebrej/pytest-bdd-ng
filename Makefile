.PHONY: develop sync tox-list test quick-test pre-commit coverage coveralls build dist-check release-check \
	clean compat-list compat-check validate-headings features-docs render-formatters \
	local-pr-gate messages-audit render-tox-reports render-tox-reports-run sync-message-schemas

UV_SYNC_EXTRAS := --extra test --extra testtypes --extra doc-gen --extra struct-bdd
TEST_PATH ?= tests/
PYTHON_FACTOR ?= 314
PYTEST_FACTOR ?= latest
FEATURES_ROOT ?= features
FEATURE_DOCS_OUTPUT ?= docs/features
MESSAGES_NDJSON ?= .tmp/messages.ndjson
FORMATTER_ARGS ?= --cucumber-summary
TOX_NDJSON_GLOB ?= .tox/*.messages.ndjson
TOX_HTML_REPORT_DIR ?= .tmp/tox-reports

develop:
	uv python install 3.14
	uv sync $(UV_SYNC_EXTRAS)

sync: develop

tox-list: develop
	uvx --with tox-uv tox -l

test: develop
	uvx --with tox-uv tox
	$(MAKE) --no-print-directory render-tox-reports-run

quick-test: develop
	uv run pytest $(TEST_PATH) -x

compat-list: develop
	uv run compatibility_matrix --list --compatible-only

compat-check: develop
	uv run compatibility_matrix --python $(PYTHON_FACTOR) --pytest $(PYTEST_FACTOR)

pre-commit: develop
	uvx pre-commit run --all-files

validate-headings: develop
	uv run python -m pytest_bdd.script.validate_feature_headings --root-path $(FEATURES_ROOT)

features-docs: develop
	uv run bdd_tree_to_rst $(FEATURES_ROOT) $(FEATURE_DOCS_OUTPUT)

render-formatters: develop
	uv run render_cucumber_formatters --messages-ndjson $(MESSAGES_NDJSON) $(FORMATTER_ARGS)

coverage: develop
	uv run coverage run --source=pytest_bdd -m pytest tests
	uv run coverage report -m

coveralls: coverage
	uv run coveralls

build: develop
	rm -rf ./dist
	uvx --with build python -m build

dist-check: build
	uvx --with twine twine check dist/*

release-check: dist-check

local-pr-gate: develop
	@echo "[1/4] pre-commit"
	uvx pre-commit run --all-files
	@echo "[2/4] e2e tests"
	uv run python -m pytest -q tests/e2e
	@echo "[3/4] workflow matrix sanity"
	@if [ -f .github/workflows/tests.yml ]; then \
		echo "ERROR: legacy workflow .github/workflows/tests.yml exists"; \
		exit 1; \
	fi
	@if rg -n '"3\.9"|"pypy3\.9"' .github/workflows/*.yml; then \
		echo "ERROR: unsupported 3.9 matrix entries found in workflows"; \
		exit 1; \
	fi
	@echo "[4/4] dependency marker sanity"
	@if ! rg -n '"jq;platform_system!=\x27Windows\x27"' pyproject.toml >/dev/null; then \
		echo "ERROR: jq dependency marker for Windows exclusion is missing in pyproject.toml"; \
		exit 1; \
	fi
	@echo "local_pr_gate: PASS"

messages-audit: develop
	bash scripts/run_messages_coverage_audit.sh

render-tox-reports: develop render-tox-reports-run

render-tox-reports-run:
	@mkdir -p $(TOX_HTML_REPORT_DIR)
	@set -- $(TOX_NDJSON_GLOB); \
	if [ "$$1" = "$(TOX_NDJSON_GLOB)" ]; then \
		echo "ERROR: no tox NDJSON artifacts found. Run tox first."; \
		exit 1; \
	fi; \
	for ndjson in "$$@"; do \
		envname=$$(basename "$$ndjson" .messages.ndjson); \
		echo "Rendering $$envname -> $(TOX_HTML_REPORT_DIR)/$$envname.html"; \
		uv run render_cucumber_formatters --messages-ndjson "$$ndjson" --cucumber-html "$(TOX_HTML_REPORT_DIR)/$$envname.html"; \
	done

sync-message-schemas: develop
	uv run python -m pytest_bdd.script.sync_messages_contract_schemas

clean:
	-rm -rf .venv ./dist $(TOX_HTML_REPORT_DIR) .tox/*.messages.ndjson
