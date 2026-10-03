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

The built-in commands are ``validate <features-dir>``, ``generate steps``, and
``convert allure``. ``validate`` recursively scans ``.feature``, ``.gherkin``,
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

The ``generate steps`` and ``convert allure`` commands remain reserved and
return a non-zero exit status with an explicit not-implemented message.

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
