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

Run summary diagnostics
-----------------------

A failed pytest run includes ``testRunFinished.message`` and an
``exception`` with type ``PytestExitCode`` and the numeric exit status.
Consumers can inspect this terminal envelope without parsing terminal output.
Successful runs omit these diagnostic fields. Messages validation failures
instead identify ``MessageValidationError`` in the terminal envelope.

Step types, definitions and match arguments
------------------------------------------

``pickle.steps[].type`` reflects the parsed step's Context, Action, Outcome or
Unknown type. Scenario Outline expansion and Background steps retain their
parsed type. Steps without a recognized type use Unknown.

Within each reporter session or xdist worker, a ``stepDefinition`` id is
published once. Each test case continues to reference that definition's id;
reusing a definition in another scenario does not publish another envelope
with the same id. Definitions with distinct ids remain distinct, even if their
patterns are equal.

For an unambiguous parameterized match, ``testCase.testSteps`` includes the
official ``stepMatchArgumentsLists`` field. Cucumber Expression captures retain
their recursive groups, source offsets and values. Explicit anonymous group
names become ``parameterTypeName``. Other parsers retain the legacy fallback:
parsed parameter names and string values, with the first matching text offset
when available. Definition-level converters are not run for this projection.
These protocol fields accompany the existing step-binding attachments.
Ambiguous matches and unsuccessful diagnostic extraction omit the argument
list; reporting does not select a different step or change execution policy.
