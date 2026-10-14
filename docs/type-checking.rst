Runtime type checking
=====================

Mypy is the blocking type checker for all Python files under ``src/pytest_cuke``.
The runtime-source scope is declared in ``pyproject.toml`` and applies to new
modules automatically. Tests, scripts, and documentation are checked by their
own quality gates.

Installed consumer typing
--------------------------

The wheel and source distribution include the PEP 561 marker at
``pytest_cuke/py.typed``. Type checkers can therefore use the annotations from
an installed package instead of treating ``pytest_cuke`` as untyped. The
supported typed entry points are the seven-name ``pytest_cuke`` facade and its
``pytest_cuke.parsers`` facade, including decorators, parsers, and scenario
bindings. For example:

.. code-block:: python

   from pytest_cuke import given, parsers, scenario

   @given(parsers.parse("I have {count:d} items"), target_fixture="count")
   def set_count(count: int) -> int:
       return count

   @scenario("features/inventory.feature", "Items are counted")
   def test_items_are_counted() -> None: ...

Mypy 2.3.1 is the blocking primary checker. Pyright is an advisory local
check; the project does not promise that it reports an identical diagnostic
set. The base facade imports do not require optional integrations such as
Allure; code that imports optional integration modules must install their
corresponding extra. The installed-consumer contract checks wheel and sdist
installations without a checkout path or local stubs, and requires no
``type: ignore`` for the public example above. If a downstream integration
needs a suppression, scope it to the specific checker error and explain why.
The pinned-Mypy consumer scenarios run in the CPython 3.14
``py314-pytestlatest-mypy`` lane, where the checker toolchain is supported;
base-install facade and PEP 561 metadata checks remain part of the runtime
matrix, including PyPy.

Install the pinned checker and required typing support with the ``testtypes``
extra, then run the canonical local command:

.. code-block:: console

   uv run --extra testtypes python -m mypy --config-file pyproject.toml

To print the resolved checker, config, and source-scope identity before the
same gate, run the shared adapter locally:

.. code-block:: console

   uv run --extra testtypes python scripts/check_types.py

The ``testtypes`` extra pins Mypy 2.3.1, attrs 26.1.0, Pydantic 2.12.5 for
its framework plugin. The package supports Python 3.11 and newer, so the
compatibility module uses the standard-library TOML parser.
Mypy's built-in attrs support checks attrs models, while
``types-PyYAML==6.0.12.20260906`` supplies the required PyYAML typing support.
The adapter verifies these exact framework and stub versions before checking.
The pre-commit hook, ``tox -e typecheck``, and the blocking CI job use the same
configuration and runtime-source scope. Their adapter prints the resolved
checker, config hash, and source-scope identity before checking.
The tox environment also runs a focused Messages check over the extension,
converter, stream-validation, and reporter modules with that same Mypy
configuration.

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
