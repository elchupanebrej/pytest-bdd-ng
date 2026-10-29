Live formatter plugins
======================

pytest-cuke can attach one or more formatter processes to the validated
Cucumber Messages stream while pytest runs. Formatter plugins select their own
options and return declarative requests through
``pytest_cuke_formatter_requests``. The shared runtime validates the combined
catalog before tests start and owns each child process, stream, output file,
and temporary asset directory.

Formatter requests
------------------

Import ``FormatterRequest`` and ``FormatterAsset`` from the public extension
module ``pytest_cuke.formatter_api``. A request names one formatter and describes its
argument vector, working directory, optional output path, runtime requirements,
timeout, and any small files needed by the child.

The child reads one JSON Cucumber Messages envelope per line from standard
input. It writes terminal output to standard output when ``output_path`` is
``None``. For a report file, set ``output_path`` and write the complete report
to standard output; the runtime stages those bytes beside the destination and
publishes the file only after a clean child exit. Standard error is relayed to
pytest's error stream. Relative working directories and output paths are
resolved against pytest's root directory.

This example uses a Node script shipped with a formatter plugin:

.. code-block:: python

   from pathlib import Path
   import sys

   from pytest_cuke.formatter_api import FormatterAsset, FormatterRequest


   def pytest_addoption(parser):
       parser.addoption("--cuke-example-report", action="store_true")


   def pytest_cuke_formatter_requests(config):
       if not config.getoption("--cuke-example-report"):
           return ()
       return (
           FormatterRequest(
               name="example-report",
               command=("node", "formatter.mjs", "{asset_dir}/formatter-config.json"),
               output_path=Path("example.txt"),
               working_directory=Path(__file__).parent,
               required_executables=("node",),
               required_npm_packages=("@example/cucumber-formatter",),
               runtime_assets=(FormatterAsset("formatter-config.json", "{}"),),
           ),
       )

When ``{asset_dir}`` appears in a command argument, the runtime replaces it
with a temporary directory containing the request's ``FormatterAsset`` files.
Asset paths must be relative and may not escape that directory. Selected npm
packages are checked from the request's working directory. Unselected plugins
do not trigger executable or package checks.

Catalog and output rules
------------------------

Requests from independent plugins are sorted by their name before processes
start. Names must be unique. File output paths are normalized before collision
checks, and their parent directories must already exist. Multiple formatters
may write separate files, but at most one may write to the terminal.

Implementations should return no request unless their canonical ``--cuke-*``
option or configuration value is selected. The shared catalog is the single
activation and validation point for the formatter family.

Built-in Cucumber pretty output
-------------------------------

Select the official live Cucumber pretty formatter with ``--cuke-pretty`` or
``cuke_pretty = true`` in pytest configuration. It writes to pytest's terminal
stream as validated Messages arrive, so scenario output is visible during the
run. It can be combined with Messages, JSON, JUnit, usage JSON from another
formatter plugin, and other formatters that each write to a distinct file.
Only one selected formatter can write to the terminal.

Pretty output is written to the original terminal stream even while pytest
captures test output. Test output continues to follow the selected pytest
capture mode.

The pretty formatter requires Node.js and the ``@cucumber/pretty-formatter``
npm package to be installed in the pytest root directory. When the option is
not selected, pytest-cuke does not check for Node.js or the npm package. A
missing npm package is reported during pytest configuration with an install
location and command; a missing Node executable is named in the diagnostic.
The child formatter does not inherit a TTY; pytest relays its output for both
interactive and piped runs.

Built-in Cucumber progress output
---------------------------------

Select live Cucumber progress with ``--cuke-progress`` or
``cuke_progress = true`` in pytest configuration. It emits one marker when each
scenario attempt finishes, using the worst step status for that attempt. A
retry receives its own marker. The status markers are ``.`` for passed, ``F``
for failed, ``-`` for skipped, ``P`` for pending, ``U`` for undefined, ``A``
for ambiguous, and ``?`` for unknown. The official Cucumber summary follows
the marker output when the test run finishes.

Progress markers are written live at both quiet and verbose pytest levels and
remain visible while pytest captures test output. Quiet runs use one compact
marker line. Verbose runs and ``--capture=tee-sys``/``--capture=no`` start each
marker on a fresh line so it stays separate from test output. Progress can be
combined with Messages and file formatters. It cannot share stdout with
``--cuke-pretty``.

Progress uses Node.js and the ``@cucumber/pretty-formatter`` package installed
in the pytest root directory. When the option is not selected, pytest-cuke
does not check for either dependency.

Built-in Cucumber progress bar
------------------------------

Select the progress bar with ``--cuke-progress-bar`` or
``cuke_progress_bar = true`` in pytest configuration. In a TTY it updates the
completed/total scenario count, width-aware bar, and status marker as each
scenario attempt finishes. The width falls back to 80 columns when pytest has
no terminal width metadata. Retry attempts update their Pickle's completed
count without increasing the total past 100 percent.

