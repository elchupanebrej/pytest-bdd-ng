Documentation Generation Notes
==============================

Scope Boundary for ``docs/features/features.rst``
-------------------------------------------------

``docs/features/features.rst`` is reserved for feature-file-driven generated
navigation and short user-facing context.

This file must not contain:

- runtime implementation internals;
- migration/change-history notes;
- conversion process policy details.

Conversion Traceability
-----------------------

Conversion traceability is documented in:

* ``specs/002-e2e-test-conversion/conversion-parity-audit.md``

Validation Policy
-----------------

Markdown lint and pre-commit checks must pass for converted feature
documentation before commit.

Related Internal Docs
---------------------

Runtime execution-context and compatibility notes are documented in:

* ``docs/internal/execution-context-and-api-compatibility.rst``
