Cucumber Messages schema provenance
====================================

The bundled schemas correspond to the installed ``cucumber-messages``
distribution version ``28.0.0`` and upstream Cucumber Messages release
``v28.0.0``. The upstream tag resolves to immutable commit
``f5b1f30dc3ea234f44ea4cc6289726e7d8f2cbe0``. The vendored set contains only
the JSON files from that commit's ``jsonschema/`` directory, with filenames
normalized from ``.json`` to ``.schema.json``.

The ``cucumber-messages`` wheel does not publish its source schema release in
distribution metadata. The tool therefore keeps this association as an
explicit compatibility mapping and rejects any unrecognized distribution
version. Before adding a mapping for a newer contract package, compare its
generated message models with the candidate upstream release and review the
schema change.

The source tree and archive used by the tool are pinned to the same commit:
before downloading, the tool checks that ``v28.0.0`` still resolves to that
commit. A missing or moved tag fails with an actionable error.

.. code-block:: text

   https://github.com/cucumber/messages/tree/f5b1f30dc3ea234f44ea4cc6289726e7d8f2cbe0/jsonschema
   https://codeload.github.com/cucumber/messages/tar.gz/f5b1f30dc3ea234f44ea4cc6289726e7d8f2cbe0