When stdout is piped, the formatter emits only the readable status markers and
the final Cucumber summary; it does not write cursor-control sequences. Failed
and skipped attempts use their worse step outcome. The bar can share a run
with Messages and file formatters, but it cannot share stdout with
``--cuke-pretty`` or ``--cuke-progress``.

The runnable consumer in ``examples/cucumber-progress-bar/`` shows the public
autoload and step-definition setup with the pinned
``@cucumber/pretty-formatter`` 4.0.2 package.

The progress bar uses Node.js and ``@cucumber/pretty-formatter`` in the pytest
root directory. The shared formatter catalog checks these dependencies only
when the option is selected. Unselected tests remain independent of Node and
npm.

Built-in Cucumber snippets
--------------------------

Select Cucumber's snippets formatter with ``--cuke-snippets`` or
``cuke_snippets = true`` in pytest configuration. At the end of the run, it
prints JavaScript step definitions for undefined steps. Defined steps are
omitted, and the undefined pytest result and exit status remain unchanged.
The formatter uses Cucumber Messages execution results and parameter type
metadata; it does not execute user step definitions to build suggestions.

The snippets formatter writes to the terminal stream and can be combined with
Messages and distinct file formatters. It cannot share stdout with
``--cuke-pretty``, ``--cuke-progress``, or ``--cuke-progress-bar``.

The formatter uses Node.js, npm, and the ``@cucumber/cucumber`` package
installed in the pytest root directory. When snippets are not selected,
pytest-cuke does not check for these dependencies.

The runnable consumer in ``examples/cucumber-snippets/`` demonstrates the
JavaScript output from the pinned ``@cucumber/cucumber`` 13.3.0 runtime. For
example, an undefined quoted Given produces this binding shape:

.. code-block:: javascript

   Given('a customer named {string} is registered', function (string) {
     return 'pending';
   });

Built-in Cucumber summary
------------------------

Select Cucumber's official scenario and step summary with ``--cuke-summary``
or ``cuke_summary = true`` in pytest configuration. The summary reports
scenario and step outcomes, run duration, and useful details for failures,
pending steps, and undefined steps. It counts executed outline rows and keeps
retry attempts distinct according to their Cucumber Messages results.

The summary writes to the terminal and can be combined with Messages and
distinct file formatters. It cannot share stdout with ``--cuke-pretty``,
``--cuke-progress``, ``--cuke-progress-bar``, or ``--cuke-snippets``.

The formatter uses Node.js, npm, and the ``@cucumber/cucumber`` package
installed in the pytest root directory. When the summary is not selected,
pytest-cuke does not check for these dependencies.

The runnable consumer in ``examples/cucumber-summary/`` demonstrates the
public step facade, autoloaded outline rows, and the pinned
``@cucumber/cucumber`` 13.3.0 formatter.

Built-in Cucumber JSON
----------------------

Select the message-driven Cucumber JSON formatter with ``--cuke-json[=PATH]``
or ``cuke_json = "PATH"`` in pytest configuration. The option without a path
writes ``cucumber.json`` under pytest's root directory; relative paths resolve
from that root. The ``cuke_json_backend`` setting defaults to ``"cucumber"``.
This backend uses the JSON formatter from ``@cucumber/cucumber`` and preserves
the formatter's feature, scenario, step, argument, attachment, status, duration,
and diagnostic fields. In this legacy JSON projection, feature and
scenario descriptions appear in their respective ``description`` fields. Rules
are flattened into the feature's scenario entries: there is no separate Rule
object, and Rule description text is omitted. Rule tags are carried onto the
scenarios inside the Rule. Scenario hooks appear in each scenario's ``steps`` as
hidden ``Before`` and ``After`` entries, not as separate hook fields.

The former pytest-cuke JSON writer remains available through explicit routing:
set ``--cuke-json-backend=native`` or ``cuke_json_backend = "native"``. Both
backends use the same ``--cuke-json`` destination setting. The native backend
does not need Node.js or npm; the message-driven backend requires Node.js, npm,
and ``@cucumber/cucumber`` installed in the pytest root directory. These
optional dependencies are checked only when the message-driven backend is
selected.

The message-driven formatter writes a file and can run beside one terminal
formatter and other reports with distinct paths. It also works with saved
streams through ``cuke replay MESSAGES.ndjson --formatter
cucumber-json=PATH``; replay does not collect or execute tests. Live and replay
both use the shared formatter catalog and output lifecycle.

Built-in Cucumber JUnit XML
---------------------------

Select Cucumber's official message-driven JUnit XML formatter with
``--cuke-junit[=PATH]`` or ``cuke_junit = "PATH"`` in pytest configuration.
The option without a path writes ``cucumber.xml`` under pytest's root directory;
relative paths resolve from that root. The report follows
``@cucumber/junit-xml-formatter``'s XML projection: suites and test cases carry
scenario identity and outcomes, test cases carry source ``file`` and ``line``
attributes, step details appear in ``system-out``, and failed or skipped cases
use the corresponding JUnit elements. Scenario outline rows remain distinct
test cases. Feature, Rule, Scenario, and Examples tags; Feature, Rule, and
Scenario descriptions; step doc strings and data tables; and Examples tables
are recorded as suite ``<property>`` values, not dedicated XML elements.

