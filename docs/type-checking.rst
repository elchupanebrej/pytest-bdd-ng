Runtime type checking
=====================

Mypy is the blocking type checker for all Python files under ``src/pytest_cuke``.
The runtime-source scope is declared in ``pyproject.toml`` and applies to new
modules automatically. Tests, scripts, and documentation are checked by their
own quality gates.

Install the pinned checker and required typing support with the ``testtypes``
extra, then run the canonical local command:

.. code-block:: console

   uv run --extra testtypes python -m mypy --config-file pyproject.toml

To print the resolved checker, config, and source-scope identity before the
same gate, run the shared adapter locally:

.. code-block:: console

   uv run --extra testtypes python scripts/check_types.py

The ``testtypes`` extra pins Mypy 2.3.1, attrs 26.1.0, Pydantic 2.12.5 for
its framework plugin, and Tomli 2.2.1 for the Python 3.10 compatibility module.
Mypy's built-in attrs support checks attrs models, while
``types-PyYAML==6.0.12.20260906`` supplies the required PyYAML typing support.
The adapter verifies these exact framework and stub versions before checking.
The pre-commit hook, ``tox -e typecheck``, and the blocking CI job use the same
configuration and runtime-source scope. Their adapter prints the resolved
checker, config hash, and source-scope identity before checking.

Keep suppressions attached to the specific diagnostic and explain them in
English. Do not disable errors for a whole module tree or move runtime files
outside the configured scope. When a dependency lacks typing information,
prefer a small typed boundary in pytest-cuke; use a narrow error-specific
suppression only when no typed boundary is practical.

Pyright is an advisory local check and does not replace the blocking Mypy gate:

.. code-block:: console

   uv run --extra pyright pyright

Ty output is monitor-only. It is useful for tracking future type coverage, but
it is not a pass condition and cannot substitute for Mypy.
