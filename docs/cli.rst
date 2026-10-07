pytest-cuke command line
=======================

pytest-cuke installs two equivalent standalone command names:

.. code-block:: console

   cuke --help
   pytest-cuke --help

Both commands show the same command tree and package version. The pytest plugin
settings use the ``--cuke-*`` command-line namespace and ``cuke_*`` ini keys.
For example, feature autoload can be selected with ``--cuke-autoload`` and the
feature root can be changed with ``--cuke-features-dir=features``.

The built-in commands are ``validate <features-dir>``, ``generate steps``,
``sync messages schemas``, ``convert allure``, and ``replay``. ``validate`` recursively
scans ``.feature``, ``.gherkin``,
``.feature.md`` and ``.gherkin.md`` files using the same parser registry as
feature collection. It checks parsed Feature, Scenario and Scenario Outline
titles after trimming whitespace. Empty Background and Rule titles are not
part of this policy.

.. code-block:: console

   cuke validate features
   cuke validate features --include-pattern '**/*.feature.md' --json
   cuke validate features --baseline-audit --json
   cuke validate features --policy --json

Repeat ``--include-pattern`` to select multiple glob patterns. Matching files
are deduplicated and sorted by normalized path before scanning. A normal scan
returns non-zero when a title violates the policy. Add
``--no-fail-on-violation`` for advisory output with the same findings and a
zero status. ``--baseline-audit`` emits the compact compliance record, while
``--policy`` emits the active policy payload. Both ``--json`` modes retain
stable field names and violation code ``EMPTY_HEADING_TITLE``; run timestamps
and IDs vary by invocation.

An empty discovery is a valid scan with zero documents. An invalid root, file
read failure, or Gherkin parse failure returns non-zero and a structured error
when JSON output is selected.

Feature collection can reject the same violations before any scenario steps
run by enabling ``--cuke-strict`` or ``cuke_strict = true`` in pytest
configuration. It is opt-in and defaults to false, so ordinary collection
does not change when the validation policy is installed.

Binding-only scenario validation
--------------------------------

Use ``--cuke-mock-run`` or ``cuke_mock_run = true`` to validate bindings for
the selected collected scenarios without executing their Gherkin steps. This
option is disabled by default. It keeps ordinary collection, explicit
``@scenario`` bindings, autoload, ``-k``/``-m`` selection and the step
registry. Validation visits compiled steps in execution order, including
Feature and Rule backgrounds and expanded Scenario Outline rows, and passes
each step's predecessor to the same matcher used during normal execution.

Every missing step binding is reported before the scenario fails validation.
Ambiguous matches retain the normal matcher behavior. Step bodies and the BDD
scenario/step execution lifecycle hooks do not run. Pytest collection and item
selection still run, including user collection and plugin hooks. Test modules
and plugins are imported, the step registry and pytest fixtures are built, and
fixture setup or test-function fixture refresh may run. After successful
validation, the ordinary pytest test function also runs. These pytest-side
effects are not suppressed by binding-only validation.

.. code-block:: console

   pytest --cuke-mock-run

The same option can be enabled for a project in pytest configuration:

.. code-block:: ini

   [pytest]
   cuke_mock_run = true

Explicit scenario collection validation
---------------------------------------

By default, pytest-cuke stops collection with a ``UsageError`` when an
explicitly bound, non-empty scenario has no step that matches any registered
step definition. The diagnostic includes the feature, scenario and source
locations and text for the scenario's executable steps, including Feature and
Rule backgrounds. Scenarios with at least one match keep the usual runtime
behavior for any remaining missing steps.

Use ``--cuke-allow-empty-scenarios`` or
``cuke_allow_empty_scenarios = true`` to collect those scenarios as skipped
items instead. This policy applies only to explicit ``@scenario`` bindings.
Autoload, generation, binding-only mock runs, and non-empty ``-k`` or ``-m``
selections retain their own diagnostics. Scenarios with no executable steps
are unaffected, and this option does not relax title validation.

.. code-block:: console

   pytest --cuke-allow-empty-scenarios

The collection check uses the same matcher and applicable module/conftest step
registries as runtime matching. It does not set up fixtures or execute step
bodies. A parser that depends on a user fixture value unavailable during
collection is left to ordinary runtime matching rather than setting up that
fixture.

Feature source roots
--------------------

