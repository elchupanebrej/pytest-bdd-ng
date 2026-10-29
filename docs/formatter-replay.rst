Standalone formatter replay
===========================

The ``cuke`` and ``pytest-cuke`` commands can render a saved Cucumber Messages
NDJSON stream without starting pytest or importing a test suite:

.. code-block:: console

   cuke replay messages.ndjson --formatter pretty=reports/pretty.txt
   pytest-cuke replay messages.ndjson \
      --formatter usage-json=reports/usage.json \
      --formatter summary=reports/summary.txt

The input and output paths are resolved from the current working directory.
Pass at least one ``--formatter NAME=DESTINATION`` selection. Repeat the option
to write multiple reports through the shared formatter catalog. Use
``--formatter NAME=-`` for a terminal formatter; only one formatter may write
to the terminal. The input path cannot also be used as an output destination.

The built-in selectors are ``pretty``, ``progress``, ``progress-bar``,
``snippets``, ``summary``, ``usage``, ``usage-json``, ``cucumber-json`` and
``cucumber-junit``. They use the same Node adapters as the corresponding live
formatters. Install Node.js and the formatter packages in the current working
directory before replay; the tested package versions are:

.. code-block:: console

   npm install @cucumber/cucumber@13.3.0 @cucumber/pretty-formatter@4.0.2
   cuke replay messages.ndjson --formatter summary=-

``pretty``, ``progress`` and ``progress-bar`` use
``@cucumber/pretty-formatter``; the remaining built-ins use
``@cucumber/cucumber``. File and piped progress-bar output uses readable
progress characters without cursor controls. ``snippets`` emits the official
Cucumber JavaScript suggestions for undefined steps; a fully defined stream
has no snippets. Replay returns zero when conversion succeeds, even if the
saved test run contains failed or undefined steps. Input validation or a
formatter/runtime error returns 2 and preserves existing file reports.

Formatter distributions register factories in the
``pytest_cuke.formatters`` entry-point group. The entry-point name is the value
used after ``--formatter``. A factory receives a public ``FormatterSelection``
and returns a ``FormatterRequest``:

.. code-block:: toml

   [project.entry-points."pytest_cuke.formatters"]
   html = "my_reporter:make_replay_request"

.. code-block:: python

   from pytest_cuke.formatter_api import FormatterRequest, FormatterSelection


   def make_replay_request(selection: FormatterSelection) -> FormatterRequest:
       return FormatterRequest(
           name=selection.name,
           command=("node", "formatter.mjs"),
           output_path=selection.destination,
           working_directory=selection.working_directory,
           required_executables=("node",),
           required_npm_packages=("@example/cucumber-formatter",),
       )

The selected factory and its runtime requirements are checked before any child
starts. Relative formatter working directories and destinations resolve from
the replay command's current directory. The child reads one canonical Messages
envelope per line on standard input. Report bytes written to standard output
are staged beside each destination and published only after every selected
formatter exits successfully. Standard error is forwarded to the command's
error stream. Formatter processes, temporary assets, timeouts, and multi-file
publication use the same runtime as live formatter plugins.

Every input envelope and the complete stream lifecycle are validated while
reading. Blank lines are ignored. JSON, schema, reference, and incomplete
stream errors identify the input and line or end-of-file location. A failed
input or formatter does not publish staged reports, and the source file is
never modified. The replay command does not collect tests, execute fixtures,
or import ``conftest.py``.
