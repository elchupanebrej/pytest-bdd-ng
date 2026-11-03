Generation exit status
======================

The standalone ``cuke generate steps`` command strictly adheres to standard
POSIX conventions for process exit status:

* **0** on success: returned when generation completes successfully, whether
  generating step definitions to standard output, writing updates to a target
  file, displaying preview differences (``--preview``), or finding that all
  step definitions are already present (unchanged).
* **2** on handled errors: returned when a generation request cannot be completed
  safely (e.g. invalid target Python syntax, missing target file, missing
  required ``--target`` when using ``--preview`` or ``--bind-only``), as well as
  on command-line argument parser errors (unknown flags, missing required
  ``--feature``).

Historical exit code 100 and the ``--exit-status`` option have been completely
retired in 3.0. Generation commands behave consistently with POSIX tools and
standard CLI expectations across all workflows.