Select the local feature root for autoload and relative path bindings with
``--cuke-features-dir`` or ``cuke_features_dir``. Select the base URL for
URL-backed bindings with ``--cuke-features-base-url`` or
``cuke_features_base_url``. The precedence for each setting is an explicit
``scenarios(..., features_base_dir=...)`` or
``scenarios(..., features_base_url=...)`` binding, then the command line, then
pytest configuration. The local directory defaults to ``features``.

Relative local roots are resolved from pytest's project root, including when
pytest is started from another working directory. Relative feature paths under
a URL base keep the base path prefix; a trailing slash on the base is optional.
Absolute HTTP(S) feature URLs are used as given. URL bases must be absolute
HTTP(S) URLs without a query or fragment, and URL-backed bindings fetch only
the named feature paths.

.. code-block:: console

   pytest --cuke-features-dir=specs/features
   pytest --cuke-features-base-url=https://example.test/project/features

Project configuration can set the same roots:

.. code-block:: ini

   [pytest]
   cuke_features_dir = specs/features
   cuke_features_base_url = https://example.test/project/features

Batch feature collection
------------------------

Feature files are read and parsed serially while their count is below the batch
threshold. At the threshold and above, collection reads files asynchronously
when ``aiofiles`` is installed and parses built-in Gherkin formats in spawn
workers. ``aiofiles`` is optional; when it is absent, collection reads files
synchronously and still uses spawn workers for parsing. Custom parsers and
features that load external Examples tables keep the regular parser path. A
read, worker or pool failure is reported and falls back to serial processing
for the affected files.

Set the threshold with ``--cuke-batch-threshold`` or
``cuke_batch_threshold`` in pytest configuration. The command-line value takes
precedence. The platform default is 50 files on POSIX and 1000 files elsewhere.

.. code-block:: console

   pytest --cuke-batch-threshold=25

The pending requests and parsed Feature cache live for one pytest session and
are cleared when the session ends. Equivalent paths share a parse result while
each binding retains its own URI and scenario filters.

To compare collection locally, run the reproducible benchmark from the checkout
root. It checks that both strategies collect the same scenario identities and
prints paired timings without enforcing a speed threshold:

.. code-block:: console

   uv run python scripts/benchmark_batch_feature_collection.py --files 100 --repeats 3

Selecting a Gherkin parser
--------------------------

The parser backend can be selected with ``--cuke-parser`` or the matching
``cuke_parser`` pytest setting. The command-line option takes precedence over
the ini value:

.. code-block:: console

   pytest --cuke-parser=python
   pytest --cuke-parser=auto
   pytest --cuke-parser=go

The default is ``auto``. It uses the optional packaged Go parser when that
library is available and compatible, and otherwise reports a diagnostic and
parses with Python. If the Go parser rejects malformed Gherkin, Python parses
it again so collection keeps the usual location-aware syntax error. Markdown
whose native result differs from the Python model also uses the Python result
in ``auto`` mode.

``python`` always uses the Python parser and does not initialize the native
library. ``go`` requires an installable native library and reports how to
build or reinstall the package if it is unavailable. An unsupported
``cuke_parser`` value emits a warning and behaves as ``auto``.

The Go library is optional at package build time. Normal Python-only installs
do not require Go or a C compiler. When building distributions, the default
``PYTEST_CUKE_BUILD_GO=auto`` includes the library when a supported Go and C
toolchain is available. Set ``PYTEST_CUKE_BUILD_GO=off`` to force a pure
Python wheel or source distribution, or set it to ``required`` to fail the
build unless the native library can be built. Source distributions include
the Go source and module files so a native wheel can be built from the sdist.

Generating step definitions
----------------------------

``generate steps`` reads one or more feature files and prints missing step
stubs when no target is selected. Pass ``--target`` to update an existing
Python module. The command imports that module to inspect its registered step
definitions, including parser-based definitions and aliased public decorators;
it does not call step functions.

.. code-block:: console

   cuke generate steps --feature features/login.feature
   cuke generate steps --feature features/login.feature --feature features/admin.feature \
     --target tests/test_login.py --preview
   cuke generate steps --feature features/login.feature --target tests/test_login.py

Updates append only missing step definitions and preserve the original source
bytes, encoding, and newline style. The generated fragment is formatted with
Ruff when ``ruff`` is available on ``PATH`` and the complete result is checked
as Python before the file changes. Formatting or validation errors restore the
original bytes by default. ``--keep-on-error`` retains the attempted update
while still returning a non-zero status. ``--preview`` prints a unified diff
without writing. Repeating a successful update makes no further changes.

