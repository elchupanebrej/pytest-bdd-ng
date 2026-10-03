Custom parser adapters
======================

Parser extensions written for the historical parser protocol can be registered
explicitly while pytest-cuke continues to expose its native ``Feature`` model
to collection, execution, and reporting. The adapter does not inspect parser
signatures or retry a failed call.

Register the historical contract from a parser hook:

.. code-block:: python

   from pathlib import Path

   from pytest_cuke.compatibility.parser import ParsedFeature
   from pytest_cuke.parser import ParserRegistration

   class LegacyFeatureParser:
       id_generator = None

       def parse(self, config, path: Path, uri: str, *args, **kwargs) -> ParsedFeature:
           # Read and parse the source, then return a messages.GherkinDocument.
           ...

   def pytest_cuke_get_parser(config, mimetype):
       if mimetype == "application/x-example-feature":
           return ParserRegistration.legacy(LegacyFeatureParser)
       return None

The result must provide ``gherkin_document``, ``filename``, and decoded text in
``raw_data``. ``gherkin_document`` must serialize as the installed Cucumber
``messages.GherkinDocument`` shape. pytest-cuke validates and converts that
document into its immutable ``Feature`` tree, preserving the parser's feature,
scenario, example, step, tag, location, and ID data. The locator-provided URI
remains the source URI used by collection and reports. Invalid documents include
the parser identity and source path in a collection diagnostic, with guidance to
register through ``ParserRegistration.legacy``.

The legacy call receives ``config``, the feature path, URI, positional values
from ``parse_args.args``, and keyword values from ``parse_args.kwargs``. The
locator's encoding is the default ``encoding`` keyword; an explicit
``parse_args.kwargs["encoding"]`` overrides it. pytest-cuke attaches the current
run's ``IdGenerator`` to the parser before invoking it. Exceptions from parser
code, including ``TypeError``, pass through unchanged.

``ParserRegistration`` is imported from ``pytest_cuke.parser``;
``ParsedFeature`` is imported from ``pytest_cuke.compatibility.parser``. The
root ``pytest_cuke`` facade remains limited to its seven documented names.

Provider lifetime is explicit:

* A parser class is instantiated once for each pytest config and reused for
  features collected by that run.
* A zero-argument factory is called once for each pytest config and its result is
  reused for that run.
* A parser instance is used exactly as supplied. It is caller-owned and shared
  wherever that registration instance is reused; use a class or factory when
  runs need independent mutable parser state.

``ParserRegistration.native(provider)`` opts a parser into the current native
``parse(path, uri, encoding, **kwargs) -> Feature`` contract. Native parser
behavior does not change when using that descriptor. Legacy adapters run through
the serial collection path, including when the batch collector is enabled, so
their parser objects and ID generators stay in the pytest process.

The runnable extension project is in ``examples/custom-parser-adapter``.
