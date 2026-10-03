Cucumber Messages schema provenance
====================================

The bundled schemas correspond to the installed ``cuke-messages`` contract
distribution version ``0.1.0`` and upstream Cucumber Messages release
``v24.0.1``. The upstream tag resolves to immutable commit
``30ecba04a90613d0f1fa50c9ab0c2bb1fc25d22d``. The vendored set contains only
the JSON files from that commit's ``jsonschema/`` directory, with filenames
normalized from ``.json`` to ``.schema.json``.

The ``cuke-messages`` wheel does not publish its source schema release in
distribution metadata. The tool therefore keeps this association as an
explicit compatibility mapping and rejects any unrecognized distribution
version. Before adding a mapping for a newer contract package, compare its
generated message models with the candidate upstream release and review the
schema change.

The source tree and archive used by the tool are pinned to the same commit:
before downloading, the tool checks that ``v24.0.1`` still resolves to that
commit. A missing or moved tag fails with an actionable error.

.. code-block:: text

   https://github.com/cucumber/messages/tree/30ecba04a90613d0f1fa50c9ab0c2bb1fc25d22d/jsonschema
   https://codeload.github.com/cucumber/messages/tar.gz/30ecba04a90613d0f1fa50c9ab0c2bb1fc25d22d