Autoload remains the default collection model and does not create mirror test
wrappers. Add ``--bind-scenarios`` with an explicit target when you want
scenario bindings appended to an existing test module. The executable
consumer contract in ``features/generation/transactional-step-generation.feature``
covers preview, update, rollback, keep-on-error, and generated-project
collection.

Synchronizing Cucumber Messages schemas
---------------------------------------

``sync messages schemas`` synchronizes vendored wire schemas for the exact
installed ``cucumber-messages`` contract version. The tool maps each supported
distribution version to an upstream release and immutable commit. An unknown
version fails with an instruction to add an explicit mapping. Before a remote
sync, the tool verifies that the release tag still resolves to its recorded
commit. The command normalizes upstream ``.json`` names to the packaged
``.schema.json`` form.

Pass ``--schema-path`` to select the managed output directory. ``--check`` is
read-only and exits non-zero when schemas are changed, missing, or extra. A
local source directory can be supplied for deterministic tests and CI; without
it, the tool downloads the pinned upstream archive. Failed downloads or invalid
source trees return actionable errors and leave the existing output tree
untouched.

.. code-block:: console

   cuke sync messages schemas --schema-path src/pytest_cuke/model/message_schemas
   cuke sync messages schemas --schema-path src/pytest_cuke/model/message_schemas --check
   cuke sync messages schemas --schema-path src/pytest_cuke/model/message_schemas \
     --source-dir tests/fixtures/message-schemas-v24-0-1 --check

Schema assets are included in the wheel and available to runtime code through
package resources. Package imports never start synchronization or access the
network. See ``message-schema-provenance.rst`` for the exact upstream source
pin.

Governing Cucumber Messages capabilities
----------------------------------------

``messages capabilities`` manages a deterministic field inventory and the
release decisions made against it. Capability IDs use the form
``payload_kind.field.path`` with snake_case segments, for example
``test_run_started.timestamp.seconds``. Inventory snapshots include the
baseline release, source schema reference, relevance and category for each
field. The committed policy for the pinned Messages 28.0.0 schema is in
``specs/message-capability-governance/``.

Synchronize an inventory from the installed schema assets, validate a decision
file, and compare snapshots without changing either input:

.. code-block:: console

   cuke messages capabilities sync --baseline-release 28.0.0 \
     --output build/capabilities-v28-0-0.json
   cuke messages capabilities validate-decision \
     --input specs/message-capability-governance/decisions-v28-0-0.json
   cuke messages capabilities diff \
     --previous-baseline 27.0.0 --previous build/capabilities-v27-0-0.json \
     --current-baseline 28.0.0 --current build/capabilities-v28-0-0.json \
     --previous-decisions specs/message-capability-governance/decisions-v27-0-0.json \
     --current-decisions specs/message-capability-governance/decisions-v28-0-0.json

When ``--schema-dir`` is omitted, sync accepts only the exact baseline pinned
to the installed ``cucumber-messages`` package. Pass an explicit schema
directory when synchronizing a different release.

The diff reports sorted added, removed and changed capability IDs and decision
IDs. Sync writes a new inventory; it never edits decisions. Decision files are
JSON arrays or objects with a ``decisions`` array. Each record has a
``capability_id``, ``status`` and ``release_target``. ``next-release`` is an
explicit fallback; a decision for the exact baseline takes precedence. A
status is one of ``Implemented``, ``Partly-Applicable``, ``Non-Implementable``,
``Not-Acceptable``, ``Not-Applicable`` or ``Pending``. A non-implemented
status requires a non-empty ``comment``. Conflicting or
duplicate decisions for the same capability and release are errors.

Create JSON or Markdown release checklists from the committed baseline, scope
and decisions:

.. code-block:: console

   cuke messages capabilities checklist \
     --capabilities specs/message-capability-governance/capabilities-v28-0-0.json \
     --decisions specs/message-capability-governance/decisions-v28-0-0.json \
     --mandatory-capabilities-file specs/message-capability-governance/mandatory-v28-0-0.txt \
     --format markdown --output build/messages-checklist.md

Scope files contain one canonical or camelCase capability ID per line; blank
lines and lines beginning with ``#`` are ignored. Checklist entries are sorted
and include status, decision comment, baseline change and release-blocker
state. Removed fields from an optional baseline diff remain visible for review.