The report can run beside pytest's native ``--junitxml`` when the two outputs
use distinct paths. It also works with saved streams through ``cuke replay
MESSAGES.ndjson --formatter cucumber-junit=PATH``; replay does not collect or
execute tests. Live and replay both use the shared formatter catalog and output
lifecycle. The formatter requires Node.js, npm, and
``@cucumber/junit-xml-formatter`` installed in the pytest root directory. These
dependencies are checked only when the formatter is selected.

Built-in Cucumber step-definition usage
---------------------------------------

Select Cucumber's step-definition usage report with ``--cuke-usage`` or
``--cuke-usage=-`` to write it to the terminal. Provide a path with
``--cuke-usage=PATH`` to write the report to a file; relative paths are
resolved from the pytest root directory. The equivalent ``cuke_usage`` ini
setting accepts ``-`` for terminal output or a file path. With no option or
setting, the formatter is disabled.

The report includes every discovered step definition, marks unused definitions,
and reports match examples, durations, patterns and source locations from
Cucumber Messages. Terminal output adapts its columns to the available width.
File output does not occupy the terminal formatter slot, so it can coexist
with a terminal renderer and distinct JSON, JUnit XML, and other formatter
files. Terminal usage output cannot share stdout with ``--cuke-pretty``,
``--cuke-progress``, ``--cuke-progress-bar``, ``--cuke-snippets`` or
``--cuke-summary``.

The formatter uses Node.js, npm, and the ``@cucumber/cucumber`` package
installed in the pytest root directory. When usage is not selected, pytest-cuke
does not check for these dependencies.

The runnable consumer in ``examples/cucumber-usage/`` demonstrates autoloaded
step definitions, outline matches, and an unused definition with the pinned
``@cucumber/cucumber`` 13.3.0 formatter.

Built-in machine-readable step-definition usage
------------------------------------------------

Write Cucumber's machine-readable step-definition usage report with
``--cuke-usage-json=PATH`` or the ``cuke_usage_json`` pytest setting. A file
path is required; relative paths resolve from the pytest root directory. The
report uses the JSON schema emitted by the selected Cucumber backend and keeps
definition rows, match records, source locations, and available durations
machine-readable, including discovered definitions without matches. Match
records identify feature URI, source line, and interpolated step text; the
backend does not serialize per-execution IDs.

The runnable consumer in ``examples/cucumber-usage-json/`` demonstrates the
autoloaded feature, outline matches, and a discovered definition with no
matches. It uses the pinned ``@cucumber/cucumber`` 13.3.0 package.

This formatter writes only to its requested file. It can run beside one
terminal formatter such as ``--cuke-summary`` and other report files, provided
each destination is distinct. Missing directories, duplicate destinations,
and formatter failures are reported by the shared formatter runtime.

The formatter uses Node.js, npm, and the ``@cucumber/cucumber`` package
installed in the pytest root directory. When usage JSON is not selected,
pytest-cuke does not check for these optional dependencies.

Lifecycle and distributed runs
-------------------------------

The runtime starts children before scenario messages are emitted, forwards only
validated controller envelopes, and adapts xdist worker batches into one
controller run. The controller's run hooks remain canonical; duplicate
worker-level run hooks are omitted because worker batches can arrive after
another worker has started a scenario. Worker IDs and references are
normalized, and duplicate structural definitions are removed. Worker batches
must arrive in sequence; an incomplete transfer fails the run and prevents
publication of a partial report.

The runtime closes child input after the final envelope, waits up to
``timeout_seconds``, and kills only the child it started if it does not finish.
Non-zero exits, broken pipes, missing runtimes, and timeouts fail pytest with a
diagnostic. A formatter, stream, or process failure before publication does
not publish newly staged report files or fall back to post-run replay.
Temporary formatter assets and staged output are removed when the session
closes.

After every formatter exits successfully, staged report files are published
and any existing destinations are held as backups until publication finishes.
If a publish step fails, the runtime attempts to restore the previous files. If
restoration fails, it preserves the affected backup and includes its path in
the pytest error. If removing an old backup fails after all new files have been
published, pytest reports the cleanup error with the backup path; the complete
new reports remain published and the old contents remain recoverable from that
backup.

The lower-level ``pytest_cuke_message_validated`` and
``pytest_cuke_message_batch`` hooks are available for plugins that need to
observe accepted events directly. A batch is partial transport evidence and
has a worker ID and per-worker sequence number; it is not a complete Cucumber
Messages stream. Formatter implementations should use ``FormatterRequest`` so
the shared runtime can normalize and manage that stream.
