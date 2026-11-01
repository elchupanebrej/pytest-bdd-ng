Latest Cucumber Messages schema
===============================

pytest-cuke uses one current Messages protocol. The runtime dependency is pinned
at ``cucumber-messages==34.2.0``, the latest published official Python binding.
Its JSON schemas are byte-identical to the latest upstream release, ``v34.2.1``;
the patch does not change the Messages JSON schemas. The producer advertises protocol
``34.2.1`` and validates against that release's schemas. There is no legacy
protocol profile.

Schema provenance
-----------------

The schema source is the immutable upstream commit
``e5769e89dd8dd7aa7e8c8163023f38bad539e3aa`` from
https://github.com/cucumber/messages/tree/v34.2.1/jsonschema/src.
The 28 individual schemas under ``jsonschema/src`` are vendored without content
changes. Root-level package manifests and the combined ``messages.schema.json``
are not individual runtime schema assets.

The published Python binding's upstream tag, ``v34.2.0``, resolves to
``073f951ce615149a1532185fbae013ad908a918e``. The integration audit compares all
28 schema files from both immutable commits by SHA256 before selecting the
latest schema patch. Python package version and protocol/schema version are
recorded separately; no unpublished ``cucumber-messages==34.2.1`` package is
claimed.

Reproduce the schema check in a source checkout::

    cuke sync messages schemas --schema-path src/pytest_cuke/model/message_schemas --source-dir tests/fixtures/message-schemas-v34-2-1 --check

Omit ``--source-dir`` to verify the pinned upstream tag and fetch its immutable
archive. A check reports changed, missing, and extra files without modifying the
target. A sync replaces the dedicated schema directory only after validating the
complete selected source. Invalid JSON, unsafe archive paths, oversized inputs,
and a changed upstream tag remain errors.
