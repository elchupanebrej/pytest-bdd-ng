Cucumber Messages schema provenance
====================================

pytest-cuke targets the latest Cucumber Messages protocol, ``34.2.1``.
The latest official Python binding is ``cucumber-messages==34.2.0``.
The ``v34.2.1`` release notes list a Java dependency fix. Its individual
JSON schemas are byte-identical to ``v34.2.0``; the tagged Python source is
not assumed identical to the published Python wheel. The binding and
schema patch versions therefore differ without defining a legacy profile.

The schema release is pinned to immutable upstream commit
``e5769e89dd8dd7aa7e8c8163023f38bad539e3aa``. The vendored set contains
28 individual schemas from ``jsonschema/src/``, with filenames normalized to
``.schema.json``. Package metadata and the monolithic bundle are not included
as individual runtime schemas.

The wheel does not declare its source schema release in package metadata.
The sync command records the verified binding-to-schema association explicitly
and rejects unrecognized binding versions. Updating the pin requires comparing
models and schemas, regenerating assets and validating real emitted streams.
Before downloading an archive, the tool verifies the release tag still resolves
to the pinned commit; a missing or moved tag fails the check.

.. code-block:: text

   https://github.com/cucumber/messages/tree/e5769e89dd8dd7aa7e8c8163023f38bad539e3aa/jsonschema/src
   https://codeload.github.com/cucumber/messages/tar.gz/e5769e89dd8dd7aa7e8c8163023f38bad539e3aa

Undefined-step suggestions
--------------------------

A failed step lookup emits an official ``suggestion`` envelope linked to the
pickle step. Its Python snippet uses the public ``pytest_cuke`` decorators.
Unknown parameter types also retain their separate
``undefinedParameterType`` diagnostic. Successful lookups emit neither message.

Source navigation
-----------------

For an unchanged parsed feature, ``gherkinDocument`` retains the parser's
original source metadata, including columns, keyword types, comments and
DocString delimiters. Reading or mutating an observation document does not
modify the feature model. Programmatic features and structurally edited models
use the model projection; unavailable source positions are not invented.
Outline pickle locations point to the originating Examples row when that
position is available. Pickles retain the feature language and inherited tags.

Parser pattern families
-----------------------

Explicit literal, ``parse``, ``cfparse`` and Python regex parsers publish
``REGULAR_EXPRESSION`` patterns using Python regex syntax. Literal patterns
are escaped, compiled parser patterns retain their capture structure, and
matching flags are encoded in the expression. Actual Cucumber Expressions
retain ``CUCUMBER_EXPRESSION``. IDE step-binding attachments keep the original
parser pattern for display independently of this standard wire projection.
Custom parsers remain responsible for their declared expression family.
For the hybrid heuristic parser, the standard pattern is descriptive metadata
and does not promise equivalent recognition of every runtime fallback language.
Its matching priority and fixture-based parameter registries are preserved.
Use an explicit parser when an exact standard pattern is required.

Run summary diagnostics
-----------------------

A failed pytest run includes ``testRunFinished.message`` and an
``exception`` with type ``PytestExitCode`` and the numeric exit status.
Consumers can inspect this terminal envelope without parsing terminal output.
Successful runs omit these diagnostic fields. Accumulated reporting failures
(such as rejected schema payloads or failed sinks) identify
``MessageReportingError``, even when the original pytest exit status was zero.
New terminal-stream validation errors identify ``MessageValidationError``.
A reporting failure changes the run result, while preserving the existing
classification of the individual step.

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
Parser arguments are captured once and projected independently into protocol
groups and JSON-safe step-binding attachments. The protocol keeps the legacy
string representation of raw values, including tuples; the IDE attachment
keeps its JSON representation. Reporting adds no parser calls relative to the
existing attachment consumer.
These protocol fields accompany the existing step-binding attachments.
Ambiguous matches and unsuccessful diagnostic extraction omit the argument
list; reporting does not select a different step or change execution policy.

Extension matcher diagnostics
------------------------------

Structured unknown-parameter diagnostics take precedence. When an extension
matcher raises a lookup error with ``Undefined parameter type 'name'`` or
``Undefined parameter type {name}`` in its exception chain, the Messages reader
receives ``undefinedParameterType`` with that name and the current step text as
its expression. Ordinary matcher errors and exceptions from step bodies do not
trigger this text fallback.

Attachment correlation and lifecycle
------------------------------------

The attachment fixture accepts explicit ``test_run_started_id`` and
``test_run_hook_started_id`` correlations and emits a timestamp. Run-hook
start messages identify their worker. Correlations must refer to an active
lifecycle scope: attaching to an already completed hook fails validation and
marks the run unsuccessful. External attachments obey the same correlation
checks as inline attachments. Suggestion IDs must be unique and reference a
declared pickle step.

Invalid attachment source types
-------------------------------

An attachment source must declare a supported Gherkin media type. The
attachment API validates that type before publishing the message; an invalid
type raises ``ValueError`` in its calling step. The step is reported as
``FAILED``, no invalid attachment is published, and the run finishes
unsuccessfully. Transport and formatter failures retain their separate
run-level reporting diagnostics.

Feature model serialization
---------------------------

Parser source projections are internal observations. They are excluded from
``as_dict`` and JSON model serialization, and input dictionaries cannot replace
them. Serialized Feature models retain the existing public shape and rebuild
Messages documents from the model when original parser metadata is unavailable.

External Examples source coordinates
-----------------------------------

External CSV/JSON rows are runtime data, rather than physical Gherkin source
rows. Generated table nodes with no original feature location are excluded
from the source document. Remaining nodes keep their original mapped lines.
The expanded runtime model and scenario identities retain the external rows.
Standard Pickle AST references include only actual source nodes; external
row IDs remain runtime identities and do not acquire invented source locations.
This keeps source lineage valid for downstream formatters.

Unknown external-row positions are not encoded as ``line=0``: that value is
invalid in the current protocol. External-outline Pickles can therefore have
only their Scenario AST ID, while inline outlines retain their source row ID.
Consumers should use Pickle identity and the external-source provenance when
identifying external rows, rather than requiring a second source AST node.

Source AST identifier scope
---------------------------

Wire AST identifiers are scoped by the Gherkin document URI. Pickle scenario,
step and tag references use the same scope, so separate files cannot collide
when their parsers reuse local numeric identifiers. Internal Feature model
identifiers and runtime scenario identities are unchanged. Consumers should
correlate message sources using the identifiers in the protocol objects.
