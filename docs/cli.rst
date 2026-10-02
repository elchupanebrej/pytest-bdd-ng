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

The built-in command paths are ``validate features``, ``generate steps``, and
``convert allure``. These commands are reserved in this release and return a
non-zero exit status with an explicit not-implemented message.

Registering command extensions
------------------------------

An installed extension can register additional commands through the
``pytest_cuke.commands`` entry-point group. Each entry point loads a callable
that receives a ``CommandRegistry``. Its handler receives arguments after the
registered command path and returns the process exit code.

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
