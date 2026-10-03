# Custom parser adapter

This runnable extension uses the historical parser signature while pytest-cuke
collects its result as the native frozen `Feature` model. The registration is
explicit, so the same hook can coexist with native parsers without signature
inspection or `TypeError` retries.

`ParserRegistration.legacy(LegacyFeatureParser)` creates one parser instance for
each pytest config and reuses it for features in that run. A parser class or
zero-argument factory is therefore appropriate for mutable run-local state. An
explicit parser instance is used as supplied; use a factory when separate pytest
runs need separate instance state. `ParserRegistration.native(provider)` uses
the same provider lifetimes but keeps the native `parse(path, uri, encoding,
**kwargs) -> Feature` contract.

The adapter passes the pytest config, source path, URI, positional parser args,
and keyword parser args to the old `parse(config, path, uri, *args, **kwargs)`
method. The locator encoding supplies the default `encoding` keyword, and an
explicit `parse_args.kwargs["encoding"]` overrides it. The configured
`IdGenerator` is attached to the parser before each call.

Run the example from this directory after installing the checkout:

```sh
python -m pip install -e "../.."
python -m pytest --cuke-autoload
```

The parser writes its observed inputs to `parser-invocations.json`. Set
`PYTEST_CUKE_INVOCATION_LOG` to choose another log path. The sample has two
diagnostic modes for consumer tests: `PYTEST_CUKE_LEGACY_MODE=malformed` returns
an invalid result, while `PYTEST_CUKE_LEGACY_MODE=type-error` raises an internal
`TypeError` that collection reports without wrapping.

Import `ParserRegistration` from `pytest_cuke.parser` and `ParsedFeature` from
`pytest_cuke.compatibility.parser`. These compatibility names stay outside the
seven-name root `pytest_cuke` facade.
