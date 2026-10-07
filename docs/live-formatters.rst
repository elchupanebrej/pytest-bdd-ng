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

Import ``FormatterRequest`` and ``FormatterAsset`` from the public
``pytest_cuke`` package. A request names one formatter and describes its
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

   from pytest_cuke import FormatterRequest


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