Coverage reports read and validate the complete Messages NDJSON stream. The
caller must label its provenance with ``--input-kind runtime`` or
``--input-kind synthetic``. Synthetic samples remain visible as samples and
never satisfy runtime-required coverage. Runtime observation does not replace
an explicit implementation decision for mandatory fields.

.. code-block:: console

   cuke messages capabilities report \
     --messages-file build/runtime-messages.ndjson --input-kind runtime \
     --capabilities specs/message-capability-governance/capabilities-v28-0-0.json \
     --decisions specs/message-capability-governance/decisions-v28-0-0.json \
     --mandatory-capabilities-file specs/message-capability-governance/mandatory-v28-0-0.txt \
     --runtime-required-capabilities-file specs/message-capability-governance/runtime-required-v28-0-0.txt \
     --require-fully-governed --require-runtime-required-covered --format json

``--require-fully-governed`` fails when mandatory fields lack explicit
``Implemented`` decisions. ``--require-runtime-required-covered`` fails when
the runtime stream omits a runtime-required field.
``--require-non-runtime-classified`` fails when an uncovered relevant field
outside the runtime-required scope lacks
an explicit non-runtime classification. Each gate is independent. A gate
failure returns exit code 1 and preserves the report with offending IDs;
malformed inputs return exit code 2 and do not replace an existing output.
JSON and Markdown reports include the baseline, scope, observed fields and
selected explicit decisions in stable order. Reports against supplied files
use local schema and policy artifacts and do not access the network.

Converting saved Cucumber Messages to Allure
---------------------------------------------

``convert allure`` writes Allure result and container JSON from a completed
Cucumber Messages NDJSON stream. It does not collect or execute the original
tests, import their ``conftest.py`` files, or require Allure's pytest adapter.
Input paths are resolved from the current working directory. The output
directory defaults to ``allure-results`` and is created when needed.

.. code-block:: console

   cuke convert allure messages.ndjson
   cuke convert allure messages.ndjson --output build/allure-results
   pytest-cuke convert allure messages.ndjson --output build/allure-results

The converter reads UTF-8, skips blank lines, and reports missing files,
malformed JSON, invalid messages, and output errors with a non-zero exit code.
Attachment references use relative paths inside the result directory so the
directory can be moved as a unit.

The pytest reporting mode can import an existing stream with
``--cuke-allure-messages-in`` and write to the configured Allure result
directory:

.. code-block:: console

   pytest --cuke-allure=allure-results --cuke-allure-messages-in=messages.ndjson

This import path uses the same message-to-Allure mapping as the standalone
command; it does not re-run the scenarios.

Replaying saved Messages with formatters
----------------------------------------

Use ``replay`` to send a saved Messages stream to installed formatter plugins
without starting pytest or importing the test suite. Provide one or more
``--formatter NAME=DESTINATION`` selections; use ``-`` as the destination for
terminal output. Paths are relative to the current working directory. Formatter
plugins register through the ``pytest_cuke.formatters`` entry-point group and
use the same request and runtime contracts as live formatters.

.. code-block:: console

   cuke replay messages.ndjson --formatter html=reports/cucumber.html
   pytest-cuke replay messages.ndjson --formatter summary=reports/summary.txt

See :doc:`formatter-replay` for the entry-point factory contract, publication
rules, and input validation behavior.

Registering command extensions
------------------------------

An installed extension can register additional commands through the
``pytest_cuke.commands`` entry-point group. Each entry point loads a callable
that receives a ``CommandRegistry``. Its handler receives arguments after the
registered command path and returns the process exit code. A command may pass
``positionals=(...)`` to declare required positional arguments; the registry
shows them in help and passes their values to the handler in order.

.. code-block:: python

   def register_report_commands(registry):
       def summarize(arguments):
           print("summary options:", *arguments)
           return 0

       registry.add(("report", "summary"), "summarize a report", summarize)

The extension declares the registration callable in its package metadata:

.. code-block:: toml

   [project.entry-points."pytest_cuke.commands"]
   reports = "my_report_plugin:register_report_commands"

Command paths are shown in help in a stable alphabetical order. Duplicate
paths and paths that conflict with an existing command are rejected during
registration.

Optional Debug MCP failure inspection is documented in :doc:`debug-mcp`.
