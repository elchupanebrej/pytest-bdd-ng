Run-aware lifecycle hooks
=========================

Consumer plugins can inspect the active feature, scenario, current step, and
previous step through the session-owned ``RunContext`` passed as the ``run``
hook argument. The canonical runnable consumer project is
``examples/run-aware-hooks``.

The example's ``conftest.py`` loads its hook plugin through pytest's ordinary
plugin discovery:

.. literalinclude:: ../examples/run-aware-hooks/conftest.py
   :language: python

The hook plugin reads the public run accessors directly. The previous step is
``None`` for a scenario's first step and refers to the immediately preceding
step for later steps. Lifecycle observers see the runtime transition before
the hook executes; for example, ``pytest_cuke_before_step`` observes
``stage == "step-running"`` and ``pytest_cuke_after_scenario`` observes the
``finished`` stage.

Hook implementations may declare a supported subset of the hook arguments.
This example uses the request and run pair for scenario setup, reads step
context from ``run``, and shows run-only implementations for after-step and
after-scenario hooks. It also calls the public ``attach`` fixture from a step;
the consumer's ``pytest_cuke_attach`` hook receives the active run context and
the attachment's body, media type, and file name:

.. literalinclude:: ../examples/run-aware-hooks/run_aware_plugin.py
   :language: python

Run the example from its directory after installing the project dependencies:

.. code-block:: console

   python -m pip install -r requirements.txt
   npm install --no-save --no-package-lock "@cucumber/cucumber@13.3.0"
   python -m pytest --cuke-autoload --cuke-features-dir=features --cuke-summary

The plugin records hook order, transition state, step function inputs, and the
attachment event in ``run-aware-observations.jsonl``. Its matcher, caller, and
dispatcher return ``None`` to use pytest-cuke's default implementations. The
E2E suite executes this checked-in directory from an installed consumer
project.

Collection read hooks
---------------------

Source observers do not need a Messages reporter. During scenario resolution,
pytest-cuke calls these hooks in order:

* ``pytest_cuke_source_read(config, gherkin_document, source)`` receives the
  original source text and URI as an official ``cucumber_messages.Source``.
  Parsers that do not retain source text omit this event.
* ``pytest_cuke_feature_read(config, gherkin_document)`` receives an official
  ``cucumber_messages.GherkinDocument`` for the parsed feature.
* ``pytest_cuke_pickle_read(config, gherkin_document, pickle)`` receives each
  official ``cucumber_messages.Pickle`` after expanding Scenario Outline rows
  and before applying the locator's scenario filter.

The document and pickle are protocol projections of pytest-cuke's immutable
models; changing them does not change collection or execution. A source may be
resolved more than once when consumers bind it through separate locators.
Observers that aggregate by source should use the URI to identify the source.
The document is projected once for each feature resolution and shared by its
source, feature and pickle callbacks. No protocol projection is created when
none of these read hooks has observers.

For plugins migrated from pytest-bdd, rename the ``pytest_bdd_`` prefix to
``pytest_cuke_`` for these hooks. Their ``gherkin_document``, ``source`` and
``pickle`` argument names and official Messages payload types are preserved.
These hooks observe collection inputs; the run-aware hooks above observe live
execution state.

Attachment source metadata and links
-------------------------------------

The ``attach`` fixture accepts optional keyword-only source metadata and a URL:

.. code-block:: python

   def publish_evidence(attach):
       attach(
           "inspection result",
           media_type="text/plain",
           source_data="Feature: Evidence",
           source_media_type="text/x.cucumber.gherkin+plain",
           source_uri="file:evidence.feature",
       )
       attach(
           "external evidence",
           media_type="text/plain",
           url="https://example.com/evidence.txt",
           as_external=True,
       )

A complete ``source_data``, ``source_media_type`` and ``source_uri`` triple
populates ``Attachment.source``. An incomplete triple leaves ``source`` absent.
The Messages v28 source media types are ``text/x.cucumber.gherkin+plain`` and
``text/x.cucumber.gherkin+markdown``. Other values are rejected by the existing
Messages validation gate; for example, ``text/plain`` is an attachment media
type but is not a valid source media type in that protocol.

``url`` populates ``Attachment.url`` and preserves the supplied body.
``as_external`` is accepted for migration compatibility and is visible to
attachment observers. It does not change the envelope type or upload the body.
The URL is retained with either value of ``as_external``.

``pytest_cuke_attach`` observers may receive ``source_data``,
``source_media_type``, ``source_uri``, ``url`` and ``as_external`` in addition to
the existing arguments. As with other pytest hooks, declare only the arguments
needed by the observer. Text, bytes, streams and positional ``media_type`` and
``file_name`` arguments retain their existing behavior.

Tag conversion supports both current models and official protocol payloads;
see :doc:`tag-conversion-protocol`.
Tag and mark hook expression languages are described in
:doc:`tag-expression-contract`.
