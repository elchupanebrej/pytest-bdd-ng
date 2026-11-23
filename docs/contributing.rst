Contributing
============

This page documents the reproducible documentation environment used by
maintainers and CI. Feature pages are generated from the Gherkin files; all
other pages are maintained directly in ``docs/``.

Documentation environment
-------------------------

The documentation toolchain is the ``docs`` extra. It pins Sphinx and every
package Sphinx needs at build time. From the repository root, install exactly
that set into the development environment::

    make develop
    .env/bin/pip install -e ".[docs]"

For a throwaway clean environment, use ``uv``::

    uv venv /tmp/pytest-cuke-docs --python 3.13
    uv pip install --python /tmp/pytest-cuke-docs/bin/python -e ".[docs]"

The pinned Sphinx release supports Python 3.11 and newer; CI builds the
documentation with Python 3.14.

Build the documentation
-----------------------

Run the strict build from the repository root::

    .env/bin/sphinx-build -b html -W --keep-going docs docs/_build/html

or use ``make docs``, which installs the ``docs`` extra and runs the same
command. ``docs/Makefile`` carries the same strict flags::

    make -C docs html

The build fails with a non-zero status on any warning, including missing
includes, documents outside every toctree, broken local links and malformed
section structure. ``--keep-going`` reports every problem before exiting, so
one run names all offending files and lines.

Generated feature pages
-----------------------

``docs/features/features.rst`` and the Markdown feature fragments under
``docs/features/`` are produced from the Gherkin files under ``features/``.
The generator requires Pandoc 3.4, which CI pins; other releases emit
different RST. Regenerate them with the ``doc-gen`` extra::

    .env/bin/pip install -e ".[doc-gen]"
    .env/bin/python src/pytest_cuke/script/bdd_tree_to_rst.py features docs/features

The generator rewrites the tree and exits non-zero whenever it finds any
difference, including on a tree it just synchronized, so read its diff report
instead of its exit status. Do not hand-edit the generated fragments; update
the generator instead.

The ``Documentation drift`` workflow regenerates the pages into a temporary
tree, strips trailing whitespace, and fails when the result differs from
``docs/features``. Run the same check locally with the pinned Pandoc on
``PATH``::

    python -m pytest_cuke.script.docs_drift features docs/features

CI gate
-------

The ``doc-generation`` quality lane runs ``tox -e py314-doc-gen``. That
environment installs the ``test``, ``doc-gen`` and ``docs`` extras, runs
``tests/unit/docs/test_doc.py -m doc_gen``, and then runs the strict Sphinx
build. The lane is declared in ``config/env-matrix.yaml`` and selected by the
``quality`` matrix job in ``.github/workflows/main.yml``. A documentation build
warning fails that lane and therefore the aggregate proof. The separate
``Documentation drift`` workflow fails a branch whose checked-in pages no
longer match a fresh generation.
