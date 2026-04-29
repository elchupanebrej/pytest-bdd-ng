Feature Heading Validation
==========================

Purpose
-------

This note documents repository policy for parsed BDD heading titles in
``features/`` files.

Rules
-----

- Parsed ``Feature`` headings must have non-empty titles.
- Parsed ``Scenario`` and ``Scenario Outline`` headings must have non-empty
  titles.
- Whitespace-only titles are treated as empty.

Scope Boundary
--------------

Validation is based on parser-recognized headings only.
Keyword-like text in literal snippets or fenced blocks is not interpreted as
parsed BDD structure and is intentionally ignored.

Workflow
--------

- Run the validator directly:

  .. code-block:: bash

     uv run python \
       src/pytest_bdd/script/validate_feature_headings.py --root-path features

- Pre-commit hook ``validate-feature-headings`` runs the same validation before
  commit.
